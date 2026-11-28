# -*- coding: utf-8 -*-
"""
Migrador Independiente de Datos Históricos HIDROPAUTE / CELEC (Proceso V2 -> Formato Moderno RSA).

Ubicado fuera de `procesamiento/` (`hidropaute/`) y reutilizando directamente las librerías
consolidadas de `procesamiento/src/librerias/`:
  - metodos_gestion (obtener_directorios, parametros_estaciones, obtencion_hora)
  - rsa_io (lectura_archivo, escritura_archivo)
  - rsa_procesamiento (reconstruir_eventos_dia)

Opera EXCLUSIVAMENTE dentro de la carpeta destino de HIDROPAUTE (ej. C:\\DIA\\HIDROPAUTE\\DIA\\)
sin modificar jamás el directorio principal C:\\DIA\\.

Dos pestañas:
  1. Estandarizar HIDROPAUTE preliminar (2003-2010):
       Sanea cabeceras heredadas y tokens cortos de 4 letras (AREN -> AREN11000000) y delega
       a `reconstruir_eventos_dia(..., normalizar_4_digitos=True, regenerar_consolidado_dia=True)`.
  2. Convertir Proceso V2 (Celec 2011-2016: .sis / .fas / .rsa):
       Decodifica los binarios .sis (16 canales x 64 Hz) a mseed/eventos/*.mseed, organiza
       dia/, fastHypo/, _estaciones.csv y AAAAMMDD000000.csv en HIDROPAUTE\\DIA y delega el
       cierre oficial del día (_aux.csv, _cat, _rep, _res, .xml) a `reconstruir_eventos_dia()`.
"""

import os
import re
import shutil
import struct
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
from obspy import Stream, Trace, UTCDateTime
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


# ---------------------------------------------------------------------------
# Conexión directa a las librerías existentes de procesamiento/src/librerias
# ---------------------------------------------------------------------------
RUTA_ESTE = Path(__file__).resolve()
RUTA_REPO = RUTA_ESTE.parent.parent
RUTA_PROC_LIBS = str(RUTA_REPO / "procesamiento" / "src" / "librerias")
RUTA_PROC_DATOS = str(RUTA_REPO / "procesamiento" / "datos")

if RUTA_PROC_LIBS not in sys.path:
    sys.path.insert(0, RUTA_PROC_LIBS)

from metodos_gestion import obtener_directorios, obtencion_hora, parametros_estaciones
from rsa_io import escritura_archivo, lectura_archivo
from rsa_procesamiento import reconstruir_eventos_dia


MARCA_TRAMA_SIS = b"\x02\x20\x02\x00\x40\x00"


# ===========================================================================
# FUNCIONES DE TRANSFORMACIÓN (REUTILIZABLES Y TESTEABLES)
# ===========================================================================
def normalizar_nombre_sis_4d(nombre_archivo: str) -> str:
    """
    Normaliza cualquier nombre .sis/.fas antiguo (110107051050.sis, 050106_211940.sis,
    20110107_051050.sis) al formato estándar de 4 dígitos con guion bajo:
      AAAAMMDD_HHMMSS.<ext>
    """
    p = Path(str(nombre_archivo).strip())
    ext = p.suffix.lower() or ".sis"
    digs = re.sub(r"\D", "", p.stem)
    if len(digs) == 12:
        digs = "20" + digs
    if len(digs) == 14:
        return f"{digs[:8]}_{digs[8:14]}{ext}"
    return p.name


def extraer_fecha_desde_nombre_sis(nombre_archivo: str):
    """Devuelve (YYYY, MM, DD, HH, mm, ss) desde un nombre .sis/.fas o None."""
    norm = normalizar_nombre_sis_4d(nombre_archivo)
    m = re.match(r"^(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})\.", norm)
    if not m:
        return None
    return tuple(int(g) for g in m.groups())


