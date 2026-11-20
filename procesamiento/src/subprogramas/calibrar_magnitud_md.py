"""
================================================================================
Subprograma: calibrar_magnitud_md.py
Propósito:   Calibración empírica de coeficientes de Magnitud de Duración (Md)
             por estación para Mag2000.txt (Lee et al., 1972 / Iaspei.frm /
             FASTHYPO):
                 Md = b1 + c1 * log10(Coda) + c2 * dist_km

             Recolecta eventos bien caracterizados desde el árbol ..\DIA\
             cruzando catálogos diarios (_cat.csv con referencias USGS, IGEPN y
             RSA) y salidas hipocentrales (.rsa en fastHypo/), ejecuta la
             regresión lineal múltiple por estación, muestra gráficas de ajuste
             y genera los archivos CSV, reporte técnico y Mag2000.txt.
================================================================================
"""

import csv
import datetime
import math
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)


def extraer_hasta_directorio(ruta_completa: str, nombre_directorio: str) -> str:
    partes = Path(ruta_completa).parts
    if nombre_directorio in partes:
        indice = partes.index(nombre_directorio)
        return str(Path(*partes[: indice + 1])) + "/"
    return ""


ruta_modulo = os.path.dirname(os.path.abspath(__file__))
ruta_proyecto = extraer_hasta_directorio(ruta_modulo, "procesamiento")
if not ruta_proyecto:
    ruta_proyecto = os.path.abspath(os.path.join(ruta_modulo, "..", ".."))
ruta_librerias = os.path.abspath(os.path.join(ruta_proyecto, "src", "librerias"))
ruta_datos = os.path.abspath(os.path.join(ruta_proyecto, "datos"))
if ruta_librerias not in sys.path:
    sys.path.insert(0, ruta_librerias)

try:
    from rsa_utilidades import cargar_config_local_pc
except Exception:
    def cargar_config_local_pc() -> dict:
        return {"directorio_trabajo": ""}


# =============================================================================
# LÓGICA DE EXTRACCIÓN, REGRESIÓN Y GENERACIÓN DE ARCHIVOS (REUTILIZABLE / CLI)
# =============================================================================

COLUMNAS_DATASET = [
    "Incluir",
    "Fecha_Hora",
    "Evento_ID",
    "Estacion",
    "Dist_km",
    "Coda_s",
    "RMS_s",
    "N_Estaciones",
    "Fuente_Ref",
    "Mag_Ref",
    "Tipo_Mag_Ref",
    "Archivo_RSA",
]

PRIORIDADES_FUENTE = {
    "USGS > IGEPN > RSA": ["USGS", "IGEPN", "RSA"],
    "IGEPN > USGS > RSA": ["IGEPN", "USGS", "RSA"],
    "Solo USGS e IGEPN": ["USGS", "IGEPN"],
    "Solo USGS": ["USGS"],
    "Solo IGEPN": ["IGEPN"],
    "Solo RSA (Transferencia)": ["RSA"],
}


def _a_float(valor, defecto: Optional[float] = None) -> Optional[float]:
    if valor is None:
        return defecto
    txt = str(valor).strip().replace(",", ".")
    if not txt or txt.upper() in ("NMG", "NAN", "NONE", "---"):
        return defecto
    try:
        return float(txt)
    except ValueError:
        return defecto


def extraer_datos_archivo_rsa(ruta_rsa: Path) -> Optional[dict]:
    """
    Extrae fecha, RMS, número de estaciones y lecturas (estacion, dist_km, coda_s)
    desde un archivo .rsa generado por FASTHYPO + Iaspei.frm.
    """
    try:
        lineas = ruta_rsa.read_bytes().decode("latin-1", errors="replace").splitlines()
    except Exception:
        return None

    rms: Optional[float] = None
    fecha_dt: Optional[datetime.datetime] = None
    distancias_tabla: Dict[str, float] = {}
    lecturas_mag: List[Tuple[str, float, float]] = []

    en_tabla_sta = False
    en_bloque_mag = False

    for ln in lineas:
        s = ln.strip()
        if not s:
            if en_tabla_sta and distancias_tabla:
                en_tabla_sta = False
            continue

        if s.lower().startswith("sta") and "dist" in s.lower() and "azm" in s.lower():
            en_tabla_sta = True
            continue

        if en_tabla_sta:
            partes = s.split()
            if len(partes) >= 4 and len(partes[0]) <= 5:
                d_val = _a_float(partes[1])
                if d_val is not None:
                    distancias_tabla[partes[0].upper()] = d_val
            else:
                en_tabla_sta = False

        if "event is dated:" in s.lower():
            nums = re.findall(r"\d+", s.split(":", 1)[1])
            if len(nums) >= 5:
                try:
                    yy, mm, dd, hh, mi = (int(x) for x in nums[:5])
                    anio = 2000 + yy if yy < 80 else 1900 + yy
                    fecha_dt = datetime.datetime(anio, mm, dd, hh, mi, 0)
                except ValueError:
                    pass

        if s.lower().startswith("rms="):
            rms = _a_float(s.split("=", 1)[1])

        if "CALCULO DE LA MAGNITUD" in s.upper():
            en_bloque_mag = True
            continue

        if en_bloque_mag:
            if s.lower().startswith("sta") and "coda" in s.lower():
                continue
            if "promedio" in s.lower():
                en_bloque_mag = False
                continue
            partes = s.split()
            if len(partes) >= 3:
                sta = partes[0].upper()
                dist_val = _a_float(partes[1])
                coda_val = _a_float(partes[2], 0.0)
                if dist_val is not None:
                    lecturas_mag.append((sta, dist_val, coda_val or 0.0))

    if not lecturas_mag and distancias_tabla:
        for sta, dist_val in distancias_tabla.items():
            lecturas_mag.append((sta, dist_val, 0.0))

    if not lecturas_mag:
        return None

    return {
        "archivo_rsa": str(ruta_rsa),
        "nombre_rsa": ruta_rsa.name,
        "fecha_dt": fecha_dt,
        "rms": rms if rms is not None else 99.0,
        "n_estaciones": max(len(distancias_tabla), len(lecturas_mag)),
        "lecturas": lecturas_mag,
    }


