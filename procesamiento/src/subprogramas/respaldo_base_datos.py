# -*- coding: utf-8 -*-
"""
Subprograma de Respaldo y Sincronización de Base de Datos Sísmica (DIA).

Ofrece tres flujos seguros e incrementales (nunca elimina archivos del destino):
  1. Sincronizar a Carpeta: copia desde un directorio origen (ej. Google Drive G:\\Mi unidad\\DIA\\)
     hacia un directorio destino maestro (ej. C:\\DIA\\), reemplazando únicamente si el archivo
     no existe o es más reciente (tolerancia 2 s para compatibilidad Google Drive / NTFS).
  2. Exportar a ZIP: empaqueta el directorio origen en un archivo .zip (ZIP64) con manifiesto
     interno de fechas exactas (`rsa_manifiesto_respaldo.json`), en modo Completo o Liviano
     (omitiendo mseed/registros/ y archivos .pdf).
  3. Importar / Descomprimir ZIP: extrae en la computadora de destino aplicando la misma regla
     segura incremental por fecha (o reemplazo forzado opcional) con protección Zip Slip.
"""

import json
import os
import re
import shutil
import sys
import zipfile
from datetime import date, datetime
from pathlib import Path

from PyQt5 import uic
from PyQt5.QtCore import QDate, QThread, pyqtSignal
from PyQt5.QtWidgets import QFileDialog, QMainWindow, QMessageBox


NOMBRE_MANIFIESTO_ZIP = "rsa_manifiesto_respaldo.json"
NOMBRE_MARCADOR_TIPO_BD = "rsa_tipo_base_datos.json"
TOLERANCIA_MTIME_SEG = 2.0


def obtener_tipo_base_datos(directorio_trabajo: str) -> str:
    """
    Lee el marcador `rsa_tipo_base_datos.json` en la raíz del directorio de trabajo (DIA).
    Devuelve 'liviano' si corresponde a un respaldo simplificado sin registros continuos
    ni PDFs; en cualquier otro caso (o si no existe marcador) devuelve 'completo'.
    """
    if not directorio_trabajo:
        return 'completo'
    ruta_marc = os.path.join(os.path.abspath(str(directorio_trabajo)), NOMBRE_MARCADOR_TIPO_BD)
    if not os.path.isfile(ruta_marc):
        return 'completo'
    try:
        with open(ruta_marc, 'r', encoding='utf-8') as f:
            datos = json.load(f)
        tipo = str(datos.get('tipo', 'completo')).strip().lower()
        return 'liviano' if tipo == 'liviano' else 'completo'
    except Exception:
        return 'completo'


def es_base_datos_liviana(directorio_trabajo: str) -> bool:
    """True únicamente si `directorio_trabajo` está marcado como base de datos liviana."""
    return obtener_tipo_base_datos(directorio_trabajo) == 'liviano'


