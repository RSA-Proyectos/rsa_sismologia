import sys
import os
from pathlib import Path
def extraer_hasta_directorio(ruta_completa, nombre_directorio):
    partes = Path(ruta_completa).parts
    if nombre_directorio in partes:
        indice = partes.index(nombre_directorio)
        ruta_recortada = Path(*partes[:indice + 1])
        return str(ruta_recortada) + '/'
    else:
        return ''
ruta_librerias=os.path.dirname(__file__)
ruta_proyecto=extraer_hasta_directorio(ruta_librerias, 'procesamiento')
ruta_librerias = os.path.abspath(os.path.join(ruta_proyecto, 'src','librerias'))

# Insertar la ruta al inicio del sys.path
if ruta_librerias not in sys.path:
    sys.path.insert(0, ruta_librerias)



import geopandas as gpd
import os
import matplotlib.pyplot as plt
from shapely.geometry import Point, Polygon
from scipy.spatial import ConvexHull
import numpy as np
from metodos_rsa import lectura_archivo
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

import warnings
from shapely.errors import ShapelyDeprecationWarning

warnings.filterwarnings("ignore", category=ShapelyDeprecationWarning)

_CACHE_CAPAS_GIS = {}


def _obtener_capas_base_gis():
    """
    Carga y mantiene en caché los shapefiles base de Ecuador y provincias
    para que el redibujado interactivo en interfaces PyQt5 sea instantáneo.
    """
    if "ecuador" not in _CACHE_CAPAS_GIS:
        ruta_ec = os.path.join(ruta_proyecto, 'datos', 'GIS', 'ecuador.shp')
        _CACHE_CAPAS_GIS["ecuador"] = gpd.read_file(ruta_ec) if os.path.isfile(ruta_ec) else None
    if "provincias" not in _CACHE_CAPAS_GIS:
        ruta_prov = os.path.join(ruta_proyecto, 'datos', 'GIS', 'ECU provincias.shp')
        try:
            g_prov = gpd.read_file(ruta_prov) if os.path.isfile(ruta_prov) else None
            if g_prov is not None and g_prov.crs is not None and str(g_prov.crs) != "EPSG:4326":
                g_prov = g_prov.to_crs("EPSG:4326")
            _CACHE_CAPAS_GIS["provincias"] = g_prov
        except Exception:
            _CACHE_CAPAS_GIS["provincias"] = None
    return _CACHE_CAPAS_GIS["ecuador"], _CACHE_CAPAS_GIS["provincias"]


