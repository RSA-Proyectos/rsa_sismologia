"""
================================================================================
Módulo: fasthypo.py
Propósito: Reconstrucción en Python puro de FAST.EXE / FPONG.EXE (FASTHYPO,
           R. B. Herrmann 1979, paquete IASPEI) para localización hipocentral
           en medio estratificado horizontal, cálculo de elipse de error y
           magnitud de duración (Md).

Entradas estándar:
  - FHVELOC.DAT : Modelos corticales de velocidad (Vp, profundidad techo, Vs).
  - FHSTA.DAT   : Catálogo de estaciones (lat, lon, correcciones de estación P/S).
  - *.P         : Archivo de fases generado por convert1.py (ej. 111917.01P).
  - Phase*      : Opcional, para extraer duraciones de coda y calcular Md (.rsa).

Salidas estándar:
  - MMDDHH.MML  : Listado completo de iteraciones, residuales, elipse y errores.
  - MMDDHH.MMS  : Línea resumen de solución hipocentral.
  - MMDDHHMM.rsa: Listado completo + bloque 'CALCULO DE LA MAGNITUD' (Md).
================================================================================
"""

from dataclasses import dataclass, field
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np


RADIO_TIERRA_KM = 6371.0
FACTOR_GEOCENTRICO = 0.993277  # 1 - e^2 clásico de FASTHYPO (Herrmann 1979)


@dataclass
class CapaVelocidad:
    """Capa horizontal de velocidad sísmica (Vp, profundidad techo z, Vs)."""
    vp: float
    z_techo: float
    vs: float


@dataclass
class EstacionFH:
    """Estación sísmica leída desde FHSTA.DAT."""
    codigo: str
    latitud: float       # Grados decimales (Sur negativo)
    longitud: float      # Grados decimales (Oeste negativo)
    modelo_id: int
    corr_p: float        # Corrección de estación P (s)
    corr_s: float        # Corrección de estación S (s)
    descripcion: str = ""


@dataclass
class FaseEstacionP:
    """Lectura de una estación en el archivo .P de FASTHYPO."""
    estacion: str
    seg_p: float
    polaridad: str
    peso_p: int
    seg_s: float
    peso_s: int
    coda: float = 0.0


@dataclass
class EventoP:
    """Contenido completo de un archivo .P de FASTHYPO."""
    anio: int
    mes: int
    dia: int
    hora: int
    minuto: int
    fases: List[FaseEstacionP] = field(default_factory=list)


@dataclass
class ResultadoEstacion:
    """Detalle final de cada estación tras la localización."""
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
    """Resultado completo de la localización hipocentral FASTHYPO."""
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


# =============================================================================
# LECTURA DE ARCHIVOS FHVELOC.DAT, FHSTA.DAT Y *.P
# =============================================================================

def leer_modelos_velocidad(ruta_fhveloc: Path) -> Dict[str, List[CapaVelocidad]]:
    """
    Lee FHVELOC.DAT con formato fijo Fortran:
      Encabezado: <nombre_3chars> <n_capas_2d>   (ej. 'asw 05')
      Cada capa : cols 0:5 Vp, cols 5:9 z_techo, cols 9:14 Vs (ej. '3.32 00.01.94')
    """
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
    """
    Lee FHSTA.DAT con formato fijo Fortran:
      'LABR 02 43.71s 79 04.34w         1-0.07 -0.83                    Labrado'
    """
    lineas = ruta_fhsta.read_bytes().decode("latin-1", errors="replace").splitlines()
    estaciones: Dict[str, EstacionFH] = {}
    for linea in lineas:
        if len(linea.strip()) < 24:
            continue
        pad = linea.ljust(65)
        codigo = pad[0:4].strip()
        if not codigo:
            continue
        try:
            lat_g = float(pad[5:7].strip())
            lat_m = float(pad[8:13].strip())
            hem_lat = pad[13:14].strip().lower()
            lat = lat_g + lat_m / 60.0
            if hem_lat == "s":
                lat = -lat

            lon_g = float(pad[15:17].strip())
            lon_m = float(pad[18:23].strip())
            hem_lon = pad[23:24].strip().lower()
            lon = lon_g + lon_m / 60.0
            if hem_lon == "w":
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
    return estaciones