def leer_catalogo_diario_csv(ruta_cat: Path) -> List[dict]:
    """
    Lee un archivo *_cat.csv del árbol ..\DIA\ y extrae eventos con su fuente
    (USGS, IGEPN, RSA), fecha/hora, magnitud, tipo de magnitud y código de evento.
    """
    registros: List[dict] = []
    try:
        with open(ruta_cat, "r", encoding="latin-1", errors="replace", newline="") as f:
            lector = csv.reader(f, delimiter=";")
            filas = list(lector)
        # Si no usó ';', probar con ','
        if filas and len(filas[0]) < 10:
            with open(ruta_cat, "r", encoding="latin-1", errors="replace", newline="") as f:
                filas = list(csv.reader(f, delimiter=","))
    except Exception:
        return registros

    for fila in filas:
        if len(fila) < 18:
            continue
        anio = _a_float(fila[1])
        mes = _a_float(fila[2])
        dia = _a_float(fila[3])
        hora = _a_float(fila[4])
        minu = _a_float(fila[5])
        seg = _a_float(fila[6], 0.0)
        mag = _a_float(fila[15])
        if None in (anio, mes, dia, hora, minu) or mag is None or mag <= 0.0:
            continue
        try:
            a_i = int(anio)
            if a_i < 100:
                a_i += 2000
            dt = datetime.datetime(a_i, int(mes), int(dia), int(hora), int(minu), max(0, min(59, int(seg or 0))))
        except ValueError:
            continue

        fuente_raw = str(fila[17]).strip().upper()
        if "USGS" in fuente_raw:
            fuente = "USGS"
        elif "IGEPN" in fuente_raw or "IG-" in fuente_raw or "IGEP" in fuente_raw:
            fuente = "IGEPN"
        elif "RSA" in fuente_raw or fuente_raw == "":
            fuente = "RSA"
        else:
            fuente = fuente_raw

        registros.append(
            {
                "fecha_dt": dt,
                "mag": float(mag),
                "tipo_mag": str(fila[16]).strip() if len(fila) > 16 else "",
                "fuente": fuente,
                "rms": _a_float(fila[10], 99.0),
                "evento_id": str(fila[18]).strip() if len(fila) > 18 else "",
            }
        )
    return registros


def recolectar_dataset_calibracion(
    dir_trabajo: Path,
    fecha_ini: datetime.date,
    fecha_fin: datetime.date,
    rms_max: float = 0.35,
    min_estaciones: int = 3,
    coda_min: float = 5.0,
    coda_max: float = 600.0,
    dist_min: float = 1.0,
    dist_max: float = 400.0,
    mag_min: float = 1.0,
    mag_max: float = 7.5,
    prioridad_fuentes: Optional[List[str]] = None,
    ventana_cruce_seg: int = 120,
    callback_progreso=None,
) -> List[dict]:
    """
    Recorre el árbol ..\DIA\ en el rango de fechas, empareja archivos .rsa en
    fastHypo/ con referencias de magnitud en *_cat.csv (priorizando USGS/IGEPN/RSA)
    y construye el dataset de lecturas (estacion, dist_km, coda_s, mag_ref).
    """
    prioridad = prioridad_fuentes or ["USGS", "IGEPN", "RSA"]
    anios = range(fecha_ini.year, fecha_fin.year + 1)
    archivos_rsa: List[Path] = []
    catalogos_eventos: List[dict] = []

    for anio in anios:
        base_anio = dir_trabajo / str(anio)
        if not base_anio.exists():
            # También permitir apuntar directamente a una carpeta con .rsa y _cat.csv
            continue
        for p_cat in base_anio.rglob("*_cat.csv"):
            catalogos_eventos.extend(leer_catalogo_diario_csv(p_cat))
        for p_rsa in base_anio.rglob("*.rsa"):
            archivos_rsa.append(p_rsa)

    # Si no se halló subestructura por año, buscar directamente bajo dir_trabajo
    if not archivos_rsa and dir_trabajo.exists():
        for p_cat in dir_trabajo.rglob("*_cat.csv"):
            catalogos_eventos.extend(leer_catalogo_diario_csv(p_cat))
        for p_rsa in dir_trabajo.rglob("*.rsa"):
            archivos_rsa.append(p_rsa)

    dataset: List[dict] = []
    total = max(1, len(archivos_rsa))

    for idx, ruta_rsa in enumerate(sorted(archivos_rsa), 1):
        if callback_progreso:
            callback_progreso(int((idx / total) * 100), f"Analizando {ruta_rsa.name} ({idx}/{total})...")

        info = extraer_datos_archivo_rsa(ruta_rsa)
        if not info or info["fecha_dt"] is None:
            continue

        dt_ev = info["fecha_dt"]
        if not (fecha_ini <= dt_ev.date() <= fecha_fin):
            continue
        if info["rms"] > rms_max or info["n_estaciones"] < min_estaciones:
            continue

        # Buscar la mejor magnitud de referencia dentro de la ventana temporal
        candidatos = [
            ev
            for ev in catalogos_eventos
            if abs((ev["fecha_dt"] - dt_ev).total_seconds()) <= ventana_cruce_seg
            and mag_min <= ev["mag"] <= mag_max
        ]
        mejor_ref = None
        for f_prio in prioridad:
            coinc = [c for c in candidatos if c["fuente"] == f_prio]
            if coinc:
                coinc.sort(key=lambda c: abs((c["fecha_dt"] - dt_ev).total_seconds()))
                mejor_ref = coinc[0]
                break

        if mejor_ref is None:
            continue

        ev_id = mejor_ref["evento_id"] or dt_ev.strftime("%Y%m%d_%H%M")
        for sta, dist_km, coda_s in info["lecturas"]:
            if not (coda_min <= coda_s <= coda_max):
                continue
            if not (dist_min <= dist_km <= dist_max):
                continue
            dataset.append(
                {
                    "Incluir": True,
                    "Fecha_Hora": dt_ev.strftime("%Y-%m-%d %H:%M"),
                    "Evento_ID": ev_id,
                    "Estacion": sta,
                    "Dist_km": round(dist_km, 2),
                    "Coda_s": round(coda_s, 2),
                    "RMS_s": round(info["rms"], 3),
                    "N_Estaciones": info["n_estaciones"],
                    "Fuente_Ref": mejor_ref["fuente"],
                    "Mag_Ref": round(mejor_ref["mag"], 2),
                    "Tipo_Mag_Ref": mejor_ref["tipo_mag"] or "Md",
                    "Archivo_RSA": info["nombre_rsa"],
                }
            )

    return dataset