def _renderizar_brush_gaussiano_gis(ax, grupos, lon_min, lon_max, lat_min, lat_max):
    """
    Renderiza un campo continuo de densidad / energía sísmica mediante un pincel
    radial gaussiano multicapa (Gaussian Airbrush) sobre una rejilla 2D RGBA.
    Emula y suaviza de forma continua el efecto de nidos sísmicos del reporte PDF
    de 'Fuentes' (acumulación de opacidad por superposición sin bordes duros).
    """
    ancho_lon = max(1e-4, float(lon_max - lon_min))
    alto_lat = max(1e-4, float(lat_max - lat_min))
    span_max = max(ancho_lon, alto_lat)

    # Resolución de la rejilla proporcional al encuadre geográfico
    res_base = 420
    nx = max(180, int(round(res_base * (ancho_lon / span_max))))
    ny = max(180, int(round(res_base * (alto_lat / span_max))))

    # Acumuladores de densidad de opacidad por red (RSA en gama azul, Otras en gama violeta)
    campo_rsa = np.zeros((ny, nx), dtype=np.float32)
    campo_otras = np.zeros((ny, nx), dtype=np.float32)

    dx = ancho_lon / float(nx - 1)
    dy = alto_lat / float(ny - 1)

    tiene_rsa = False
    tiene_otras = False

    for (red_k, _prof_k), g in grupos.items():
        xs = g.get('x', [])
        ys = g.get('y', [])
        ms = g.get('m', [])
        if not xs:
            continue

        campo_destino = campo_rsa if red_k == 'RSA' else campo_otras
        if red_k == 'RSA':
            tiene_rsa = True
        else:
            tiene_otras = True

        for lon_ev, lat_ev, mag_ev in zip(xs, ys, ms):
            if not (lon_min <= lon_ev <= lon_max and lat_min <= lat_ev <= lat_max):
                continue

            # Escala radial continua inspirada en 2**(2*mag - 5) del PDF pero acotada
            mag_util = min(max(float(mag_ev), 2.0), 5.5)
            r_grados = span_max * 0.015 * (1.48 ** (mag_util - 2.5))
            r_grados = min(max(r_grados, span_max * 0.011), span_max * 0.14)

            # Índices de la sub-ventana local del pincel en la rejilla
            cx = (lon_ev - lon_min) / dx
            cy = (lat_ev - lat_min) / dy
            rx_pix = int(np.ceil(r_grados / dx)) + 2
            ry_pix = int(np.ceil(r_grados / dy)) + 2

            ix0 = max(0, int(np.floor(cx)) - rx_pix)
            ix1 = min(nx, int(np.floor(cx)) + rx_pix + 1)
            iy0 = max(0, int(np.floor(cy)) - ry_pix)
            iy1 = min(ny, int(np.floor(cy)) + ry_pix + 1)
            if ix0 >= ix1 or iy0 >= iy1:
                continue

            # Coordenadas normalizadas r/R_max dentro del parche local
            vx = (np.arange(ix0, ix1, dtype=np.float32) - cx) * dx
            vy = (np.arange(iy0, iy1, dtype=np.float32) - cy) * dy
            dist_norm = np.sqrt((vx[None, :] ** 2) + (vy[:, None] ** 2)) / float(r_grados)

            mascara = dist_norm < 1.0
            if not np.any(mascara):
                continue

            u = dist_norm[mascara]
            # Pincel radial multicapa (núcleo + halo medio + halo difuso) con caída suave a 0 en el borde
            ventana_suave = (1.0 - (u ** 2)) ** 2
            pincel = (
                0.22 * np.exp(-0.5 * ((u / 0.18) ** 2))
                + 0.12 * np.exp(-0.5 * ((u / 0.42) ** 2))
                + 0.06 * np.exp(-0.5 * ((u / 0.75) ** 2))
            ) * ventana_suave

            parche = campo_destino[iy0:iy1, ix0:ix1]
            parche[mascara] += pincel

    # Composición RGBA con ley de saturación exponencial (1 - exp(-S)) idéntica al alpha-blending del PDF
    rgba = np.zeros((ny, nx, 4), dtype=np.float32)

    if tiene_rsa:
        alfa_rsa = 1.0 - np.exp(-campo_rsa)
        intensidad_nucleo = np.clip(campo_rsa / 2.2, 0.0, 1.0)
        # Transición suave de azul brillante en el halo (#2563eb) a azul profundo en el núcleo del nido (#1e3a8a)
        rgba[..., 0] = (1.0 - intensidad_nucleo) * (37.0 / 255.0) + intensidad_nucleo * (20.0 / 255.0)
        rgba[..., 1] = (1.0 - intensidad_nucleo) * (99.0 / 255.0) + intensidad_nucleo * (45.0 / 255.0)
        rgba[..., 2] = (1.0 - intensidad_nucleo) * (235.0 / 255.0) + intensidad_nucleo * (138.0 / 255.0)
        rgba[..., 3] = np.clip(alfa_rsa * 0.94, 0.0, 0.95)
        ax.scatter(
            [], [], s=42, facecolors='#2563eb', edgecolors='none',
            alpha=0.75, label='Nidos / Densidad RSA (Brush)',
        )

    if tiene_otras:
        alfa_otr = np.clip(1.0 - np.exp(-campo_otras), 0.0, 0.92)
        mask_o = alfa_otr > 1e-3
        if np.any(mask_o):
            rgba[mask_o, 0] = 124.0 / 255.0
            rgba[mask_o, 1] = 58.0 / 255.0
            rgba[mask_o, 2] = 237.0 / 255.0
            rgba[mask_o, 3] = np.maximum(rgba[mask_o, 3], alfa_otr[mask_o])
        ax.scatter(
            [], [], s=42, facecolors='#7c3aed', edgecolors='none',
            alpha=0.75, label='Nidos / Densidad Otras (Brush)',
        )

    if tiene_rsa or tiene_otras:
        ax.imshow(
            rgba,
            extent=(lon_min, lon_max, lat_min, lat_max),
            origin='lower',
            interpolation='bicubic',
            zorder=4,
        )
        ax.axis([lon_min, lon_max, lat_min, lat_max])