def leer_archivo_p(ruta_p: Path) -> EventoP:
    """Lee un archivo de fases FASTHYPO (.P)."""
    lineas = [l for l in ruta_p.read_bytes().decode("latin-1", errors="replace").splitlines() if l.strip()]
    if not lineas:
        raise ValueError(f"Archivo .P vacío: {ruta_p}")

    hdr = lineas[0].split()
    anio, mes, dia, hora, minuto = (int(x) for x in hdr[:5])
    fases: List[FaseEstacionP] = []
    for ln in lineas[1:]:
        pad = ln.ljust(26)
        est = pad[0:4].strip().upper()
        if not est:
            continue
        seg_p = float(pad[4:10].strip()) if pad[4:10].strip() else 0.0
        pol = pad[11:12].strip() or "u"
        pwt = int(pad[13:15].strip()) if pad[13:15].strip() else 4
        seg_s = float(pad[16:22].strip()) if pad[16:22].strip() else 0.0
        swt = int(pad[23:26].strip()) if pad[23:26].strip() else 4
        fases.append(
            FaseEstacionP(
                estacion=est,
                seg_p=seg_p,
                polaridad=pol,
                peso_p=pwt,
                seg_s=seg_s,
                peso_s=swt,
            )
        )
    return EventoP(anio=anio, mes=mes, dia=dia, hora=hora, minuto=minuto, fases=fases)


# =============================================================================
# GEOMETRÍA GEOCÉNTRICA Y TRAZADO DE RAYOS EN MEDIO ESTRATIFICADO
# =============================================================================

def latitud_geocentrica(lat_deg: float) -> float:
    """Convierte latitud geográfica (grados) a latitud geocéntrica (radianes)."""
    return math.atan(FACTOR_GEOCENTRICO * math.tan(math.radians(lat_deg)))


def distancia_y_azimut(lat1: float, lon1: float, lat2: float, lon2: float) -> Tuple[float, float]:
    """
    Calcula distancia epicentral (km) y azimut estación desde epicentro (grados)
    usando latitud geocéntrica (convención FASTHYPO / Herrmann).
    """
    p1 = latitud_geocentrica(lat1)
    p2 = latitud_geocentrica(lat2)
    dlon = math.radians(lon2 - lon1)
    cos_d = math.sin(p1) * math.sin(p2) + math.cos(p1) * math.cos(p2) * math.cos(dlon)
    cos_d = max(-1.0, min(1.0, cos_d))
    delta = math.acos(cos_d)
    dist_km = delta * RADIO_TIERRA_KM
    y = math.sin(dlon) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dlon)
    azm = math.degrees(math.atan2(y, x)) % 360.0
    return dist_km, azm


def tiempo_viaje_estratificado(
    dist_km: float,
    prof_km: float,
    capas: List[CapaVelocidad],
    usar_s: bool = False,
) -> Tuple[float, float, float, float]:
    """
    Calcula tiempo de viaje mínimo (rayo directo vs. refractados críticos),
    derivadas parciales (dt/ddist, dt/dz) y ángulo de salida 'ain' (grados,
    medido desde la vertical hacia abajo: >90° rayo ascendente, <90° descendente).
    """
    z = max(0.01, prof_km)
    vels = [c.vs if usar_s else c.vp for c in capas]
    z_top = [c.z_techo for c in capas]
    n_capas = len(capas)

    # Identificar capa fuente (ks)
    ks = 0
    for k in range(n_capas):
        if z >= z_top[k]:
            ks = k

    # Espesores atravesados por el rayo directo ascendente desde z hasta superficie
    espesores = []
    for k in range(ks):
        espesores.append(z_top[k + 1] - z_top[k])
    espesores.append(z - z_top[ks])
    v_sub = vels[: ks + 1]
    v_src = vels[ks]

    # 1) Rayo directo ascendente
    if dist_km < 1e-6:
        t_dir = sum(h / v for h, v in zip(espesores, v_sub))
        p_dir = 0.0
    else:
        p_lo = 0.0
        p_hi = 1.0 / max(v_sub) - 1e-12
        for _ in range(70):
            pm = 0.5 * (p_lo + p_hi)
            x_est = sum(
                h * pm * v / math.sqrt(max(1e-15, 1.0 - (pm * v) ** 2))
                for h, v in zip(espesores, v_sub)
            )
            if x_est < dist_km:
                p_lo = pm
            else:
                p_hi = pm
        p_dir = 0.5 * (p_lo + p_hi)
        t_dir = sum(
            h / (v * math.sqrt(max(1e-15, 1.0 - (p_dir * v) ** 2)))
            for h, v in zip(espesores, v_sub)
        )

    cos_src = math.sqrt(max(1e-15, 1.0 - (p_dir * v_src) ** 2))
    dtdx_mejor = p_dir
    dtdz_mejor = cos_src / v_src  # Positivo: al aumentar profundidad aumenta tiempo directo
    ain_mejor = 180.0 - math.degrees(math.asin(min(1.0, p_dir * v_src)))
    t_mejor = t_dir

    # 2) Ondas refractadas críticas en capas más profundas (m > ks)
    for m in range(ks + 1, n_capas):
        vm = vels[m]
        if vm <= max(vels[:m]):
            continue
        pm = 1.0 / vm
        # Tramo ascendente desde superficie hasta m + tramo descendente desde z hasta m
        x_crit = 0.0
        t_int = 0.0
        valido = True
        # Tramo superficie -> interfaz m
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
        # Tramo fuente z -> interfaz m
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
            # Para onda refractada descendente, aumentar z reduce el camino hasta el refractor
            dtdz_mejor = -math.sqrt(max(1e-15, 1.0 - (pm * v_src) ** 2)) / v_src
            ain_mejor = math.degrees(math.asin(min(1.0, pm * v_src)))

    return t_mejor, dtdx_mejor, dtdz_mejor, ain_mejor


