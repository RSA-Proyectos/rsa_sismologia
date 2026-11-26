"""
marcar_tiempo  ok
obtener_marcas_tiempo ok
encontrar_cadena ok
dibujo_sismos_  ok
caja_simbologia ok
formato ok
mapa ok
mapa_configuracion ok
escalado ok
grafico_cobertura ok
imprimir_acelerograma ok
imprimir_seniales ok
estadistica_ ok


from rsa_graficos_pdf import marcar_tiempo,obtener_marcas_tiempo,dibujo_sismos_,caja_simbologia,formato,mapa ,mapa_configuracion,escalado ,grafico_cobertura,imprimir_acelerograma,imprimir_seniales,estadistica_

"""
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
ruta_datos = os.path.abspath(os.path.join(ruta_proyecto, 'datos'))

# Insertar la ruta al inicio del sys.path
if ruta_librerias not in sys.path:
    sys.path.insert(0, ruta_librerias)
if ruta_datos not in sys.path:
    sys.path.insert(0, ruta_datos)



import math 



from rsa_dominio import correccion

#from rsa_graficos_pdf import *
#from rsa_reportes_pdf import *
#from rsa_catalogo_pdf import *
from PyQt5.QtCore import QDate
from rsa_procesamiento import espectro_respuesta
from metodos_gestion import parametros_estaciones,obtener_directorios
from metodos_gis_rsa import cobertura_red
import scipy.fft
import matplotlib.pyplot as plt
from datetime import timedelta
from reportlab.lib import colors
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.textlabels import Label
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4,landscape
from reportlab.graphics.shapes import Drawing, Rect,Circle,String,Line
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.rl_config import defaultPageSize
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.lib.colors import white
from reportlab.graphics.charts.barcharts import VerticalBarChart
import numpy as np
import csv

#from rsa_reportes_pdf import impresion_reporte_sismo

IDX_INDICE,IDX_ANIO,IDX_MES,IDX_DIA,IDX_HORA,IDX_MINUTO,IDX_SEGUNDO,\
IDX_LATITUD,IDX_LONGITUD,IDX_PROFUNDIDAD,IDX_RMS,IDX_E_X,IDX_E_Y,IDX_E_0,\
IDX_E_Z,IDX_MAGNITUD,IDX_UNIDAD_MAG,\
IDX_FUENTE,IDX_EVENTO,IDX_LUGAR = 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19

NUMERO_ESTACIONES=101

IDX_LONGITUD_MINIMA,IDX_LATITUD_MINIMA,IDX_LONGITUD_MAXIMA,IDX_LATITUD_MAXIMA=0,1,2,3
IDX_POSICION_X,IDX_POSICION_Y,IDX_ANCHO,IDX_ALTO,=0,1,2,3

# =========================
#  MODOS DE REPORTE (1–7)
# =========================
MODO_PERIODO_FRANJAS          = 1   # M1 – Período por franjas (00–12, 12–18, 18–24) – Control interno
MODO_DIARIO_REVISION          = 2   # M2 – Diario de revisión (día/ad-hoc) con detalle y dummies locales
MODO_OFICIAL_DETALLADO        = 3   # M3 – Oficial detallado (solo catálogo) + página/resumen de responsables
MODO_OFICIAL_RESUMEN          = 4   # M4 – Oficial resumen (solo catálogo, sin detalle)
MODO_FACULTAD_RESUMEN         = 5   # M5 – Facultad/resumen (redes sociales), sin detalle
MODO_INSTITUCIONAL_DETALLADO  = 6   # M6 – Institucional detallado (solo catálogo), sin extras ni responsables
MODO_INSTITUCIONAL_RESUMEN    = 7   # M7 – Institucional, sin detalle

def marcar_tiempo(lienzo,x_,y_,tiempo_inicio,ancho,duracion,catNames):
    membrete=0
    intervalo=ancho/duracion   #Escala en el gráfico.
    pos_y=y_+50
    for k in range(0, int(duracion)):
        pos_x=x_+k*intervalo
        if k==0:
            fuente=6
            offset=8
            linea=10
            membrete=1
            texto=catNames[0]
            lienzo.line(pos_x,pos_y-linea,pos_x,pos_y)
            lienzo.setFont('Helvetica', fuente)
            lienzo.drawString(pos_x-10,y_+42-offset,texto)
        else:
            tiempo_=tiempo_inicio.second+k
            if tiempo_%10==0:  #Con esto solo se grafican las divisiones enteras o las decenas en este caso.
                texto=catNames[membrete]
                if len(texto)==2:
                    fuente=4
                    offset=2
                    linea=5
                else:
                    fuente=4
                    offset=6
                    linea=10
                pos_x=x_+k*intervalo#pos_x=x_+k*intervalo-10
                lienzo.line(pos_x,pos_y-linea,pos_x,pos_y)
                lienzo.setFont('Helvetica', fuente)
                lienzo.drawString(pos_x-offset,y_+42-offset,texto)
                membrete=membrete+1
    return lienzo

def obtener_marcas_tiempo(tr):
    #tr  es el stream que contiene el achivo mseed de la señal.
    #### Marcas de tiempo    Las unidades de tiempo son segundos
    duracion=tr[0].stats.endtime.timestamp-tr[0].stats.starttime.timestamp
    tiempo_inicio=tr[0].stats.starttime
    tiempo_inicial=tr[0].stats.starttime.time.second
    # Cálculo de las marcas de tiempo
    catNames=[]#Varible qu contiene las marcas de tiempo.
    for k in range(0, int(duracion)):
        if k==0:
            catNames.append(str(tiempo_inicio.time))
            #El primer valor es el tiempo inicial HH:MM:SS
        else:
            tiempo_real=tiempo_inicio+k#Formato HH:MM:SS
            tiempo_=tiempo_inicio.second+k #Formato en segundos.
            if tiempo_%60==0:
                formato_hora_minuto = tiempo_real.strftime("%H:%M")
                catNames.append(formato_hora_minuto)
                #El formato es de la forma HH:MM, cada paso por el segundo 60.
            else:
                if  tiempo_%10==0:
                    segundos = tiempo_real.second
                    segundos_2_digitos = "{:02d}".format(segundos)
                    catNames.append(segundos_2_digitos)
    return tiempo_inicio,tiempo_inicial,duracion, catNames



def encontrar_cadena(lista, cadena):
    for i, elemento in enumerate(lista):
        if elemento == cadena:
            return i  # Devuelve la ubicación de la cadena en la lista
    return -1  # La cadena no se encuentra en la lista

