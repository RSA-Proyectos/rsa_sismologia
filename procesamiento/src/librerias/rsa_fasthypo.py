"""
================================================================================
Librería:  rsa_fasthypo.py
Propósito: Motor autónomo en Python de FASTHYPO (R. B. Herrmann 1979) y
           conversor PECQ/HYPO71 + cálculo de magnitud Md (Mag2000.txt) +
           diálogo gráfico PyQt5 (`DialogoLocalizarFastHypo`) para integrar
           directamente en `fases.py` y producir `.P`, `.L`, `.S`, `Phase*`
           y `.rsa` compatibles con `lectura_rsa()` de `rsa_procesamiento.py`.
================================================================================
"""

from dataclasses import dataclass, field
import math
import os
from pathlib import Path
import sys
from typing import Dict, List, Optional, Tuple

import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.collections import PolyCollection
from matplotlib.figure import Figure
from matplotlib.patches import Ellipse
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

try:
    import shapefile as pyshp
except ImportError:
    pyshp = None


def extraer_hasta_directorio(ruta_completa: str, nombre_directorio: str) -> str:
    partes = Path(ruta_completa).parts
    if nombre_directorio in partes:
        indice = partes.index(nombre_directorio)
        return str(Path(*partes[: indice + 1])) + "/"
    return ""


ruta_librerias = os.path.dirname(os.path.abspath(__file__))
ruta_proyecto = extraer_hasta_directorio(ruta_librerias, "procesamiento")
if not ruta_proyecto:
    ruta_proyecto = os.path.abspath(os.path.join(ruta_librerias, "..", ".."))
ruta_datos_fasthypo = os.path.abspath(os.path.join(ruta_proyecto, "datos", "fasthypo"))
ruta_datos_gis = os.path.abspath(os.path.join(ruta_proyecto, "datos", "GIS"))

RADIO_TIERRA_KM = 6371.0
FACTOR_GEOCENTRICO = 0.993277


@dataclass
class CapaVelocidad:
    vp: float
    z_techo: float
    vs: float


@dataclass
class EstacionFH:
    codigo: str
    latitud: float
    longitud: float
    modelo_id: int
    corr_p: float
    corr_s: float
    descripcion: str = ""


@dataclass
class FaseEstacionP:
    estacion: str
    seg_p: float
    polaridad: str
    peso_p: int
    seg_s: float
    peso_s: int
    coda: float = 0.0
    tipo_p: str = "I"
    polaridad_s: str = " "


@dataclass
class EventoP:
    anio: int
    mes: int
    dia: int
    hora: int
    minuto: int
    fases: List[FaseEstacionP] = field(default_factory=list)


@dataclass
class ResultadoEstacion:
    estacion: str
    dist_km: float
    azimut: float
    angulo_salida: float
    p_obs: float
    tp_cal: float
    p_res: float
    peso_p: int
    s_obs: float
    ts_cal: float
    s_res: float
    peso_s: int
    coda: float = 0.0


@dataclass
class ResultadoLocalizacion:
    evento: EventoP
    modelo_nombre: str
    capas: List[CapaVelocidad]
    latitud: float
    longitud: float
    profundidad_km: float
    tiempo_origen_s: float
    rms: float
    err_lat_deg: float
    err_lat_km: float
    err_lon_deg: float
    err_lon_km: float
    err_prof_km: float
    err_t0_s: float
    elipse_x_km: float
    elipse_y_km: float
    elipse_theta_deg: float
    historial_iteraciones: List[Tuple[float, float, float, float, float]]
    estaciones: List[ResultadoEstacion]
    magnitudes_estacion: List[Tuple[str, float, float, Optional[float]]] = field(default_factory=list)
    magnitud_promedio: Optional[float] = None


def mapear_polaridad_fasthypo(polaridad: str) -> str:
    ch = (polaridad or " ").strip()
    if ch in ("+", "C", "c"):
        return "+"
    if ch in ("-", "D", "d"):
        return "-"
    if ch in ("U", "u", ""):
        return "u"
    return ch.lower()


def leer_modelos_velocidad(ruta_fhveloc: Path) -> Dict[str, List[CapaVelocidad]]:
    if not ruta_fhveloc.exists():
        candidatos = [
            Path(ruta_fhveloc),
            Path(ruta_datos_fasthypo) / "FHVELOC.DAT",
            Path(ruta_proyecto) / "datos" / "fasthypo" / "FHVELOC.DAT",
            Path(ruta_proyecto).parent / "datos" / "fasthypo" / "FHVELOC.DAT",
            Path(ruta_proyecto).parent / "hypo" / "binarios_originales" / "FHVELOC.DAT",
            Path(r"C:\proyectos\rsa_sismologia\datos\fasthypo\FHVELOC.DAT"),
            Path(r"C:\proyectos\rsa_sismologia\hypo\binarios_originales\FHVELOC.DAT"),
        ]
        for c in candidatos:
            if c.exists():
                ruta_fhveloc = c
                break
        else:
            print(f"Advertencia: No se encontró FHVELOC.DAT en {ruta_fhveloc} ni en rutas candidatas.")
            return {}

    lineas = ruta_fhveloc.read_bytes().decode("latin-1", errors="replace").splitlines()
    modelos: Dict[str, List[CapaVelocidad]] = {}
    i = 0
    while i < len(lineas):
        linea = lineas[i].strip()
        if not linea:
            i += 1
            continue
        partes = linea.split()
        if len(partes) >= 2 and partes[1].isdigit():
            nombre = partes[0].strip().lower()
            n_capas = int(partes[1])
            capas: List[CapaVelocidad] = []
            for j in range(1, n_capas + 1):
                if i + j >= len(lineas):
                    break
                raw = lineas[i + j].ljust(16)
                vp = float(raw[0:5].strip())
                z = float(raw[5:9].strip())
                vs_txt = raw[9:15].strip()
                vs = float(vs_txt) if vs_txt else vp / 1.732
                capas.append(CapaVelocidad(vp=vp, z_techo=z, vs=vs))
            if capas:
                modelos[nombre] = capas
            i += n_capas + 1
        else:
            i += 1
    return modelos


def leer_estaciones(ruta_fhsta: Path) -> Dict[str, EstacionFH]:
    if not ruta_fhsta.exists():
        candidatos = [
            Path(ruta_fhsta),
            Path(ruta_datos_fasthypo) / "FHSTA.DAT",
            Path(ruta_proyecto) / "datos" / "fasthypo" / "FHSTA.DAT",
            Path(ruta_proyecto).parent / "datos" / "fasthypo" / "FHSTA.DAT",
            Path(ruta_proyecto).parent / "hypo" / "binarios_originales" / "FHSTA.DAT",
            Path(r"C:\proyectos\rsa_sismologia\datos\fasthypo\FHSTA.DAT"),
            Path(r"C:\proyectos\rsa_sismologia\hypo\binarios_originales\FHSTA.DAT"),
        ]
        for c in candidatos:
            if c.exists():
                ruta_fhsta = c
                break
        else:
            print(f"Advertencia: No se encontró FHSTA.DAT en {ruta_fhsta} ni en rutas candidatas.")

    estaciones: Dict[str, EstacionFH] = {}
    if ruta_fhsta.exists():
        lineas = ruta_fhsta.read_bytes().decode("latin-1", errors="replace").splitlines()
        for linea in lineas:
            if len(linea.strip()) < 24:
                continue
            pad = linea.ljust(65)
            codigo = pad[0:4].strip()
            if not codigo:
                continue
            try:
                lat = float(pad[5:7].strip()) + float(pad[8:13].strip()) / 60.0
                if pad[13:14].strip().lower() == "s":
                    lat = -lat
                lon = float(pad[15:17].strip()) + float(pad[18:23].strip()) / 60.0
                if pad[23:24].strip().lower() == "w":
                    lon = -lon
                modelo_id = int(pad[33:34].strip()) if pad[33:34].strip().isdigit() else 1
                corr_p = float(pad[34:39].strip()) if pad[34:39].strip() else 0.0
                corr_s = float(pad[40:45].strip()) if pad[40:45].strip() else 0.0
                desc = pad[45:].strip()
            except ValueError:
                continue
            estaciones[codigo.upper()] = EstacionFH(
                codigo=codigo.upper(),
                latitud=lat,
                longitud=lon,
                modelo_id=modelo_id,
                corr_p=corr_p,
                corr_s=corr_s,
                descripcion=desc,
            )

    # Suplementar estaciones activas desde estaciones.csv si no están ya en FHSTA.DAT
    for ruta_csv in (
        Path(ruta_proyecto) / "datos" / "estaciones.csv",
        Path(ruta_proyecto).parent / "datos" / "estaciones.csv",
        Path(r"C:\proyectos\rsa_sismologia\datos\estaciones.csv"),
    ):
        if ruta_csv.exists():
            try:
                import csv
                with open(ruta_csv, "r", encoding="latin-1", errors="replace") as f_csv:
                    lector = csv.DictReader(f_csv, delimiter=";")
                    for fila in lector:
                        cod = fila.get("CODIGO(1)", "").strip().upper()
                        if not cod or cod in estaciones:
                            continue
                        try:
                            lat = float(fila.get("LATITUD(13)", 0.0))
                            lon = float(fila.get("LONGITUD(12)", 0.0))
                            if lat == 0.0 and lon == 0.0:
                                continue
                            nom = fila.get("NOMBRE(0)", cod).strip()
                            estaciones[cod] = EstacionFH(
                                codigo=cod,
                                latitud=lat,
                                longitud=lon,
                                modelo_id=1,
                                corr_p=0.0,
                                corr_s=0.0,
                                descripcion=nom,
                            )
                        except (ValueError, TypeError):
                            continue
                break
            except Exception as e_csv:
                print(f"Aviso cargando estaciones.csv suplementario en rsa_fasthypo: {e_csv}")

    return estaciones