def peso_calidad_fasthypo(wt_codigo: int) -> float:
    """
    Factor de ponderación de calidad estándar FASTHYPO / HYPO71 (códigos 0..4):
      0 -> 1.00, 1 -> 0.75, 2 -> 0.50, 3 -> 0.25, >=4 -> 0.00
    """
    if wt_codigo <= 0:
        return 1.0
    if wt_codigo == 1:
        return 0.75
    if wt_codigo == 2:
        return 0.50
    if wt_codigo == 3:
        return 0.25
    return 0.0


# =============================================================================
# INVERSIÓN HIPOCENTRAL FASTHYPO (GEIGER AMORTIGUADO + ELIPSE DE ERROR)
# =============================================================================

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
    """
    Ejecuta la inversión hipocentral iterativa estilo FASTHYPO (Geiger amortiguado
    con limitación de paso en profundidad |dz| <= 5 km, cálculo de covarianza,
    elipse de error horizontal y estadísticas por estación).
    """
    if prof_ini < 0.0:
        prof_fija = True
        prof_ini = abs(prof_ini)

    # Filtrar fases cuyas estaciones existan en FHSTA.DAT
    fases_validas = [f for f in evento.fases if f.estacion.upper() in estaciones_cat]
    if not fases_validas:
        raise ValueError("Ninguna estación del archivo .P se encontró en FHSTA.DAT.")

    lat = float(lat_ini)
    lon = float(lon_ini)
    z = max(0.5, float(prof_ini))
    t0 = float(t0_ini)

    km_por_deg_lat = 111.195 * FACTOR_GEOCENTRICO
    historial: List[Tuple[float, float, float, float, float]] = []
    amortiguamiento = 0.001

    def evaluar_sistema(la: float, lo: float, zz: float, tt0: float):
        km_por_deg_lon = 111.195 * math.cos(latitud_geocentrica(la))
        filas_a = []
        vec_r = []
        vec_w = []
        detalles = []

        for f in fases_validas:
            est = estaciones_cat[f.estacion.upper()]
            dist, azm = distancia_y_azimut(la, lo, est.latitud, est.longitud)
            az_rad = math.radians(azm)

            tp, dtdx_p, dtdz_p, ain_p = tiempo_viaje_estratificado(dist, zz, capas, usar_s=False)
            ts, dtdx_s, dtdz_s, _ = tiempo_viaje_estratificado(dist, zz, capas, usar_s=True)

            # Residuales con corrección de estación (FHSTA.DAT)
            rp = f.seg_p - (tt0 + tp + est.corr_p)
            rs = (f.seg_s - (tt0 + ts + est.corr_s)) if f.seg_s > 0.0 else 0.0

            wp = peso_calidad_fasthypo(f.peso_p)
            ws = peso_calidad_fasthypo(f.peso_s) if f.seg_s > 0.0 else 0.0

            # Derivadas respecto a [d_norte_km, d_este_km, dz_km, dt0]
            # Si el epicentro se mueve al Norte (+dN), la distancia hacia la estación disminuye en cos(azm)
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
                    estacion=est.codigo,
                    dist_km=dist,
                    azimut=azm,
                    angulo_salida=ain_p,
                    p_obs=f.seg_p,
                    tp_cal=tp,
                    p_res=rp,
                    peso_p=f.peso_p,
                    s_obs=f.seg_s,
                    ts_cal=ts,
                    s_res=rs,
                    peso_s=f.peso_s,
                    coda=f.coda,
                )
            )

        A = np.array(filas_a, dtype=float)
        r = np.array(vec_r, dtype=float)
        w = np.array(vec_w, dtype=float)
        sum_sq = float(np.sum((w * r) ** 2))
        return A, r, w, sum_sq, detalles, km_por_deg_lon

    A, r, w, sum_sq, detalles, km_por_deg_lon = evaluar_sistema(lat, lon, z, t0)
    historial.append((lat, lon, z, t0, sum_sq))

    for _ in range(max_iter):
        # Resolver sistema ponderado (W^(1/2) A) dx = W^(1/2) r con amortiguamiento
        sw = np.sqrt(w)[:, None]
        Aw = A * sw
        rw = r * np.sqrt(w)

        if prof_fija:
            cols = [0, 1, 3]
            Aw_sub = Aw[:, cols]
        else:
            cols = [0, 1, 2, 3]
            Aw_sub = Aw

        ATA = Aw_sub.T @ Aw_sub
        ATr = Aw_sub.T @ rw

        # Escala diagonal para amortiguamiento tipo Levenberg-Marquardt
        diag = np.diag(np.maximum(np.diag(ATA), 1e-8))
        try:
            dx_sub = np.linalg.solve(ATA + amortiguamiento * diag, ATr)
        except np.linalg.LinAlgError:
            dx_sub = np.linalg.lstsq(ATA + 1e-3 * diag, ATr, rcond=None)[0]

        dx = np.zeros(4, dtype=float)
        for idx_c, c in enumerate(cols):
            dx[c] = dx_sub[idx_c]

        # Limitación de paso clásica de FASTHYPO (|dz| <= 5.0 km, |d_horiz| <= 50 km)
        if not prof_fija and abs(dx[2]) > 5.0:
            dx[2] = math.copysign(5.0, dx[2])
        paso_h = math.hypot(dx[0], dx[1])
        if paso_h > 50.0:
            escala_h = 50.0 / paso_h
            dx[0] *= escala_h
            dx[1] *= escala_h

        # Probar actualización; si empeora, aumentar amortiguamiento y acortar paso
        mejorado = False
        for intento in range(8):
            factor = 0.5 ** intento
            n_lat = lat + (dx[0] * factor) / km_por_deg_lat
            n_lon = lon + (dx[1] * factor) / km_por_deg_lon
            n_z = max(0.5, z + dx[2] * factor)
            n_t0 = t0 + dx[3] * factor

            nA, nr, nw, n_ssq, ndet, n_kmlon = evaluar_sistema(n_lat, n_lon, n_z, n_t0)
            if n_ssq <= sum_sq + 1e-9 or intento == 7:
                cambio = math.hypot(dx[0] * factor, dx[1] * factor) + abs(dx[2] * factor) + abs(dx[3] * factor)
                lat, lon, z, t0 = n_lat, n_lon, n_z, n_t0
                A, r, w, sum_sq, detalles, km_por_deg_lon = nA, nr, nw, n_ssq, ndet, n_kmlon
                historial.append((lat, lon, z, t0, sum_sq))
                if intento == 0:
                    amortiguamiento = max(1e-6, amortiguamiento * 0.5)
                else:
                    amortiguamiento = min(10.0, amortiguamiento * 2.0)
                mejorado = True
                break

        if not mejorado or cambio < 1e-4:
            break

    # Estadísticas finales, matriz de covarianza (SVD amortiguada estilo Herrmann/error.for)
    # y elipse de error horizontal
    n_obs = len(r)
    n_par = 3 if prof_fija else 4
    dof = max(1, n_obs - n_par)
    rms = math.sqrt(float(np.sum(r ** 2)) / dof)

    sw = np.sqrt(w)[:, None]
    Aw = A * sw
    cols = [0, 1, 3] if prof_fija else [0, 1, 2, 3]
    M = Aw[:, cols]

    # Covarianza amortiguada por SVD (evita explosión en redes con gap azimutal alto)
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
    err_lat_deg = err_n_km / km_por_deg_lat
    err_lon_deg = err_e_km / km_por_deg_lon

    # Elipse de error horizontal (autovalores de la submatriz 2x2 [N, E])
    cov_ne = cov[0:2, 0:2]
    evals, evecs = np.linalg.eigh(cov_ne)
    evals = np.maximum(evals, 0.0)
    elipse_x = math.sqrt(evals[0])
    elipse_y = math.sqrt(evals[1])
    # Azimut del eje mayor desde el Norte (eje 0 = N, eje 1 = E)
    v_mayor = evecs[:, 1]
    theta = math.degrees(math.atan2(v_mayor[1], v_mayor[0])) % 180.0

    return ResultadoLocalizacion(
        evento=evento,
        modelo_nombre=modelo_nombre,
        capas=capas,
        latitud=lat,
        longitud=lon,
        profundidad_km=z,
        tiempo_origen_s=t0,
        rms=rms,
        err_lat_deg=err_lat_deg,
        err_lat_km=err_n_km,
        err_lon_deg=err_lon_deg,
        err_lon_km=err_e_km,
        err_prof_km=err_z_km,
        err_t0_s=err_t0_s,
        elipse_x_km=elipse_x,
        elipse_y_km=elipse_y,
        elipse_theta_deg=theta,
        historial_iteraciones=historial,
        estaciones=detalles,
    )