def construir_poligono_lugar_geometrico(definicion_lugar):
    """
    Construye un objeto `shapely.geometry.Polygon` en EPSG:4326 (lon, lat) a partir
    de una definición de lugar geométrico para delimitación de enjambres sísmicos:
      - Si `definicion_lugar` ya es un `Polygon`, lo retorna directamente.
      - Si es un `dict` con `tipo`:
          * `'circulo'`: `{'tipo': 'circulo', 'lat': float, 'lon': float, 'radio_km': float}`
            Genera una aproximación geodésica elíptica de 72 vértices corrigiendo por `cos(lat)`.
          * `'rectangulo'`: `{'tipo': 'rectangulo', 'lat_min': float, 'lat_max': float, 'lon_min': float, 'lon_max': float}`
          * `'poligono'`: `{'tipo': 'poligono', 'vertices': [(lon1, lat1), (lon2, lat2), ...]}`
    Retorna `None` si la definición está vacía o es inválida.
    """
    if definicion_lugar is None:
        return None
    if isinstance(definicion_lugar, Polygon):
        return definicion_lugar if not definicion_lugar.is_empty else None
    if not isinstance(definicion_lugar, dict):
        return None

    tipo = str(definicion_lugar.get('tipo', '')).strip().lower()
    try:
        if tipo == 'circulo':
            lat_c = float(definicion_lugar['lat'])
            lon_c = float(definicion_lugar['lon'])
            radio_km = max(0.1, float(definicion_lugar['radio_km']))
            d_lat = radio_km / 110.574
            cos_lat = max(0.1, float(np.cos(np.radians(lat_c))))
            d_lon = radio_km / (111.320 * cos_lat)
            angulos = np.linspace(0.0, 2.0 * np.pi, 73)
            pts = [(lon_c + d_lon * float(np.cos(a)), lat_c + d_lat * float(np.sin(a))) for a in angulos]
            return Polygon(pts)
        elif tipo == 'rectangulo':
            lat_min = float(definicion_lugar['lat_min'])
            lat_max = float(definicion_lugar['lat_max'])
            lon_min = float(definicion_lugar['lon_min'])
            lon_max = float(definicion_lugar['lon_max'])
            if lat_min > lat_max:
                lat_min, lat_max = lat_max, lat_min
            if lon_min > lon_max:
                lon_min, lon_max = lon_max, lon_min
            if abs(lat_max - lat_min) < 1e-6 or abs(lon_max - lon_min) < 1e-6:
                return None
            return Polygon([
                (lon_min, lat_min),
                (lon_max, lat_min),
                (lon_max, lat_max),
                (lon_min, lat_max),
                (lon_min, lat_min),
            ])
        elif tipo == 'poligono':
            vertices = definicion_lugar.get('vertices') or []
            if len(vertices) < 3:
                return None
            pts = [(float(v[0]), float(v[1])) for v in vertices]
            if pts[0] != pts[-1]:
                pts.append(pts[0])
            poly = Polygon(pts)
            if not poly.is_valid:
                poly = poly.buffer(0)
            return poly if isinstance(poly, Polygon) and not poly.is_empty else None
    except Exception:
        return None
    return None