def decodificar_sis_a_mseed(
    ruta_sis: str,
    dir_eventos: str,
    parametros: dict,
    sobrescribir: bool = False,
) -> dict:
    """
    Decodifica un archivo binario `.sis` de Proceso V2 (PCI6034E / VERSION 2, 16 canales
    a 64 Hz, enteros int16 little-endian) y escribe un archivo MiniSEED por cada estación
    activa en `dir_eventos` con nombre `<COD>_AAAAMMDD_HHMMSS.mseed` (STEIM1, reclen=512).

    Retorna:
      {'estaciones': [cod1, ...], 'mseed_creados': int, 'duracion_s': float}
    """
    res = {'estaciones': [], 'mseed_creados': 0, 'duracion_s': 0.0}
    if not os.path.isfile(ruta_sis):
        return res

    raw = Path(ruta_sis).read_bytes()
    idx_primera = raw.find(MARCA_TRAMA_SIS)
    if idx_primera < 0:
        return res

    # 1) Extraer códigos de estación de 4 caracteres desde las etiquetas b'\x08\x00' de cabecera
    mapa_cod_validos = set(parametros.get('CODIGO', []))
    codigos_canales = []
    pos = 0
    while pos + 4 < idx_primera:
        if raw[pos:pos + 2] == b"\x08\x00":
            ln = struct.unpack("<H", raw[pos + 2:pos + 4])[0]
            if pos + 4 + ln <= idx_primera:
                texto = raw[pos + 4:pos + 4 + ln].decode("latin-1", errors="ignore").strip()
                if len(texto) == 4 and (texto in mapa_cod_validos or texto == "____"):
                    codigos_canales.append(texto)
                    if len(codigos_canales) >= 16:
                        break
                pos += 4 + ln
                continue
        pos += 1

    # 2) Determinar fecha/hora exacta de inicio del archivo .sis
    fecha_tupla = extraer_fecha_desde_nombre_sis(os.path.basename(ruta_sis))
    if fecha_tupla is None:
        return res
    anio, mes, dia, hh, mm, ss = fecha_tupla
    t_inicio = UTCDateTime(anio, mes, dia, hh, mm, ss)

    # Verificar si justo antes de la primera trama hay segundo exacto del día (b'\x08\x00\x05\x00<5d>')
    ventana_prev = raw[max(0, idx_primera - 16):idx_primera]
    m_seg = re.search(rb"\x08\x00\x05\x00(\d{5})", ventana_prev)
    if m_seg:
        try:
            seg_dia = int(m_seg.group(1).decode("ascii"))
            if 0 <= seg_dia < 86400:
                t_inicio = UTCDateTime(anio, mes, dia, 0, 0, 0) + seg_dia
        except Exception:
            pass

    # 3) Detectar paso de trama automáticamente (2068 bytes o 2077 bytes)
    idx_segunda = raw.find(MARCA_TRAMA_SIS, idx_primera + 20)
    paso_trama = (idx_segunda - idx_primera) if idx_segunda > idx_primera else 2068
    if paso_trama not in (2068, 2077):
        paso_trama = 2068

    n_segs = (len(raw) - idx_primera) // paso_trama
    if n_segs <= 0:
        return res

    # 4) Demultiplexar los 16 canales x 64 muestras/s
    datos_canales = [np.empty(n_segs * 64, dtype=np.int32) for _ in range(16)]
    for s_i in range(n_segs):
        off = idx_primera + s_i * paso_trama + 20
        bloque = raw[off:off + 2048]
        if len(bloque) < 2048:
            n_segs = s_i
            break
        arr = np.frombuffer(bloque, dtype="<i2").reshape(64, 16)
        i0 = s_i * 64
        i1 = i0 + 64
        for ch in range(16):
            datos_canales[ch][i0:i1] = arr[:, ch]

    if n_segs <= 0:
        return res

    res['duracion_s'] = float(n_segs)
    os.makedirs(dir_eventos, exist_ok=True)
    sufijo_ms = f"_{anio:04d}{mes:02d}{dia:02d}_{hh:02d}{mm:02d}{ss:02d}.mseed"

    for ch, cod in enumerate(codigos_canales):
        if not cod or cod == "____" or cod not in mapa_cod_validos:
            continue
        res['estaciones'].append(cod)
        ruta_ms = os.path.join(dir_eventos, cod + sufijo_ms)
        if not sobrescribir and os.path.isfile(ruta_ms):
            continue
        muestras = datos_canales[ch][:n_segs * 64]
        tr = Trace(data=muestras)
        tr.stats.network = "RS"
        tr.stats.station = cod
        tr.stats.channel = "EHZ"
        tr.stats.sampling_rate = 64.0
        tr.stats.starttime = t_inicio
        Stream([tr]).write(ruta_ms, format="MSEED", encoding="STEIM1", reclen=512)
        res['mseed_creados'] += 1

    return res