def leer_coeficientes_magnitud(ruta_mag2000: Path) -> Dict[str, Tuple[float, float, float]]:
    coefs: Dict[str, Tuple[float, float, float]] = {}
    if not ruta_mag2000.exists():
        candidatos = [
            Path(ruta_mag2000),
            Path(ruta_datos_fasthypo) / "Mag2000.txt",
            Path(ruta_proyecto) / "datos" / "fasthypo" / "Mag2000.txt",
            Path(ruta_proyecto) / "datos" / "Mag2000.txt",
            Path(ruta_proyecto).parent / "datos" / "fasthypo" / "Mag2000.txt",
            Path(ruta_proyecto).parent / "datos" / "Mag2000.txt",
            Path(ruta_proyecto).parent / "hypo" / "fuentes_vb5" / "ProcesoV2Con rsa" / "Iaspe-ArchDConfig" / "Mag2000.txt",
            Path(r"C:\proyectos\rsa_sismologia\datos\fasthypo\Mag2000.txt"),
            Path(r"C:\proyectos\rsa_sismologia\datos\Mag2000.txt"),
        ]
        for c in candidatos:
            if c.exists():
                ruta_mag2000 = c
                break
        else:
            return coefs

    for linea in ruta_mag2000.read_bytes().decode("latin-1", errors="replace").splitlines():
        if len(linea.strip()) < 10:
            continue
        pad = linea.ljust(35)
        sta = pad[0:4].strip().upper()
        if not sta or sta == "____":
            continue
        try:
            b1 = float(pad[4:13].strip())
            c1 = float(pad[13:22].strip())
            c2 = float(pad[22:32].strip())
            coefs[sta] = (b1, c1, c2)
        except ValueError:
            continue
    return coefs


def latitud_geocentrica(lat_deg: float) -> float:
    return math.atan(FACTOR_GEOCENTRICO * math.tan(math.radians(lat_deg)))


def distancia_y_azimut(lat1: float, lon1: float, lat2: float, lon2: float) -> Tuple[float, float]:
    p1 = latitud_geocentrica(lat1)
    p2 = latitud_geocentrica(lat2)
    dlon = math.radians(lon2 - lon1)
    cos_d = max(-1.0, min(1.0, math.sin(p1) * math.sin(p2) + math.cos(p1) * math.cos(p2) * math.cos(dlon)))
    dist_km = math.acos(cos_d) * RADIO_TIERRA_KM
    y = math.sin(dlon) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dlon)
    azm = math.degrees(math.atan2(y, x)) % 360.0
    return dist_km, azm


def tiempo_viaje_estratificado(
    dist_km: float, prof_km: float, capas: List[CapaVelocidad], usar_s: bool = False
) -> Tuple[float, float, float, float]:
    z = max(0.01, prof_km)
    vels = [c.vs if usar_s else c.vp for c in capas]
    z_top = [c.z_techo for c in capas]
    n_capas = len(capas)

    ks = 0
    for k in range(n_capas):
        if z >= z_top[k]:
            ks = k

    espesores = [z_top[k + 1] - z_top[k] for k in range(ks)] + [z - z_top[ks]]
    v_sub = vels[: ks + 1]
    v_src = vels[ks]

    if dist_km < 1e-6:
        t_dir = sum(h / v for h, v in zip(espesores, v_sub))
        p_dir = 0.0
    else:
        p_lo, p_hi = 0.0, 1.0 / max(v_sub) - 1e-12
        for _ in range(70):
            pm = 0.5 * (p_lo + p_hi)
            x_est = sum(h * pm * v / math.sqrt(max(1e-15, 1.0 - (pm * v) ** 2)) for h, v in zip(espesores, v_sub))
            if x_est < dist_km:
                p_lo = pm
            else:
                p_hi = pm
        p_dir = 0.5 * (p_lo + p_hi)
        t_dir = sum(h / (v * math.sqrt(max(1e-15, 1.0 - (p_dir * v) ** 2))) for h, v in zip(espesores, v_sub))

    cos_src = math.sqrt(max(1e-15, 1.0 - (p_dir * v_src) ** 2))
    t_mejor = t_dir
    dtdx_mejor = p_dir
    dtdz_mejor = cos_src / v_src
    ain_mejor = 180.0 - math.degrees(math.asin(min(1.0, p_dir * v_src)))

    for m in range(ks + 1, n_capas):
        vm = vels[m]
        if vm <= max(vels[:m]):
            continue
        pm = 1.0 / vm
        x_crit, t_int, valido = 0.0, 0.0, True
        for k in range(m):
            hk = z_top[k + 1] - z_top[k]
            vk = vels[k]
            if pm * vk >= 1.0:
                valido = False
                break
            eta = math.sqrt(1.0 - (pm * vk) ** 2)
            x_crit += hk * (pm * vk) / eta
            t_int += hk * eta / vk
        if not valido:
            continue
        for k in range(ks, m):
            hk = (z_top[k + 1] - z) if k == ks else (z_top[k + 1] - z_top[k])
            vk = vels[k]
            if pm * vk >= 1.0:
                valido = False
                break
            eta = math.sqrt(1.0 - (pm * vk) ** 2)
            x_crit += hk * (pm * vk) / eta
            t_int += hk * eta / vk
        if not valido or dist_km < x_crit:
            continue
        t_ref = pm * dist_km + t_int
        if t_ref < t_mejor:
            t_mejor = t_ref
            dtdx_mejor = pm
            dtdz_mejor = -math.sqrt(max(1e-15, 1.0 - (pm * v_src) ** 2)) / v_src
            ain_mejor = math.degrees(math.asin(min(1.0, pm * v_src)))

    return t_mejor, dtdx_mejor, dtdz_mejor, ain_mejor


def peso_calidad_fasthypo(wt_codigo: int) -> float:
    return {0: 1.0, 1: 0.75, 2: 0.50, 3: 0.25}.get(wt_codigo, 1.0 if wt_codigo < 0 else 0.0)