def escribir_marcador_tipo_bd(directorio_destino: str, modo_liviano: bool, origen: str = "") -> None:
    """Escribe `rsa_tipo_base_datos.json` en la raíz del destino indicando 'liviano' o 'completo'."""
    if not directorio_destino:
        return
    try:
        os.makedirs(directorio_destino, exist_ok=True)
        ruta_marc = os.path.join(os.path.abspath(directorio_destino), NOMBRE_MARCADOR_TIPO_BD)
        payload = {
            'tipo': 'liviano' if modo_liviano else 'completo',
            'actualizado_en': datetime.now().isoformat(),
            'origen': str(origen or ''),
            'descripcion': (
                'Base de datos liviana (sin mseed/registros ni PDFs) — solo consulta y reportes de período.'
                if modo_liviano else
                'Base de datos completa operativa.'
            ),
        }
        with open(ruta_marc, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
    except Exception as exc:
        print(f"Aviso escribiendo marcador de tipo de BD: {exc}")


def solicitar_destino_externo_si_liviana(parent, directorio_trabajo: str, titulo: str = "Seleccionar carpeta externa para guardar el informe"):
    """
    Si `directorio_trabajo` es una base de datos normal ('completo'), retorna None
    (sin alterar el flujo actual).
    Si es una base de datos 'liviano', solicita al usuario una carpeta externa fuera
    de `directorio_trabajo` para guardar los reportes/PDFs sin contaminar la base.
    Retorna:
      - None : base completa (usar ruta estándar)
      - ""   : usuario canceló el diálogo
      - str  : ruta absoluta de la carpeta externa válida
    """
    if not es_base_datos_liviana(directorio_trabajo):
        return None

    carpeta_inicial = os.path.expanduser("~\\Desktop")
    while True:
        carpeta = QFileDialog.getExistingDirectory(parent, titulo, carpeta_inicial)
        if not carpeta:
            return ""
        if rutas_se_solapan(directorio_trabajo, carpeta):
            QMessageBox.warning(
                parent,
                "Destino no permitido en Base Liviana",
                "La carpeta de trabajo actual es una BASE DE DATOS LIVIANA.\n\n"
                "No se pueden guardar archivos PDF ni reportes dentro de ese directorio.\n"
                "Por favor seleccione una carpeta externa (por ejemplo en Escritorio o Documentos).",
            )
            continue
        return os.path.normpath(carpeta)


def extraer_hasta_directorio(ruta_completa, nombre_directorio):
    partes = Path(ruta_completa).parts
    if nombre_directorio in partes:
        indice = partes.index(nombre_directorio)
        return str(Path(*partes[:indice + 1])) + '/'
    return ''


ruta_actual = os.path.dirname(__file__)
ruta_proyecto = extraer_hasta_directorio(ruta_actual, 'procesamiento')


def formatear_tamano(num_bytes: int) -> str:
    valor = float(max(0, num_bytes))
    for unidad in ('B', 'KB', 'MB', 'GB', 'TB'):
        if valor < 1024.0 or unidad == 'TB':
            return f"{valor:.2f} {unidad}" if unidad != 'B' else f"{int(valor)} B"
        valor /= 1024.0
    return f"{num_bytes} B"


def es_archivo_excluido(ruta_relativa: str, modo_liviano: bool = True) -> bool:
    """
    Determina si un archivo debe excluirse del respaldo.
    - Siempre excluye temporales del sistema (desktop.ini, thumbs.db, *.tmp, ~$*, __pycache__).
    - Si modo_liviano=True, excluye además:
        * Cualquier archivo dentro de .../mseed/registros/ (registros continuos de 24h).
        * Cualquier archivo con extensión .pdf.
    """
    partes = [p.lower() for p in Path(ruta_relativa).parts]
    if not partes:
        return True
    nombre = partes[-1]

    if nombre in ('desktop.ini', 'thumbs.db', NOMBRE_MANIFIESTO_ZIP.lower(), NOMBRE_MARCADOR_TIPO_BD.lower()):
        return True
    if nombre.endswith('.tmp') or nombre.startswith('~$'):
        return True
    if '__pycache__' in partes:
        return True

    if modo_liviano:
        if nombre.endswith('.pdf'):
            return True
        for i in range(len(partes) - 1):
            if partes[i] == 'mseed' and partes[i + 1] == 'registros':
                return True

    return False


def rutas_se_solapan(ruta_a: str, ruta_b: str) -> bool:
    """Devuelve True si ruta_a y ruta_b son iguales o una es subdirectorio de la otra."""
    try:
        pa = os.path.normcase(os.path.abspath(ruta_a))
        pb = os.path.normcase(os.path.abspath(ruta_b))
        if pa == pb:
            return True
        comun = os.path.commonpath([pa, pb])
        return comun in (pa, pb)
    except ValueError:
        # Unidades distintas (ej. G:\ y C:\) nunca se solapan
        return False


_PAT_DIA_GUION = re.compile(r"^(\d{4})_(\d{2})_(\d{2})$")
_PAT_DIA_JUNTO = re.compile(r"^(\d{4})(\d{2})(\d{2})$")
_PAT_MES = re.compile(r"^(\d{4})_(\d{2})$")
_PAT_ANIO = re.compile(r"^(\d{4})$")


def ruta_dentro_de_periodo(ruta_relativa: str, fecha_ini: date, fecha_fin: date) -> bool:
    """
    Evalúa si una ruta relativa dentro de DIA\\ corresponde al rango [fecha_ini, fecha_fin]:
      - Carpeta diaria (AAAA_MM_DD o AAAAMMDD): fecha_ini <= fecha_dia <= fecha_fin.
      - Carpeta mensual (AAAA_MM sin día): el mes intersecta [fecha_ini, fecha_fin].
      - Carpeta anual (AAAA sin mes ni día): fecha_ini.year <= anio <= fecha_fin.year.
      - Archivos en raíz de DIA\\ (sin carpeta de fecha): se incluyen siempre.
    """
    if fecha_ini is None or fecha_fin is None:
        return True

    partes = list(Path(ruta_relativa).parts)
    if len(partes) <= 1:
        return True

    carpetas = partes[:-1]
    anio_det = None
    mes_det = None

    for c in carpetas:
        m_dg = _PAT_DIA_GUION.match(c)
        m_dj = _PAT_DIA_JUNTO.match(c) if not m_dg else None
        if m_dg or m_dj:
            m = m_dg or m_dj
            try:
                f_dia = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                return fecha_ini <= f_dia <= fecha_fin
            except ValueError:
                continue
        m_m = _PAT_MES.match(c)
        if m_m:
            try:
                anio_det, mes_det = int(m_m.group(1)), int(m_m.group(2))
            except ValueError:
                pass
        elif _PAT_ANIO.match(c):
            try:
                anio_det = int(c)
            except ValueError:
                pass

    if anio_det is not None and mes_det is not None:
        ym = (anio_det, mes_det)
        return (fecha_ini.year, fecha_ini.month) <= ym <= (fecha_fin.year, fecha_fin.month)
    if anio_det is not None:
        return fecha_ini.year <= anio_det <= fecha_fin.year
    return True


def planificar_sincronizacion_carpeta(
    dir_origen: str,
    dir_destino: str,
    modo_liviano: bool = True,
    fecha_ini: date = None,
    fecha_fin: date = None,
) -> dict:
    """
    Escanea dir_origen y compara contra dir_destino (si se especifica), aplicando
    opcionalmente el filtro por período [fecha_ini, fecha_fin].
    Retorna el plan detallado de archivos nuevos, a actualizar (más recientes),
    omitidos (destino igual o más reciente) y excluidos por filtro.
    """
    plan = {
        'nuevos': [],            # [(ruta_abs_orig, ruta_rel, tamano, mtime)]
        'actualizar': [],        # [(ruta_abs_orig, ruta_rel, tamano, mtime)]
        'omitidos': 0,
        'excluidos': 0,
        'bytes_a_copiar': 0,
        'bytes_excluidos': 0,
    }
    raiz_orig = os.path.abspath(dir_origen)
    raiz_dest = os.path.abspath(dir_destino) if dir_destino else None

    for dir_act, subdirs, archivos in os.walk(raiz_orig):
        rel_dir = os.path.relpath(dir_act, raiz_orig)
        partes_dir = [p.lower() for p in Path(rel_dir).parts] if rel_dir != '.' else []

        # Poda rápida de __pycache__, mseed/registros en modo liviano y carpetas fuera de período
        nuevos_subdirs = []
        for d in subdirs:
            if d.lower() == '__pycache__':
                continue
            if modo_liviano and d.lower() == 'registros' and partes_dir and partes_dir[-1] == 'mseed':
                continue
            if fecha_ini is not None and fecha_fin is not None:
                rel_sub = os.path.join(rel_dir, d, '_check_') if rel_dir != '.' else os.path.join(d, '_check_')
                if not ruta_dentro_de_periodo(rel_sub, fecha_ini, fecha_fin):
                    continue
            nuevos_subdirs.append(d)
        subdirs[:] = nuevos_subdirs

        for nom in archivos:
            ruta_abs = os.path.join(dir_act, nom)
            ruta_rel = os.path.relpath(ruta_abs, raiz_orig)
            if fecha_ini is not None and fecha_fin is not None:
                if not ruta_dentro_de_periodo(ruta_rel, fecha_ini, fecha_fin):
                    continue
            try:
                st = os.stat(ruta_abs)
            except OSError:
                continue

            if es_archivo_excluido(ruta_rel, modo_liviano=modo_liviano):
                plan['excluidos'] += 1
                plan['bytes_excluidos'] += st.st_size
                continue

            if not raiz_dest:
                plan['nuevos'].append((ruta_abs, ruta_rel, st.st_size, st.st_mtime))
                plan['bytes_a_copiar'] += st.st_size
                continue

            ruta_dest = os.path.join(raiz_dest, ruta_rel)
            if not os.path.exists(ruta_dest):
                plan['nuevos'].append((ruta_abs, ruta_rel, st.st_size, st.st_mtime))
                plan['bytes_a_copiar'] += st.st_size
            else:
                try:
                    st_d = os.stat(ruta_dest)
                    if st.st_mtime > (st_d.st_mtime + TOLERANCIA_MTIME_SEG):
                        plan['actualizar'].append((ruta_abs, ruta_rel, st.st_size, st.st_mtime))
                        plan['bytes_a_copiar'] += st.st_size
                    else:
                        plan['omitidos'] += 1
                except OSError:
                    plan['actualizar'].append((ruta_abs, ruta_rel, st.st_size, st.st_mtime))
                    plan['bytes_a_copiar'] += st.st_size

    return plan


def planificar_importacion_zip(ruta_zip: str, dir_destino: str, forzar_reemplazo: bool = False) -> dict:
    """
    Inspecciona un archivo ZIP de respaldo (leyendo rsa_manifiesto_respaldo.json si existe)
    y determina qué entradas son nuevas, cuáles son más recientes y cuáles se omiten.
    Incluye validación estricta contra Zip Slip.
    """
    plan = {
        'nuevos': [],         # [(zip_name, ruta_dest_abs, tamano, mtime)]
        'actualizar': [],     # [(zip_name, ruta_dest_abs, tamano, mtime)]
        'omitidos': 0,
        'inseguros': 0,
        'bytes_a_extraer': 0,
        'manifiesto': {},
    }
    dest_abs = os.path.abspath(dir_destino)

    with zipfile.ZipFile(ruta_zip, 'r') as zf:
        mtimes_manif = {}
        if NOMBRE_MANIFIESTO_ZIP in zf.namelist():
            try:
                manif = json.loads(zf.read(NOMBRE_MANIFIESTO_ZIP).decode('utf-8'))
                plan['manifiesto'] = manif
                mtimes_manif = manif.get('archivos_mtime', {}) or {}
            except Exception:
                pass

        for info in zf.infolist():
            if info.is_dir():
                continue
            nombre_zip = info.filename.replace('\\', '/')
            if nombre_zip == NOMBRE_MANIFIESTO_ZIP or nombre_zip.endswith('/' + NOMBRE_MANIFIESTO_ZIP):
                continue

            # Validación Zip Slip
            ruta_dest = os.path.abspath(os.path.join(dest_abs, *nombre_zip.split('/')))
            try:
                if os.path.commonpath([dest_abs, ruta_dest]) != dest_abs:
                    plan['inseguros'] += 1
                    continue
            except ValueError:
                plan['inseguros'] += 1
                continue

            # Determinar mtime del archivo dentro del ZIP
            if nombre_zip in mtimes_manif:
                mtime_zip = float(mtimes_manif[nombre_zip])
            else:
                try:
                    mtime_zip = datetime(*info.date_time).timestamp()
                except Exception:
                    mtime_zip = 0.0

            if not os.path.exists(ruta_dest):
                plan['nuevos'].append((info.filename, ruta_dest, info.file_size, mtime_zip))
                plan['bytes_a_extraer'] += info.file_size
            elif forzar_reemplazo:
                plan['actualizar'].append((info.filename, ruta_dest, info.file_size, mtime_zip))
                plan['bytes_a_extraer'] += info.file_size
            else:
                try:
                    mtime_dest = os.stat(ruta_dest).st_mtime
                    if mtime_zip > (mtime_dest + TOLERANCIA_MTIME_SEG):
                        plan['actualizar'].append((info.filename, ruta_dest, info.file_size, mtime_zip))
                        plan['bytes_a_extraer'] += info.file_size
                    else:
                        plan['omitidos'] += 1
                except OSError:
                    plan['actualizar'].append((info.filename, ruta_dest, info.file_size, mtime_zip))
                    plan['bytes_a_extraer'] += info.file_size

    return plan


def copiar_archivo_atomico(origen: str, destino: str) -> None:
    """Copia un archivo preservando metadatos (mtime) mediante archivo temporal atómico."""
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    ruta_tmp = destino + ".rsa_tmp"
    try:
        shutil.copy2(origen, ruta_tmp)
        os.replace(ruta_tmp, destino)
    finally:
        if os.path.exists(ruta_tmp):
            try:
                os.remove(ruta_tmp)
            except OSError:
                pass


class HiloRespaldoBaseDatos(QThread):
    """Hilo de trabajo en segundo plano para análisis, copia, compresión y extracción ZIP."""

    progreso = pyqtSignal(int, int, str)
    bitacora = pyqtSignal(str)
    finalizado = pyqtSignal(dict)

    def __init__(
        self,
        operacion: str,
        solo_analisis: bool = False,
        dir_origen: str = "",
        dir_destino: str = "",
        ruta_zip: str = "",
        modo_liviano: bool = True,
        forzar_reemplazo: bool = False,
        fecha_ini: date = None,
        fecha_fin: date = None,
        parent=None,
    ):
        super().__init__(parent)
        self.operacion = operacion  # 'carpeta' | 'exportar_zip' | 'importar_zip'
        self.solo_analisis = bool(solo_analisis)
        self.dir_origen = dir_origen
        self.dir_destino = dir_destino
        self.ruta_zip = ruta_zip
        self.modo_liviano = bool(modo_liviano)
        self.forzar_reemplazo = bool(forzar_reemplazo)
        self.fecha_ini = fecha_ini
        self.fecha_fin = fecha_fin
        self._cancelado = False

    def solicitar_cancelacion(self):
        self._cancelado = True

    def run(self):
        res = {
            'operacion': self.operacion,
            'solo_analisis': self.solo_analisis,
            'ok': False,
            'cancelado': False,
            'nuevos': 0,
            'actualizados': 0,
            'omitidos': 0,
            'excluidos': 0,
            'errores': 0,
            'bytes': 0,
            'mensaje': '',
        }

        try:
            if self.operacion == 'carpeta':
                self._ejecutar_carpeta(res)
            elif self.operacion == 'exportar_zip':
                self._ejecutar_exportar_zip(res)
            elif self.operacion == 'importar_zip':
                self._ejecutar_importar_zip(res)
            else:
                res['mensaje'] = f"Operación no reconocida: {self.operacion}"
        except Exception as exc:
            res['errores'] += 1
            res['mensaje'] = f"Error inesperado: {exc}"
            self.bitacora.emit(f"❌ {res['mensaje']}")

        self.finalizado.emit(res)

    def _ejecutar_carpeta(self, res: dict):
        self.bitacora.emit(f"Analizando origen: {self.dir_origen}")
        self.bitacora.emit(f"Comparando con destino: {self.dir_destino}")
        if self.fecha_ini and self.fecha_fin:
            self.bitacora.emit(f"Período filtrado: {self.fecha_ini.strftime('%d/%m/%Y')} al {self.fecha_fin.strftime('%d/%m/%Y')}")
        self.bitacora.emit(f"Modo: {'Liviano (omite mseed/registros y .pdf)' if self.modo_liviano else 'Completo (todo)'}")

        plan = planificar_sincronizacion_carpeta(
            self.dir_origen,
            self.dir_destino,
            modo_liviano=self.modo_liviano,
            fecha_ini=self.fecha_ini,
            fecha_fin=self.fecha_fin,
        )
        items = [('nuevo', it) for it in plan['nuevos']] + [('act', it) for it in plan['actualizar']]
        res['omitidos'] = plan['omitidos']
        res['excluidos'] = plan['excluidos']
        res['bytes'] = plan['bytes_a_copiar']

        self.bitacora.emit(
            f"Resultado del análisis:\n"
            f"  • Archivos nuevos a copiar:      {len(plan['nuevos'])}\n"
            f"  • Archivos más recientes:        {len(plan['actualizar'])}\n"
            f"  • Omitidos (ya actualizados):    {plan['omitidos']}\n"
            f"  • Excluidos por filtro liviano:  {plan['excluidos']} ({formatear_tamano(plan['bytes_excluidos'])})\n"
            f"  • Volumen total a transferir:    {formatear_tamano(plan['bytes_a_copiar'])}"
        )

        if self.solo_analisis:
            res['nuevos'] = len(plan['nuevos'])
            res['actualizados'] = len(plan['actualizar'])
            res['ok'] = True
            res['mensaje'] = "Análisis completado (sin copiar archivos)."
            self.progreso.emit(1, 1, res['mensaje'])
            return

        total = max(1, len(items))
        raiz_dest = os.path.abspath(self.dir_destino)
        os.makedirs(raiz_dest, exist_ok=True)

        for idx, (tipo, (ruta_orig, ruta_rel, _tam, _mt)) in enumerate(items, start=1):
            if self._cancelado:
                res['cancelado'] = True
                res['mensaje'] = "Respaldo cancelado por el usuario."
                self.bitacora.emit("⚠ Proceso cancelado por el usuario.")
                return
            ruta_dest = os.path.join(raiz_dest, ruta_rel)
            try:
                copiar_archivo_atomico(ruta_orig, ruta_dest)
                if tipo == 'nuevo':
                    res['nuevos'] += 1
                else:
                    res['actualizados'] += 1
            except Exception as e_cp:
                res['errores'] += 1
                self.bitacora.emit(f"  ❌ Error copiando {ruta_rel}: {e_cp}")

            if idx % 20 == 0 or idx == len(items):
                self.progreso.emit(idx, total, f"Copiando ({idx}/{len(items)}): {ruta_rel}")

        escribir_marcador_tipo_bd(raiz_dest, modo_liviano=self.modo_liviano, origen=self.dir_origen)
        res['ok'] = True
        res['mensaje'] = (
            f"Respaldo completado: {res['nuevos']} nuevos, {res['actualizados']} actualizados, "
            f"{res['omitidos']} omitidos, {res['errores']} errores."
        )
        self.progreso.emit(total, total, res['mensaje'])

    def _ejecutar_exportar_zip(self, res: dict):
        self.bitacora.emit(f"Analizando origen para ZIP: {self.dir_origen}")
        if self.fecha_ini and self.fecha_fin:
            self.bitacora.emit(f"Período filtrado: {self.fecha_ini.strftime('%d/%m/%Y')} al {self.fecha_fin.strftime('%d/%m/%Y')}")
        self.bitacora.emit(f"Modo: {'Liviano (omite mseed/registros y .pdf)' if self.modo_liviano else 'Completo (todo)'}")

        plan = planificar_sincronizacion_carpeta(
            self.dir_origen,
            dir_destino=None,
            modo_liviano=self.modo_liviano,
            fecha_ini=self.fecha_ini,
            fecha_fin=self.fecha_fin,
        )
        items = plan['nuevos']
        res['excluidos'] = plan['excluidos']
        res['bytes'] = plan['bytes_a_copiar']

        self.bitacora.emit(
            f"Resultado del análisis ZIP:\n"
            f"  • Archivos a empaquetar:         {len(items)}\n"
            f"  • Excluidos por filtro liviano:  {plan['excluidos']} ({formatear_tamano(plan['bytes_excluidos'])})\n"
            f"  • Tamaño sin comprimir:          {formatear_tamano(plan['bytes_a_copiar'])}"
        )

        if self.solo_analisis:
            res['nuevos'] = len(items)
            res['ok'] = True
            res['mensaje'] = "Análisis ZIP completado (sin generar archivo)."
            self.progreso.emit(1, 1, res['mensaje'])
            return

        os.makedirs(os.path.dirname(os.path.abspath(self.ruta_zip)), exist_ok=True)
        ruta_zip_tmp = self.ruta_zip + ".rsa_tmp"
        total = max(1, len(items))
        mtimes_map = {}

        try:
            with zipfile.ZipFile(ruta_zip_tmp, 'w', compression=zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
                for idx, (ruta_orig, ruta_rel, _tam, mtime) in enumerate(items, start=1):
                    if self._cancelado:
                        res['cancelado'] = True
                        res['mensaje'] = "Exportación ZIP cancelada por el usuario."
                        self.bitacora.emit("⚠ Proceso cancelado por el usuario.")
                        return
                    arcname = ruta_rel.replace('\\', '/')
                    try:
                        zf.write(ruta_orig, arcname=arcname)
                        mtimes_map[arcname] = mtime
                        res['nuevos'] += 1
                    except Exception as e_z:
                        res['errores'] += 1
                        self.bitacora.emit(f"  ❌ Error empaquetando {arcname}: {e_z}")

                    if idx % 20 == 0 or idx == len(items):
                        self.progreso.emit(idx, total, f"Empaquetando ({idx}/{len(items)}): {arcname}")

                manifiesto = {
                    'creado_en': datetime.now().isoformat(),
                    'origen': os.path.abspath(self.dir_origen),
                    'modo': 'liviano' if self.modo_liviano else 'completo',
                    'total_archivos': res['nuevos'],
                    'archivos_mtime': mtimes_map,
                }
                zf.writestr(NOMBRE_MANIFIESTO_ZIP, json.dumps(manifiesto, ensure_ascii=False))

            os.replace(ruta_zip_tmp, self.ruta_zip)
            tam_zip = os.path.getsize(self.ruta_zip)
            res['ok'] = True
            res['mensaje'] = (
                f"ZIP generado: {res['nuevos']} archivos ({formatear_tamano(tam_zip)}) en {os.path.basename(self.ruta_zip)}"
            )
            self.bitacora.emit(f"✓ Archivo ZIP guardado: {self.ruta_zip} ({formatear_tamano(tam_zip)})")
            self.progreso.emit(total, total, res['mensaje'])
        finally:
            if os.path.exists(ruta_zip_tmp):
                try:
                    os.remove(ruta_zip_tmp)
                except OSError:
                    pass

    def _ejecutar_importar_zip(self, res: dict):
        self.bitacora.emit(f"Analizando ZIP: {self.ruta_zip}")
        self.bitacora.emit(f"Destino de extracción: {self.dir_destino}")
        self.bitacora.emit(
            f"Política: {'Forzar reemplazo total' if self.forzar_reemplazo else 'Incremental (solo nuevos o más recientes)'}"
        )

        plan = planificar_importacion_zip(
            self.ruta_zip, self.dir_destino, forzar_reemplazo=self.forzar_reemplazo
        )
        items = [('nuevo', it) for it in plan['nuevos']] + [('act', it) for it in plan['actualizar']]
        res['omitidos'] = plan['omitidos']
        res['bytes'] = plan['bytes_a_extraer']

        manif = plan.get('manifiesto') or {}
        if manif:
            self.bitacora.emit(
                f"Manifiesto detectado: creado {manif.get('creado_en', '?')} | "
                f"modo={manif.get('modo', '?')} | origen={manif.get('origen', '?')}"
            )
        self.bitacora.emit(
            f"Resultado del análisis:\n"
            f"  • Archivos nuevos a extraer:     {len(plan['nuevos'])}\n"
            f"  • Archivos a actualizar:         {len(plan['actualizar'])}\n"
            f"  • Omitidos (destino vigente):    {plan['omitidos']}\n"
            f"  • Volumen a extraer:             {formatear_tamano(plan['bytes_a_extraer'])}"
        )

        if self.solo_analisis:
            res['nuevos'] = len(plan['nuevos'])
            res['actualizados'] = len(plan['actualizar'])
            res['ok'] = True
            res['mensaje'] = "Análisis del ZIP completado (sin extraer archivos)."
            self.progreso.emit(1, 1, res['mensaje'])
            return

        total = max(1, len(items))
        os.makedirs(os.path.abspath(self.dir_destino), exist_ok=True)

        with zipfile.ZipFile(self.ruta_zip, 'r') as zf:
            for idx, (tipo, (nombre_zip, ruta_dest, _tam, mtime_zip)) in enumerate(items, start=1):
                if self._cancelado:
                    res['cancelado'] = True
                    res['mensaje'] = "Extracción cancelada por el usuario."
                    self.bitacora.emit("⚠ Proceso cancelado por el usuario.")
                    return
                try:
                    os.makedirs(os.path.dirname(ruta_dest), exist_ok=True)
                    ruta_tmp = ruta_dest + ".rsa_tmp"
                    with zf.open(nombre_zip, 'r') as f_in, open(ruta_tmp, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out, length=1024 * 1024)
                    if mtime_zip and mtime_zip > 0:
                        os.utime(ruta_tmp, (mtime_zip, mtime_zip))
                    os.replace(ruta_tmp, ruta_dest)
                    if tipo == 'nuevo':
                        res['nuevos'] += 1
                    else:
                        res['actualizados'] += 1
                except Exception as e_ex:
                    res['errores'] += 1
                    self.bitacora.emit(f"  ❌ Error extrayendo {nombre_zip}: {e_ex}")

                if idx % 20 == 0 or idx == len(items):
                    self.progreso.emit(idx, total, f"Extrayendo ({idx}/{len(items)}): {nombre_zip}")

        modo_zip_liv = (str(manif.get('modo', '')).strip().lower() == 'liviano') if manif else False
        escribir_marcador_tipo_bd(self.dir_destino, modo_liviano=modo_zip_liv, origen=self.ruta_zip)
        res['ok'] = True
        res['mensaje'] = (
            f"Extracción completada: {res['nuevos']} nuevos, {res['actualizados']} actualizados, "
            f"{res['omitidos']} omitidos, {res['errores']} errores."
        )
        self.progreso.emit(total, total, res['mensaje'])


class RespaldoBaseDatos(QMainWindow):
    """Ventana de Respaldo y Sincronización de Base de Datos Sísmica (DIA)."""

    cerrado = pyqtSignal()

    def __init__(self, directorio_trabajo="", parent=None):
        super().__init__(parent)
        ruta_ui = os.path.abspath(os.path.join(ruta_proyecto, 'src', 'ui', 'respaldo_base_datos.ui'))
        uic.loadUi(ruta_ui, self)

        self.directorio_trabajo = str(directorio_trabajo or "").strip()
        self.hilo_trabajo = None

        # Sugerir rutas por defecto sensatas según lo que exista en la PC
        origen_def = self._detectar_origen_por_defecto()
        destino_def = "C:\\DIA" if os.path.isdir("C:\\DIA") else ""

        self.txt_origen_carpeta.setText(origen_def)
        self.txt_destino_carpeta.setText(destino_def if destino_def.lower() != origen_def.lower() else "")
        self.txt_origen_zip.setText(origen_def)
        self.txt_destino_importar.setText(destino_def or origen_def)

        hoy = QDate.currentDate()
        hace_30 = hoy.addDays(-30)
        self.date_carpeta_ini.setDate(hace_30)
        self.date_carpeta_fin.setDate(hoy)
        self.date_zip_ini.setDate(hace_30)
        self.date_zip_fin.setDate(hoy)

        self.chk_periodo_carpeta.stateChanged.connect(self._actualizar_checks_periodo)
        self.chk_periodo_zip.stateChanged.connect(self._actualizar_checks_periodo)
        self._actualizar_checks_periodo()

        # Conectar examinadores
        self.btn_examinar_origen_carpeta.clicked.connect(lambda: self._elegir_carpeta(self.txt_origen_carpeta, "Seleccionar carpeta origen"))
        self.btn_examinar_destino_carpeta.clicked.connect(lambda: self._elegir_carpeta(self.txt_destino_carpeta, "Seleccionar carpeta destino"))
        self.btn_examinar_origen_zip.clicked.connect(lambda: self._elegir_carpeta(self.txt_origen_zip, "Seleccionar carpeta a comprimir"))
        self.btn_examinar_zip_salida.clicked.connect(self._elegir_zip_salida)
        self.btn_examinar_zip_entrada.clicked.connect(self._elegir_zip_entrada)
        self.btn_examinar_destino_importar.clicked.connect(lambda: self._elegir_carpeta(self.txt_destino_importar, "Seleccionar carpeta destino de extracción"))

        # Conectar acciones
        self.btn_analizar_carpeta.clicked.connect(lambda: self._lanzar_carpeta(solo_analisis=True))
        self.btn_ejecutar_carpeta.clicked.connect(lambda: self._lanzar_carpeta(solo_analisis=False))
        self.btn_analizar_zip_exp.clicked.connect(lambda: self._lanzar_exportar_zip(solo_analisis=True))
        self.btn_ejecutar_zip_exp.clicked.connect(lambda: self._lanzar_exportar_zip(solo_analisis=False))
        self.btn_analizar_zip_imp.clicked.connect(lambda: self._lanzar_importar_zip(solo_analisis=True))
        self.btn_ejecutar_zip_imp.clicked.connect(lambda: self._lanzar_importar_zip(solo_analisis=False))

        self.btn_cancelar_respaldo.clicked.connect(self._cancelar_operacion)
        self.btn_salir_respaldo.clicked.connect(self.close)

    def _detectar_origen_por_defecto(self) -> str:
        for cand in (
            r"G:\Mi unidad\DIA",
            r"G:\DIA",
            self.directorio_trabajo,
            r"C:\DIA",
        ):
            if cand and os.path.isdir(cand):
                return os.path.normpath(cand)
        return ""

    def _elegir_carpeta(self, line_edit, titulo):
        actual = line_edit.text().strip() or self._detectar_origen_por_defecto()
        carpeta = QFileDialog.getExistingDirectory(self, titulo, actual)
        if carpeta:
            line_edit.setText(os.path.normpath(carpeta))

    def _elegir_zip_salida(self):
        sugerido = f"respaldo_DIA_{datetime.now().strftime('%Y%m%d_%H%M')}.zip"
        base_dir = os.path.dirname(self.txt_archivo_zip_salida.text().strip()) or os.path.expanduser("~\\Desktop")
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Guardar archivo ZIP de respaldo", os.path.join(base_dir, sugerido), "Archivos ZIP (*.zip)"
        )
        if ruta:
            if not ruta.lower().endswith('.zip'):
                ruta += '.zip'
            self.txt_archivo_zip_salida.setText(os.path.normpath(ruta))

    def _elegir_zip_entrada(self):
        base_dir = os.path.dirname(self.txt_archivo_zip_entrada.text().strip()) or os.path.expanduser("~\\Desktop")
        ruta, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar archivo ZIP de respaldo", base_dir, "Archivos ZIP (*.zip)"
        )
        if ruta:
            self.txt_archivo_zip_entrada.setText(os.path.normpath(ruta))

    def _establecer_ejecutando(self, ejecutando: bool):
        self.tabs_respaldo.setEnabled(not ejecutando)
        self.btn_cancelar_respaldo.setEnabled(ejecutando)
        self.btn_salir_respaldo.setEnabled(not ejecutando)

    def _iniciar_hilo(self, hilo: HiloRespaldoBaseDatos):
        self.txt_bitacora_respaldo.clear()
        self.barra_progreso_respaldo.setRange(0, 1)
        self.barra_progreso_respaldo.setValue(0)
        self.lbl_estado_respaldo.setText("Ejecutando operación...")
        self._establecer_ejecutando(True)

        self.hilo_trabajo = hilo
        hilo.progreso.connect(self._al_progresar)
        hilo.bitacora.connect(self.txt_bitacora_respaldo.appendPlainText)
        hilo.finalizado.connect(self._al_finalizar)
        hilo.start()

    def _actualizar_checks_periodo(self):
        hab_c = self.chk_periodo_carpeta.isChecked()
        self.date_carpeta_ini.setEnabled(hab_c)
        self.date_carpeta_fin.setEnabled(hab_c)
        hab_z = self.chk_periodo_zip.isChecked()
        self.date_zip_ini.setEnabled(hab_z)
        self.date_zip_fin.setEnabled(hab_z)

    def _lanzar_carpeta(self, solo_analisis: bool):
        orig = self.txt_origen_carpeta.text().strip()
        dest = self.txt_destino_carpeta.text().strip()
        if not orig or not os.path.isdir(orig):
            QMessageBox.warning(self, "Origen inválido", "Seleccione una carpeta de ORIGEN existente.")
            return
        if not dest:
            QMessageBox.warning(self, "Destino inválido", "Indique la carpeta de DESTINO para el respaldo.")
            return
        if rutas_se_solapan(orig, dest):
            QMessageBox.warning(
                self, "Rutas inválidas",
                "La carpeta de origen y destino no pueden ser la misma ni una contener a la otra."
            )
            return

        f_ini, f_fin = None, None
        if self.chk_periodo_carpeta.isChecked():
            f_ini = self.date_carpeta_ini.date().toPyDate()
            f_fin = self.date_carpeta_fin.date().toPyDate()
            if f_ini > f_fin:
                QMessageBox.warning(self, "Período inválido", "La fecha Desde no puede ser posterior a Hasta.")
                return

        hilo = HiloRespaldoBaseDatos(
            operacion='carpeta',
            solo_analisis=solo_analisis,
            dir_origen=orig,
            dir_destino=dest,
            modo_liviano=self.rb_carpeta_liviano.isChecked(),
            fecha_ini=f_ini,
            fecha_fin=f_fin,
            parent=self,
        )
        self._iniciar_hilo(hilo)

    def _lanzar_exportar_zip(self, solo_analisis: bool):
        orig = self.txt_origen_zip.text().strip()
        ruta_z = self.txt_archivo_zip_salida.text().strip()
        if not orig or not os.path.isdir(orig):
            QMessageBox.warning(self, "Origen inválido", "Seleccione una carpeta de ORIGEN existente.")
            return
        if not solo_analisis and not ruta_z:
            QMessageBox.warning(self, "Archivo ZIP requerido", "Indique la ruta donde se guardará el archivo .zip.")
            return
        if ruta_z and rutas_se_solapan(orig, os.path.dirname(os.path.abspath(ruta_z))):
            QMessageBox.warning(
                self, "Ruta ZIP inválida",
                "Guarde el archivo .zip fuera de la carpeta de origen para evitar incluir el propio ZIP."
            )
            return

        f_ini, f_fin = None, None
        if self.chk_periodo_zip.isChecked():
            f_ini = self.date_zip_ini.date().toPyDate()
            f_fin = self.date_zip_fin.date().toPyDate()
            if f_ini > f_fin:
                QMessageBox.warning(self, "Período inválido", "La fecha Desde no puede ser posterior a Hasta.")
                return

        hilo = HiloRespaldoBaseDatos(
            operacion='exportar_zip',
            solo_analisis=solo_analisis,
            dir_origen=orig,
            ruta_zip=ruta_z,
            modo_liviano=self.rb_zip_liviano.isChecked(),
            fecha_ini=f_ini,
            fecha_fin=f_fin,
            parent=self,
        )
        self._iniciar_hilo(hilo)

    def _lanzar_importar_zip(self, solo_analisis: bool):
        ruta_z = self.txt_archivo_zip_entrada.text().strip()
        dest = self.txt_destino_importar.text().strip()
        if not ruta_z or not os.path.isfile(ruta_z):
            QMessageBox.warning(self, "ZIP no encontrado", "Seleccione un archivo .zip válido.")
            return
        if not dest:
            QMessageBox.warning(self, "Destino requerido", "Indique la carpeta de DESTINO donde se extraerá el ZIP.")
            return

        hilo = HiloRespaldoBaseDatos(
            operacion='importar_zip',
            solo_analisis=solo_analisis,
            ruta_zip=ruta_z,
            dir_destino=dest,
            forzar_reemplazo=self.chk_forzar_reemplazo_zip.isChecked(),
            parent=self,
        )
        self._iniciar_hilo(hilo)

    def _al_progresar(self, actual: int, total: int, texto: str):
        self.barra_progreso_respaldo.setMaximum(max(1, total))
        self.barra_progreso_respaldo.setValue(min(actual, max(1, total)))
        self.lbl_estado_respaldo.setText(texto)

    def _cancelar_operacion(self):
        if self.hilo_trabajo and self.hilo_trabajo.isRunning():
            self.hilo_trabajo.solicitar_cancelacion()
            self.btn_cancelar_respaldo.setEnabled(False)
            self.lbl_estado_respaldo.setText("Cancelando al terminar el archivo actual...")

    def _al_finalizar(self, res: dict):
        self._establecer_ejecutando(False)
        self.lbl_estado_respaldo.setText(res.get('mensaje', 'Finalizado.'))
        self.txt_bitacora_respaldo.appendPlainText(f"\n=== {res.get('mensaje', 'Finalizado')} ===")
        if res.get('ok') and not res.get('solo_analisis'):
            QMessageBox.information(self, "Respaldo de Base de Datos", res.get('mensaje', 'Completado.'))
        elif not res.get('ok') and not res.get('cancelado'):
            QMessageBox.warning(self, "Aviso de Respaldo", res.get('mensaje', 'Ocurrió un inconveniente.'))

    def limpiar_estado(self):
        if self.hilo_trabajo and self.hilo_trabajo.isRunning():
            self.hilo_trabajo.solicitar_cancelacion()
            self.hilo_trabajo.wait(5000)
        self.hilo_trabajo = None

    def closeEvent(self, event):
        self.limpiar_estado()
        self.cerrado.emit()
        event.accept()