def sanear_csv_preliminar_hidropaute(ruta_csv: str, parametros: dict) -> int:
    """
    Sanea un archivo `AAMMDD000000.csv` o `AAAAMMDD000000.csv` del formato preliminar
    de HIDROPAUTE (2003-2010):
      - Elimina la fila cabecera antigua ('0;Fecha, Hora (UTC);Evento;...').
      - Expande tokens cortos de 4 letras (ej. 'AREN') a tokens canónicos de 12 caracteres
        'EEEECBFFIISS' (ej. 'AREN11000000', pos5='1' porque en el CSV preliminar solo se
        listaban las estaciones activas del evento).
    Retorna el número de tokens expandidos.
    """
    if not ruta_csv or not os.path.isfile(ruta_csv):
        return 0
    filas = lectura_archivo(ruta_csv) or []
    if not filas:
        return 0

    codigos = parametros.get('CODIGO', [])
    componentes = parametros.get('COMPONENTE', [])
    total_est = min(101, len(codigos))

    filas_limpias = []
    tokens_expandidos = 0
    modificado = False

    for fila in filas:
        if not fila or len(fila) < 3:
            continue
        # Saltar fila cabecera antigua
        if str(fila[0]).strip() == '0' and 'fecha' in str(fila[1]).lower():
            modificado = True
            continue

        nueva = list(fila)
        if len(nueva) < 3 + total_est:
            nueva.extend(['-'] * (3 + total_est - len(nueva)))

        for idx_e in range(total_est):
            tok = str(nueva[idx_e + 3]).strip()
            if tok in ('', '-'):
                nueva[idx_e + 3] = '-'
            elif len(tok) == 4 and tok == codigos[idx_e]:
                canal = str(componentes[idx_e]).strip() or '1'
                nueva[idx_e + 3] = f"{tok}{canal}1000000"
                tokens_expandidos += 1
                modificado = True

        filas_limpias.append(nueva)

    if modificado:
        escritura_archivo(ruta_csv, filas_limpias)
    return tokens_expandidos