def leer_coeficientes_magnitud(ruta_mag2000: Path) -> Dict[str, Tuple[float, float, float]]:
    """
    Lee Mag2000.txt (formato VB5 Iaspei.frm):
      <STA_4> <b1> <c1> <c2>
      Md = b1 + c1 * log10(Coda) + c2 * dist_km
    Si b1 == c1 == c2 == 0, la estación reporta 'NMG'.
    """
    coefs: Dict[str, Tuple[float, float, float]] = {}
    if not ruta_mag2000.exists():
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


def calcular_magnitud_coda(
    resultado: ResultadoLocalizacion,
    coeficientes_estacion: Optional[Dict[str, Tuple[float, float, float]]] = None,
    coef_defecto: Tuple[float, float, float] = (2.131382, 0.975177, 0.001410),
) -> ResultadoLocalizacion:
    """
    Calcula magnitud de duración Md por estación exactamente como Iaspei.frm (VB5):
      Md = b1 + c1 * log10(Coda) + c2 * dist_km
    usando los coeficientes por estación de Mag2000.txt.
    """
    mags = []
    validas = []
    tabla = coeficientes_estacion or {}
    for est in resultado.estaciones:
        sta = est.estacion.upper()
        b1, c1, c2 = tabla.get(sta, coef_defecto)
        if (b1 == 0.0 and c1 == 0.0 and c2 == 0.0) or not est.coda or est.coda <= 0.0:
            mags.append((est.estacion, est.dist_km, est.coda if est.coda > 0 else 0.0, None))
        else:
            md = b1 + c1 * math.log10(est.coda) + c2 * est.dist_km
            mags.append((est.estacion, est.dist_km, est.coda, md))
            validas.append(md)
    resultado.magnitudes_estacion = mags
    resultado.magnitud_promedio = float(np.mean(validas)) if validas else None
    return resultado