def graficar_periodo_gis(
    widget,
    catalogo,
    coordenadas_mapa=None,
    estilo_circulos=True,
    titulo_mapa="VISTA PREVIA GIS",
    parametros_est=None,
    mostrar_estaciones=True,
    poligono_enjambre=None,
    sismo_principal=None,
):
    """
    Renderiza en el lienzo embebido `widget` (widget_grafico_mpl) el catálogo
    sísmico filtrado de un período, respetando el recorte espacial de la región,
    la clasificación por profundidad (Superficial <40 km, Intermedio 40-70 km,
    Profundo >70 km), la fuente (RSA vs Otras redes) y el estilo de círculos
    seleccionado (rellenos, sin relleno o concéntricos).
    """
    widget.figure.clf()
    ax = widget.figure.add_subplot(111)

    mapa_ec, mapa_prov = _obtener_capas_base_gis()
    if mapa_ec is not None:
        mapa_ec.plot(ax=ax, color='#f1f5f9', edgecolor='#475569', linewidth=0.6, zorder=1)
    if mapa_prov is not None:
        try:
            mapa_prov.boundary.plot(ax=ax, color='#94a3b8', linewidth=0.35, linestyle='--', zorder=2)
        except Exception:
            pass

    # Encuadre geográfico según coordenadas de mapas.csv: [lat_min, lat_max, lon_min, lon_max, salto, estaciones]
    lon_min, lon_max, lat_min, lat_max = -81.5, -75.0, -5.0, 1.5
    estaciones_region = []
    if coordenadas_mapa and len(coordenadas_mapa) >= 4:
        try:
            lat_min = float(coordenadas_mapa[0])
            lat_max = float(coordenadas_mapa[1])
            lon_min = float(coordenadas_mapa[2])
            lon_max = float(coordenadas_mapa[3])
            if len(coordenadas_mapa) >= 6 and coordenadas_mapa[5]:
                estaciones_region = [int(x) for x in str(coordenadas_mapa[5]).split() if x.isdigit()]
        except (ValueError, TypeError):
            pass

    ax.axis([lon_min, lon_max, lat_min, lat_max])
    ax.set_facecolor('#e0f2fe')
    ax.set_title(titulo_mapa, pad=5, fontdict={'fontsize': 8.5, 'fontweight': 'bold', 'color': '#1e3a8a'})
    ax.set_xlabel('Longitud (°)', fontsize=7, labelpad=2)
    ax.set_ylabel('Latitud (°)', fontsize=7, labelpad=2)
    ax.tick_params(axis='both', which='major', labelsize=6.5, pad=1)
    ax.grid(True, linestyle=':', linewidth=0.4, color='#64748b', alpha=0.5, zorder=2)

    # Graficar estaciones sísmicas habilitadas dentro del encuadre
    if mostrar_estaciones and parametros_est:
        try:
            codigos = parametros_est.get('CODIGO', [])
            lats_est = parametros_est.get('LATITUD', [])
            lons_est = parametros_est.get('LONGITUD', [])
            hab_est = parametros_est.get('HAB_CANAL', [])
            indices_est = estaciones_region if estaciones_region else range(len(codigos))
            est_x, est_y = [], []
            for idx_e in indices_est:
                if idx_e >= len(codigos):
                    continue
                if not estaciones_region and idx_e < len(hab_est) and str(hab_est[idx_e]).strip() != '1':
                    continue
                lat_e = float(lats_est[idx_e]) / 10000.0 if abs(float(lats_est[idx_e])) > 90 else float(lats_est[idx_e])
                lon_e = float(lons_est[idx_e]) / 10000.0 if abs(float(lons_est[idx_e])) > 180 else float(lons_est[idx_e])
                if lon_min <= lon_e <= lon_max and lat_min <= lat_e <= lat_max:
                    est_x.append(lon_e)
                    est_y.append(lat_e)
                    ax.annotate(
                        str(codigos[idx_e]).strip(),
                        (lon_e, lat_e),
                        textcoords="offset points",
                        xytext=(0, 4),
                        ha='center',
                        fontsize=5.5,
                        fontweight='bold',
                        color='#0f172a',
                        zorder=6,
                    )
            if est_x:
                ax.scatter(
                    est_x, est_y,
                    marker='^', s=26, color='#1e40af', edgecolor='white',
                    linewidths=0.5, label='Estaciones RSA', zorder=5,
                )
        except Exception:
            pass

    stats = {'total': 0, 'rsa': 0, 'otras': 0, 'sup': 0, 'med': 0, 'pro': 0}
    grupos = {
        ('RSA', 'Sup (<40 km)'): {'x': [], 'y': [], 's': [], 'm': [], 'color': '#dc2626', 'edge': '#7f1d1d'},
        ('RSA', 'Med (40-70 km)'): {'x': [], 'y': [], 's': [], 'm': [], 'color': '#eab308', 'edge': '#713f12'},
        ('RSA', 'Prof (>70 km)'): {'x': [], 'y': [], 's': [], 'm': [], 'color': '#16a34a', 'edge': '#14532d'},
        ('Otras', 'Sup (<40 km)'): {'x': [], 'y': [], 's': [], 'm': [], 'color': '#f97316', 'edge': '#7c2d12'},
        ('Otras', 'Med (40-70 km)'): {'x': [], 'y': [], 's': [], 'm': [], 'color': '#0284c7', 'edge': '#0c4a6e'},
        ('Otras', 'Prof (>70 km)'): {'x': [], 'y': [], 's': [], 'm': [], 'color': '#7c3aed', 'edge': '#4c1d95'},
    }

    filas_datos = catalogo[1:] if (catalogo and len(catalogo) > 0 and str(catalogo[0][0]).strip() == 'Id') else (catalogo or [])
    for fila in filas_datos:
        if not fila or len(fila) < 19:
            continue
        id_ev = str(fila[0]).strip()
        if id_ev in ('Id', '00000000000000'):
            continue
        try:
            lat = float(fila[7])
            lon = float(fila[8])
            prof = abs(float(fila[9]))
            mag = max(1.0, float(fila[15]))
        except (ValueError, TypeError, IndexError):
            continue

        fuente_raw = str(fila[17]).strip()
        es_rsa = (fuente_raw == 'RSA' or id_ev.endswith('00'))
        clave_red = 'RSA' if es_rsa else 'Otras'

        if prof < 40.0:
            clave_prof = 'Sup (<40 km)'
            stats['sup'] += 1
        elif prof <= 70.0:
            clave_prof = 'Med (40-70 km)'
            stats['med'] += 1
        else:
            clave_prof = 'Prof (>70 km)'
            stats['pro'] += 1

        stats['total'] += 1
        if es_rsa:
            stats['rsa'] += 1
        else:
            stats['otras'] += 1

        # Si hay sismo principal definido, excluirlo de los grupos de réplicas para dibujarlo
        # encima con los 5 círculos concéntricos rojos del reporte de evento individual
        if isinstance(sismo_principal, dict):
            id_princ = str(sismo_principal.get('id', '')).strip()
            ev_princ = str(sismo_principal.get('evento', '')).strip()
            ruta_fila = str(fila[18]).strip() if len(fila) > 18 else ''
            if (id_princ and id_ev == id_princ) or (ev_princ and ruta_fila == ev_princ):
                continue

        tam = max(14.0, (mag ** 2.2) * 3.2)
        g = grupos[(clave_red, clave_prof)]
        g['x'].append(lon)
        g['y'].append(lat)
        g['s'].append(tam)
        g['m'].append(mag)

    # Renderizado según las 3 opciones de círculos: rellenos (True), sin relleno (False) o brush gaussiano (2)
    if estilo_circulos == 2:
        _renderizar_brush_gaussiano_gis(ax, grupos, lon_min, lon_max, lat_min, lat_max)
    elif estilo_circulos is False:
        for (red_k, prof_k), g in grupos.items():
            if not g['x']:
                continue
            ax.scatter(
                g['x'], g['y'], s=g['s'],
                facecolors='none', edgecolors=g['color'],
                linewidths=1.1, zorder=4, label=f"{red_k}: {prof_k} ({len(g['x'])})",
            )
    else:
        for (red_k, prof_k), g in grupos.items():
            if not g['x']:
                continue
            ax.scatter(
                g['x'], g['y'], s=g['s'],
                facecolors=g['color'], edgecolors=g['edge'],
                linewidths=0.5, alpha=0.72, zorder=4, label=f"{red_k}: {prof_k} ({len(g['x'])})",
            )

    # Si se especificó un Sismo Principal (modo Sismo Principal + Réplicas), dibujarlo en capa superior
    # usando los 5 círculos concéntricos rojos idénticos al reporte de evento individual
    if isinstance(sismo_principal, dict):
        try:
            lat_p = float(sismo_principal.get('lat', 0.0))
            lon_p = float(sismo_principal.get('lon', 0.0))
            mag_p = sismo_principal.get('mag', '')
            uni_p = str(sismo_principal.get('unidad_mag', 'Md') or 'Md').strip()
            anillos_rojos = [
                (480, 0.35),
                (290, 0.65),
                (145, 1.25),
                (52, 1.90),
                (6, 1.00),
            ]
            for idx_a, (area_pt, lw_pt) in enumerate(anillos_rojos):
                ax.scatter(
                    [lon_p],
                    [lat_p],
                    s=area_pt,
                    facecolors='none',
                    edgecolors='#dc2626',
                    linewidths=lw_pt,
                    zorder=8,
                    label=f"Sismo Principal ({mag_p} {uni_p})" if idx_a == 2 else None,
                )
            ax.annotate(
                f"{mag_p}{uni_p}",
                (lon_p, lat_p),
                textcoords="offset points",
                xytext=(0, -14),
                ha='center',
                fontsize=6.5,
                fontweight='bold',
                color='#991b1b',
                bbox=dict(boxstyle='round,pad=0.15', facecolor='white', alpha=0.82, edgecolor='#fca5a5'),
                zorder=9,
            )
        except Exception:
            pass

    # Dibujar el lugar geométrico del enjambre si está definido
    poly_geom = construir_poligono_lugar_geometrico(poligono_enjambre)
    if poly_geom is not None:
        try:
            xs_p, ys_p = poly_geom.exterior.xy
            ax.fill(xs_p, ys_p, facecolor='#2563eb', alpha=0.10, zorder=3)
            ax.plot(
                xs_p, ys_p,
                color='#1d4ed8', linestyle='--', linewidth=1.6,
                label='Lugar Geométrico (Enjambre)', zorder=6,
            )
            ax.axis([lon_min, lon_max, lat_min, lat_max])
        except Exception:
            pass

    handles, labels = ax.get_legend_handles_labels()
    if handles:
        by_label = dict(zip(labels, handles))
        ax.legend(
            by_label.values(), by_label.keys(),
            loc='upper left', fontsize=5.8, framealpha=0.85,
            borderpad=0.3, labelspacing=0.25, handletextpad=0.3,
        )

    linea_principal = ""
    if isinstance(sismo_principal, dict):
        mag_p = sismo_principal.get('mag', '')
        uni_p = str(sismo_principal.get('unidad_mag', 'Md') or 'Md').strip()
        prof_p = sismo_principal.get('prof', '')
        n_rep = max(0, stats['total'] - 1)
        linea_principal = f"Principal: {mag_p} {uni_p} ({prof_p} km) | Réplicas: {n_rep}\n"

    resumen_box = (
        f"{linea_principal}"
        f"Total graficados: {stats['total']}\n"
        f"RSA: {stats['rsa']} | Otras redes: {stats['otras']}\n"
        f"Sup: {stats['sup']} | Med: {stats['med']} | Prof: {stats['pro']}"
    )
    ax.text(
        0.98, 0.02, resumen_box,
        transform=ax.transAxes, fontsize=6.2, color='#0f172a',
        verticalalignment='bottom', horizontalalignment='right',
        multialignment='left', linespacing=1.2,
        bbox=dict(boxstyle='round,pad=0.28', facecolor='white', alpha=0.86, edgecolor='#94a3b8'),
        zorder=7,
    )

    widget.figure.subplots_adjust(left=0.10, right=0.98, top=0.92, bottom=0.09)
    widget.canvas.draw()
    return stats