def ajustar_coeficientes_estacion(
    filas_estacion: List[dict],
    filtrar_outliers: bool = True,
    fijar_c2_cero: bool = False,
    forzar_c2_no_negativo: bool = True,
    min_eventos: int = 5,
) -> dict:
    """
    Ajusta Md = b1 + c1 * log10(Coda) + c2 * dist_km por mínimos cuadrados.
    Retorna diccionario con coeficientes, métricas (R2, sigma, sesgo) y predicciones.
    """
    validas = [
        f for f in filas_estacion
        if f.get("Incluir", True) and f["Coda_s"] > 0 and f["Mag_Ref"] > 0
    ]
    n_tot = len(validas)
    if n_tot < 3:
        return {
            "n_usados": n_tot,
            "n_excluidos": 0,
            "b1": 0.0,
            "c1": 0.0,
            "c2": 0.0,
            "r2": 0.0,
            "sigma": 0.0,
            "sesgo": 0.0,
            "estado": "Insuficientes (<3)",
            "mascara": [True] * n_tot,
            "y_pred": [],
            "residuales": [],
        }

    log_coda = np.array([math.log10(f["Coda_s"]) for f in validas], dtype=float)
    dist = np.array([float(f["Dist_km"]) for f in validas], dtype=float)
    y = np.array([float(f["Mag_Ref"]) for f in validas], dtype=float)

    def _resolver(mask: np.ndarray) -> Tuple[float, float, float]:
        lc = log_coda[mask]
        dd = dist[mask]
        yy = y[mask]
        if fijar_c2_cero or np.std(dd) < 1e-6:
            X = np.column_stack([np.ones_like(lc), lc])
            coef, *_ = np.linalg.lstsq(X, yy, rcond=None)
            return float(coef[0]), float(coef[1]), 0.0
        X = np.column_stack([np.ones_like(lc), lc, dd])
        coef, *_ = np.linalg.lstsq(X, yy, rcond=None)
        b1, c1, c2 = float(coef[0]), float(coef[1]), float(coef[2])
        if forzar_c2_no_negativo and c2 < 0.0:
            X2 = np.column_stack([np.ones_like(lc), lc])
            coef2, *_ = np.linalg.lstsq(X2, yy, rcond=None)
            return float(coef2[0]), float(coef2[1]), 0.0
        return b1, c1, c2

    mascara = np.ones(n_tot, dtype=bool)
    b1, c1, c2 = _resolver(mascara)

    if filtrar_outliers and n_tot >= 6:
        for _ in range(2):
            pred = b1 + c1 * log_coda + c2 * dist
            res = y - pred
            sig = float(np.std(res[mascara]))
            if sig < 1e-6:
                break
            nueva = np.abs(res) <= 2.0 * sig
            if int(np.sum(nueva)) < 3 or np.array_equal(nueva, mascara):
                break
            mascara = nueva
            b1, c1, c2 = _resolver(mascara)

    y_pred = b1 + c1 * log_coda + c2 * dist
    residuales = y_pred - y
    res_u = residuales[mascara]
    y_u = y[mascara]
    ss_res = float(np.sum((y_u - y_pred[mascara]) ** 2))
    ss_tot = float(np.sum((y_u - np.mean(y_u)) ** 2))
    r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 1e-9 else 1.0
    sigma = float(np.std(res_u, ddof=1)) if len(res_u) > 1 else 0.0
    sesgo = float(np.mean(res_u)) if len(res_u) > 0 else 0.0
    n_usados = int(np.sum(mascara))

    if n_usados < min_eventos:
        estado = f"Pocas muestras (<{min_eventos})"
    elif r2 >= 0.75 and sigma <= 0.30 and c1 > 0.0:
        estado = "Óptimo"
    elif r2 >= 0.50 and sigma <= 0.45 and c1 > 0.0:
        estado = "Aceptable"
    else:
        estado = "Revisar ajuste"

    return {
        "n_usados": n_usados,
        "n_excluidos": n_tot - n_usados,
        "b1": b1,
        "c1": c1,
        "c2": c2,
        "r2": r2,
        "sigma": sigma,
        "sesgo": sesgo,
        "estado": estado,
        "mascara": mascara.tolist(),
        "y_pred": y_pred.tolist(),
        "residuales": residuales.tolist(),
    }


def leer_mag2000_existente(ruta_mag: Path) -> List[Tuple[str, float, float, float]]:
    """Lee un archivo Mag2000.txt existente preservando orden de estaciones."""
    filas: List[Tuple[str, float, float, float]] = []
    if not ruta_mag.exists():
        return filas
    for ln in ruta_mag.read_bytes().decode("latin-1", errors="replace").splitlines():
        if len(ln.strip()) < 10:
            continue
        pad = ln.ljust(35)
        sta = pad[0:4].strip().upper()
        b1 = _a_float(pad[4:13], 0.0) or 0.0
        c1 = _a_float(pad[13:22], 0.0) or 0.0
        c2 = _a_float(pad[22:32], 0.0) or 0.0
        if sta:
            filas.append((sta, b1, c1, c2))
    return filas


def generar_texto_mag2000(
    resumen_estaciones: Dict[str, dict],
    plantilla_previa: Optional[List[Tuple[str, float, float, float]]] = None,
) -> str:
    """
    Genera el contenido de Mag2000.txt con el formato exacto de columnas de Iaspei.frm:
      <STA4> <b1:8.6f> <c1:8.6f> <c2:8.6f>
    Conserva estaciones existentes de la plantilla que no fueron recalibradas.
    """
    orden: List[str] = []
    valores: Dict[str, Tuple[float, float, float]] = {}

    if plantilla_previa:
        for sta, b1, c1, c2 in plantilla_previa:
            if sta not in valores:
                orden.append(sta)
            valores[sta] = (b1, c1, c2)

    for sta in sorted(resumen_estaciones.keys()):
        r = resumen_estaciones[sta]
        if r["n_usados"] >= 3 and r["c1"] > 0.0:
            if sta not in valores:
                orden.append(sta)
            valores[sta] = (r["b1"], r["c1"], r["c2"])

    lineas = []
    for sta in orden:
        b1, c1, c2 = valores[sta]
        lineas.append(f"{sta:<4s} {b1:8.6f} {c1:8.6f} {c2:8.6f}")
    return "\n".join(lineas) + "\n"


# =============================================================================
# HILO EN SEGUNDO PLANO PARA ESCANEO DEL ÁRBOL ..\DIA\
# =============================================================================