def localizar_hipocentro(
    evento: EventoP,
    estaciones_cat: Dict[str, EstacionFH],
    capas: List[CapaVelocidad],
    modelo_nombre: str,
    lat_ini: float = -2.5,
    lon_ini: float = -79.0,
    prof_ini: float = 60.0,
    t0_ini: float = 0.0,
    max_iter: int = 100,
    prof_fija: bool = False,
) -> ResultadoLocalizacion:
    if prof_ini < 0.0:
        prof_fija = True
        prof_ini = abs(prof_ini)

    fases_validas = [f for f in evento.fases if f.estacion.upper() in estaciones_cat]
    if not fases_validas:
        raise ValueError("Ninguna estación del evento se encontró en FHSTA.DAT.")

    lat, lon, z, t0 = float(lat_ini), float(lon_ini), max(0.5, float(prof_ini)), float(t0_ini)
    km_por_deg_lat = 111.195 * FACTOR_GEOCENTRICO
    historial: List[Tuple[float, float, float, float, float]] = []
    amortiguamiento = 0.001

    def evaluar(la: float, lo: float, zz: float, tt0: float):
        km_por_deg_lon = 111.195 * math.cos(latitud_geocentrica(la))
        filas_a, vec_r, vec_w, detalles = [], [], [], []
        for f in fases_validas:
            est = estaciones_cat[f.estacion.upper()]
            dist, azm = distancia_y_azimut(la, lo, est.latitud, est.longitud)
            az_rad = math.radians(azm)
            tp, dtdx_p, dtdz_p, ain_p = tiempo_viaje_estratificado(dist, zz, capas, False)
            ts, dtdx_s, dtdz_s, _ = tiempo_viaje_estratificado(dist, zz, capas, True)

            rp = f.seg_p - (tt0 + tp + est.corr_p)
            rs = (f.seg_s - (tt0 + ts + est.corr_s)) if f.seg_s > 0.0 else 0.0
            wp = peso_calidad_fasthypo(f.peso_p)
            ws = peso_calidad_fasthypo(f.peso_s) if f.seg_s > 0.0 else 0.0

            if wp > 0.0 and f.seg_p > 0.0:
                filas_a.append([-dtdx_p * math.cos(az_rad), -dtdx_p * math.sin(az_rad), dtdz_p, 1.0])
                vec_r.append(rp)
                vec_w.append(wp)
            if ws > 0.0 and f.seg_s > 0.0:
                filas_a.append([-dtdx_s * math.cos(az_rad), -dtdx_s * math.sin(az_rad), dtdz_s, 1.0])
                vec_r.append(rs)
                vec_w.append(ws)

            detalles.append(
                ResultadoEstacion(
                    estacion=est.codigo, dist_km=dist, azimut=azm, angulo_salida=ain_p,
                    p_obs=f.seg_p, tp_cal=tp, p_res=rp, peso_p=f.peso_p,
                    s_obs=f.seg_s, ts_cal=ts, s_res=rs, peso_s=f.peso_s, coda=f.coda,
                )
            )
        if not filas_a:
            raise ValueError("No hay fases con peso > 0 para localizar el evento.")
        A = np.array(filas_a, dtype=float)
        r = np.array(vec_r, dtype=float)
        w = np.array(vec_w, dtype=float)
        return A, r, w, float(np.sum((w * r) ** 2)), detalles, km_por_deg_lon

    A, r, w, sum_sq, detalles, km_por_deg_lon = evaluar(lat, lon, z, t0)
    historial.append((lat, lon, z, t0, sum_sq))

    for _ in range(max_iter):
        sw = np.sqrt(w)[:, None]
        Aw = A * sw
        rw = r * np.sqrt(w)
        cols = [0, 1, 3] if prof_fija else [0, 1, 2, 3]
        Aw_sub = Aw[:, cols]
        ATA = Aw_sub.T @ Aw_sub
        ATr = Aw_sub.T @ rw
        diag = np.diag(np.maximum(np.diag(ATA), 1e-8))
        try:
            dx_sub = np.linalg.solve(ATA + amortiguamiento * diag, ATr)
        except np.linalg.LinAlgError:
            dx_sub = np.linalg.lstsq(ATA + 1e-3 * diag, ATr, rcond=None)[0]

        dx = np.zeros(4, dtype=float)
        for idx_c, c in enumerate(cols):
            dx[c] = dx_sub[idx_c]

        if not prof_fija and abs(dx[2]) > 5.0:
            dx[2] = math.copysign(5.0, dx[2])
        paso_h = math.hypot(dx[0], dx[1])
        if paso_h > 50.0:
            dx[0] *= 50.0 / paso_h
            dx[1] *= 50.0 / paso_h

        mejorado = False
        cambio = 0.0
        for intento in range(8):
            factor = 0.5 ** intento
            n_lat = lat + (dx[0] * factor) / km_por_deg_lat
            n_lon = lon + (dx[1] * factor) / km_por_deg_lon
            n_z = max(0.5, z + dx[2] * factor)
            n_t0 = t0 + dx[3] * factor
            nA, nr, nw, n_ssq, ndet, n_kmlon = evaluar(n_lat, n_lon, n_z, n_t0)
            if n_ssq <= sum_sq + 1e-9 or intento == 7:
                cambio = math.hypot(dx[0] * factor, dx[1] * factor) + abs(dx[2] * factor) + abs(dx[3] * factor)
                lat, lon, z, t0 = n_lat, n_lon, n_z, n_t0
                A, r, w, sum_sq, detalles, km_por_deg_lon = nA, nr, nw, n_ssq, ndet, n_kmlon
                historial.append((lat, lon, z, t0, sum_sq))
                amortiguamiento = max(1e-6, amortiguamiento * 0.5) if intento == 0 else min(10.0, amortiguamiento * 2.0)
                mejorado = True
                break
        if not mejorado or cambio < 1e-4:
            break

    n_obs = len(r)
    n_par = 3 if prof_fija else 4
    dof = max(1, n_obs - n_par)
    rms = math.sqrt(float(np.sum(r ** 2)) / dof)

    sw = np.sqrt(w)[:, None]
    cols = [0, 1, 3] if prof_fija else [0, 1, 2, 3]
    M = (A * sw)[:, cols]
    _, s_vals, Vt = np.linalg.svd(M, full_matrices=False)
    theta_damp = 0.01
    factores_svd = (s_vals ** 2) / ((s_vals ** 2 + theta_damp ** 2) ** 2)
    cov_sub = (rms ** 2) * (Vt.T * factores_svd) @ Vt

    cov = np.zeros((4, 4), dtype=float)
    for i, ci in enumerate(cols):
        for j, cj in enumerate(cols):
            cov[ci, cj] = cov_sub[i, j]

    err_n_km = math.sqrt(max(0.0, cov[0, 0]))
    err_e_km = math.sqrt(max(0.0, cov[1, 1]))
    err_z_km = math.sqrt(max(0.0, cov[2, 2]))
    err_t0_s = math.sqrt(max(0.0, cov[3, 3]))
    evals, evecs = np.linalg.eigh(cov[0:2, 0:2])
    evals = np.maximum(evals, 0.0)
    elipse_x, elipse_y = math.sqrt(evals[0]), math.sqrt(evals[1])
    v_mayor = evecs[:, 1]
    theta = math.degrees(math.atan2(v_mayor[1], v_mayor[0])) % 180.0

    return ResultadoLocalizacion(
        evento=evento, modelo_nombre=modelo_nombre, capas=capas,
        latitud=lat, longitud=lon, profundidad_km=z, tiempo_origen_s=t0, rms=rms,
        err_lat_deg=err_n_km / km_por_deg_lat, err_lat_km=err_n_km,
        err_lon_deg=err_e_km / km_por_deg_lon, err_lon_km=err_e_km,
        err_prof_km=err_z_km, err_t0_s=err_t0_s,
        elipse_x_km=elipse_x, elipse_y_km=elipse_y, elipse_theta_deg=theta,
        historial_iteraciones=historial, estaciones=detalles,
    )