def catalogo_gis(catalogo):
    """
    Genera un mapa con información de un catálogo sísmico.
    
    Argumentos:
        catalogo (list): Información en el formato de catálogo sísmico.
        indice (int): Índice del evento a graficar.

    Returns:
        None
    """

    file_path=os.path.join(ruta_proyecto,'datos','GIS','ecuador.shp')
    mapa_ec = gpd.read_file(file_path)
    fig, ax = plt.subplots(1, 1, figsize=(8, 8))
    mapa_ec.plot(ax=ax, color='lightgrey')  # Cargar el mapa de Ecuador como fondo
    ax.axis([-81.5, -75, -5, 1.5])
    ax.set_title('SISMO', pad=6, fontdict={'fontsize': 10, 'fontweight': 'bold', 'color': '#4873ab'})
    ax.set_xlabel('Longitud', fontsize=8, labelpad=2)
    ax.set_ylabel('Latitud', fontsize=8, labelpad=2)
    ax.tick_params(axis='both', which='major', labelsize=7, pad=2)
    colores = {'RSA': 'yellow', 'IGEPN': 'blue', 'USGS': 'black', 'Otras redes': 'orange'}
    bordes = {'RSA': 'red', 'IGEPN': 'green', 'USGS': 'white', 'Otras redes': 'black'}
    texto_datos = ""
    for evento in catalogo:
        if not evento or len(evento) < 20:
            continue
        latitud = float(evento[7])
        longitud = float(evento[8])
        profundidad = evento[9]
        magnitud = evento[15]
        epicentro = evento[19]
        fuente = evento[17]
        if not texto_datos or fuente == 'RSA':
            texto_datos = (
                f"Latitud: {latitud}\n"
                f"Longitud: {longitud}\n"
                f"Profundidad: {profundidad}\n"
                f"Magnitud: {magnitud}\n"
                f"Epicentro: {epicentro}"
            )
        ax.scatter(
            longitud,
            latitud,
            color=colores.get(fuente, 'orange'),
            linewidths=1.5,
            marker="o",
            edgecolor=bordes.get(fuente, 'black'),
            s=60,
            label=fuente,
        )
    if texto_datos:
        ax.text(
            0.98, 0.02, texto_datos,
            transform=ax.transAxes,
            fontsize=7,
            color='black',
            verticalalignment='bottom',
            horizontalalignment='right',
            multialignment='left',
            linespacing=1.2,
            bbox=dict(boxstyle='round,pad=0.25', facecolor='white', alpha=0.8, edgecolor='none')
        )
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(), fontsize=7)
    fig.subplots_adjust(left=0.10, right=0.98, top=0.93, bottom=0.09)
    plt.show()