class HiloEscaneoEventosMd(QThread):
    progreso = pyqtSignal(int, str)
    finalizado = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, params: dict, parent=None):
        super().__init__(parent)
        self.params = params

    def run(self):
        try:
            datos = recolectar_dataset_calibracion(
                dir_trabajo=Path(self.params["dir_trabajo"]),
                fecha_ini=self.params["fecha_ini"],
                fecha_fin=self.params["fecha_fin"],
                rms_max=self.params["rms_max"],
                min_estaciones=self.params["min_estaciones"],
                coda_min=self.params["coda_min"],
                coda_max=self.params["coda_max"],
                dist_min=self.params["dist_min"],
                dist_max=self.params["dist_max"],
                mag_min=self.params["mag_min"],
                mag_max=self.params["mag_max"],
                prioridad_fuentes=self.params["prioridad_fuentes"],
                callback_progreso=lambda p, m: self.progreso.emit(p, m),
            )
            self.finalizado.emit(datos)
        except Exception as e:
            self.error.emit(str(e))


# =============================================================================
# INTERFAZ PYQT5 INTEGRADA EN CONFIGURACIÓN DE PROGRAMA_INTEGRADO.PY
# =============================================================================

class Calibrar_magnitud_md(QWidget):
    """
    Subprograma de Configuración para calibración empírica de coeficientes de
    Magnitud de Duración (Md = b1 + c1*log10(Coda) + c2*dist_km) y generación
    trazable de Mag2000.txt sobre eventos bien caracterizados (USGS / IGEPN / RSA).
    """

    def __init__(self, directorio_trabajo: str = "", parent=None):
        super().__init__(parent)
        cfg = cargar_config_local_pc()
        self.directorio_trabajo = directorio_trabajo or cfg.get("directorio_trabajo", "")
        self.dataset_actual: List[dict] = []
        self.resultados_estaciones: Dict[str, dict] = {}
        self.hilo_escaneo: Optional[HiloEscaneoEventosMd] = None

        self._construir_ui()

    def _construir_ui(self) -> None:
        layout_raiz = QVBoxLayout(self)
        layout_raiz.setContentsMargins(10, 8, 10, 8)
        layout_raiz.setSpacing(8)

        # Cabecera institucional
        fila_cab = QHBoxLayout()
        lbl_titulo = QLabel(
            "<b>Calibración de Magnitud de Duración (Md — Mag2000.txt)</b><br>"
            "<span style='color:#475569; font-size:11px;'>"
            "Ecuación de Lee et al. (1972) / Iaspei.frm:  Md = b₁ + c₁ · log₁₀(Coda) + c₂ · dist_km  "
            "(referencias: USGS, IGEPN y RSA)</span>"
        )
        fila_cab.addWidget(lbl_titulo, 1)

        self.btn_manual = QPushButton("📖 Manual de Usuario")
        self.btn_manual.setMinimumHeight(32)
        self.btn_manual.setStyleSheet("background-color: #1d4ed8; color: white; font-weight: bold; padding: 0 12px;")
        self.btn_manual.clicked.connect(self.abrir_manual_usuario)
        fila_cab.addWidget(self.btn_manual)

        layout_raiz.addLayout(fila_cab)

        # Pestañas principales
        self.tabs = QTabWidget()
        self.tabs.addTab(self._crear_tab_eventos(), "1. Eventos Bien Caracterizados (USGS / IGEPN / RSA)")
        self.tabs.addTab(self._crear_tab_regresion(), "2. Cálculo de Coeficientes y Mag2000.txt")
        self.tabs.addTab(self._crear_tab_graficas(), "3. Gráficas de Ajuste y Residuales")
        layout_raiz.addWidget(self.tabs, 1)

        # Pie de estado y botón volver
        fila_pie = QHBoxLayout()
        self.lbl_estado = QLabel("Listo. Seleccione el directorio ..\\DIA\\ y escanee eventos o importe un CSV.")
        self.lbl_estado.setStyleSheet("color: #334155; font-size: 11px;")
        fila_pie.addWidget(self.lbl_estado, 1)

        self.btn_volver = QPushButton("Volver al Menú Principal")
        self.btn_volver.setMinimumHeight(32)
        self.btn_volver.clicked.connect(self.close)
        fila_pie.addWidget(self.btn_volver)
        layout_raiz.addLayout(fila_pie)

    def _crear_tab_eventos(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)

        grp_filtros = QGroupBox("Parámetros de Recolección y Criterios de Eventos Bien Caracterizados")
        grid = QGridLayout(grp_filtros)

        grid.addWidget(QLabel("Directorio ..\\DIA\\:"), 0, 0)
        self.txt_dir_trabajo = QLineEdit(self.directorio_trabajo)
        grid.addWidget(self.txt_dir_trabajo, 0, 1, 1, 3)
        btn_dir = QPushButton("Examinar...")
        btn_dir.clicked.connect(self._seleccionar_dir_trabajo)
        grid.addWidget(btn_dir, 0, 4)

        grid.addWidget(QLabel("Desde:"), 1, 0)
        self.date_ini = QDateEdit()
        self.date_ini.setCalendarPopup(True)
        self.date_ini.setDisplayFormat("yyyy-MM-dd")
        hoy = datetime.date.today()
        self.date_ini.setDate(hoy.replace(year=max(2000, hoy.year - 1)))
        grid.addWidget(self.date_ini, 1, 1)

        grid.addWidget(QLabel("Hasta:"), 1, 2)
        self.date_fin = QDateEdit()
        self.date_fin.setCalendarPopup(True)
        self.date_fin.setDisplayFormat("yyyy-MM-dd")
        self.date_fin.setDate(hoy)
        grid.addWidget(self.date_fin, 1, 3)

        grid.addWidget(QLabel("Prioridad Referencia:"), 2, 0)
        self.cmb_prioridad = QComboBox()
        self.cmb_prioridad.addItems(list(PRIORIDADES_FUENTE.keys()))
        grid.addWidget(self.cmb_prioridad, 2, 1, 1, 2)

        grid.addWidget(QLabel("RMS máx (s):"), 2, 3)
        self.spin_rms_max = QDoubleSpinBox()
        self.spin_rms_max.setRange(0.05, 5.0)
        self.spin_rms_max.setSingleStep(0.05)
        self.spin_rms_max.setValue(0.35)
        grid.addWidget(self.spin_rms_max, 2, 4)

        grid.addWidget(QLabel("Mín. Estaciones:"), 3, 0)
        self.spin_min_est = QSpinBox()
        self.spin_min_est.setRange(1, 30)
        self.spin_min_est.setValue(3)
        grid.addWidget(self.spin_min_est, 3, 1)

        grid.addWidget(QLabel("Coda mín / máx (s):"), 3, 2)
        fila_coda = QHBoxLayout()
        self.spin_coda_min = QDoubleSpinBox()
        self.spin_coda_min.setRange(1.0, 200.0)
        self.spin_coda_min.setValue(5.0)
        self.spin_coda_max = QDoubleSpinBox()
        self.spin_coda_max.setRange(10.0, 2000.0)
        self.spin_coda_max.setValue(600.0)
        fila_coda.addWidget(self.spin_coda_min)
        fila_coda.addWidget(self.spin_coda_max)
        grid.addLayout(fila_coda, 3, 3, 1, 2)

        grid.addWidget(QLabel("Distancia mín / máx (km):"), 4, 0)
        fila_dist = QHBoxLayout()
        self.spin_dist_min = QDoubleSpinBox()
        self.spin_dist_min.setRange(0.0, 500.0)
        self.spin_dist_min.setValue(1.0)
        self.spin_dist_max = QDoubleSpinBox()
        self.spin_dist_max.setRange(10.0, 2000.0)
        self.spin_dist_max.setValue(400.0)
        fila_dist.addWidget(self.spin_dist_min)
        fila_dist.addWidget(self.spin_dist_max)
        grid.addLayout(fila_dist, 4, 1, 1, 2)

        grid.addWidget(QLabel("Magnitud mín / máx:"), 4, 3)
        fila_mag = QHBoxLayout()
        self.spin_mag_min = QDoubleSpinBox()
        self.spin_mag_min.setRange(0.0, 9.0)
        self.spin_mag_min.setValue(1.0)
        self.spin_mag_max = QDoubleSpinBox()
        self.spin_mag_max.setRange(1.0, 9.5)
        self.spin_mag_max.setValue(7.5)
        fila_mag.addWidget(self.spin_mag_min)
        fila_mag.addWidget(self.spin_mag_max)
        grid.addLayout(fila_mag, 4, 4)

        lay.addWidget(grp_filtros)

        # Botones de acción sobre el dataset
        fila_acc = QHBoxLayout()
        self.btn_escanear = QPushButton("🔍 Escanear Eventos en ..\\DIA\\")
        self.btn_escanear.setMinimumHeight(34)
        self.btn_escanear.setStyleSheet("background-color: #15803d; color: white; font-weight: bold; padding: 0 14px;")
        self.btn_escanear.clicked.connect(self.iniciar_escaneo_eventos)
        fila_acc.addWidget(self.btn_escanear)

        self.btn_importar_csv = QPushButton("📂 Importar Dataset CSV")
        self.btn_importar_csv.setMinimumHeight(34)
        self.btn_importar_csv.clicked.connect(self.importar_dataset_csv)
        fila_acc.addWidget(self.btn_importar_csv)

        self.btn_exportar_csv = QPushButton("💾 Exportar Dataset CSV")
        self.btn_exportar_csv.setMinimumHeight(34)
        self.btn_exportar_csv.clicked.connect(self.exportar_dataset_csv)
        fila_acc.addWidget(self.btn_exportar_csv)

        fila_acc.addStretch(1)
        lay.addLayout(fila_acc)

        self.barra_progreso = QProgressBar()
        self.barra_progreso.setRange(0, 100)
        self.barra_progreso.setValue(0)
        self.barra_progreso.setVisible(False)
        lay.addWidget(self.barra_progreso)

        self.tabla_dataset = QTableWidget()
        self.tabla_dataset.setColumnCount(len(COLUMNAS_DATASET))
        self.tabla_dataset.setHorizontalHeaderLabels(COLUMNAS_DATASET)
        self.tabla_dataset.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla_dataset.setAlternatingRowColors(True)
        lay.addWidget(self.tabla_dataset, 1)

        return w

    def _crear_tab_regresion(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)

        grp_opt = QGroupBox("Opciones de Regresión Lineal Múltiple (Md = b₁ + c₁·log₁₀(Coda) + c₂·dist)")
        fila_opt = QHBoxLayout(grp_opt)

        self.chk_outliers = QCheckBox("Filtrar atípicos (|r| > 2σ)")
        self.chk_outliers.setChecked(True)
        fila_opt.addWidget(self.chk_outliers)

        self.chk_c2_no_neg = QCheckBox("Restringir c₂ ≥ 0")
        self.chk_c2_no_neg.setChecked(True)
        fila_opt.addWidget(self.chk_c2_no_neg)

        self.chk_c2_cero = QCheckBox("Fijar c₂ = 0 (red local)")
        self.chk_c2_cero.setChecked(False)
        fila_opt.addWidget(self.chk_c2_cero)

        fila_opt.addWidget(QLabel("Mín. eventos óptimos:"))
        self.spin_min_ev_reg = QSpinBox()
        self.spin_min_ev_reg.setRange(3, 200)
        self.spin_min_ev_reg.setValue(10)
        fila_opt.addWidget(self.spin_min_ev_reg)

        fila_opt.addStretch(1)

        self.btn_calcular = QPushButton("📐 Calcular Coeficientes")
        self.btn_calcular.setMinimumHeight(34)
        self.btn_calcular.setStyleSheet("background-color: #7c3aed; color: white; font-weight: bold; padding: 0 14px;")
        self.btn_calcular.clicked.connect(self.calcular_coeficientes_todas_estaciones)
        fila_opt.addWidget(self.btn_calcular)

        lay.addWidget(grp_opt)

        self.tabla_coefs = QTableWidget()
        self.tabla_coefs.setColumnCount(9)
        self.tabla_coefs.setHorizontalHeaderLabels(
            ["Estación", "N Usados", "Excluidos", "b₁", "c₁ (log Coda)", "c₂ (Dist)", "R²", "σ (Mag)", "Estado"]
        )
        self.tabla_coefs.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla_coefs.setAlternatingRowColors(True)
        lay.addWidget(self.tabla_coefs, 1)

        # Panel de generación de Mag2000.txt y reportes
        grp_gen = QGroupBox("Generación de Archivos de Salida (Mag2000.txt, CSV de Coeficientes y Reporte)")
        form_gen = QFormLayout(grp_gen)

        fila_plantilla = QHBoxLayout()
        ruta_mag_def = os.path.join(ruta_datos, "Mag2000.txt")
        self.txt_plantilla_mag = QLineEdit(ruta_mag_def if os.path.exists(ruta_mag_def) else "")
        self.txt_plantilla_mag.setPlaceholderText("Opcional: Mag2000.txt previo para conservar estaciones no recalibradas")
        btn_plant = QPushButton("Buscar Mag2000.txt...")
        btn_plant.clicked.connect(self._seleccionar_plantilla_mag)
        fila_plantilla.addWidget(self.txt_plantilla_mag, 1)
        fila_plantilla.addWidget(btn_plant)
        form_gen.addRow("Plantilla Mag2000.txt previa:", fila_plantilla)

        self.btn_generar_archivos = QPushButton("💾 Generar Mag2000.txt, CSVs y Reporte Técnico...")
        self.btn_generar_archivos.setMinimumHeight(36)
        self.btn_generar_archivos.setStyleSheet("background-color: #0284c7; color: white; font-weight: bold;")
        self.btn_generar_archivos.clicked.connect(self.generar_archivos_salida)
        form_gen.addRow(self.btn_generar_archivos)

        lay.addWidget(grp_gen)
        return w

    def _crear_tab_graficas(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)

        fila_sel = QHBoxLayout()
        fila_sel.addWidget(QLabel("<b>Estación a graficar:</b>"))
        self.cmb_estacion_graf = QComboBox()
        self.cmb_estacion_graf.setMinimumWidth(140)
        self.cmb_estacion_graf.currentIndexChanged.connect(self.actualizar_graficas_estacion)
        fila_sel.addWidget(self.cmb_estacion_graf)
        fila_sel.addStretch(1)
        lay.addLayout(fila_sel)

        self.figura = Figure(figsize=(10, 4.5), dpi=100)
        self.canvas = FigureCanvas(self.figura)
        lay.addWidget(self.canvas, 1)
        return w

    # -------------------------------------------------------------------------
    # ACCIONES Y EVENTOS UI
    # -------------------------------------------------------------------------

    def _seleccionar_dir_trabajo(self) -> None:
        carpeta = QFileDialog.getExistingDirectory(self, "Seleccionar directorio ..\\DIA\\", self.txt_dir_trabajo.text())
        if carpeta:
            self.txt_dir_trabajo.setText(carpeta)

    def _seleccionar_plantilla_mag(self) -> None:
        archivo, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Mag2000.txt existente", ruta_datos, "Archivos TXT (*.txt);;Todos (*.*)"
        )
        if archivo:
            self.txt_plantilla_mag.setText(archivo)

    def iniciar_escaneo_eventos(self) -> None:
        dir_t = self.txt_dir_trabajo.text().strip()
        if not dir_t or not os.path.isdir(dir_t):
            QMessageBox.warning(self, "Directorio inválido", "Seleccione un directorio ..\\DIA\\ existente.")
            return

        params = {
            "dir_trabajo": dir_t,
            "fecha_ini": self.date_ini.date().toPyDate(),
            "fecha_fin": self.date_fin.date().toPyDate(),
            "rms_max": self.spin_rms_max.value(),
            "min_estaciones": self.spin_min_est.value(),
            "coda_min": self.spin_coda_min.value(),
            "coda_max": self.spin_coda_max.value(),
            "dist_min": self.spin_dist_min.value(),
            "dist_max": self.spin_dist_max.value(),
            "mag_min": self.spin_mag_min.value(),
            "mag_max": self.spin_mag_max.value(),
            "prioridad_fuentes": PRIORIDADES_FUENTE[self.cmb_prioridad.currentText()],
        }

        self.btn_escanear.setEnabled(False)
        self.barra_progreso.setVisible(True)
        self.barra_progreso.setValue(0)
        self.lbl_estado.setText("Escaneando catálogos y archivos .rsa...")

        self.hilo_escaneo = HiloEscaneoEventosMd(params, self)
        self.hilo_escaneo.progreso.connect(self._al_progreso_escaneo)
        self.hilo_escaneo.finalizado.connect(self._al_finalizar_escaneo)
        self.hilo_escaneo.error.connect(self._al_error_escaneo)
        self.hilo_escaneo.start()

    def _al_progreso_escaneo(self, pct: int, msg: str) -> None:
        self.barra_progreso.setValue(pct)
        self.lbl_estado.setText(msg)

    def _al_finalizar_escaneo(self, datos: List[dict]) -> None:
        self.btn_escanear.setEnabled(True)
        self.barra_progreso.setVisible(False)
        self.dataset_actual = datos
        self._poblar_tabla_dataset()
        self.lbl_estado.setText(f"Escaneo finalizado: {len(datos)} lecturas de estaciones recolectadas.")
        if not datos:
            QMessageBox.information(
                self,
                "Sin Lecturas",
                "No se encontraron lecturas que cumplan los filtros en ese rango de fechas.\n"
                "Verifique el directorio ..\\DIA\\, el rango de fechas o amplíe los criterios.",
            )

    def _al_error_escaneo(self, err: str) -> None:
        self.btn_escanear.setEnabled(True)
        self.barra_progreso.setVisible(False)
        QMessageBox.critical(self, "Error en Escaneo", f"Error escaneando eventos:\n{err}")

    def _poblar_tabla_dataset(self) -> None:
        self.tabla_dataset.setRowCount(len(self.dataset_actual))
        for i, fila in enumerate(self.dataset_actual):
            chk = QCheckBox()
            chk.setChecked(bool(fila.get("Incluir", True)))
            chk.stateChanged.connect(lambda st, idx=i: self._al_cambiar_check_fila(idx, st == Qt.Checked))
            self.tabla_dataset.setCellWidget(i, 0, chk)

            for c_idx, col in enumerate(COLUMNAS_DATASET[1:], 1):
                item = QTableWidgetItem(str(fila.get(col, "")))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.tabla_dataset.setItem(i, c_idx, item)

    def _al_cambiar_check_fila(self, idx: int, incluir: bool) -> None:
        if 0 <= idx < len(self.dataset_actual):
            self.dataset_actual[idx]["Incluir"] = incluir

    def importar_dataset_csv(self) -> None:
        ruta, _ = QFileDialog.getOpenFileName(self, "Importar Dataset CSV", ruta_proyecto, "CSV (*.csv)")
        if not ruta:
            return
        try:
            datos = []
            with open(ruta, "r", encoding="utf-8-sig", newline="") as f:
                lector = csv.DictReader(f)
                for row in lector:
                    coda = _a_float(row.get("Coda_s"), 0.0) or 0.0
                    dist = _a_float(row.get("Dist_km"), 0.0) or 0.0
                    mag = _a_float(row.get("Mag_Ref"), 0.0) or 0.0
                    if coda <= 0 or mag <= 0:
                        continue
                    datos.append(
                        {
                            "Incluir": str(row.get("Incluir", "True")).strip().lower() not in ("false", "0", "no"),
                            "Fecha_Hora": row.get("Fecha_Hora", ""),
                            "Evento_ID": row.get("Evento_ID", ""),
                            "Estacion": str(row.get("Estacion", "")).strip().upper(),
                            "Dist_km": dist,
                            "Coda_s": coda,
                            "RMS_s": _a_float(row.get("RMS_s"), 0.0) or 0.0,
                            "N_Estaciones": int(_a_float(row.get("N_Estaciones"), 3) or 3),
                            "Fuente_Ref": str(row.get("Fuente_Ref", "EXT")).strip().upper(),
                            "Mag_Ref": mag,
                            "Tipo_Mag_Ref": row.get("Tipo_Mag_Ref", "Md"),
                            "Archivo_RSA": row.get("Archivo_RSA", ""),
                        }
                    )
            self.dataset_actual = datos
            self._poblar_tabla_dataset()
            self.lbl_estado.setText(f"Dataset importado: {len(datos)} registros desde {os.path.basename(ruta)}.")
        except Exception as e:
            QMessageBox.critical(self, "Error al Importar", f"No se pudo leer el CSV:\n{e}")

    def exportar_dataset_csv(self) -> None:
        if not self.dataset_actual:
            QMessageBox.warning(self, "Sin Datos", "No hay lecturas en el dataset para exportar.")
            return
        sug = os.path.join(ruta_datos, f"dataset_calibracion_md_{datetime.date.today().strftime('%Y%m%d')}.csv")
        ruta, _ = QFileDialog.getSaveFileName(self, "Exportar Dataset CSV", sug, "CSV (*.csv)")
        if not ruta:
            return
        try:
            with open(ruta, "w", encoding="utf-8", newline="") as f:
                w = csv.DictWriter(f, fieldnames=COLUMNAS_DATASET)
                w.writeheader()
                w.writerows(self.dataset_actual)
            self.lbl_estado.setText(f"Dataset exportado en: {ruta}")
        except Exception as e:
            QMessageBox.critical(self, "Error al Exportar", f"No se pudo guardar el CSV:\n{e}")

    def calcular_coeficientes_todas_estaciones(self) -> None:
        if not self.dataset_actual:
            QMessageBox.warning(self, "Sin Dataset", "Primero escanee eventos o importe un dataset CSV.")
            return

        por_estacion: Dict[str, List[dict]] = {}
        for fila in self.dataset_actual:
            if not fila.get("Incluir", True):
                continue
            sta = fila["Estacion"]
            por_estacion.setdefault(sta, []).append(fila)

        self.resultados_estaciones.clear()
        for sta, filas in sorted(por_estacion.items()):
            res = ajustar_coeficientes_estacion(
                filas_estacion=filas,
                filtrar_outliers=self.chk_outliers.isChecked(),
                fijar_c2_cero=self.chk_c2_cero.isChecked(),
                forzar_c2_no_negativo=self.chk_c2_no_neg.isChecked(),
                min_eventos=self.spin_min_ev_reg.value(),
            )
            res["filas"] = filas
            self.resultados_estaciones[sta] = res

        self._poblar_tabla_coeficientes()
        self.cmb_estacion_graf.blockSignals(True)
        self.cmb_estacion_graf.clear()
        self.cmb_estacion_graf.addItems(sorted(self.resultados_estaciones.keys()))
        self.cmb_estacion_graf.blockSignals(False)
        self.actualizar_graficas_estacion()
        self.lbl_estado.setText(
            f"Regresión calculada para {len(self.resultados_estaciones)} estaciones."
        )

    def _poblar_tabla_coeficientes(self) -> None:
        estaciones = sorted(self.resultados_estaciones.keys())
        self.tabla_coefs.setRowCount(len(estaciones))
        for i, sta in enumerate(estaciones):
            r = self.resultados_estaciones[sta]
            vals = [
                sta,
                str(r["n_usados"]),
                str(r["n_excluidos"]),
                f"{r['b1']:.6f}",
                f"{r['c1']:.6f}",
                f"{r['c2']:.6f}",
                f"{r['r2']:.4f}",
                f"{r['sigma']:.3f}",
                r["estado"],
            ]
            for c, val in enumerate(vals):
                it = QTableWidgetItem(val)
                it.setFlags(it.flags() & ~Qt.ItemIsEditable)
                if c == 8:
                    if r["estado"] == "Óptimo":
                        it.setForeground(QColor("#15803d"))
                        it.setFont(QFont("Segoe UI", 9, QFont.Bold))
                    elif r["estado"] == "Aceptable":
                        it.setForeground(QColor("#b45309"))
                    else:
                        it.setForeground(QColor("#b91c1c"))
                self.tabla_coefs.setItem(i, c, it)

    def actualizar_graficas_estacion(self) -> None:
        self.figura.clear()
        sta = self.cmb_estacion_graf.currentText().strip()
        if not sta or sta not in self.resultados_estaciones:
            self.canvas.draw()
            return

        r = self.resultados_estaciones[sta]
        filas = r.get("filas", [])
        if not filas or not r["y_pred"]:
            self.canvas.draw()
            return

        ax1 = self.figura.add_subplot(1, 2, 1)
        ax2 = self.figura.add_subplot(1, 2, 2)

        colores = {"USGS": "#2563eb", "IGEPN": "#16a34a", "RSA": "#ea580c"}
        y_ref = np.array([f["Mag_Ref"] for f in filas], dtype=float)
        y_pred = np.array(r["y_pred"], dtype=float)
        dist = np.array([f["Dist_km"] for f in filas], dtype=float)
        res = np.array(r["residuales"], dtype=float)
        masc = np.array(r["mascara"], dtype=bool)

        for fuente in sorted(set(f["Fuente_Ref"] for f in filas)):
            idx_f = np.array([f["Fuente_Ref"] == fuente for f in filas], dtype=bool)
            usados = idx_f & masc
            excl = idx_f & (~masc)
            col = colores.get(fuente, "#6b7280")
            if np.any(usados):
                ax1.scatter(y_ref[usados], y_pred[usados], c=col, label=fuente, alpha=0.85, edgecolors="k", s=38)
                ax2.scatter(dist[usados], res[usados], c=col, label=fuente, alpha=0.85, edgecolors="k", s=38)
            if np.any(excl):
                ax1.scatter(y_ref[excl], y_pred[excl], c=col, marker="x", s=45, alpha=0.5)
                ax2.scatter(dist[excl], res[excl], c=col, marker="x", s=45, alpha=0.5)

        mn = min(float(np.min(y_ref)), float(np.min(y_pred))) - 0.3
        mx = max(float(np.max(y_ref)), float(np.max(y_pred))) + 0.3
        eje = np.linspace(mn, mx, 40)
        ax1.plot(eje, eje, "k--", lw=1.2, label="1:1")
        ax1.fill_between(eje, eje - 0.3, eje + 0.3, color="#94a3b8", alpha=0.18, label="±0.3")
        ax1.set_title(f"{sta}: Md vs M_ref (R²={r['r2']:.3f}, σ={r['sigma']:.2f})")
        ax1.set_xlabel("Magnitud de Referencia (M_ref)")
        ax1.set_ylabel("Magnitud Calculada (Md)")
        ax1.grid(True, alpha=0.3)
        ax1.legend(fontsize=8)

        ax2.axhline(0.0, color="k", linestyle="--", lw=1.1)
        ax2.axhline(0.3, color="#dc2626", linestyle=":", lw=0.9)
        ax2.axhline(-0.3, color="#dc2626", linestyle=":", lw=0.9)
        ax2.set_title(f"{sta}: Residuales (Md - M_ref) vs Distancia")
        ax2.set_xlabel("Distancia epicentral (km)")
        ax2.set_ylabel("Residual (Md - M_ref)")
        ax2.grid(True, alpha=0.3)

        self.figura.tight_layout()
        self.canvas.draw()

    def generar_archivos_salida(self) -> None:
        if not self.resultados_estaciones:
            QMessageBox.warning(self, "Sin Coeficientes", "Calcule primero los coeficientes en la pestaña 2.")
            return

        dir_out = QFileDialog.getExistingDirectory(
            self, "Seleccionar carpeta destino para Mag2000.txt y reportes", ruta_datos
        )
        if not dir_out:
            return

        dir_path = Path(dir_out)
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        try:
            # 1. Plantilla previa (si existe) y respaldo de seguridad
            plantilla = []
            ruta_plant = self.txt_plantilla_mag.text().strip()
            if ruta_plant and os.path.isfile(ruta_plant):
                plantilla = leer_mag2000_existente(Path(ruta_plant))

            ruta_mag_out = dir_path / "Mag2000.txt"
            if ruta_mag_out.exists():
                shutil.copy2(ruta_mag_out, dir_path / f"Mag2000_respaldo_{ts}.txt")

            texto_mag = generar_texto_mag2000(self.resultados_estaciones, plantilla_previa=plantilla)
            ruta_mag_out.write_text(texto_mag, encoding="ascii", errors="replace")

            # 2. CSV de dataset utilizado
            ruta_ds = dir_path / f"dataset_calibracion_md_{ts}.csv"
            with open(ruta_ds, "w", encoding="utf-8", newline="") as f:
                w = csv.DictWriter(f, fieldnames=COLUMNAS_DATASET)
                w.writeheader()
                w.writerows(self.dataset_actual)

            # 3. CSV de coeficientes por estación
            ruta_coef = dir_path / f"coeficientes_md_{ts}.csv"
            with open(ruta_coef, "w", encoding="utf-8", newline="") as f:
                w = csv.writer(f)
                w.writerow(["Estacion", "N_Usados", "N_Excluidos", "b1", "c1", "c2", "R2", "Sigma_Mag", "Sesgo", "Estado"])
                for sta, r in sorted(self.resultados_estaciones.items()):
                    w.writerow([
                        sta, r["n_usados"], r["n_excluidos"],
                        f"{r['b1']:.6f}", f"{r['c1']:.6f}", f"{r['c2']:.6f}",
                        f"{r['r2']:.4f}", f"{r['sigma']:.4f}", f"{r['sesgo']:.4f}", r["estado"],
                    ])

            # 4. Reporte técnico de trazabilidad
            ruta_rep = dir_path / f"reporte_calibracion_md_{ts}.txt"
            lineas_rep = [
                "==========================================================================",
                "REPORTE DE CALIBRACIÓN DE MAGNITUD DE DURACIÓN (Md) — RSA",
                "==========================================================================",
                f"Fecha generación : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"Directorio DIA   : {self.txt_dir_trabajo.text().strip()}",
                f"Rango fechas     : {self.date_ini.date().toString('yyyy-MM-dd')} a {self.date_fin.date().toString('yyyy-MM-dd')}",
                f"Prioridad fuentes: {self.cmb_prioridad.currentText()}",
                f"Filtros calidad  : RMS <= {self.spin_rms_max.value():.2f} s | Min est >= {self.spin_min_est.value()} | "
                f"Coda [{self.spin_coda_min.value():.1f}, {self.spin_coda_max.value():.1f}] s | "
                f"Dist [{self.spin_dist_min.value():.1f}, {self.spin_dist_max.value():.1f}] km",
                "--------------------------------------------------------------------------",
                "COEFICIENTES CALIBRADOS (Md = b1 + c1*log10(Coda) + c2*dist_km):",
            ]
            for sta, r in sorted(self.resultados_estaciones.items()):
                lineas_rep.append(
                    f"  {sta:<4s} | N={r['n_usados']:3d} | b1={r['b1']:9.6f}  c1={r['c1']:9.6f}  c2={r['c2']:9.6f} "
                    f"| R2={r['r2']:.4f} | sigma={r['sigma']:.3f} | {r['estado']}"
                )
            ruta_rep.write_text("\n".join(lineas_rep) + "\n", encoding="utf-8")

            QMessageBox.information(
                self,
                "Archivos Generados",
                f"Se generaron exitosamente los archivos en:\n{dir_out}\n\n"
                f"• Mag2000.txt\n• {ruta_coef.name}\n• {ruta_ds.name}\n• {ruta_rep.name}",
            )
            self.lbl_estado.setText(f"Mag2000.txt y reportes guardados en {dir_out}.")
        except Exception as e:
            QMessageBox.critical(self, "Error al Guardar", f"No se pudieron generar los archivos:\n{e}")

    def abrir_manual_usuario(self) -> None:
        ruta_manual = Path(ruta_proyecto) / "docs" / "manual_calibracion_magnitud_md.md"
        dlg = QDialog(self)
        dlg.setWindowTitle("Manual de Usuario — Calibración de Magnitud de Duración (Md)")
        dlg.resize(860, 640)
        lay = QVBoxLayout(dlg)
        visor = QTextBrowser(dlg)
        if ruta_manual.exists():
            txt = ruta_manual.read_text(encoding="utf-8", errors="replace")
            if hasattr(visor, "setMarkdown"):
                visor.setMarkdown(txt)
            else:
                visor.setPlainText(txt)
        else:
            visor.setPlainText(f"No se encontró el manual en:\n{ruta_manual}")
        lay.addWidget(visor, 1)
        btn = QPushButton("Cerrar")
        btn.clicked.connect(dlg.accept)
        lay.addWidget(btn)
        dlg.exec_()