# =============================================================================
# FORMATEADORES DE SALIDA (.L, .S Y .RSA)
# =============================================================================

def formatear_salida_l(res: ResultadoLocalizacion) -> str:
    """Genera el listado completo .L compatible con FASTHYPO."""
    ev = res.evento
    out = ["", "", "", "       crustal model", "     velocity      depth               s velocity"]
    for c in res.capas:
        out.append(f"       {c.vp:6.3f}   {c.z_techo:7.3f}    {c.vs:6.3f}")
    for f in ev.fases:
        out.append(f" {f.estacion:<4s} {f.peso_p:1d}  {f.seg_p:6.2f} {f.polaridad:1s} {f.peso_s:1d}  {f.seg_s:6.2f}")
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
    out.append(
        f" error ellipse  x={res.elipse_x_km:7.2f} km  y={res.elipse_y_km:7.2f} km  theta ={res.elipse_theta_deg:7.2f}"
    )
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
    """Genera la línea resumen .S compatible con FASTHYPO."""
    ev = res.evento
    return (
        f"{ev.anio:2d} {ev.mes:2d} {ev.dia:2d} {ev.hora:2d} {ev.minuto:2d}  "
        f"{res.tiempo_origen_s:5.2f} {res.latitud:7.4f} {res.longitud:8.4f} "
        f"{res.profundidad_km:6.2f} {res.rms:5.3f} {res.elipse_x_km:5.2f} "
        f"{res.elipse_y_km:5.2f} {res.elipse_theta_deg:6.2f} {res.err_prof_km:5.2f}\n"
    )