def dibujo_sismos_(lienzo,vector,coordenadas,tamanio,mapa_,bandera_dia,bandera_relleno,banderas=None,sismo_principal=None):
    """
    #########################################################################################
    # Método para proyectar y dibujar los epicentros de la RSA sobre el mapa de portada.
    # ---------------------------------------------------------------------------------------
    # lienzo          : Lienzo ReportLab donde se dibuja el mapa.
    # vector          : Lista de tuplas [lat, lon, prof, mag, red, id_sis] de los sismos.
    # coordenadas     : Límites geográficos del mapa (lon_min, lat_min, lon_max, lat_max).
    # tamanio         : Geometría física del mapa en puntos (xpos, ypos, ancho, alto).
    # mapa_           : Índice del mapa en datos/mapas/mapas.csv (0=Region, 1=Ecuador, 2=Facultad, etc.).
    # bandera_dia     : True (1) si es reporte de período; False (0) si es reporte diario.
    # bandera_relleno : True para círculos sólidos con opacidad; False para solo contorno.
    # banderas        : Diccionario maestro de banderas (PERFILES_MAPA_ZONA en rsa_pdf_catalogo.py):
    #                     - 'estilo_color_sismos'         : 'por_profundidad' (<40 rojo, 40-70 naranja, >70 azul),
    #                                                       'azul_unico' (Facultad) o 'halos_difuminados' (Fuentes).
    #                     - 'escala_circulos'             : 'mitad' (r = mag - 2.5 en Region) o 'normal' (r = 2*mag - 5).
    #                     - 'etiquetar_magnitud_hora_mapa': True en reporte diario (M2) para rotular Mag/HH:MM.
    # sismo_principal : Diccionario opcional {'id', 'evento', 'lat', 'lon', 'prof', 'mag', 'unidad_mag'}
    #                   para secuencias de Sismo Principal + Réplicas. Si se provee, las réplicas se
    #                   dibujan con la simbología convencional y el sismo principal se dibuja encima
    #                   con los 5 círculos concéntricos rojos del reporte de evento individual.
    #########################################################################################
    """
    estilo_color = (
        banderas.get('estilo_color_sismos')
        if isinstance(banderas, dict) and 'estilo_color_sismos' in banderas
        else ('azul_unico' if mapa_ == 2 else ('halos_difuminados' if mapa_ == 3 else 'por_profundidad'))
    )
    escala_circulos = (
        banderas.get('escala_circulos')
        if isinstance(banderas, dict) and 'escala_circulos' in banderas
        else ('mitad' if mapa_ == 0 else 'normal')
    )
    etiquetar_evento = (
        banderas.get('etiquetar_magnitud_hora_mapa')
        if isinstance(banderas, dict) and 'etiquetar_magnitud_hora_mapa' in banderas
        else (not bandera_dia)
    )

    longitud_min=coordenadas[0]
    latitud_min=coordenadas[1]
    longitud_max=coordenadas[2]
    latitud_max=coordenadas[3]
    xpos=tamanio[0]
    ypos=tamanio[1]
    ancho=tamanio[2]
    alto=tamanio[3]
    dibujo_sismos = Drawing(ancho, alto)
    aux=len(vector)
    ev_principal_ruta = (
        str(sismo_principal.get('evento', '')).strip()
        if isinstance(sismo_principal, dict)
        else ''
    )
    for i in range(0,aux):
        longitud=vector[i][1]
        latitud=vector[i][0]
        profundidad=abs(vector[i][2])
        magnitud=vector[i][3]
        ruta_actual = str(vector[i][5]).strip() if len(vector[i]) > 5 else ''

        # Si este evento es el Sismo Principal, se reserva para dibujarlo al final (en la capa superior)
        # con los 5 círculos concéntricos rojos del reporte individual
        if isinstance(sismo_principal, dict):
            if ev_principal_ruta and ruta_actual == ev_principal_ruta:
                continue
            if (
                abs(latitud - float(sismo_principal.get('lat', 999))) < 1e-4
                and abs(longitud - float(sismo_principal.get('lon', 999))) < 1e-4
                and abs(magnitud - float(sismo_principal.get('mag', -999))) < 1e-3
            ):
                continue

        filtro=(longitud<=longitud_max)and(longitud>=longitud_min)and(latitud<=latitud_max)and(latitud>=latitud_min)#Variable que indica si la localizacion está dentro del nmapa de despliegue
        if estilo_color == 'azul_unico':#Reporte de Facultad.
            color=colors.blue
        else: #Todos los otros reportes
            if profundidad>=40:
                if profundidad<=70:
                    color=colors.orange
                else:
                    color=colors.blue
            else:
                color=colors.red
        if filtro: #Si no está dentro del mapa no hace nada.
            if not(vector[i][4]):# Solo ubica los eventos de la RSA(valor 0), ignora los de otras redes(valor 1)
                x_cen=xpos+(longitud-longitud_min)*ancho/(longitud_max-longitud_min)#x_cen=(longitud+80)*200+xpos
                y_cen=ypos+(latitud-latitud_min)*alto/(latitud_max-latitud_min)#y_cen=(latitud+4)*200+ypos
                if escala_circulos == 'mitad':
                    r=1*(magnitud)-2.5
                else:
                    r=2*(magnitud)-5
                char_=str(magnitud)+'/'+vector[i][5][9:11]+':'+vector[i][5][11:13]
                if estilo_color == 'halos_difuminados':# Es el mapa para fuentes.
                    if color!=colors.blue:
                        for k in range(1,10):
                            radio=0.05*k*(2**r)
                            opacidad=(0.1/k)#*(2**r)
                            dibujo_sismos.add(Circle(x_cen, y_cen,radio, fillColor='blue',strokeWidth = 0,fillOpacity=opacidad,strokeOpacity=opacidad))
                            #dibujo_sismos.add(Circle(x_cen, y_cen, radio, strokeWidth=0, fillColor=color, fillOpacity=0.7))
                else:
                    if bandera_relleno:
                        dibujo_sismos.add(Circle(x_cen, y_cen, r, strokeWidth=0, fillColor=color, fillOpacity=0.7))
                    else:
                        dibujo_sismos.add(Circle(x_cen, y_cen, r, strokeColor=color,strokeWidth = 0.2,fillColor=color,fillOpacity=0.))
                    

                if etiquetar_evento:
                    dibujo_sismos.add(String(x_cen+1,y_cen+1, char_, fontSize=4, fillColor=colors.red))
    dibujo_sismos.drawOn(lienzo, 0, 0)#dibujo_sismos.drawOn(c, xpos, ypos)

    # Si se especificó un Sismo Principal (modo Sismo Principal + Réplicas), dibujarlo encima de
    # todas las réplicas exactamente igual que en el reporte de evento solo (5 círculos concéntricos en rojo)
    if isinstance(sismo_principal, dict):
        try:
            lat_p = float(sismo_principal.get('lat', 0.0))
            lon_p = float(sismo_principal.get('lon', 0.0))
            mag_p = sismo_principal.get('mag', '')
            uni_p = str(sismo_principal.get('unidad_mag', 'Md') or 'Md').strip()
            if (longitud_min <= lon_p <= longitud_max) and (latitud_min <= lat_p <= latitud_max):
                coor_x = xpos + (lon_p - longitud_min) * ancho / (longitud_max - longitud_min)
                coor_y = ypos + (lat_p - latitud_min) * alto / (latitud_max - latitud_min)
                dibujo_sismo_principal = Drawing(10, 10)
                for valores in [(11, 0.005), (8.5, 0.2), (6, 0.8), (3.5, 1.4), (1, 0.5)]:
                    dibujo_sismo_principal.add(
                        Circle(
                            0,
                            0,
                            valores[0],
                            strokeColor=colors.red,
                            strokeWidth=valores[1],
                            fillOpacity=0,
                        )
                    )
                dibujo_sismo_principal.drawOn(lienzo, coor_x, coor_y)
                lienzo.saveState()
                lienzo.setFillColor(colors.black)
                lienzo.setFont('Helvetica-Bold', 8)
                lienzo.drawString(coor_x - 15, coor_y - 22, f"{mag_p}{uni_p}")
                lienzo.restoreState()
        except Exception as err_sp:
            print(f"Aviso dibujando sismo principal en PDF: {err_sp}")

    return lienzo


def dibujar_lugar_geometrico_pdf(lienzo, poligono_enjambre, coordenadas, tamanio):
    """
    Dibuja el contorno del lugar geométrico (círculo, rectángulo o polígono de enjambre)
    sobre el mapa de portada del reporte PDF en ReportLab, recortado a los límites
    geográficos `coordenadas` = (lon_min, lat_min, lon_max, lat_max).
    """
    if poligono_enjambre is None:
        return lienzo
    try:
        from shapely.geometry import Polygon, box
        from metodos_gis_rsa import construir_poligono_lugar_geometrico
        poly = construir_poligono_lugar_geometrico(poligono_enjambre)
        if poly is None or poly.is_empty:
            return lienzo

        lon_min, lat_min, lon_max, lat_max = (
            float(coordenadas[0]),
            float(coordenadas[1]),
            float(coordenadas[2]),
            float(coordenadas[3]),
        )
        xpos, ypos, ancho, alto = (
            float(tamanio[0]),
            float(tamanio[1]),
            float(tamanio[2]),
            float(tamanio[3]),
        )

        recorte_mapa = box(lon_min, lat_min, lon_max, lat_max)
        poly_recortado = poly.intersection(recorte_mapa)
        if poly_recortado.is_empty:
            return lienzo

        geoms = [poly_recortado] if isinstance(poly_recortado, Polygon) else getattr(poly_recortado, 'geoms', [])
        lienzo.saveState()
        lienzo.setStrokeColor(colors.HexColor('#1d4ed8'))
        lienzo.setLineWidth(1.3)
        lienzo.setDash(4, 2)
        for g in geoms:
            if not isinstance(g, Polygon) or g.is_empty:
                continue
            coords = list(g.exterior.coords)
            if len(coords) < 2:
                continue
            path = lienzo.beginPath()
            for idx_pt, (lon_pt, lat_pt) in enumerate(coords):
                x_pt = xpos + (lon_pt - lon_min) * ancho / (lon_max - lon_min)
                y_pt = ypos + (lat_pt - lat_min) * alto / (lat_max - lat_min)
                if idx_pt == 0:
                    path.moveTo(x_pt, y_pt)
                else:
                    path.lineTo(x_pt, y_pt)
            path.close()
            lienzo.drawPath(path, stroke=1, fill=0)
        lienzo.restoreState()
    except Exception as e:
        print(f"Aviso dibujando lugar geométrico en PDF: {e}")
    return lienzo