def convertir_anio_celec_v2(
    dir_anio_celec: str,
    dir_destino_dia: str,
    parametros: dict,
    sobrescribir_mseed: bool = False,
    progreso_cb=None,
    cancelar_cb=None,
) -> dict:
    """
    Convierte una carpeta anual de Proceso V2 (`Celec 2011` .. `Celec 2016`) hacia
    `dir_destino_dia` (ej. `C:\\DIA\\HIDROPAUTE\\DIA\\`) en formato moderno de 4 dígitos,
    reutilizando `reconstruir_eventos_dia()` de `procesamiento/src/librerias/rsa_procesamiento.py`.
    """
    res = {
        'dias_procesados': 0,
        'sis_convertidos': 0,
        'mseed_creados': 0,
        'fas_copiados': 0,
        'rsa_copiados': 0,
        'errores': 0,
        'cancelado': False,
    }
    raiz_dest = str(dir_destino_dia).rstrip("/\\") + "/"
    mapa_cod_idx = {c: i for i, c in enumerate(parametros.get('CODIGO', []))}
    componentes = parametros.get('COMPONENTE', [])
    total_est = min(101, len(parametros.get('CODIGO', [])))

    # 1) Recolectar todos los .sis, .fas, .rsa y _estaciones.csv del año Celec
    #    agrupados por día (YYYY, MM, DD)
    eventos_por_dia = {}   # (Y, M, D) -> {'sis': {norm: path}, 'fas': {norm: path}, 'rsa': [path], 'est_csv': path}

    def _asegurar_dia(ymd):
        if ymd not in eventos_por_dia:
            eventos_por_dia[ymd] = {'sis': {}, 'fas': {}, 'rsa': [], 'est_csv': None}
        return eventos_por_dia[ymd]

    m_anio = re.search(r"(20\d{2})", os.path.basename(dir_anio_celec))
    anio_carpeta = int(m_anio.group(1)) if m_anio else None

    for r_act, _ds, fs in os.walk(dir_anio_celec):
        for f in fs:
            fl = f.lower()
            ruta_f = os.path.join(r_act, f)
            if fl.endswith(".sis"):
                ft = extraer_fecha_desde_nombre_sis(f)
                if ft:
                    ymd = ft[:3]
                    norm = normalizar_nombre_sis_4d(f)
                    _asegurar_dia(ymd)['sis'][norm] = ruta_f
            elif fl.endswith(".fas"):
                ft = extraer_fecha_desde_nombre_sis(f)
                if ft:
                    ymd = ft[:3]
                    norm = normalizar_nombre_sis_4d(f)
                    _asegurar_dia(ymd)['fas'][norm] = ruta_f
            elif fl.endswith(".rsa") or fl.startswith("phase") or fl.endswith((".l", ".p", ".s")):
                # Archivos FASTHYPO: MMDDHHMM.rsa (o con sufijo a/b/c)
                stem_r = Path(f).stem.rstrip("abc")
                if len(stem_r) >= 8 and stem_r[:8].isdigit() and anio_carpeta:
                    try:
                        mm_r, dd_r = int(stem_r[0:2]), int(stem_r[2:4])
                        datetime(anio_carpeta, mm_r, dd_r)
                        _asegurar_dia((anio_carpeta, mm_r, dd_r))['rsa'].append(ruta_f)
                    except ValueError:
                        pass
            elif fl.endswith("_estaciones.csv"):
                digs = re.sub(r"\D", "", f)
                if len(digs) >= 6:
                    try:
                        y_e = int(digs[:4]) if len(digs) >= 8 else (2000 + int(digs[:2]))
                        m_e = int(digs[4:6]) if len(digs) >= 8 else int(digs[2:4])
                        d_e = int(digs[6:8]) if len(digs) >= 8 else int(digs[4:6])
                        datetime(y_e, m_e, d_e)
                        _asegurar_dia((y_e, m_e, d_e))['est_csv'] = ruta_f
                    except ValueError:
                        pass

    dias_ordenados = sorted(eventos_por_dia.keys())
    total_dias = max(1, len(dias_ordenados))

    for idx_d, (anio, mes, dia) in enumerate(dias_ordenados, start=1):
        if cancelar_cb and cancelar_cb():
            res['cancelado'] = True
            return res

        info_dia = eventos_por_dia[(anio, mes, dia)]
        fecha_larga = f"{anio:04d}{mes:02d}{dia:02d}"
        if progreso_cb:
            progreso_cb(idx_d, total_dias, f"{anio:04d}-{mes:02d}-{dia:02d} ({len(info_dia['sis'])} .sis)")

        archivo_base = os.path.join(raiz_dest, f"{fecha_larga}000000")
        dirs = obtener_directorios(archivo_base)
        for k_dir in (
            'Directorio_base', 'Directorio_dia', 'Directorio_eventos',
            'Directorio_registros', 'Directorio_fastHypo', 'Directorio_reportes',
            'Directorio_acelerogramas',
        ):
            os.makedirs(dirs[k_dir], exist_ok=True)

        # Copiar _estaciones.csv si existe (en 4 dígitos)
        ruta_est_dest = os.path.join(dirs['Directorio_base'], f"{fecha_larga}_estaciones.csv")
        if info_dia['est_csv'] and not os.path.isfile(ruta_est_dest):
            try:
                shutil.copy2(info_dia['est_csv'], ruta_est_dest)
            except OSError:
                pass

        # Copiar archivos fastHypo (.rsa, Phase*, .L/.P/.S)
        claves_min_rsa = set()
        for ruta_rsa in info_dia['rsa']:
            dest_r = os.path.join(dirs['Directorio_fastHypo'], os.path.basename(ruta_rsa))
            if not os.path.isfile(dest_r):
                try:
                    shutil.copy2(ruta_rsa, dest_r)
                    if ruta_rsa.lower().endswith('.rsa'):
                        res['rsa_copiados'] += 1
                except OSError:
                    pass
            if ruta_rsa.lower().endswith('.rsa'):
                claves_min_rsa.add(Path(ruta_rsa).stem.rstrip("abc")[:8])

        # Procesar cada .sis del día
        filas_csv_dia = []
        for idx_ev, (norm_sis, ruta_sis_orig) in enumerate(sorted(info_dia['sis'].items()), start=1):
            dest_sis = os.path.join(dirs['Directorio_dia'], norm_sis)
            if not os.path.isfile(dest_sis):
                try:
                    shutil.copy2(ruta_sis_orig, dest_sis)
                except OSError:
                    res['errores'] += 1
                    continue

            norm_fas = Path(norm_sis).stem + ".fas"
            tiene_fas = norm_fas in info_dia['fas']
            if tiene_fas:
                dest_fas = os.path.join(dirs['Directorio_dia'], norm_fas)
                if not os.path.isfile(dest_fas):
                    try:
                        shutil.copy2(info_dia['fas'][norm_fas], dest_fas)
                        res['fas_copiados'] += 1
                    except OSError:
                        pass

            # Decodificar binario .sis -> mseed/eventos/<EST>_AAAAMMDD_HHMMSS.mseed
            dec = decodificar_sis_a_mseed(
                dest_sis,
                dirs['Directorio_eventos'],
                parametros,
                sobrescribir=sobrescribir_mseed,
            )
            res['sis_convertidos'] += 1
            res['mseed_creados'] += dec['mseed_creados']

            # Determinar clasificación (SISMO si tiene .fas o .rsa correspondiente; sino FF)
            ft = extraer_fecha_desde_nombre_sis(norm_sis)
            tiene_rsa = False
            if ft:
                dt_e = datetime(*ft)
                k1 = dt_e.strftime("%m%d%H%M")
                from datetime import timedelta
                k2 = (dt_e + timedelta(minutes=1)).strftime("%m%d%H%M")
                tiene_rsa = (k1 in claves_min_rsa) or (k2 in claves_min_rsa)
            tipo_ev = "SISMO" if (tiene_fas or tiene_rsa) else "FF"

            # Armar fila de AAAAMMDD000000.csv con tokens de 12 caracteres (pos5='1')
            guiones = ['-'] * total_est
            for cod in dec['estaciones']:
                idx_c = mapa_cod_idx.get(cod)
                if idx_c is not None and idx_c < total_est:
                    canal = str(componentes[idx_c]).strip() or '1'
                    guiones[idx_c] = f"{cod}{canal}1000000"
            filas_csv_dia.append([str(idx_ev), norm_sis, tipo_ev] + guiones)

        # Guardar AAAAMMDD000000.csv base y delegar estandarización completa a reconstruir_eventos_dia()
        ruta_csv_4d = os.path.join(dirs['Directorio_base'], f"{fecha_larga}000000.csv")
        if filas_csv_dia:
            escritura_archivo(ruta_csv_4d, filas_csv_dia)
            try:
                reconstruir_eventos_dia(
                    archivo=archivo_base,
                    responsable="HIDROPAUTE",
                    sobrescribir_existentes=False,
                    solo_presentes_en_csv=True,
                    reconstruir_sis=False,
                    regenerar_consolidado_dia=True,
                    regenerar_pdf_diario=False,
                    normalizar_4_digitos=True,
                    parametros=parametros,
                )
            except Exception as e_rec:
                res['errores'] += 1
                print(f"Aviso reconstruyendo día {fecha_larga}: {e_rec}")

        res['dias_procesados'] += 1

    return res