def catalogo_gis_(catalogo,indice):
    #catalogo, es la información en el formato de catálogo sismico que se va a graficar en el mapa
    #          con la posibilidad de que haya información de otras redes.
    contador=0
    ext=len(catalogo)
    if catalogo[0]!=[]:
        longitud=catalogo[0][8]
        latitud=catalogo[0][7]
        profundidad=catalogo[0][9]
        magnitud=catalogo[0][15]
        epicentro=catalogo[0][19]
    else:
        longitud=catalogo[1][8]
        latitud=catalogo[1][7]
        profundidad=catalogo[1][9]
        magnitud=catalogo[1][15]
        epicentro=catalogo[1][19]        
    file_path=os.path.join(ruta_proyecto,'datos','GIS','ecuador.shp')
    mapa_ec = gpd.read_file(file_path)
    # Control del tamaño de la figura del mapa
    fig, ax = plt.subplots(1, 1, figsize=(8, 8))
    # Control del encuadre (área geográfica) del mapa
    ax.axis([-81.5, -75, -5, 1.5])
    # Control del título y los ejes
    ax.set_title('SISMO', 
             pad = 6, 
             fontdict={'fontsize': 10, 'fontweight': 'bold', 'color': '#4873ab'})
    ax.set_xlabel('Longitud', fontsize=8, labelpad=2)
    ax.set_ylabel('Latitud', fontsize=8, labelpad=2)
    ax.tick_params(axis='both', which='major', labelsize=7, pad=2)
    texto_datos = (
        f"Latitud: {latitud}\n"
        f"Longitud: {longitud}\n"
        f"Profundidad: {profundidad}\n"
        f"Magnitud: {magnitud}\n"
        f"Epicentro {epicentro}"
    )
    ax.text(
        0.98, 0.02, texto_datos,
        transform=ax.transAxes,
        fontsize=7,
        color='black',
        verticalalignment='bottom',
        horizontalalignment='right',
        multialignment='left',
        linespacing=1.2,
        bbox=dict(boxstyle='round,pad=0.25', facecolor='white', alpha=0.8, edgecolor='none')
    )
    ax.scatter(longitud,latitud,color='yellow',linewidths = 1.5,
            marker ="o",
            edgecolor ="red",
            s = 60)
    if ext>1:
        if catalogo[1][2]=='USGS':
            color_='black'
            ax.text(-80.68,-4.30,"USGS ",fontsize=6,color='black')
            ax.scatter(-80.75,-4.28,color="black",linewidths = 2, marker ="o",edgecolor ="black",s = 40)
        else:
            color_='red'
            ax.text(-80.68,-4.20,"IGEPN ",fontsize=6,color='black')
            ax.scatter(-80.75,-4.18,color="red",linewidths = 2,marker ="o", edgecolor ="red", s = 40)
        ax.scatter(catalogo[1][6],catalogo[1][5],color=color_,linewidths = 2,
            marker ="o",
            edgecolor = color_,
            s = 30)
        if ext>2:
            if catalogo[2][2]=='USGS':
                color_='black'
                ax.text(-80.68,-4.30,"USGS ",fontsize=6,color='black')
                ax.scatter(-80.75,-4.28,color="black",linewidths = 2, marker ="o",edgecolor ="black",s = 40)
            else:
                color_='red'
                ax.text(-80.68,-4.20,"IGEPN ",fontsize=6,color='black')
                ax.scatter(-80.75,-4.18,color="red",linewidths = 2,marker ="o", edgecolor ="red", s = 40)
            ax.scatter(catalogo[2][6],catalogo[2][5],color=color_,linewidths = 2,
                marker ="o",
                edgecolor = color_,
                s = 30)
    mapa_ec.plot(ax=ax,alpha=0.3,color="white",edgecolor="black",linewidth=0.4)
    fig.subplots_adjust(left=0.10, right=0.98, top=0.93, bottom=0.09)
    return 