def calcular_magnitud_coda(
    resultado: ResultadoLocalizacion,
    coeficientes_estacion: Optional[Dict[str, Tuple[float, float, float]]] = None,
) -> ResultadoLocalizacion:
    mags, validas = [], []
    tabla = coeficientes_estacion or {}
    # Coeficientes regionales estándar por defecto para la Red RSA (HUAJ/GUAL/LABR)
    COEFS_DEFECTO = (2.131382, 0.975177, 0.001410)

    for est in resultado.estaciones:
        sta = est.estacion.upper()
        b1, c1, c2 = tabla.get(sta, (0.0, 0.0, 0.0))
        # Si la estación tiene coda válida pero coeficientes en cero o no registrados,
        # aplicar coeficientes regionales estándar para garantizar el cálculo de magnitud
        if (b1 == 0.0 and c1 == 0.0 and c2 == 0.0) and (est.coda and est.coda > 0.0):
            b1, c1, c2 = COEFS_DEFECTO

        if (b1 == 0.0 and c1 == 0.0 and c2 == 0.0) or not est.coda or est.coda <= 0.0:
            mags.append((est.estacion, est.dist_km, est.coda if est.coda > 0 else 0.0, None))
        else:
            md = b1 + c1 * math.log10(est.coda) + c2 * est.dist_km
            mags.append((est.estacion, est.dist_km, est.coda, md))
            validas.append(md)
    resultado.magnitudes_estacion = mags
    resultado.magnitud_promedio = float(np.mean(validas)) if validas else None
    return resultado


def formatear_archivo_phase(ev: EventoP) -> str:
    lineas = []
    for f in ev.fases:
        pol_p = f.polaridad if f.polaridad in ("+", "-", "U", "D", " ") else " "
        s_txt = f"{f.seg_s:5.2f} S{f.polaridad_s:1s}{f.peso_s:1d}" if f.seg_s > 0 else "         "
        coda_txt = f"{f.coda:4.1f}" if f.coda > 0 else "    "
        linea = (
            f"{f.estacion:<4s}{f.tipo_p:1s}P{pol_p:1s}{f.peso_p:1d} "
            f"{ev.anio:02d}{ev.mes:02d}{ev.dia:02d}{ev.hora:02d}{ev.minuto:02d}{f.seg_p:05.2f}"
            f"       {s_txt}                               {coda_txt}"
        )
        lineas.append(linea)
    lineas.append("                  10 ")
    return "\n".join(lineas) + "\n"


def formatear_archivo_p(ev: EventoP) -> str:
    lineas = [f"{ev.anio:2d} {ev.mes:2d} {ev.dia:2d} {ev.hora:2d} {ev.minuto:2d}"]
    for f in ev.fases:
        pol = mapear_polaridad_fasthypo(f.polaridad)
        lineas.append(f"{f.estacion:<4s}{f.seg_p:6.2f} {pol:1s} {f.peso_p:2d} {f.seg_s:6.2f} {f.peso_s:2d}")
    return "\n".join(lineas) + "\n"


def formatear_salida_l(res: ResultadoLocalizacion) -> str:
    ev = res.evento
    out = ["", "", "", "       crustal model", "     velocity      depth               s velocity"]
    for c in res.capas:
        out.append(f"       {c.vp:6.3f}   {c.z_techo:7.3f}    {c.vs:6.3f}")
    for f in ev.fases:
        pol = mapear_polaridad_fasthypo(f.polaridad)
        out.append(f" {f.estacion:<4s} {f.peso_p:1d}  {f.seg_p:6.2f} {pol:1s} {f.peso_s:1d}  {f.seg_s:6.2f}")
    for la, lo, zz, tt, ssq in res.historial_iteraciones:
        out.append(f"   {la:8.4f}  {lo:8.4f}    {zz:6.2f}    {tt:6.2f}  {ssq:8.2f}")
    out.append("  sta   dist   azm  ain  p-sec  tpcal  p-res  wt  s-sec  s-res  wt")
    for e in res.estaciones:
        out.append(
            f"  {e.estacion:<4s} {e.dist_km:5.1f}  {int(round(e.azimut)):3d}  {int(round(e.angulo_salida)):3d}  "
            f"{e.p_obs:5.2f}  {e.tp_cal:5.2f}  {e.p_res:5.2f}  {e.peso_p:1d}   "
            f"{e.s_obs:5.2f}  {e.s_res:5.2f}  {e.peso_s:1d}"
        )
    out.append("")
    out.append(f" error ellipse  x={res.elipse_x_km:7.2f} km  y={res.elipse_y_km:7.2f} km  theta ={res.elipse_theta_deg:7.2f}")
    out.append("")
    out.append(f" event is dated: {ev.anio:2d} {ev.mes:2d} {ev.dia:2d} {ev.hora:2d} {ev.minuto:2d}")
    out.append("")
    out.append(f" rms=    {res.rms:6.3f}")
    out.append(f"   {res.latitud:8.4f}+-   {res.err_lat_deg:7.4f}n       {res.err_lat_km:8.4f}km")
    out.append(f"  {res.longitud:9.4f}+-   {res.err_lon_deg:7.4f}e       {res.err_lon_km:8.4f}km")
    out.append(f"    {res.profundidad_km:7.2f}+-    {res.err_prof_km:6.2f}km")
    out.append(f"     {res.tiempo_origen_s:6.2f}+-     {res.err_t0_s:5.2f}sec")
    out.append("")
    return "\n".join(out) + "\n"


def formatear_salida_s(res: ResultadoLocalizacion) -> str:
    ev = res.evento
    return (
        f"{ev.anio:2d} {ev.mes:2d} {ev.dia:2d} {ev.hora:2d} {ev.minuto:2d}  "
        f"{res.tiempo_origen_s:5.2f} {res.latitud:7.4f} {res.longitud:8.4f} "
        f"{res.profundidad_km:6.2f} {res.rms:5.3f} {res.elipse_x_km:5.2f} "
        f"{res.elipse_y_km:5.2f} {res.elipse_theta_deg:6.2f} {res.err_prof_km:5.2f}\n"
    )


def formatear_salida_rsa(res: ResultadoLocalizacion) -> str:
    base = formatear_salida_l(res)
    bloque = ["CALCULO DE LA MAGNITUD", "", "sta           dist          Coda          Mag"]
    for sta, dist, coda, md in res.magnitudes_estacion:
        mag_txt = f"{md:4.1f}" if md is not None else "NMG"
        bloque.append(f"{sta:<14s}{dist:06.2f}        {coda:05.2f}         {mag_txt}")
    prom = f"{res.magnitud_promedio:4.1f}" if res.magnitud_promedio is not None else "No Existe Magnitud"
    bloque.extend(["", f"Promedio de las Magnitudes: {prom}", ""])
    return base + "\n".join(bloque)


# =============================================================================
# DIÁLOGO PYQT5 INTEGRADO EN FASES.PY (REEMPLAZO DIRECTO DE IASPEI.FRM / VB5)
# =============================================================================

def formatear_resumen_ultima_iteracion(res: ResultadoLocalizacion) -> str:
    """
    Genera la vista de pantalla centrada en la última iteración por estación,
    elipse de error, hipocentro final y magnitud (omite el bloque 'crustal model'
    y las iteraciones previas, que sí se conservan íntegros al grabar .L/.rsa).
    """
    ev = res.evento
    mapa_md = {sta: md for sta, _, _, md in res.magnitudes_estacion}
    n_iter = max(0, len(res.historial_iteraciones) - 1)
    out = [
        f"ULTIMA ITERACION (#{n_iter}) — MODELO: {res.modelo_nombre.upper()}  |  "
        f"EVENTO: 20{ev.anio:02d}-{ev.mes:02d}-{ev.dia:02d} {ev.hora:02d}:{ev.minuto:02d} UTC",
        " sta   dist  azm  ain  p-obs  tpcal  p-res wt  s-obs  tscal  s-res wt  coda   Md",
        "-" * 80,
    ]
    for e in res.estaciones:
        md_v = mapa_md.get(e.estacion)
        s_obs_txt = f"{e.s_obs:6.2f}" if e.s_obs > 0 else "   ---"
        ts_cal_txt = f"{e.ts_cal:6.2f}" if e.s_obs > 0 else "   ---"
        s_res_txt = f"{e.s_res:+6.2f}" if e.s_obs > 0 else "   ---"
        coda_txt = f"{e.coda:5.1f}" if e.coda > 0 else "  ---"
        md_txt = f"{md_v:4.1f}" if md_v is not None else " NMG"
        out.append(
            f" {e.estacion:<4s} {e.dist_km:5.1f}  {int(round(e.azimut)):3d}  {int(round(e.angulo_salida)):3d} "
            f"{e.p_obs:6.2f} {e.tp_cal:6.2f} {e.p_res:+6.2f}  {e.peso_p:1d} "
            f"{s_obs_txt} {ts_cal_txt} {s_res_txt}  {e.peso_s:1d} {coda_txt} {md_txt}"
        )
    prom = f"{res.magnitud_promedio:4.1f}" if res.magnitud_promedio is not None else "NMG"
    out.extend([
        "-" * 80,
        f" rms= {res.rms:6.3f} s  |  error ellipse: x={res.elipse_x_km:6.2f} km, y={res.elipse_y_km:6.2f} km, theta={res.elipse_theta_deg:6.2f}°  |  Md={prom}",
        f" Lat: {res.latitud:8.4f} +- {res.err_lat_deg:6.4f}° ({res.err_lat_km:6.2f} km)  |  "
        f"Lon: {res.longitud:9.4f} +- {res.err_lon_deg:6.4f}° ({res.err_lon_km:6.2f} km)",
        f" Prof: {res.profundidad_km:6.2f} +- {res.err_prof_km:5.2f} km  |  t0: {res.tiempo_origen_s:6.2f} +- {res.err_t0_s:5.2f} s",
    ])
    return "\n".join(out)