def caja_simbologia(lienzo,resumen,vector,ubicacion_caja,mapa_,bandera_dia,bandera_relleno,banderas=None):
    #########################################################################################
    # Método que dibuja los recuadros de simbología (escalas de magnitud y profundidad)
    # y el resumen de promedios diarios en la portada del reporte.
    # ---------------------------------------------------------------------------------------
    # lienzo          : Lienzo ReportLab activo.
    # resumen         : Matriz global (con fila Total y columnas SISMO/FF) o vector filtrado por día.
    # vector          : Vector de eventos graficados en el mapa.
    # ubicacion_caja  : Tupla (pos_x, pos_y) de la esquina inferior izquierda de la caja.
    # mapa_           : Índice del mapa en datos/mapas/mapas.csv.
    # bandera_dia     : 1 si es reporte de período, 0 si es reporte diario.
    # bandera_relleno : True para círculos rellenos, False para círculos sin relleno.
    # banderas        : Diccionario maestro de banderas (PERFILES_MAPA_ZONA en rsa_pdf_catalogo.py):
    #                     - 'caja_simbologia_compacta': True en Facultad (240+200 pt, solo azul);
    #                                                   False en general (295+215 pt, 3 profundidades).
    #                     - 'escala_circulos'         : 'mitad' o 'normal'.
    #                     - 'tipo_resumen_estadistico': 'matriz_global' (calcula localizados + sin localizar)
    #                                                   o 'vector_filtrado' (suma directa de sismos en la zona).
    #########################################################################################
    es_caja_compacta = (
        banderas.get('caja_simbologia_compacta')
        if isinstance(banderas, dict) and 'caja_simbologia_compacta' in banderas
        else (mapa_ == 2)
    )
    escala_circulos = (
        banderas.get('escala_circulos')
        if isinstance(banderas, dict) and 'escala_circulos' in banderas
        else ('mitad' if mapa_ == 0 else 'normal')
    )
    es_resumen_matriz = (
        (banderas.get('tipo_resumen_estadistico') == 'matriz_global')
        if isinstance(banderas, dict) and 'tipo_resumen_estadistico' in banderas
        else (mapa_ < 4 or bandera_dia == 0)
    )

    pos_x=ubicacion_caja[0]#pos_x=55
    pos_y=ubicacion_caja[1]#pos_y=234

    lienzo.setFont('Helvetica', 11)
    lienzo.drawString(pos_x+105,pos_y+50,"SIMBOLOGIA:")
    lienzo.setFont('Helvetica', 9)
    lienzo.drawString(pos_x+31,pos_y+48,"Magnitud(Md):")
    lienzo.drawString(pos_x+5,pos_y+38,"3.0 - 3.5 - 4.0 - 4.5 - 5.0")
    if es_caja_compacta:#Reporte a la Facultad
        lienzo.rect(pos_x+240,pos_y,200,64)
        lienzo.rect(pos_x,pos_y,240,64)
        lienzo.drawString(pos_x+105,pos_y+27,"Sismos procesados")
    else:
        lienzo.rect(pos_x+295,pos_y,215,64)
        lienzo.rect(pos_x,pos_y,295,64)
        lienzo.drawString(pos_x+105,pos_y+27,"Sismo superficial, < 40 km.")
        lienzo.drawString(pos_x+105,pos_y+16,"Sismo con profundidad media, de 40 a 70 Km.")
        lienzo.drawString(pos_x+105,pos_y+5,"Sismo profundo, > 70 Km.")
    lienzo.setFont('Helvetica', 11)
    if es_resumen_matriz:  #Region Ecuador Facultad Fuentes o Reporte diario
        divisor_matriz = max(1, (len(resumen) - 1) if (len(resumen) < 3 and mapa_ != 3) else (len(resumen) - 2))
        promedio_sismos_localizados=round(resumen[1][1]/divisor_matriz,1)
        promedio_sismos_no_localizados=round(resumen[1][2]/divisor_matriz,1)
        promedio_total=round(promedio_sismos_localizados+promedio_sismos_no_localizados,1)
        if es_caja_compacta:
            lienzo.drawString(pos_x+280,pos_y+50,"Promedio diario de registros")
            lienzo.drawString(pos_x+250,pos_y+28,"Sismos localizados:    "+str(promedio_sismos_localizados)+" sismos/dia")
            lienzo.drawString(pos_x+250,pos_y+17,"Eventos sin localizar:  "+str(promedio_sismos_no_localizados)+" eventos/dia")
            lienzo.drawString(pos_x+250,pos_y+6,"Total:                         "+str(promedio_total)+" registros/dia")
        else:
            lienzo.drawString(pos_x+340,pos_y+50,"Promedio diario de registros")
            lienzo.drawString(pos_x+305,pos_y+28,"Sismos localizados:    "+str(promedio_sismos_localizados)+" sismos/dia")
            lienzo.drawString(pos_x+305,pos_y+17,"Eventos sin localizar:  "+str(promedio_sismos_no_localizados)+" eventos/dia")
            lienzo.drawString(pos_x+305,pos_y+6,"Total:                         "+str(promedio_total)+" registros/dia")


    else: #Reporte de periodo desde Austro en adelante.
        aux=sum(resumen)
        divisor_vec = max(1, len(resumen) - 2)
        promedio_sismos_localizados=round(aux/divisor_vec,1)
        if es_caja_compacta:
            lienzo.drawString(pos_x+280,pos_y+50,"Promedio diario de registros")
            lienzo.drawString(pos_x+250,pos_y+28,"Sismos localizados:    "+str(promedio_sismos_localizados)+" sismos/dia")
            lienzo.drawString(pos_x+250,pos_y+6,"Total:                         "+str(aux)+" sismos")
        else:
            lienzo.drawString(pos_x+340,pos_y+50,"Promedio diario de registros")
            lienzo.drawString(pos_x+305,pos_y+28,"Sismos localizados:    "+str(promedio_sismos_localizados)+" sismos/dia")
            lienzo.drawString(pos_x+305,pos_y+6,"Total:                         "+str(aux)+" sismos")
    dibujo_leyenda_sismos = Drawing(300, 60)
    color=[colors.blue,colors.orange,colors.red]
    for i in range(0,5):
        for j in range(0,3):
            if not es_caja_compacta:
                if escala_circulos == 'mitad':
                    if bandera_relleno:
                        dibujo_leyenda_sismos.add(Circle(i*21, j*12, (i+1)/2., strokeColor=color[j],strokeWidth = 0.2,fillColor=color[j],fillOpacity=0.7))#Dibuja los circulos a la mitad
                    else:
                        dibujo_leyenda_sismos.add(Circle(i*21, j*12, (i+1)/2., strokeColor=color[j],strokeWidth = 0.2,fillColor=color[j],fillOpacity=0.))
                else:
                    if bandera_relleno:
                        dibujo_leyenda_sismos.add(Circle(i*21, j*12, i+1, strokeColor=color[j],strokeWidth = 0.2,fillColor=color[j],fillOpacity=0.7))#Normales los circulos
                    else:
                        dibujo_leyenda_sismos.add(Circle(i*21, j*12, i+1, strokeColor=color[j],strokeWidth = 0.2,fillColor=color[j],fillOpacity=0.))
            else:
                if j==2:
                    dibujo_leyenda_sismos.add(Circle(i*21, j*12, i+1, strokeColor=colors.blue,strokeWidth = 0.2,fillColor=colors.blue,fillOpacity=0.7))#Pone todos azules para la Facultad.
    dibujo_leyenda_sismos.drawOn(lienzo,pos_x+ 9,pos_y+8)
    return lienzo