def proceso_gis(widget, procesamiento, archivo_estaciones):
    widget.figure.clf()
    ax = widget.figure.add_subplot(111)
    gdf_1,estaciones = cobertura_red(archivo_estaciones, 50)
    gdf_2,estaciones = cobertura_red(archivo_estaciones, 150)
    ext = len(procesamiento)
    file_path=os.path.join(ruta_proyecto,'datos','GIS','ecuador.shp')
    mapa_ec = gpd.read_file(file_path)
    ax.axis([-81.5, -75, -5, 1.5])
    ax.set_title('SISMO', pad=4, fontdict={'fontsize': 9, 'fontweight': 'bold', 'color': '#4873ab'})
    longitud = 0
    latitud = 0
    profundidad = 0
    magnitud = 0
    rms = 'Intento fallido'
    for i in range(2, ext):
        if procesamiento[i][2] == "Fallido":
            continue
        longitud = float(procesamiento[i][5])
        latitud = float(procesamiento[i][4])
        profundidad = float(procesamiento[i][2])
        magnitud = float(procesamiento[i][3])
        rms = procesamiento[i][6]
        if i == ext - 1:
            ax.scatter(longitud, latitud, color='yellow', linewidths=1.2, marker="o", edgecolor="red", s=55, zorder=5)
        else:
            ax.scatter(longitud, latitud, color='black', s=22, zorder=4)
    
    point = Point(longitud, latitud)
    in_gdf_1 = gdf_1.contains(point).values[0]
    in_gdf_2 = gdf_2.contains(point).values[0]
    
    ax.set_xlabel('Longitud', fontsize=7, labelpad=2)
    ax.set_ylabel('Latitud', fontsize=7, labelpad=2)
    ax.tick_params(axis='both', which='major', labelsize=6, pad=1)

    texto_datos = (
        f"Latitud: {latitud}\n"
        f"Longitud: {longitud}\n"
        f"Profundidad: {profundidad}\n"
        f"Magnitud: {magnitud}\n"
        f"rms {rms}"
    )
    ax.text(
        0.98, 0.02, texto_datos,
        transform=ax.transAxes,
        fontsize=6.5,
        color='black',
        verticalalignment='bottom',
        horizontalalignment='right',
        multialignment='left',
        linespacing=1.2,
        bbox=dict(boxstyle='round,pad=0.25', facecolor='white', alpha=0.8, edgecolor='none'),
        zorder=6
    )
    
    gdf_1.boundary.plot(ax=ax, color='blue', linewidth=0.8)
    gdf_2.boundary.plot(ax=ax, color='green', linewidth=0.8)
    
    mapa_ec.plot(ax=ax, alpha=0.3, color="white", edgecolor="black", linewidth=0.4)
    widget.figure.subplots_adjust(left=0.10, right=0.98, top=0.92, bottom=0.09)
    widget.canvas.draw()
    
    return (in_gdf_1, in_gdf_2)