def formatear_salida_rsa(res: ResultadoLocalizacion) -> str:
    """Genera el archivo .rsa combinando .L + bloque de cálculo de magnitud."""
    base = formatear_salida_l(res)
    bloque = ["CALCULO DE LA MAGNITUD", "", "sta           dist          Coda          Mag"]
    for sta, dist, coda, md in res.magnitudes_estacion:
        mag_txt = f"{md:4.1f}" if md is not None else "NMG"
        bloque.append(f"{sta:<14s}{dist:06.2f}        {coda:05.2f}         {mag_txt}")
    prom = f"{res.magnitud_promedio:4.1f}" if res.magnitud_promedio is not None else "NMG"
    bloque.extend(["", f"Promedio de las Magnitudes: {prom}", ""])
    return base + "\n".join(bloque)


if __name__ == "__main__":
    import argparse
    import convert1

    parser = argparse.ArgumentParser(description="Localizador hipocentral FASTHYPO en Python.")
    parser.add_argument("entrada", help="Archivo .P de FASTHYPO o archivo Phase* (PECQ).")
    parser.add_argument("--modelo", default="asw", help="Nombre del modelo en FHVELOC.DAT (defecto: asw).")
    parser.add_argument("--fhveloc", default=None, help="Ruta a FHVELOC.DAT.")
    parser.add_argument("--fhsta", default=None, help="Ruta a FHSTA.DAT.")
    parser.add_argument("--semilla", default="-2.5,-79.0,60.0,0.0", help="lat,lon,prof_km,t0_s iniciales.")
    parser.add_argument("--max-iter", type=int, default=100, help="Máximo de iteraciones.")
    parser.add_argument("--salida", default=None, help="Carpeta de salida para .P, .L, .S y .rsa.")
    args = parser.parse_args()

    ruta_in = Path(args.entrada).resolve()
    raiz_def = Path(__file__).resolve().parent.parent / "binarios_originales"
    ruta_vel = Path(args.fhveloc) if args.fhveloc else (raiz_def / "FHVELOC.DAT")
    ruta_sta = Path(args.fhsta) if args.fhsta else (raiz_def / "FHSTA.DAT")
    dir_out = Path(args.salida) if args.salida else ruta_in.parent
    dir_out.mkdir(parents=True, exist_ok=True)

    modelos = leer_modelos_velocidad(ruta_vel)
    estaciones = leer_estaciones(ruta_sta)
    mod_key = args.modelo.strip().lower()
    if mod_key not in modelos:
        raise ValueError(f"Modelo '{args.modelo}' no encontrado en {ruta_vel}. Disponibles: {list(modelos)}")

    lat_i, lon_i, prof_i, t0_i = (float(x) for x in args.semilla.split(","))

    if ruta_in.suffix.upper() == ".P":
        ev_p = leer_archivo_p(ruta_in)
        base_nom = ruta_in.stem
    else:
        ev_pecq, ruta_p = convert1.convertir_pecq_a_fasthypo(ruta_in, dir_out)[0]
        ev_p = leer_archivo_p(ruta_p)
        mapa_coda = {l.estacion.upper(): l.coda for l in ev_pecq.lecturas}
        for f in ev_p.fases:
            f.coda = mapa_coda.get(f.estacion.upper(), 0.0)
        base_nom = ev_pecq.nombre_base_evento

    res = localizar_hipocentro(
        evento=ev_p,
        estaciones_cat=estaciones,
        capas=modelos[mod_key],
        modelo_nombre=mod_key,
        lat_ini=lat_i,
        lon_ini=lon_i,
        prof_ini=prof_i,
        t0_ini=t0_i,
        max_iter=args.max_iter,
    )
    calcular_magnitud_coda(res)

    (dir_out / f"{base_nom}L").write_text(formatear_salida_l(res), encoding="ascii")
    (dir_out / f"{base_nom}S").write_text(formatear_salida_s(res), encoding="ascii")
    rsa_nom = f"{ev_p.mes:02d}{ev_p.dia:02d}{ev_p.hora:02d}{ev_p.minuto:02d}.rsa"
    (dir_out / rsa_nom).write_text(formatear_salida_rsa(res), encoding="ascii")
    print(formatear_salida_s(res).strip())