def formato(marca_agua,tamanio_hoja,titulo, subtitulo,formato_,lienzo): 
    #marca _agua     Localizacionde la marca de agua del logo de la rsa
    #tamanio_hoja    Tamaño de la hoja a imprimir.  No se esta usando
    #titulo          Titulo a imprimir
    #subtitulo       subtitulo a imprimir
    #formato_        Tipo de impresion, 0 reporte sísmico, 1 reporte acelerográfico, 2 reporte Facultad.
    #lienzo          Lienzo donde se imprime el informe
    #retorna:        Lienzo con mas detalles colocados n este método
    cabecera=os.path.join(ruta_proyecto, 'datos','cabecera.emf')
    pie=os.path.join(ruta_proyecto, 'datos','pie.emf')
    logoRSA=os.path.join(ruta_proyecto, 'datos','logoRSA.emf')
    cabecera_1=os.path.join(ruta_proyecto, 'datos','cabecera_1.emf')
    xpos= marca_agua[0]
    ypos= marca_agua[1]
    ancho=marca_agua[2]
    alto=marca_agua[3]
    PAGE_WIDTH  = defaultPageSize[0]#PAGE_WIDTH  = tamanio_hoja[0]#595.2755#
    PAGE_HEIGHT = defaultPageSize[1]# PAGE_HEIGHT = tamanio_hoja[1]#841.8897#
    ######Reporte sísmico
    if formato_==0:
        canvas.Canvas.setPageSize(lienzo, A4)
        lienzo.drawImage(cabecera, 56, 780, 500, 50)# posx, posy, ancho, alto
        lienzo.drawImage(pie, 456, 10, 140, 50)# posx, posy, ancho, alto
        lienzo.drawImage(logoRSA, xpos, ypos, ancho, alto)# posx, posy, ancho, alto=
        lienzo.setFont('Helvetica', 18)
        text_width = stringWidth(titulo,'Helvetica-Bold', 18)
        lienzo.drawString((PAGE_WIDTH - text_width) / 2.0,760,titulo)
        lienzo.setFont('Helvetica', 10)
        text_width = stringWidth(subtitulo,'Helvetica', 10)
        lienzo.drawString((PAGE_WIDTH - text_width) / 2.0,745,subtitulo)
    ######Reporte acelerografico
    elif formato_==1:
        canvas.Canvas.setPageSize(lienzo, (landscape(A4)))
        lienzo.drawImage(cabecera_1, 56, 530,750, 50)# posx, posy, ancho, alto
        lienzo.drawImage(pie, 720, 17, 110, 30)# posx, posy, ancho, alto
        lienzo.drawImage(logoRSA, xpos, ypos, ancho, alto)# posx, posy, ancho, alto
        lienzo.setFont('Helvetica', 18)
        text_width = stringWidth(titulo,'Helvetica-Bold', 18)
        lienzo.drawString((PAGE_HEIGHT - text_width) / 2.0,500,titulo)#450
        lienzo.setFont('Helvetica', 11)
        text_width = stringWidth(subtitulo,'Helvetica', 11)
        lienzo.drawString((PAGE_HEIGHT - text_width) / 2.0,495,subtitulo)
    ######Reporte facultad
    else:
        canvas.Canvas.setPageSize(lienzo, A4)
        lienzo.drawImage(cabecera, 61, 744, 474, 43)# posx, posy, ancho, alto
        lienzo.drawImage(pie, 426, 53, 109, 39)# posx, posy, ancho, alto
        lienzo.drawImage(logoRSA, xpos, ypos, ancho, alto)# posx, posy, ancho, alto
        lienzo.setFillColor('Black')
        lienzo.setFont('Helvetica-Bold', 20)
        lienzo.setFillColor('Gray')
        text_width = stringWidth(titulo,'Helvetica-Bold', 20)
        lienzo.drawString((PAGE_WIDTH - text_width) / 2.0,700,titulo)
        lienzo.setFont('Helvetica', 16)
        text_width = stringWidth(subtitulo,'Helvetica', 16)
        lienzo.drawString((PAGE_WIDTH - text_width) / 2.0,670,subtitulo)
        lienzo.setFillColor('Black')
    return lienzo

def mapa(lienzo,imagen, tamanio, coordenadas,salto,bandera):
    # Metodo que dibuja um mapa del tamaño dada por la variable tamanio dentro de las coordenadas geográficas dadas por la variable corrdenadas, que dibuja las coordenadas 
    # o no de acuerdo a la variable bandera con una escala dada por la variable salto.  Las unidades geográficas están en grados.
    #Lienzo  ------ Imagen de trabajo
    #imagen  ------ Imagen, mas concretamente el mapa, que será dibujado en el lienzo
    #tamanio ------ Tamaño de la imagen, cuatro variables en el sigueinte orden: xpos, ypos, ancho , alto 
    #coordenadas--- Coordenadas límite del mapa o imagen, cuatro variables en el siguiente orden: latitud mínima, longitud minima, latitd maxima, longitud máxima
    #salto -------- Salto de las marcas en el mapa
    #bandera ------ Variable que indica si son dibujados o no las masrcas geográficas en el mapa.
    marca_x=[]
    marca_y=[]
    xpos= tamanio[0]
    ypos= tamanio[1]
    ancho=tamanio[2]
    alto=tamanio[3]
    latitud_min=coordenadas[0]
    longitud_min=coordenadas[1]
    latitud_max=coordenadas[2]
    longitud_max=coordenadas[3]
    lienzo.drawImage(imagen, xpos, ypos, ancho, alto)# posx, posy, ancho, alto
    numero_x=round((latitud_max-latitud_min)/salto,0)
    numero_y=round((longitud_max-longitud_min)/salto,0)
    for i in range(0,int(numero_x)+1):
        valor=round(i*salto+latitud_min,1)
        if salto > 0.2:
            if (valor-int(valor))==0:
                marca_x.append(str(valor))
            else:
                marca_x.append(" ")
        else:
            marca_x.append(str(valor))
    for i in range(0,int(numero_y)+1):
        valor=round(i*salto+longitud_min,1)
        if salto > 0.2:
            if (valor-int(valor))==0:
                marca_y.append(str(valor))
            else:
                marca_y.append(" ")
        else:
            marca_y.append(str(valor))
    intervalo_x=ancho/(len(marca_x)-1)
    intervalo_y=alto/(len(marca_y)-1)
    if bandera :
        d=Drawing(10,10)
        lab=Label()
        lab.angle=90
        lab.setText('Latitud')
        d.add(lab)
        d.drawOn(lienzo, xpos-34,ypos+alto/2-5)
        d=Drawing(10,10)
        lab=Label()
        lab.setText('Longitud')
        d.add(lab)
        d.drawOn(lienzo, xpos+ancho/2-10,ypos-20)        
        lienzo.setFont('Helvetica', 8)
        for i in range(0,len(marca_x)):
        #marcas horizontales
            lienzo.line(xpos+intervalo_x*i,ypos-5,xpos+intervalo_x*i,ypos)
            lienzo.line(xpos+intervalo_x*i,ypos+alto,xpos+intervalo_x*i,ypos+alto+5)
        #Texto Horizontal
            lienzo.drawString(xpos+intervalo_x*i-14,ypos-15,marca_x[i])
            lienzo.drawString(xpos+intervalo_x*i-14,ypos+alto+7,marca_x[i])
        for i in range(0,len(marca_y)):
        #marcas verticales
            lienzo.line(xpos-5,ypos+i*intervalo_y,xpos,ypos+i*intervalo_y)
            lienzo.line(xpos+ancho,ypos+i*intervalo_y,xpos+ancho+5,ypos+i*intervalo_y)
        #Texto Vertical
            lienzo.drawString(xpos-28,ypos+intervalo_y*i-4,marca_y[i])
            lienzo.drawString(xpos+ancho+6,ypos+intervalo_y*i-4,marca_y[i])            
    lienzo.rect(xpos,ypos,ancho,alto) #c.rect(50,200,300,60)
    return lienzo

def mapa_configuracion(mapa_numero, detalle):
    #mapa_numero: numero de mapa para el reporte dado en el archivo mapas.csv  
    #detalle:     Tio de detalla, de basico a detalles
    #retorna:     (nombre_mapa,coordenadas,salto,mapa_escogido[0],estaciones_informe)
    #               nombre_mapa -------- archivo que contiene el mapa a cargar en formato emf
    #               coordenadas -------- coordenadas geograficas del mapa
    #               salto       -------- variable para el escalamiento del mapa
    #               mapa_escogido[0] --- nombre del mapa escogido
    #               estaciones_informe - Estaciones involucradas en el informe.
    archivo = os.path.abspath(os.path.join(ruta_proyecto, 'datos','mapas','mapas.csv'))

    with open(archivo,newline='') as mapas_csv:
        lista_mapas=csv.reader(mapas_csv,delimiter=';',quotechar=';')
        mapa=[]
        for x in lista_mapas:
            if x[0]!='nombre':
                mapa.append(x)
        mapa_escogido=mapa[mapa_numero]
        nombre_mapa=os.path.join(ruta_datos, 'mapas',mapa_escogido[0]+'_'+str(detalle)+'.emf')
        coordenadas=(float(mapa_escogido[3]),float(mapa_escogido[1]),float(mapa_escogido[4]),float(mapa_escogido[2]))#Longitud mínima, Latitud mínima, Longitud máxima, Latitud máxima
        salto=float(mapa_escogido[5])
        estaciones_informe=mapa_escogido[6].split(' ')
        return(nombre_mapa,coordenadas,salto,mapa_escogido[0],estaciones_informe)