# ===========================================================================
# HILO DE TRABAJO EN SEGUNDO PLANO (QThread)
# ===========================================================================
class HiloMigradorHidropaute(QThread):
    progreso = pyqtSignal(int, int, str)
    bitacora = pyqtSignal(str)
    finalizado = pyqtSignal(dict)

    def __init__(self, modo: str, dir_base_hp: str, carpetas_celec=None, sobrescribir_mseed=False, parent=None):
        super().__init__(parent)
        self.modo = modo  # 'estandarizar_2003_2010' | 'convertir_celec'
        self.dir_base_hp = dir_base_hp
        self.carpetas_celec = list(carpetas_celec or [])
        self.sobrescribir_mseed = bool(sobrescribir_mseed)
        self._cancelado = False

    def solicitar_cancelacion(self):
        self._cancelado = True

    def esta_cancelado(self):
        return self._cancelado

    def run(self):
        resumen = {'ok': False, 'cancelado': False, 'mensaje': ''}
        try:
            parametros = parametros_estaciones()
            if self.modo == 'estandarizar_2003_2010':
                self._run_estandarizar(parametros, resumen)
            elif self.modo == 'convertir_celec':
                self._run_convertir_celec(parametros, resumen)
        except Exception as exc:
            resumen['mensaje'] = f"Error inesperado: {exc}"
            self.bitacora.emit(f"❌ {resumen['mensaje']}")
        self.finalizado.emit(resumen)

    def _run_estandarizar(self, parametros, resumen):
        raiz = str(self.dir_base_hp).rstrip("/\\") + "/"
        dias_encontrados = []
        pat_dia = re.compile(r"^(\d{4})_(\d{2})_(\d{2})$")

        for r_act, ds, _fs in os.walk(raiz):
            nom = os.path.basename(r_act)
            m = pat_dia.match(nom)
            if m:
                dias_encontrados.append((f"{m.group(1)}{m.group(2)}{m.group(3)}", r_act))
                ds[:] = []  # No descender dentro del día

        dias_encontrados.sort()
        total = max(1, len(dias_encontrados))
        self.bitacora.emit(f"Encontrados {len(dias_encontrados)} días en {raiz}")

        ok_dias = 0
        toks_tot = 0
        aux_tot = 0
        migr_4d_tot = 0
        errores = 0

        for idx, (fecha_larga, ruta_dia) in enumerate(dias_encontrados, start=1):
            if self._cancelado:
                resumen['cancelado'] = True
                resumen['mensaje'] = f"Cancelado en día {idx}/{len(dias_encontrados)}."
                return

            self.progreso.emit(idx, total, f"Estandarizando {fecha_larga[:4]}-{fecha_larga[4:6]}-{fecha_larga[6:8]} ({idx}/{len(dias_encontrados)})")
            archivo_base = os.path.join(raiz, f"{fecha_larga}000000")
            try:
                dirs = obtener_directorios(archivo_base)
                toks = sanear_csv_preliminar_hidropaute(dirs.get('archivo_csv', ''), parametros)
                toks_tot += toks
                r_dia = reconstruir_eventos_dia(
                    archivo=archivo_base,
                    responsable="HIDROPAUTE",
                    sobrescribir_existentes=False,
                    solo_presentes_en_csv=True,
                    reconstruir_sis=False,
                    regenerar_consolidado_dia=True,
                    regenerar_pdf_diario=False,
                    normalizar_4_digitos=True,
                    parametros=parametros,
                )
                if r_dia.get('estado') == 'ok':
                    ok_dias += 1
                    migr_4d_tot += r_dia.get('archivos_normalizados_4d', 0)
                    if r_dia.get('aux_creado_nuevo'):
                        aux_tot += 1
                if idx % 50 == 0 or idx == len(dias_encontrados):
                    self.bitacora.emit(
                        f"  Progreso {idx}/{len(dias_encontrados)}: {ok_dias} días OK | "
                        f"{toks_tot} tokens expandidos | {migr_4d_tot} archivos→4D | {aux_tot} _aux creados"
                    )
            except Exception as e_d:
                errores += 1
                self.bitacora.emit(f"  ❌ Error en {fecha_larga}: {e_d}")

        resumen['ok'] = True
        resumen['mensaje'] = (
            f"Estandarización completada: {ok_dias}/{len(dias_encontrados)} días OK | "
            f"{toks_tot} tokens expandidos | {migr_4d_tot} archivos→4D | {aux_tot} _aux creados | {errores} errores."
        )
        self.bitacora.emit(f"\n✓ {resumen['mensaje']}")

    def _run_convertir_celec(self, parametros, resumen):
        tot_dias = tot_sis = tot_ms = tot_fas = tot_rsa = tot_err = 0
        for carpeta in self.carpetas_celec:
            if self._cancelado:
                resumen['cancelado'] = True
                resumen['mensaje'] = "Conversión cancelada por el usuario."
                return
            self.bitacora.emit(f"\n=== Convirtiendo {os.path.basename(carpeta)} -> {self.dir_base_hp} ===")

            def _cb(i_d, n_d, txt):
                self.progreso.emit(i_d, n_d, f"[{os.path.basename(carpeta)}] {txt}")

            r_yr = convertir_anio_celec_v2(
                dir_anio_celec=carpeta,
                dir_destino_dia=self.dir_base_hp,
                parametros=parametros,
                sobrescribir_mseed=self.sobrescribir_mseed,
                progreso_cb=_cb,
                cancelar_cb=self.esta_cancelado,
            )
            tot_dias += r_yr['dias_procesados']
            tot_sis += r_yr['sis_convertidos']
            tot_ms += r_yr['mseed_creados']
            tot_fas += r_yr['fas_copiados']
            tot_rsa += r_yr['rsa_copiados']
            tot_err += r_yr['errores']
            self.bitacora.emit(
                f"✓ {os.path.basename(carpeta)}: {r_yr['dias_procesados']} días | "
                f"{r_yr['sis_convertidos']} .sis | {r_yr['mseed_creados']} .mseed | "
                f"{r_yr['fas_copiados']} .fas | {r_yr['rsa_copiados']} .rsa | {r_yr['errores']} err"
            )

        resumen['ok'] = True
        resumen['mensaje'] = (
            f"Conversión Proceso V2 finalizada: {tot_dias} días | {tot_sis} .sis | "
            f"{tot_ms} .mseed | {tot_fas} .fas | {tot_rsa} .rsa | {tot_err} errores."
        )
        self.bitacora.emit(f"\n=== {resumen['mensaje']} ===")