class widget_grafico_mpl(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def plot(self, procesamiento, archivo_estaciones):
        return proceso_gis(self, procesamiento, archivo_estaciones)


def graficar_catalogo_gis(catalogo):

  """
  Grafica un catálogo sísmico en un mapa GIS de Ecuador.

  Parámetros:
    catalogo: lista de listas con información de los eventos sísmicos.

  Retorno:
    None. Se genera un mapa GIS con los puntos de los eventos sísmicos.
  """

  # Carga del shapefile de Ecuador
  file_path=os.path.join(ruta_proyecto,'datos','GIS','ecuador.shp')
  mapa_ec = gpd.read_file(file_path)

  # Control del tamaño de la figura del mapa
  fig, ax = plt.subplots(1, 1, figsize=(8, 8))

  # Control del encuadre (área geográfica) del mapa
  ax.axis([-81.5, -75, -5, 1.5])

  # Control del título y los ejes
  ax.set_title('SISMO',
                pad=6,
                fontdict={'fontsize': 10, 'fontweight': 'bold', 'color': '#4873ab'})
  ax.set_xlabel('Longitud', fontsize=8, labelpad=2)
  ax.set_ylabel('Latitud', fontsize=8, labelpad=2)
  ax.tick_params(axis='both', which='major', labelsize=7, pad=2)

  # Extracción de la información de los eventos
  eventos = []
  for evento in catalogo[1:]:
    profundidad = float(evento[2])
    magnitud = float(evento[3])
    latitud = float(evento[4])
    longitud = float(evento[5])
    rms = float(evento[6])

    # Creación del diccionario con la información del evento
    evento_dict = {

        "profundidad": profundidad,
        "magnitud": magnitud,
        "latitud": latitud,
        "longitud": longitud,
        "rms": rms,
    }
    eventos.append(evento_dict)

  # Graficar los puntos de los eventos
  for evento in eventos:
    magnitud = evento["magnitud"]
    if magnitud < 4:
        color = "green"
    elif magnitud < 6:
        color = "yellow"
    else:
        color = "red"
    ax.scatter(evento["longitud"], evento["latitud"], color=color, s=magnitud*10)

  # Agregar leyenda
  leyenda_colores = {
    "green": "Magnitud < 4",
    "yellow": "4 <= Magnitud < 6",
    "red": "Magnitud >= 6",
  }
  for color, label in leyenda_colores.items():
    ax.plot([], [], color=color, marker="o", label=label)
  ax.legend(loc="best")

  # Mostrar el mapa
  #plt.show()


def cobertura_red(archivo,distancia):
    #archivo   -----  Archivo con las estaciones del día.
    #distancia  ----  distancoa en kilometros
    
    bandera=0
    if not os.path.exists(archivo):
        archivo=os.path.join(ruta_proyecto,'datos','estaciones.csv')
        bandera=1
        
    estaciones_completa=lectura_archivo(archivo)
# Lista de estaciones
    estaciones=[]
    for estacion in estaciones_completa:
        if estacion[1]=='1':
            longitud=int(estacion[3])/10000.
            latitud=int(estacion[4])/10000.
            xxx=(estacion[2],longitud, latitud)
            estaciones.append(xxx)
    # Extraer las coordenadas
    coords = np.array([[estacion[1], estacion[2]] for estacion in estaciones])
    # Calcular el polígono convexo usando ConvexHull
    hull = ConvexHull(coords)
    hull_points = coords[hull.vertices]
    # Crear el polígono convexo
    polygon = Polygon(hull_points)
    offset_polygon = polygon.buffer(distancia/110.)
    # Crear un GeoDataFrame con el polígono
    gdf = gpd.GeoDataFrame(index=[0], crs="EPSG:4326", geometry=[offset_polygon])
    return gdf,coords