def escalado(numero):
    if numero is None or numero <= 0:
        return 1.0
    try:
        escala = 1 / (10 ** int(math.log10(1 / numero)))
    except (ValueError, ZeroDivisionError, OverflowError):
        return 1.0
    if escala < 1:
        escala = escala / 10
    if numero < escala:
        escala = escala / 10
    if escala > 0 and numero / escala < 2:
        escala = escala / 2
    if escala > 0 and numero / escala > 5:
        escala = escala * 2
    return max(escala, 1e-6)
        

def grafico_cobertura(lienzo, evento, coordenadas, tamanio, directorio_trabajo):
    from math import sqrt

    def dibujar_triangulo(lienzo, x_canvas, y_canvas, radio_punto, stroke=1, fill=1):
        """Dibuja un triángulo equilátero centrado en (x_canvas, y_canvas)."""
        altura = sqrt(3) * radio_punto
        x1, y1 = x_canvas,              y_canvas + radio_punto
        x2, y2 = x_canvas - radio_punto, y_canvas - (altura - radio_punto)
        x3, y3 = x_canvas + radio_punto, y_canvas - (altura - radio_punto)

        path = lienzo.beginPath()
        path.moveTo(x1, y1)
        path.lineTo(x2, y2)
        path.lineTo(x3, y3)
        path.close()
        lienzo.drawPath(path, stroke=stroke, fill=fill)

    def transformar_coordenadas(coordenadas, tamanio, lon, lat):
        x_escala = (lon - coordenadas[IDX_LONGITUD_MINIMA]) / (coordenadas[IDX_LONGITUD_MAXIMA] - coordenadas[IDX_LONGITUD_MINIMA])
        y_escala = (lat - coordenadas[IDX_LATITUD_MINIMA])  / (coordenadas[IDX_LATITUD_MAXIMA]  - coordenadas[IDX_LATITUD_MINIMA])
        x_canvas = tamanio[IDX_POSICION_X] + x_escala * tamanio[IDX_ANCHO]
        y_canvas = tamanio[IDX_POSICION_Y] + y_escala * tamanio[IDX_ALTO]
        return x_canvas, y_canvas

    def dibujo_poligono(lienzo, distancia, color):
        poligono, estaciones = cobertura_red(archivo_estaciones, distancia)  
        if poligono is None or poligono.empty:
            return lienzo, []
        geometria = poligono.geometry.iloc[0]
        if geometria.geom_type != 'Polygon':
            return lienzo, []
        vertices = list(geometria.exterior.coords)
        puntos_transformados = [transformar_coordenadas(coordenadas, tamanio, lon, lat) for lon, lat in vertices]

        path = lienzo.beginPath()
        path.moveTo(*puntos_transformados[0])
        for punto in puntos_transformados[1:]:
            path.lineTo(*punto)
        path.close()
        lienzo.setStrokeColor(color)
        lienzo.setLineWidth(1)
        lienzo.drawPath(path, stroke=1, fill=0)
        lienzo.setStrokeColor(colors.black)
        return lienzo, estaciones

    # Obtener directorios y archivo de estaciones
    directorios = obtener_directorios(evento)
    archivo_estaciones = directorio_trabajo + directorios['archivo_estaciones'] 

    lienzo, estaciones = dibujo_poligono(lienzo, 150, colors.greenyellow)
    lienzo, estaciones = dibujo_poligono(lienzo, 50, colors.red)
    
    # Dibujar las estaciones como triángulos azules
    lienzo.setFillColor(colors.blue)
    radio_punto = 3
    for estacion in estaciones:
        x_geo, y_geo = estacion
        x_canvas, y_canvas = transformar_coordenadas(coordenadas, tamanio, x_geo, y_geo)
        dibujar_triangulo(lienzo, x_canvas, y_canvas, radio_punto, stroke=1, fill=1)

    lienzo.setStrokeColor(colors.black)
    return lienzo


def _reducir_envolvente_minmax(arr, max_puntos=2000):
    """
    Reduce una serie temporal larga a un máximo de `max_puntos` conservando el mínimo
    y máximo exactos de cada ventana (en su orden temporal real). Así el gráfico en
    ReportLab es visualmente idéntico pero ~40x más rápido y liviano.
    """
    datos = np.asarray(arr, dtype=np.float64)
    n = datos.size
    if n <= max_puntos or max_puntos < 4:
        return datos.tolist()
    n_bins = max_puntos // 2
    limites = np.linspace(0, n, n_bins + 1, dtype=np.int64)
    salida = np.empty(n_bins * 2, dtype=np.float64)
    for b in range(n_bins):
        i0, i1 = limites[b], limites[b + 1]
        if i1 <= i0:
            val = datos[min(i0, n - 1)]
            salida[2 * b] = val
            salida[2 * b + 1] = val
            continue
        seg = datos[i0:i1]
        idx_min = int(np.argmin(seg))
        idx_max = int(np.argmax(seg))
        if idx_min <= idx_max:
            salida[2 * b] = seg[idx_min]
            salida[2 * b + 1] = seg[idx_max]
        else:
            salida[2 * b] = seg[idx_max]
            salida[2 * b + 1] = seg[idx_min]
    return salida.tolist()


def _reducir_espectro_max(x_arr, y_arr, max_puntos=1500):
    """
    Reduce el espectro de Fourier preservando los picos máximos por ventana logarítmica
    para evitar decenas de miles de segmentos vectoriales en ReportLab LinePlot.
    """
    x_np = np.asarray(x_arr, dtype=np.float64)
    y_np = np.asarray(y_arr, dtype=np.float64)
    n = min(x_np.size, y_np.size)
    if n <= max_puntos or max_puntos < 4:
        return x_np[:n].tolist(), y_np[:n].tolist()
    limites = np.linspace(0, n, max_puntos + 1, dtype=np.int64)
    x_out = np.empty(max_puntos, dtype=np.float64)
    y_out = np.empty(max_puntos, dtype=np.float64)
    for b in range(max_puntos):
        i0, i1 = limites[b], limites[b + 1]
        if i1 <= i0:
            i_sel = min(i0, n - 1)
        else:
            i_sel = i0 + int(np.argmax(y_np[i0:i1]))
        x_out[b] = x_np[i_sel]
        y_out[b] = y_np[i_sel]
    return x_out.tolist(), y_out.tolist()


def _resolver_ruta_cache_acelerograma(ruta_mseed: str, dir_acelerogramas: str = None) -> str:
    """
    Resuelve la ruta canónica del caché comprimido (.npz) dentro de:
        <Directorio_acelerogramas>/señales/<stem_mseed>.npz
    """
    p_mseed = Path(ruta_mseed)
    if dir_acelerogramas:
        base_acel = Path(dir_acelerogramas)
    else:
        # .../AAAA_MM_DD/mseed/eventos/EST_AAAAMMDD_hhmmss.mseed -> .../AAAA_MM_DD/acelerogramas
        base_dia = p_mseed.parent.parent.parent if len(p_mseed.parents) >= 3 else p_mseed.parent
        base_acel = base_dia / "acelerogramas"
    return str(base_acel / "señales" / f"{p_mseed.stem}.npz")