# ===========================================================================
# INTERFAZ GRÁFICA PRINCIPAL
# ===========================================================================
class VentanaMigradorHidropaute(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Migrador Histórico HIDROPAUTE / CELEC — Formato Moderno RSA (4D)")
        self.resize(900, 650)
        self.hilo = None
        self._construir_ui()
        self._poblar_anios_celec()

    def _construir_ui(self):
        central = QWidget()
        lay = QVBoxLayout(central)
        lay.setSpacing(10)
        lay.setContentsMargins(14, 12, 14, 12)

        lbl_tit = QLabel("Migrador Independiente HIDROPAUTE / CELEC (Reutiliza librerías RSA)")
        lbl_tit.setStyleSheet("font-size: 13pt; font-weight: bold; color: #1565C0;")
        lay.addWidget(lbl_tit)

        lbl_sub = QLabel(
            "Opera exclusivamente dentro de C:\\DIA\\HIDROPAUTE\\DIA\\ (nunca toca C:\\DIA\\ principal). "
            "La integración con la red principal se realizará en una etapa posterior tras análisis de sincronía."
        )
        lbl_sub.setWordWrap(True)
        lbl_sub.setStyleSheet("color: #455A64; font-size: 9pt;")
        lay.addWidget(lbl_sub)

        self.tabs = QTabWidget()

        # --- Pestaña 1: Estandarizar 2003-2010 ---
        tab1 = QWidget()
        g1 = QGridLayout(tab1)
        g1.addWidget(QLabel("Carpeta HIDROPAUTE\\DIA (2003–2010):"), 0, 0)
        self.txt_dir_hp = QLineEdit(r"C:\DIA\HIDROPAUTE\DIA")
        g1.addWidget(self.txt_dir_hp, 0, 1)
        btn_ex1 = QPushButton("Examinar...")
        btn_ex1.clicked.connect(lambda: self._elegir_dir(self.txt_dir_hp))
        g1.addWidget(btn_ex1, 0, 2)

        lbl_d1 = QLabel(
            "• Migra nombres AAMMDD → AAAAMMDD (4 dígitos) sin tocar fastHypo/.\n"
            "• Elimina cabecera heredada '0;Fecha...' y expande tokens de 4 letras (AREN → AREN11000000).\n"
            "• Genera AAAAMMDD_aux.csv y regenera _cat.csv, _rep.csv, _res.csv y .xml vía reconstruir_eventos_dia()."
        )
        lbl_d1.setWordWrap(True)
        g1.addWidget(lbl_d1, 1, 0, 1, 3)

        self.btn_run_t1 = QPushButton("Estandarizar HIDROPAUTE\\DIA a Formato Actual (4D)")
        self.btn_run_t1.setMinimumHeight(34)
        self.btn_run_t1.setStyleSheet("font-weight: bold; background-color: #1565C0; color: white;")
        self.btn_run_t1.clicked.connect(self._lanzar_estandarizar)
        g1.addWidget(self.btn_run_t1, 2, 0, 1, 3)
        self.tabs.addTab(tab1, "1. Estandarizar Preliminar (2003–2010)")

        # --- Pestaña 2: Convertir Celec 2011-2016 (.sis -> .mseed) ---
        tab2 = QWidget()
        g2 = QGridLayout(tab2)
        g2.addWidget(QLabel("Origen Sin Procesar (Celec 2011–2016):"), 0, 0)
        self.txt_origen_sp = QLineEdit(r"C:\DIA\HIDROPAUTE\Sin procesar")
        g2.addWidget(self.txt_origen_sp, 0, 1)
        btn_ex2 = QPushButton("Examinar...")
        btn_ex2.clicked.connect(self._elegir_origen_sp)
        g2.addWidget(btn_ex2, 0, 2)

        g2.addWidget(QLabel("Destino integrado en HIDROPAUTE\\DIA:"), 1, 0)
        self.txt_dest_hp2 = QLineEdit(r"C:\DIA\HIDROPAUTE\DIA")
        g2.addWidget(self.txt_dest_hp2, 1, 1)
        btn_ex3 = QPushButton("Examinar...")
        btn_ex3.clicked.connect(lambda: self._elegir_dir(self.txt_dest_hp2))
        g2.addWidget(btn_ex3, 1, 2)

        self.lista_anios = QListWidget()
        self.lista_anios.setMaximumHeight(115)
        g2.addWidget(self.lista_anios, 2, 0, 1, 3)

        self.chk_sobrescribir_ms = QCheckBox("Sobrescribir archivos .mseed existentes")
        g2.addWidget(self.chk_sobrescribir_ms, 3, 0, 1, 3)

        self.btn_run_t2 = QPushButton("Convertir Años Seleccionados (.sis → .mseed + Estructura Moderna)")
        self.btn_run_t2.setMinimumHeight(34)
        self.btn_run_t2.setStyleSheet("font-weight: bold; background-color: #2E7D32; color: white;")
        self.btn_run_t2.clicked.connect(self._lanzar_convertir_celec)
        g2.addWidget(self.btn_run_t2, 4, 0, 1, 3)
        self.tabs.addTab(tab2, "2. Convertir Proceso V2 (Celec 2011–2016)")

        lay.addWidget(self.tabs)

        # --- Progreso y Bitácora ---
        grp_p = QGroupBox("Progreso y Bitácora")
        lp = QVBoxLayout(grp_p)
        self.lbl_estado = QLabel("Listo.")
        lp.addWidget(self.lbl_estado)
        self.barra = QProgressBar()
        self.barra.setFormat("%v / %m (%p%)")
        lp.addWidget(self.barra)
        self.txt_log = QPlainTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setStyleSheet("font-family: Consolas, monospace; font-size: 9pt;")
        lp.addWidget(self.txt_log)
        lay.addWidget(grp_p, 1)

        # --- Pie ---
        pie = QHBoxLayout()
        pie.addStretch(1)
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setEnabled(False)
        self.btn_cancelar.setMinimumHeight(32)
        self.btn_cancelar.clicked.connect(self._cancelar)
        pie.addWidget(self.btn_cancelar)
        self.btn_cerrar = QPushButton("Cerrar")
        self.btn_cerrar.setMinimumHeight(32)
        self.btn_cerrar.clicked.connect(self.close)
        pie.addWidget(self.btn_cerrar)
        lay.addLayout(pie)

        self.setCentralWidget(central)

    def _elegir_dir(self, le: QLineEdit):
        d = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta", le.text().strip())
        if d:
            le.setText(os.path.normpath(d))

    def _elegir_origen_sp(self):
        self._elegir_dir(self.txt_origen_sp)
        self._poblar_anios_celec()

    def _poblar_anios_celec(self):
        self.lista_anios.clear()
        base = self.txt_origen_sp.text().strip()
        if not os.path.isdir(base):
            return
        for nom in sorted(os.listdir(base)):
            p = os.path.join(base, nom)
            if os.path.isdir(p):
                it = QListWidgetItem(nom)
                it.setData(256, p)
                it.setCheckState(2)  # Checked
                self.lista_anios.addItem(it)

    def _set_ejecutando(self, flag: bool):
        self.tabs.setEnabled(not flag)
        self.btn_cancelar.setEnabled(flag)
        self.btn_cerrar.setEnabled(not flag)

    def _iniciar(self, hilo: HiloMigradorHidropaute):
        self.txt_log.clear()
        self.barra.setRange(0, 1)
        self.barra.setValue(0)
        self._set_ejecutando(True)
        self.hilo = hilo
        hilo.progreso.connect(lambda a, t, m: (self.barra.setMaximum(max(1, t)), self.barra.setValue(a), self.lbl_estado.setText(m)))
        hilo.bitacora.connect(self.txt_log.appendPlainText)
        hilo.finalizado.connect(self._al_finalizar)
        hilo.start()

    def _lanzar_estandarizar(self):
        d = self.txt_dir_hp.text().strip()
        if not os.path.isdir(d):
            QMessageBox.warning(self, "Carpeta inválida", "Seleccione una carpeta HIDROPAUTE\\DIA existente.")
            return
        self._iniciar(HiloMigradorHidropaute('estandarizar_2003_2010', d, parent=self))

    def _lanzar_convertir_celec(self):
        dest = self.txt_dest_hp2.text().strip()
        if not dest:
            QMessageBox.warning(self, "Destino requerido", "Indique la carpeta destino HIDROPAUTE\\DIA.")
            return
        seleccionadas = []
        for i in range(self.lista_anios.count()):
            it = self.lista_anios.item(i)
            if it.checkState() == 2:
                seleccionadas.append(it.data(256))
        if not seleccionadas:
            QMessageBox.warning(self, "Sin años", "Marque al menos una carpeta anual Celec para convertir.")
            return
        self._iniciar(
            HiloMigradorHidropaute(
                'convertir_celec',
                dest,
                carpetas_celec=seleccionadas,
                sobrescribir_mseed=self.chk_sobrescribir_ms.isChecked(),
                parent=self,
            )
        )

    def _cancelar(self):
        if self.hilo and self.hilo.isRunning():
            self.hilo.solicitar_cancelacion()
            self.btn_cancelar.setEnabled(False)
            self.lbl_estado.setText("Cancelando al terminar el día actual...")

    def _al_finalizar(self, res: dict):
        self._set_ejecutando(False)
        self.lbl_estado.setText(res.get('mensaje', 'Finalizado.'))
        if res.get('ok'):
            QMessageBox.information(self, "Migrador HIDROPAUTE", res.get('mensaje', 'Completado.'))
        elif not res.get('cancelado'):
            QMessageBox.warning(self, "Aviso", res.get('mensaje', 'Inconveniente.'))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = VentanaMigradorHidropaute()
    win.show()
    sys.exit(app.exec_())