class DialogoLocalizarFastHypo(QDialog):
    """
    Interfaz de localización hipocentral FASTHYPO en Python puro, invocada
    directamente desde `fases.py` con las fases picadas precargadas.
    """

    def __init__(
        self,
        evento_p: EventoP,
        rutas_salida: Optional[Dict[str, str]] = None,
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Localización Hipocentral — FASTHYPO (Python / RSA)")
        self.setWindowFlags(
            self.windowFlags()
            | Qt.WindowMinimizeButtonHint
            | Qt.WindowMaximizeButtonHint
            | Qt.WindowCloseButtonHint
        )
        self.resize(1360, 780)
        # Módulo profundo (nivel 3): deshabilitar la X de la ventana para volver siempre por '← Volver'
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowCloseButtonHint)
        self.setWindowState(Qt.WindowMaximized)

        self.evento_p = evento_p
        self.rutas_salida = rutas_salida or {}
        self.resultado_actual: Optional[ResultadoLocalizacion] = None
        self.corridas_disponibles: List[Tuple[float, str, ResultadoLocalizacion]] = []

        self.modelos = leer_modelos_velocidad(Path(ruta_datos_fasthypo) / "FHVELOC.DAT")
        self.estaciones_cat = leer_estaciones(Path(ruta_datos_fasthypo) / "FHSTA.DAT")
        self.coefs_mag = leer_coeficientes_magnitud(Path(ruta_datos_fasthypo) / "Mag2000.txt")
        self._poligonos_ecuador: List[List[Tuple[float, float]]] = self._cargar_poligonos_ecuador()
        self._ventana_mapa_emergente: Optional[QDialog] = None
        self._fig_mapa_emergente: Optional[Figure] = None
        self._ax_mapa_emergente = None
        self._canvas_mapa_emergente: Optional[FigureCanvasQTAgg] = None

        if not self.modelos:
            QMessageBox.warning(
                self,
                "Modelos de Velocidad Faltantes",
                "No se pudieron cargar los modelos de velocidad (FHVELOC.DAT).\n"
                "Verifique que el archivo exista en datos/fasthypo/ o hypo/binarios_originales/."
            )
        if not self.estaciones_cat:
            QMessageBox.warning(
                self,
                "Catálogo de Estaciones Faltante",
                "No se pudieron cargar las coordenadas de estaciones (FHSTA.DAT / estaciones.csv).\n"
                "Verifique que exista FHSTA.DAT en datos/fasthypo/ o estaciones.csv en datos/."
            )

        self._construir_ui()
        self._actualizar_mapa_ecuador(None)

    def _cargar_poligonos_ecuador(self) -> List[List[Tuple[float, float]]]:
        """Carga los polígonos provinciales del Ecuador desde datos/GIS/ECU provincias.shp."""
        poligonos: List[List[Tuple[float, float]]] = []
        if pyshp is None:
            return poligonos
        carpetas_gis = [
            ruta_datos_gis,
            os.path.join(ruta_proyecto, "datos", "GIS"),
            os.path.join(str(Path(ruta_proyecto).parent), "datos", "GIS"),
            r"C:\proyectos\rsa_sismologia\datos\GIS",
        ]
        for carpeta in carpetas_gis:
            if not os.path.isdir(carpeta):
                continue
            for nombre in ("ECU provincias.shp", "ecuador.shp", "ecuadorPoly.shp"):
                ruta_shp = os.path.join(carpeta, nombre)
                if not os.path.exists(ruta_shp):
                    continue
                try:
                    sf = pyshp.Reader(ruta_shp)
                    for shp in sf.shapes():
                        pts = shp.points
                        parts = list(shp.parts) + [len(pts)]
                        for k in range(len(parts) - 1):
                            anillo = pts[parts[k] : parts[k + 1]]
                            if len(anillo) >= 3:
                                poligonos.append(anillo)
                    if poligonos:
                        return poligonos
                except Exception as e:
                    print(f"Aviso cargando mapa {nombre} en {carpeta}: {e}")
        return poligonos

    def _construir_ui(self) -> None:
        lay_principal = QVBoxLayout(self)
        lay_principal.setSpacing(6)
        lay_principal.setContentsMargins(8, 8, 8, 8)

        ev = self.evento_p
        lbl_ev = QLabel(
            f"<b>Evento:</b> 20{ev.anio:02d}-{ev.mes:02d}-{ev.dia:02d} {ev.hora:02d}:{ev.minuto:02d} UTC  |  "
            f"<b>Estaciones con P picada:</b> {len(ev.fases)}"
        )
        lbl_ev.setStyleSheet("font-size: 13px; color: #1e3a8a; background:#eff6ff; padding:6px 10px; border-radius:4px;")
        lay_principal.addWidget(lbl_ev)

        splitter = QSplitter(Qt.Horizontal)
        lay_principal.addWidget(splitter, 1)

        # ---- Panel izquierdo: controles, comparativo, resumen y tabla por estación ----
        panel_izq = QWidget()
        lay = QVBoxLayout(panel_izq)
        lay.setSpacing(6)
        lay.setContentsMargins(0, 0, 4, 0)

        # Parámetros (equivalentes a fast.in / Iaspei.frm)
        grp_par = QGroupBox("Parámetros de Localización (FASTHYPO)")
        grid = QGridLayout(grp_par)

        grid.addWidget(QLabel("Modelo cortical:"), 0, 0)
        self.cmb_modelo = QComboBox()
        nombres_mod = sorted(self.modelos.keys())
        self.cmb_modelo.addItems(nombres_mod)
        if "asw" in nombres_mod:
            self.cmb_modelo.setCurrentText("asw")
        grid.addWidget(self.cmb_modelo, 0, 1)

        grid.addWidget(QLabel("Máx. iteraciones:"), 0, 2)
        self.spin_iter = QSpinBox()
        self.spin_iter.setRange(10, 500)
        self.spin_iter.setValue(100)
        grid.addWidget(self.spin_iter, 0, 3)

        self.chk_prof_fija = QCheckBox("Profundidad fija")
        grid.addWidget(self.chk_prof_fija, 0, 4)

        grid.addWidget(QLabel("Latitud inicial (°):"), 1, 0)
        self.spin_lat = QDoubleSpinBox()
        self.spin_lat.setRange(-90.0, 90.0)
        self.spin_lat.setDecimals(4)
        self.spin_lat.setValue(-2.5000)
        grid.addWidget(self.spin_lat, 1, 1)

        grid.addWidget(QLabel("Longitud inicial (°):"), 1, 2)
        self.spin_lon = QDoubleSpinBox()
        self.spin_lon.setRange(-180.0, 180.0)
        self.spin_lon.setDecimals(4)
        self.spin_lon.setValue(-79.0000)
        grid.addWidget(self.spin_lon, 1, 3)

        grid.addWidget(QLabel("Profundidad (km):"), 2, 0)
        self.spin_prof = QDoubleSpinBox()
        self.spin_prof.setRange(0.5, 500.0)
        self.spin_prof.setDecimals(2)
        self.spin_prof.setValue(60.0)
        grid.addWidget(self.spin_prof, 2, 1)

        grid.addWidget(QLabel("Tiempo origen t0 (s):"), 2, 2)
        self.spin_t0 = QDoubleSpinBox()
        self.spin_t0.setRange(-60.0, 60.0)
        self.spin_t0.setDecimals(2)
        self.spin_t0.setValue(0.0)
        grid.addWidget(self.spin_t0, 2, 3)

        # Botones de ejecución: puntual y multi-profundidad
        self.btn_localizar = QPushButton("🎯 Localizar (1 Semilla)")
        self.btn_localizar.setMinimumHeight(32)
        self.btn_localizar.setStyleSheet("background-color: #15803d; color: white; font-weight: bold;")
        self.btn_localizar.clicked.connect(self.ejecutar_localizacion)
        grid.addWidget(self.btn_localizar, 1, 4)

        self.btn_multi_prof = QPushButton("🔄 Correr 5 Profundidades\n(60 / 49.9 / 33 / 14.9 / 5)")
        self.btn_multi_prof.setMinimumHeight(40)
        self.btn_multi_prof.setStyleSheet("background-color: #7c3aed; color: white; font-weight: bold;")
        self.btn_multi_prof.clicked.connect(self.ejecutar_multi_profundidad)
        grid.addWidget(self.btn_multi_prof, 2, 4)

        # Botones rápidos de profundidades semilla RSA
        fila_presets = QHBoxLayout()
        fila_presets.addWidget(QLabel("Semillas rápidas de profundidad RSA (km):"))
        for z_preset in (60.0, 49.9, 33.0, 14.9, 5.0):
            btn_z = QPushButton(f"{z_preset:g} km")
            btn_z.setMaximumHeight(26)
            btn_z.clicked.connect(lambda _=False, zp=z_preset: self._aplicar_semilla_y_correr(zp))
            fila_presets.addWidget(btn_z)
        fila_presets.addStretch(1)
        grid.addLayout(fila_presets, 3, 0, 1, 5)

        lay.addWidget(grp_par)

        # Tabla comparativa de corridas (el usuario selecciona cuál es la mejor)
        grp_comp = QGroupBox("Comparativo de Corridas (haga clic en una fila para inspeccionarla y elegirla al guardar)")
        lay_comp = QVBoxLayout(grp_comp)
        lay_comp.setContentsMargins(6, 4, 6, 4)
        self.tabla_corridas = QTableWidget()
        self.tabla_corridas.setColumnCount(10)
        self.tabla_corridas.setHorizontalHeaderLabels(
            ["Semilla Z", "Modo", "Lat (°)", "Lon (°)", "Prof Final", "t0 (s)", "RMS (s)", "Elipse (km)", "Md", "Iter."]
        )
        self.tabla_corridas.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla_corridas.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla_corridas.setSelectionMode(QTableWidget.SingleSelection)
        self.tabla_corridas.setAlternatingRowColors(True)
        self.tabla_corridas.setMaximumHeight(160)
        self.tabla_corridas.currentCellChanged.connect(self._al_seleccionar_corrida)
        lay_comp.addWidget(self.tabla_corridas)
        lay.addWidget(grp_comp)

        # Resumen numérico (estilo Form2 de VB5)
        self.lbl_resumen = QLabel("Presione 'Correr 5 Profundidades' o 'Localizar (1 Semilla)' para calcular el hipocentro.")
        self.lbl_resumen.setStyleSheet(
            "font-family: Consolas, monospace; font-size: 12px; font-weight: bold; "
            "background-color: #0f172a; color: #38bdf8; padding: 8px 10px; border-radius: 6px;"
        )
        lay.addWidget(self.lbl_resumen)

        # Tabla de residuales por estación (última iteración completa)
        grp_est = QGroupBox("Detalle Completo de la Última Iteración por Estación")
        lay_est = QVBoxLayout(grp_est)
        lay_est.setContentsMargins(6, 4, 6, 4)
        self.tabla_res = QTableWidget()
        self.tabla_res.setColumnCount(14)
        self.tabla_res.setHorizontalHeaderLabels(
            [
                "Est.", "Dist (km)", "Azm (°)", "Ain (°)",
                "P obs (s)", "Tp cal (s)", "P-res (s)", "Wt P",
                "S obs (s)", "Ts cal (s)", "S-res (s)", "Wt S",
                "Coda (s)", "Md",
            ]
        )
        self.tabla_res.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla_res.setAlternatingRowColors(True)
        # Resaltar encabezados de P-res (col 6) y S-res (col 10)
        for col_res in (6, 10):
            hdr_item = self.tabla_res.horizontalHeaderItem(col_res)
            if hdr_item is not None:
                hdr_item.setFont(QFont("Segoe UI", 9, QFont.Bold))
                hdr_item.setForeground(QColor("#b91c1c"))
        lay_est.addWidget(self.tabla_res)
        lay.addWidget(grp_est, 1)

        splitter.addWidget(panel_izq)

        # ---- Panel derecho: Mapa de Localización del Ecuador ----
        grp_mapa = QGroupBox("Mapa de Localización — Ecuador")
        lay_mapa = QVBoxLayout(grp_mapa)
        lay_mapa.setSpacing(4)
        lay_mapa.setContentsMargins(6, 4, 6, 6)

        self.figura_mapa = Figure(figsize=(7.0, 7.6), dpi=100)
        self.ax_mapa = self.figura_mapa.add_subplot(111)
        self.canvas_mapa = FigureCanvasQTAgg(self.figura_mapa)
        self.toolbar_mapa = NavigationToolbar2QT(self.canvas_mapa, self)
        self.toolbar_mapa.setMaximumHeight(30)

        fila_hdr_mapa = QHBoxLayout()
        fila_hdr_mapa.setSpacing(6)
        fila_hdr_mapa.addWidget(self.toolbar_mapa, 1)
        self.btn_mapa_emergente = QPushButton("🗺️ Ventana Emergente")
        self.btn_mapa_emergente.setMaximumHeight(28)
        self.btn_mapa_emergente.setStyleSheet(
            "background-color: #1e40af; color: white; font-weight: bold; padding: 2px 10px;"
        )
        self.btn_mapa_emergente.setToolTip("Abrir el mapa del Ecuador en una ventana independiente y redimensionable")
        self.btn_mapa_emergente.clicked.connect(self.abrir_mapa_emergente)
        fila_hdr_mapa.addWidget(self.btn_mapa_emergente)

        lay_mapa.addLayout(fila_hdr_mapa)
        lay_mapa.addWidget(self.canvas_mapa, 1)

        splitter.addWidget(grp_mapa)
        splitter.setStretchFactor(0, 52)
        splitter.setStretchFactor(1, 48)
        splitter.setSizes([700, 660])

        # Botones inferiores (siempre visibles al fondo de la ventana)
        fila_bot = QHBoxLayout()
        self.btn_guardar = QPushButton("💾 Guardar Solución Seleccionada (.rsa, Phase*, .P, .L, .S)")
        self.btn_guardar.setMinimumHeight(36)
        self.btn_guardar.setEnabled(False)
        self.btn_guardar.setStyleSheet("background-color: #0284c7; color: white; font-weight: bold; padding: 0 14px;")
        self.btn_guardar.clicked.connect(self.guardar_solucion)
        fila_bot.addWidget(self.btn_guardar)

        fila_bot.addStretch(1)
        btn_cerrar = QPushButton("← Volver")
        btn_cerrar.setMinimumSize(110, 34)
        btn_cerrar.setStyleSheet("font-weight: bold; padding: 4px 14px;")
        btn_cerrar.clicked.connect(self.reject)
        fila_bot.addWidget(btn_cerrar)
        lay_principal.addLayout(fila_bot)

    def _aplicar_semilla_y_correr(self, prof_km: float) -> None:
        self.spin_prof.setValue(prof_km)
        self.ejecutar_localizacion()

    def _correr_una_semilla(self, prof_ini: float, prof_fija: bool) -> ResultadoLocalizacion:
        mod = self.cmb_modelo.currentText().strip().lower()
        res = localizar_hipocentro(
            evento=self.evento_p,
            estaciones_cat=self.estaciones_cat,
            capas=self.modelos[mod],
            modelo_nombre=mod,
            lat_ini=self.spin_lat.value(),
            lon_ini=self.spin_lon.value(),
            prof_ini=prof_ini,
            t0_ini=self.spin_t0.value(),
            max_iter=self.spin_iter.value(),
            prof_fija=prof_fija,
        )
        calcular_magnitud_coda(res, coeficientes_estacion=self.coefs_mag)
        return res

    def _mostrar_resultado_en_panel(self, res: ResultadoLocalizacion) -> None:
        self.resultado_actual = res
        md_txt = f"{res.magnitud_promedio:.1f}" if res.magnitud_promedio is not None else "NMG"
        self.lbl_resumen.setText(
            f"Lat: {res.latitud:+.4f}° (±{res.err_lat_km:.2f} km)  |  "
            f"Lon: {res.longitud:+.4f}° (±{res.err_lon_km:.2f} km)  |  "
            f"Prof: {res.profundidad_km:.2f} km (±{res.err_prof_km:.2f} km)\n"
            f"t0: {res.tiempo_origen_s:+.2f} s  |  RMS: {res.rms:.3f} s  |  "
            f"Elipse: {res.elipse_x_km:.2f} × {res.elipse_y_km:.2f} km (θ={res.elipse_theta_deg:.1f}°)  |  "
            f"Magnitud Md: {md_txt}"
        )

        mapa_md = {sta: md for sta, _, _, md in res.magnitudes_estacion}
        self.tabla_res.setRowCount(len(res.estaciones))
        fuente_res = QFont("Segoe UI", 9, QFont.Bold)
        for i, e in enumerate(res.estaciones):
            md_v = mapa_md.get(e.estacion)
            vals = [
                e.estacion,
                f"{e.dist_km:.1f}",
                f"{int(round(e.azimut))}",
                f"{int(round(e.angulo_salida))}",
                f"{e.p_obs:.2f}",
                f"{e.tp_cal:.2f}",
                f"{e.p_res:+.2f}",
                str(e.peso_p),
                f"{e.s_obs:.2f}" if e.s_obs > 0 else "---",
                f"{e.ts_cal:.2f}" if e.s_obs > 0 else "---",
                f"{e.s_res:+.2f}" if e.s_obs > 0 else "---",
                str(e.peso_s) if e.s_obs > 0 else "---",
                f"{e.coda:.1f}" if e.coda > 0 else "---",
                f"{md_v:.1f}" if md_v is not None else "NMG",
            ]
            for c, v in enumerate(vals):
                it = QTableWidgetItem(v)
                it.setFlags(it.flags() & ~Qt.ItemIsEditable)
                it.setTextAlignment(Qt.AlignCenter)
                # Resaltar P-res (col 6) y S-res (col 10) con color por magnitud de residual
                if c in (6, 10):
                    it.setFont(fuente_res)
                    if v == "---":
                        it.setBackground(QColor("#f1f5f9"))
                        it.setForeground(QColor("#64748b"))
                    else:
                        val_abs = abs(e.p_res if c == 6 else e.s_res)
                        if val_abs <= 0.30:
                            it.setBackground(QColor("#dcfce7"))
                            it.setForeground(QColor("#166534"))
                        elif val_abs <= 0.80:
                            it.setBackground(QColor("#fef3c7"))
                            it.setForeground(QColor("#92400e"))
                        else:
                            it.setBackground(QColor("#fee2e2"))
                            it.setForeground(QColor("#991b1b"))
                self.tabla_res.setItem(i, c, it)

        self._actualizar_mapa_ecuador(res)
        self.btn_guardar.setEnabled(True)

    def abrir_mapa_emergente(self) -> None:
        """Abre (o trae al frente) una ventana emergente independiente con el mapa del Ecuador a gran tamaño."""
        if self._ventana_mapa_emergente is not None and self._ventana_mapa_emergente.isVisible():
            self._ventana_mapa_emergente.raise_()
            self._ventana_mapa_emergente.activateWindow()
            return

        dlg_mapa = QDialog(self)
        dlg_mapa.setWindowTitle("Mapa de Localización — Ecuador (FASTHYPO / RSA)")
        dlg_mapa.setWindowFlags(
            dlg_mapa.windowFlags()
            | Qt.WindowMinimizeButtonHint
            | Qt.WindowMaximizeButtonHint
            | Qt.WindowCloseButtonHint
        )
        dlg_mapa.resize(980, 820)

        lay_m = QVBoxLayout(dlg_mapa)
        lay_m.setSpacing(4)
        lay_m.setContentsMargins(6, 6, 6, 6)

        fig = Figure(figsize=(9.5, 8.2), dpi=105)
        ax = fig.add_subplot(111)
        canvas = FigureCanvasQTAgg(fig)
        toolbar = NavigationToolbar2QT(canvas, dlg_mapa)
        lay_m.addWidget(toolbar)
        lay_m.addWidget(canvas, 1)

        self._ventana_mapa_emergente = dlg_mapa
        self._fig_mapa_emergente = fig
        self._ax_mapa_emergente = ax
        self._canvas_mapa_emergente = canvas

        self._dibujar_mapa_en_eje(ax, fig, canvas, self.resultado_actual)
        dlg_mapa.show()

    def _actualizar_mapa_ecuador(self, res: Optional[ResultadoLocalizacion]) -> None:
        """Actualiza el mapa embebido y, si está abierta, también la ventana emergente del mapa."""
        self._dibujar_mapa_en_eje(self.ax_mapa, self.figura_mapa, self.canvas_mapa, res)
        if (
            self._ventana_mapa_emergente is not None
            and self._ventana_mapa_emergente.isVisible()
            and self._ax_mapa_emergente is not None
            and self._fig_mapa_emergente is not None
            and self._canvas_mapa_emergente is not None
        ):
            self._dibujar_mapa_en_eje(
                self._ax_mapa_emergente,
                self._fig_mapa_emergente,
                self._canvas_mapa_emergente,
                res,
            )

    def _dibujar_mapa_en_eje(
        self,
        ax,
        figura: Figure,
        canvas: FigureCanvasQTAgg,
        res: Optional[ResultadoLocalizacion],
    ) -> None:
        """Dibuja el mapa del Ecuador con estaciones participantes, corridas y el epicentro seleccionado."""
        ax.clear()
        ax.set_facecolor("#dbeafe")

        if self._poligonos_ecuador:
            coleccion = PolyCollection(
                self._poligonos_ecuador,
                facecolor="#f8fafc",
                edgecolor="#64748b",
                linewidth=0.65,
                zorder=1,
            )
            ax.add_collection(coleccion)

        # Estaciones participantes en el evento
        lons_vis = [-81.3, -75.0]
        lats_vis = [-5.2, 1.7]
        codigos_ev = [f.estacion.upper() for f in self.evento_p.fases]
        for cod in codigos_ev:
            est = self.estaciones_cat.get(cod)
            if est is None:
                continue
            ax.scatter(
                est.longitud, est.latitud,
                marker="^", s=48, color="#1d4ed8", edgecolor="white", linewidth=0.6, zorder=4
            )
            ax.annotate(
                cod,
                (est.longitud, est.latitud),
                xytext=(4, 4),
                textcoords="offset points",
                fontsize=7.5,
                fontweight="bold",
                color="#1e3a8a",
                zorder=5,
            )
            lons_vis.append(est.longitud)
            lats_vis.append(est.latitud)

        # Corridas alternativas (si hay multi-profundidad)
        for z_sem, _modo, r_alt in self.corridas_disponibles:
            if res is not None and r_alt is res:
                continue
            ax.scatter(
                r_alt.longitud, r_alt.latitud,
                marker="o", s=34, color="#9333ea", alpha=0.55, edgecolor="white", linewidth=0.5, zorder=5
            )
            lons_vis.append(r_alt.longitud)
            lats_vis.append(r_alt.latitud)

        if res is not None:
            # Líneas estación-epicentro
            for e in res.estaciones:
                est = self.estaciones_cat.get(e.estacion.upper())
                if est is not None:
                    ax.plot(
                        [res.longitud, est.longitud],
                        [res.latitud, est.latitud],
                        linestyle="--",
                        linewidth=0.7,
                        color="#94a3b8",
                        alpha=0.7,
                        zorder=2,
                    )

            # Elipse de error horizontal aproximada en grados
            km_lat = 111.195
            km_lon = max(10.0, 111.320 * math.cos(math.radians(res.latitud)))
            ancho_deg = 2.0 * res.elipse_x_km / km_lon
            alto_deg = 2.0 * res.elipse_y_km / km_lat
            elipse = Ellipse(
                (res.longitud, res.latitud),
                width=ancho_deg,
                height=alto_deg,
                angle=-res.elipse_theta_deg,
                facecolor="#ef4444",
                alpha=0.18,
                edgecolor="#dc2626",
                linewidth=1.1,
                zorder=6,
            )
            ax.add_patch(elipse)

            # Epicentro seleccionado (círculo + estrella roja)
            ax.scatter(
                res.longitud, res.latitud,
                marker="*", s=220, color="#dc2626", edgecolor="#ffffff", linewidth=0.9, zorder=7
            )
            md_txt = f"Md {res.magnitud_promedio:.1f}" if res.magnitud_promedio is not None else "Md NMG"
            ax.set_title(
                f"Epicentro: {res.latitud:.3f}°, {res.longitud:.3f}° | Z={res.profundidad_km:.1f} km | {md_txt}",
                fontsize=9.5,
                fontweight="bold",
                color="#0f172a",
                pad=6,
            )
            lons_vis.append(res.longitud)
            lats_vis.append(res.latitud)
        else:
            ax.set_title("Ecuador — Estaciones con fase P picada", fontsize=9.5, fontweight="bold", color="#334155", pad=6)

        lon_min = min(lons_vis) - 0.35
        lon_max = max(lons_vis) + 0.35
        lat_min = min(lats_vis) - 0.35
        lat_max = max(lats_vis) + 0.35
        ax.set_xlim(lon_min, lon_max)
        ax.set_ylim(lat_min, lat_max)
        ax.set_aspect("equal", adjustable="box")
        ax.set_xlabel("Longitud (°)", fontsize=8.5)
        ax.set_ylabel("Latitud (°)", fontsize=8.5)
        ax.tick_params(labelsize=8)
        ax.grid(True, linestyle=":", alpha=0.55, color="#64748b")
        figura.subplots_adjust(left=0.09, right=0.98, top=0.94, bottom=0.07)
        canvas.draw_idle()

    def _refrescar_tabla_corridas(self, indice_seleccionar: int) -> None:
        self.tabla_corridas.blockSignals(True)
        self.tabla_corridas.setRowCount(len(self.corridas_disponibles))

        # Identificar el menor RMS entre las corridas para resaltarlo visualmente
        idx_mejor = min(
            range(len(self.corridas_disponibles)),
            key=lambda k: self.corridas_disponibles[k][2].rms,
        ) if self.corridas_disponibles else -1

        for i, (z_sem, modo_txt, res) in enumerate(self.corridas_disponibles):
            md_txt = f"{res.magnitud_promedio:.1f}" if res.magnitud_promedio is not None else "NMG"
            marca = " ★" if i == idx_mejor else ""
            vals = [
                f"{z_sem:g} km{marca}",
                modo_txt,
                f"{res.latitud:.4f}",
                f"{res.longitud:.4f}",
                f"{res.profundidad_km:.2f} km",
                f"{res.tiempo_origen_s:.2f}",
                f"{res.rms:.3f}",
                f"{res.elipse_x_km:.2f}×{res.elipse_y_km:.2f}",
                md_txt,
                str(max(0, len(res.historial_iteraciones) - 1)),
            ]
            for c, v in enumerate(vals):
                it = QTableWidgetItem(v)
                it.setFlags(it.flags() & ~Qt.ItemIsEditable)
                if i == idx_mejor:
                    it.setForeground(QColor("#15803d"))
                    it.setFont(QFont("Segoe UI", 9, QFont.Bold))
                self.tabla_corridas.setItem(i, c, it)

        self.tabla_corridas.blockSignals(False)
        if 0 <= indice_seleccionar < len(self.corridas_disponibles):
            self.tabla_corridas.selectRow(indice_seleccionar)
            self._mostrar_resultado_en_panel(self.corridas_disponibles[indice_seleccionar][2])

    def _al_seleccionar_corrida(self, fila_actual: int, _col_actual: int, _fila_prev: int, _col_prev: int) -> None:
        if 0 <= fila_actual < len(self.corridas_disponibles):
            self._mostrar_resultado_en_panel(self.corridas_disponibles[fila_actual][2])

    def ejecutar_localizacion(self) -> None:
        mod = self.cmb_modelo.currentText().strip().lower()
        if mod not in self.modelos:
            QMessageBox.warning(self, "Modelo", f"Modelo '{mod}' no disponible.")
            return
        try:
            z_sem = self.spin_prof.value()
            fija = self.chk_prof_fija.isChecked()
            res = self._correr_una_semilla(z_sem, fija)
            modo_txt = "Fija" if fija else "Libre"
            self.corridas_disponibles.append((z_sem, modo_txt, res))
            self._refrescar_tabla_corridas(len(self.corridas_disponibles) - 1)
        except Exception as e:
            QMessageBox.critical(self, "Error en Localización", f"No se pudo localizar el evento:\n{e}")

    def ejecutar_multi_profundidad(self) -> None:
        """Ejecuta las 5 profundidades semilla estándar RSA (60, 49.9, 33, 14.9, 5 km) y presenta el comparativo."""
        mod = self.cmb_modelo.currentText().strip().lower()
        if mod not in self.modelos:
            QMessageBox.warning(self, "Modelo", f"Modelo '{mod}' no disponible.")
            return

        self.corridas_disponibles.clear()
        fija = self.chk_prof_fija.isChecked()
        modo_txt = "Fija" if fija else "Libre"
        errores = []

        for z_sem in (60.0, 49.9, 33.0, 14.9, 5.0):
            try:
                res = self._correr_una_semilla(z_sem, fija)
                self.corridas_disponibles.append((z_sem, modo_txt, res))
            except Exception as e:
                errores.append(f"Z={z_sem} km: {e}")

        if not self.corridas_disponibles:
            QMessageBox.critical(self, "Error en Multi-Profundidad", "\n".join(errores))
            return

        idx_mejor = min(
            range(len(self.corridas_disponibles)),
            key=lambda k: self.corridas_disponibles[k][2].rms,
        )
        self._refrescar_tabla_corridas(idx_mejor)

    def guardar_solucion(self) -> None:
        if self.resultado_actual is None:
            return
        if not self.rutas_salida or not self.rutas_salida.get("rsa"):
            QMessageBox.warning(self, "Rutas", "No se resolvieron las rutas de salida fastHypo/.")
            return
        try:
            for clave in ("rsa", "phase", "L", "P", "S"):
                ruta = self.rutas_salida.get(clave)
                if ruta:
                    os.makedirs(os.path.dirname(ruta), exist_ok=True)

            Path(self.rutas_salida["phase"]).write_text(formatear_archivo_phase(self.evento_p), encoding="ascii", errors="replace")
            Path(self.rutas_salida["P"]).write_text(formatear_archivo_p(self.evento_p), encoding="ascii", errors="replace")
            Path(self.rutas_salida["L"]).write_text(formatear_salida_l(self.resultado_actual), encoding="ascii", errors="replace")
            Path(self.rutas_salida["S"]).write_text(formatear_salida_s(self.resultado_actual), encoding="ascii", errors="replace")
            Path(self.rutas_salida["rsa"]).write_text(formatear_salida_rsa(self.resultado_actual), encoding="ascii", errors="replace")

            carpeta_guardado = os.path.dirname(self.rutas_salida['rsa'])
            QMessageBox.information(
                self,
                "Solución Guardada",
                f"Archivos FASTHYPO guardados correctamente en:\n{carpeta_guardado}\n\n"
                f"• {os.path.basename(self.rutas_salida['rsa'])}\n"
                f"• {os.path.basename(self.rutas_salida['P'])}\n"
                f"• {os.path.basename(self.rutas_salida['L'])}\n"
                f"• {os.path.basename(self.rutas_salida['S'])}\n"
                f"• {os.path.basename(self.rutas_salida['phase'])}",
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error al Guardar", f"No se pudieron escribir los archivos:\n{e}")