def obtener_o_calcular_cache_acelerograma(
    ruta_mseed: str,
    factor: float,
    dir_acelerogramas: str = None,
    trcanal=None,
    solo_maximos: bool = False,
):
    """
    Carga desde `<Directorio_acelerogramas>/señales/<EST>_<AAAAMMDD>_<hhmmss>.npz`
    las señales corregidas, máximos exactos (acel/vel/desp), espectro FFT y espectro
    de respuesta al 5% si el archivo existe y el `.mseed` original no ha cambiado
    (verificado por mtime, size y factor).

    Si no existe o cambió el `.mseed`, calcula las 3 componentes una sola vez, guarda
    el `.npz` comprimido y devuelve el diccionario listo para Etapa 2 (PGA) y Etapa 3 (PDF).
    """
    if not ruta_mseed or not os.path.isfile(ruta_mseed):
        return None

    stat_ms = os.stat(ruta_mseed)
    mtime_actual = float(stat_ms.st_mtime)
    size_actual = int(stat_ms.st_size)
    factor_f = float(factor)
    ruta_npz = _resolver_ruta_cache_acelerograma(ruta_mseed, dir_acelerogramas)

    # 1. Intentar carga instantánea desde caché si está vigente
    if os.path.isfile(ruta_npz):
        try:
            with np.load(ruta_npz, allow_pickle=False) as z:
                if (
                    abs(float(z['mseed_mtime']) - mtime_actual) < 1e-3
                    and int(z['mseed_size']) == size_actual
                    and abs(float(z['factor']) - factor_f) < 1e-9
                    and int(z['version']) == 1
                ):
                    maximos_arr = z['maximos']  # shape (3, 3): [comp][acel, vel, desp]
                    pga_global = float(np.max(maximos_arr[:, 0])) if maximos_arr.size > 0 else 0.0
                    if solo_maximos:
                        return {
                            'pga_max': pga_global,
                            'maximos': maximos_arr.tolist(),
                            'ruta_npz': ruta_npz,
                        }
                    componentes = []
                    n_comp = int(z['n_comp'])
                    for c_idx in range(n_comp):
                        componentes.append({
                            'maximos': maximos_arr[c_idx].tolist(),
                            'acel_plot': z[f'c{c_idx}_acel'].tolist(),
                            'vel_plot': z[f'c{c_idx}_vel'].tolist(),
                            'desp_plot': z[f'c{c_idx}_desp'].tolist(),
                            'frec_log': z[f'c{c_idx}_frec'].tolist(),
                            'y_f': z[f'c{c_idx}_yf'].tolist(),
                            'y_f_max': float(z[f'c{c_idx}_yf_max']),
                            'T': z[f'c{c_idx}_T'].tolist(),
                            'Spa': z[f'c{c_idx}_Spa'].tolist(),
                        })
                    from obspy import UTCDateTime
                    return {
                        'pga_max': pga_global,
                        'maximos': maximos_arr.tolist(),
                        'componentes': componentes,
                        'tiempo_inicio': UTCDateTime(float(z['tiempo_inicio'])),
                        'tiempo_inicial': float(z['tiempo_inicial']),
                        'duracion': float(z['duracion']),
                        'catNames': [str(x) for x in z['catNames'].tolist()],
                        'ruta_npz': ruta_npz,
                    }
        except Exception:
            pass

    # 2. Calcular una sola vez desde el .mseed y persistir en acelerogramas/señales/
    try:
        if trcanal is None or len(trcanal) == 0:
            from obspy import read as obspy_read
            trcanal = obspy_read(ruta_mseed)
        if len(trcanal) == 0:
            return None

        tiempo_inicio, tiempo_inicial, duracion, catNames = obtener_marcas_tiempo(trcanal)
        n_comp = min(3, len(trcanal))
        maximos_arr = np.zeros((3, 3), dtype=np.float64)
        componentes = []
        payload_npz = {
            'version': np.int32(1),
            'mseed_mtime': np.float64(mtime_actual),
            'mseed_size': np.int64(size_actual),
            'factor': np.float64(factor_f),
            'n_comp': np.int32(n_comp),
            'tiempo_inicio': np.float64(tiempo_inicio.timestamp if hasattr(tiempo_inicio, 'timestamp') else float(tiempo_inicio)),
            'tiempo_inicial': np.float64(tiempo_inicial),
            'duracion': np.float64(duracion),
            'catNames': np.array(catNames, dtype='<U16'),
        }

        muestreo = float(trcanal[0].stats.sampling_rate)
        delta_tr = float(trcanal[0].stats.delta)

        for c_idx in range(n_comp):
            seniales = correccion(trcanal[c_idx], factor_f)  # [aceleración, velocidad, desplazamiento]
            aceleracion = np.asarray(seniales[0], dtype=np.float64)
            velocidad = np.asarray(seniales[1], dtype=np.float64)
            desplazamiento = np.asarray(seniales[2], dtype=np.float64)

            max_a = float(np.max(np.abs(aceleracion))) if aceleracion.size > 0 else 0.0
            max_v = float(np.max(np.abs(velocidad))) if velocidad.size > 0 else 0.0
            max_d = float(np.max(np.abs(desplazamiento))) if desplazamiento.size > 0 else 0.0
            maximos_arr[c_idx] = [max_a, max_v, max_d]

            # FFT exacta sobre el 100% de las muestras originales
            N = len(aceleracion)
            f_max = 30.0
            delta_f = 1.0 / (N * delta_tr) if (N * delta_tr) > 0 else 1.0
            N_valores = max(1, int(0.1 / delta_f))
            N_max = max(N_valores + 1, int(N // (muestreo / f_max))) if muestreo > 0 else N
            frec_ = np.arange(N_valores, N_max, dtype=np.float64) * delta_f
            frec_log_full = np.where(frec_ > 0, np.log10(np.maximum(frec_, 1e-12)), -1.0)
            y_f = scipy.fft.fft(aceleracion)
            y_f_full = (2.0 / N) * np.abs(y_f[:N_max]).astype(np.float64) if N > 0 else np.zeros(1)
            y_f_max = float(np.max(1.2 * y_f_full)) if y_f_full.size > 0 else 1e-6

            frec_log_red, y_f_red = _reducir_espectro_max(frec_log_full, y_f_full[N_valores:], max_puntos=1500)

            # Espectro de respuesta exacto (5%) sobre el 100% de las muestras originales
            dt_c = float(trcanal[c_idx].stats.delta)
            T_arr, Spa_arr, _, _, _, _ = espectro_respuesta(aceleracion, dt_c, 1.0, '')

            # Envolventes exactas min-max para trazado rápido en ReportLab
            acel_plot = _reducir_envolvente_minmax(aceleracion, max_puntos=2000)
            vel_plot = _reducir_envolvente_minmax(velocidad, max_puntos=2000)
            desp_plot = _reducir_envolvente_minmax(desplazamiento, max_puntos=2000)

            payload_npz[f'c{c_idx}_acel'] = np.asarray(acel_plot, dtype=np.float32)
            payload_npz[f'c{c_idx}_vel'] = np.asarray(vel_plot, dtype=np.float32)
            payload_npz[f'c{c_idx}_desp'] = np.asarray(desp_plot, dtype=np.float32)
            payload_npz[f'c{c_idx}_frec'] = np.asarray(frec_log_red, dtype=np.float32)
            payload_npz[f'c{c_idx}_yf'] = np.asarray(y_f_red, dtype=np.float32)
            payload_npz[f'c{c_idx}_yf_max'] = np.float64(y_f_max)
            payload_npz[f'c{c_idx}_T'] = np.asarray(T_arr, dtype=np.float32)
            payload_npz[f'c{c_idx}_Spa'] = np.asarray(Spa_arr, dtype=np.float32)

            componentes.append({
                'maximos': [max_a, max_v, max_d],
                'acel_plot': acel_plot,
                'vel_plot': vel_plot,
                'desp_plot': desp_plot,
                'frec_log': frec_log_red,
                'y_f': y_f_red,
                'y_f_max': y_f_max,
                'T': T_arr.tolist(),
                'Spa': Spa_arr.tolist(),
            })

        payload_npz['maximos'] = maximos_arr
        try:
            os.makedirs(os.path.dirname(ruta_npz), exist_ok=True)
            np.savez_compressed(ruta_npz, **payload_npz)
        except Exception as e_save:
            print(f"Aviso guardando caché acelerográfico {ruta_npz}: {e_save}")

        pga_global = float(np.max(maximos_arr[:, 0]))
        return {
            'pga_max': pga_global,
            'maximos': maximos_arr.tolist(),
            'componentes': componentes,
            'tiempo_inicio': tiempo_inicio,
            'tiempo_inicial': float(tiempo_inicial),
            'duracion': float(duracion),
            'catNames': list(catNames),
            'ruta_npz': ruta_npz,
        }
    except Exception as e_calc:
        print(f"Aviso calculando caché acelerográfico {ruta_mseed}: {e_calc}")
        return None


def imprimir_acelerograma(tamanio,trcanal,componente,factor,bandera,cache_acel=None):
    #tamanio--------- Tamaño del grafico
    #trcanal--------- achivo mseed con la informacion de la estacion 
    #componente------ Componente del acelerograma
    #factor---------- Ganancia para obtener los datos reales del acelerograma, diferenciado en entre estaciones de registro continuo en entero y los ETNA en punto flotante
    #bandera--------- Variable para mostrar o no el grafico en matplotlib de la señal, es para diferenciar un informe detallado o no.  Solo en reportes individuales de acelerogramas.
    #cache_acel------ Diccionario opcional precalculado desde acelerogramas/señales/*.npz
    ancho=tamanio[0]
    alto=tamanio[1]
    titulo_=(("Aceleración:   cm/s²      Aceleracion máxima:"," cm/s²"),("Velocidad:  cm/s        Velocidad  máxima:"," cm/s"),("Desplazamiento:   cm     Desplazamiento  máximo:"," cm"))
    drawing = Drawing(ancho,alto)
    senial_ascii=[]

    usar_cache = (
        cache_acel is not None
        and bandera
        and 'componentes' in cache_acel
        and componente < len(cache_acel['componentes'])
    )

    if usar_cache:
        catNames = cache_acel['catNames']
        comp_data = cache_acel['componentes'][componente]
        seniales_plot = [comp_data['acel_plot'], comp_data['vel_plot'], comp_data['desp_plot']]
        maximos_exactos = comp_data['maximos']
        frec_log_plot = comp_data['frec_log']
        y_f_plot = comp_data['y_f']
        y_f_max = comp_data['y_f_max']
        T = comp_data['T']
        Spa = comp_data['Spa']
    else:
        tiempo_inicio,tiempo_inicial,duracion, catNames=obtener_marcas_tiempo(trcanal)
        muestreo=trcanal[0].stats.sampling_rate
        seniales=correccion(trcanal[componente],factor)# [aceleración, velocidad, desplazamiento]
        aceleracion=seniales[0]
        senial_ascii.append(aceleracion)
        N=len(aceleracion)
        f_max=30
        delta=trcanal[0].stats.delta
        delta_f=1/(N*delta) if (N*delta) > 0 else 1.0
        N_valores=max(1, int(.1/delta_f))
        N_max=max(N_valores + 1, int(N//(muestreo/f_max))) if muestreo > 0 else N
        frec_= [k*delta_f for k in range(N_max)]
        frec_log=[math.log10(val) if val > 0 else -1.0 for val in frec_[N_valores:]]
        y_f = scipy.fft.fft(aceleracion)
        y_f_=(1./N)*2* np.abs(y_f[:N_max]).astype(float)
        y_f_max = float(max(1.2*y_f_)) if len(y_f_) > 0 else 1e-6

        dt = trcanal[componente].stats.delta
        T, Spa, Spv, Sd, Sa, Sv = espectro_respuesta(aceleracion, dt, 1, '')

        if not(bandera):
            fig, ax = plt.subplots()
            ax.set_xscale('log')
            ax.plot(frec_,y_f_)
            ax.set_xlim([0.1, f_max])
            plt.show()

        frec_log_plot, y_f_plot = _reducir_espectro_max(frec_log, y_f_[N_valores:], max_puntos=1500)
        maximos_exactos = [
            float(max(abs(max(seniales[j])), abs(min(seniales[j]))))
            for j in range(3)
        ]
        seniales_plot = [_reducir_envolvente_minmax(seniales[j], max_puntos=2000) for j in range(3)]

    # Inicia el grafico en el chart
    label = String(640, 253, 'Frecuencia(Hz)', fontSize=10)
    drawing.add(label)
    label = String(600, 453, 'ESPECTRO DE ACELERACIÓN', fontSize=12) #440
    drawing.add(label)
    label = Label()
    label.setOrigin(495, 380)#340
    label.angle = 90
    label.boxAnchor = 'ne'
    label.setText('Aceleración cm/s²')
    drawing.add(label)
    # Agregar espectro de aceleración al gráfico
    coorx=545
    coory=275
    r = Rect(coorx,  coory, 280, 170,strokeWidth = 1,fillColor=white,fillOpacity=0.6)
    drawing.add(r)
    lp = LinePlot()
    lp.x = coorx
    lp.y = coory
    lp.height = 170
    lp.width = 280
    lp.data = [list(zip(frec_log_plot, y_f_plot))]
    lp.lines[0].strokeWidth = 1
    lp.lines[0].symbol = None
    lp.lines[0].strokeColor = colors.blue
    lp.xValueAxis.valueSteps = [-1,-0.699,-0.523,-0.368,-0.301,-0.222,-0.155,-0.097,-0.046,0,0.301,0.477,0.602,0.699,0.778,0.845,0.903,0.954, 1.0,1.301]
    lp.xValueAxis.labelTextFormat = [".1","","","","","","","","","1","","","","","","","","","10",""]
    lp.xValueAxis.valueMin = -1 # valor mínimo del eje X
    lp.xValueAxis.valueMax = 1.5 # valor máximo del eje X
    lp.yValueAxis.valueMin = 0 # valor mínimo del eje Y
    lp.yValueAxis.valueMax = y_f_max if y_f_max > 0 else 1e-6 # valor máximo del eje Y
    drawing.add(lp)

    # Agregar espectro de respuesta (tanto en reporte individual como en grupo)
    label = String(645, 35, 'Periodo (s)', fontSize=10)
    drawing.add(label)
    label = String(615, 235, 'ESPECTRO DE RESPUESTA', fontSize=12)
    drawing.add(label)
    label = String(690, 220, 'Factor de Amortiguamiento del 5%', fontSize=9)
    drawing.add(label)

    label = Label()
    label.setOrigin(500, 190)
    label.angle = 90
    label.boxAnchor = 'ne'
    label.setText('Aceleración (g)')
    drawing.add(label)

    coory_espectro = coory - 215  # Espacio adicional para el espectro de respuesta
    r_respuesta = Rect(
        coorx, coory_espectro, 280, 170, strokeWidth=1, fillColor=white, fillOpacity=0.6
    )
    drawing.add(r_respuesta)
    lp_respuesta = LinePlot()
    lp_respuesta.x = coorx
    lp_respuesta.y = coory_espectro
    lp_respuesta.height = 170
    lp_respuesta.width = 280
    lp_respuesta.data = [list(zip(T, Spa))]
    lp_respuesta.lines[0].strokeWidth = 1
    lp_respuesta.lines[0].strokeColor = colors.blue
    max_spa = float(np.max(1.1 * np.asarray(Spa, dtype=np.float64))) if len(Spa) > 0 else 0.0
    lp_respuesta.yValueAxis.valueMin = 0
    lp_respuesta.yValueAxis.valueMax = max_spa if max_spa > 0 else 1e-6
    drawing.add(lp_respuesta)

    # Graficar aceleración, velocidad y desplazamiento
    maximos_componentes=[componente]

    for j in range(0,3):
        coorx=80
        coory=340-j*alto*1.2
        r = Rect(coorx,  coory, ancho, alto,strokeWidth = 1,fillColor=white,fillOpacity=0.6)
        drawing.add(r)
        maximo = maximos_exactos[j]
        maximos_componentes.append(maximo)
        max_value = 1.1 * maximo if maximo > 0 else 1e-6
        min_value = -max_value
        lab = Label()
        lab.setOrigin(250, coory+alto+6)
        lab.setText(titulo_[j][0]+str(round(maximo,5))+titulo_[j][1])
        lab.dx = 0
        lab.dy = 0
        drawing.add(lab)
        lc = HorizontalLineChart()
        lc.x = coorx
        lc.y = coory
        lc.height = alto
        lc.width = ancho
        lc.data = [seniales_plot[j]]
        lc.joinedLines = 1
        lc.categoryAxis.categoryNames = catNames
        lc.categoryAxis.visible = 0 #Hace invisible el eje x
        lc.valueAxis.visible = 1   #Hace invisible el eje y
        lc.categoryAxis.labels.boxAnchor = 'n'
        lc.valueAxis.valueMin = min_value
        lc.valueAxis.valueMax = max_value
        lc.valueAxis.valueStep = escalado(maximo) if maximo > 0 else 1e-6
        lc.lines[0].strokeColor = colors.blue
        lc.lines[0].strokeWidth = 0.5
        drawing.add(lc)
    return drawing,maximos_componentes,senial_ascii   

def imprimir_seniales(tamanio,canales,trcanal,evento,bandera_seniales,bandera_zoom):
# tamanio------------ el tamaño de las señales
# canales------------ cuales canales se imprimiran en forma de una lista de 1 y 0, denominado eventos basico
# trcanal------------ señales mseed a imprimir
# bandera_seniales--- si está en 1 imprime las señales solas para el reporte general, y si es cero los detalles de los informes
# evento------------- Evento completo a desplegar
# bandera_zoom------- si está en 1 imprime el zoom de las señales 

    parametros=parametros_estaciones()
    ancho=tamanio[0]
    alto=tamanio[1]
    dibujo = Drawing(ancho,alto)
    if bandera_seniales:
        r = Rect(0, 0, ancho, alto,strokeWidth = 0.5,fillColor=white,fillOpacity=0.6)    
        dibujo.add(r)
        lab = Label()
        lab.setOrigin(ancho/2, alto-10)
        lab.setText("SEÑALES")
        dibujo.add(lab)
    datos_np = [0] * 101
    #####Obtension de los datos para graficar
    for i in range(0, 101):
        if trcanal[i] and len(trcanal[i]) > 0 and trcanal[i][0] != ' ':#Es igual a ' ' cuando es la copia del mseed 
 
            trcanal[i].detrend(type='linear') #Correccion de linea de base

            datos_np[i]=trcanal[i][0].data
    contador=0
    #canales[6]=0#No se que hace esto.
    for i in range (0,NUMERO_ESTACIONES):
        if canales[i]!=0 and trcanal[i] and len(trcanal[i]) > 0:
            color_senial=colors.blue
            if trcanal[i][0]==' ':  #CUANDO ES COPIA PARA QUE GENERE EL ESAPACIO EN BLANCO
                contador=contador+1
                continue
            #####Obtension de la referencia de tiempo
            t_inicio=trcanal[i][0].stats.starttime #obtencion de la referencia del tiempo
            duracion=trcanal[i][0].stats.endtime.timestamp-trcanal[i][0].stats.starttime.timestamp
            ######Generacion de las marcas de tiempo para dibujar, esto en catNames
            catNames=[]               
            for j in range(0, int(duracion),10):
                tiempo=t_inicio+timedelta(seconds=j)
                catNames.append(str(tiempo.time.second))
            if not(bandera_seniales):   #######Informe
                x_=0
                y_=alto-(contador+1.8)*(int(alto/6))
                alto_=int(alto/10)
                ancho_=ancho
                if bandera_zoom:
                    alto_=int(alto/20)
                    linea=Line(x_+ancho_/2, y_, x_+ancho_/2, y_+alto_,strokeColor=colors.red,strokeWidth = 0.5)
                r = Rect(x_,y_,ancho_,alto_,strokeWidth = 1,fillColor=white,strokeColor=colors.black,fillOpacity=0.8)
                dibujo.add(r)
                if bandera_zoom:
                    dibujo.add(linea)
            else:                       #######Reporte diario
                x_=0
                y_=alto-(contador+1.8)*(int(alto/6))
                alto_=int(alto/7)
                ancho_=ancho
            datos=[]
            xx=datos_np[i].flatten().tolist()
            datos.append(xx)#Aqui pondría escalameinto a travez del parametro FACTOR_MIL(11) del archivo estaciones.
            max_value = max(datos[0])
            min_value = min(datos[0])
            grafico = HorizontalLineChart()
            grafico.x = x_
            grafico.y = y_
            grafico.height = alto_
            grafico.width = ancho_
            grafico.data = datos
            grafico.joinedLines = 1
            grafico.strokeWidth=0.25
            grafico.categoryAxis.categoryNames = catNames
            grafico.categoryAxis.labels.boxAnchor = 'n'
            grafico.valueAxis.valueMin = min_value
            grafico.valueAxis.valueMax = max_value
            grafico.categoryAxis.visible = 0 
            grafico.valueAxis.visible = 0   
            grafico.lines[0].strokeWidth = 0.5
            if len(evento)==104:
                if int(evento[i+3][5])==0:
                    color_senial=colors.grey
            grafico.lines[0].strokeColor = color_senial
            dibujo.add(grafico)
            lab = Label()
            if bandera_seniales: #Diario
                lab.fontSize=8
                lab.strokeColor = colors.blue
                lab.setOrigin(85, alto-(contador+1.1)*(int(alto/6)))
                lab.setText(parametros['CODIGO'][i])
                dibujo.add(lab)    
            else:
                pass
            contador=contador+1
    return dibujo



def estadistica_(lienzo,resumen,fecha_ini,mapa_,bandera_dia,banderas=None):
        #########################################################################################
        # Impresión del resumen diario de eventos procesados a través de un gráfico de barras
        # apiladas (VerticalBarChart) en la parte inferior de la portada de período.
        # ---------------------------------------------------------------------------------------
        # banderas: Diccionario maestro de banderas (PERFILES_MAPA_ZONA en rsa_pdf_catalogo.py):
        #             - 'tipo_resumen_estadistico': 'matriz_global' (barras verdes Procesados + rojas FF)
        #                                           o 'vector_filtrado' (solo barras verdes Procesados en la zona).
        #             - 'mostrar_grafico_barras'  : True para dibujar el histograma; False para omitirlo
        #                                           (ej. en Facultad y Reportes).
        #########################################################################################
        es_resumen_matriz = (
            (banderas.get('tipo_resumen_estadistico') == 'matriz_global')
            if isinstance(banderas, dict) and 'tipo_resumen_estadistico' in banderas
            else (mapa_ < 4 or bandera_dia == 0)
        )
        mostrar_barras = (
            banderas.get('mostrar_grafico_barras')
            if isinstance(banderas, dict) and 'mostrar_grafico_barras' in banderas
            else (mapa_ not in (2, 4))
        )

        dibujo_chart = Drawing(500, 200)
        data = [[],[]]
        nombres=[]
        maximo=0
        fecha=fecha_ini
        if es_resumen_matriz: #Resumen como matriz
            sismos_procesados=int(resumen[1][1])
        else: #Reporte de periodo filtrado por zona
            sismos_procesados=sum(resumen)#Resumen como vector con los dos primeros valores 0
        tope=int(len(resumen)/35)+1
        contador_datos=0
        for i in range(2,len(resumen)):
            if es_resumen_matriz:
                sismos_procesados=int(resumen[i][0])
                sismos_no_procesados=int(resumen[i][1])
            else:
                sismos_procesados=resumen[i]
                sismos_no_procesados=0
            data[0].append(sismos_procesados)
            data[1].append(sismos_no_procesados)
            fecha_ = QDate(fecha.year, fecha.month,fecha.day)
            if contador_datos==0:
                nombres.append(fecha_.toString('dd/MMM'))
            else:
                nombres.append(fecha_.toString(' '))
            contador_datos=contador_datos+1
            if contador_datos==tope:
                contador_datos=0
            fecha = fecha + timedelta(1)
            if((sismos_procesados+sismos_no_procesados)>maximo):
                maximo=sismos_procesados+sismos_no_procesados
        bc = VerticalBarChart()
        bc.x = 50
        bc.y = maximo
        bc.height = 112
        bc.width = 500
        bc.data = data
        bc.strokeColor = colors.black
        bc.valueAxis.valueMin = 0
        bc.valueAxis.valueMax = maximo+10
        bc.valueAxis.valueStep = 10
        bc.categoryAxis.labels.boxAnchor = 'ne'
        bc.categoryAxis.labels.dx = -8
        bc.categoryAxis.labels.angle = 90
        bc.categoryAxis.categoryNames = nombres
        bc.categoryAxis.style = 'stacked'
        bc.bars[0].fillColor = colors.darkgreen
        bc.bars[0].strokeWidth=0.01
        bc.bars[1].fillColor = colors.darkred
        bc.bars[1].strokeWidth=0.01
        if not mostrar_barras:
            pass
        else:
            dibujo_chart.add(bc)
            if es_resumen_matriz:  #Reporte general con matriz (Procesados + No procesados FF)
                dibujo_chart.add(String(185,135,'Estadística de Registros Sísmicos',fontSize=14))
                dibujo_chart.add(Rect(450,125,6,6,fillColor=colors.darkred))
                dibujo_chart.add(String(457,125,'No Procesados (FF)',fontSize=10))
                dibujo_chart.add(Rect(450,115,6,6,fillColor=colors.darkgreen))
                dibujo_chart.add(String(457,115,'Procesados',fontSize=10))
            else:  #Reporte Filtrado de acuerdo al mapa de proyecto/institución
                 dibujo_chart.add(String(185,135,'Estadística de Registros Sísmicos Procesados',fontSize=14))
        dibujo_chart.drawOn(lienzo, 15,68)
        return lienzo



