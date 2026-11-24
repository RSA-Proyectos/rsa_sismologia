"""
marcar_impresiones ok
imprimir_catalogo ok
_filtrar_catalogo_oficial_sin_dummies ok
_construir_catalogo_diario_para_detalle ok
responsables_tiempos_ ok
responsables_tiempos___ ok
reporte_resumen_modos ok
reporte_resumen_modos__ ok
normalizar_layout_por_institucional ok
normalizar_layout_por_institucional__ ok
derivar_banderas_desde_modo ok


from rsa_reportes_pdf import impresion_reporte_sismo ,impresion_reporte_acelerograma,cabecera_,reporte_resumen_modos,normalizar_layout_por_institucional,derivar_banderas_desde_modo,hoja_seniales_


from rsa_catalogo_pdf import marcar_impresiones,imprimir_catalogo,_filtrar_catalogo_oficial_sin_dummies,_construir_catalogo_diario_para_detalle,estadistica_,responsables_tiempos_,responsables_tiempos___,

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

from rsa_io import leer_mseed
from rsa_dominio import convertir_lista, correccion
import numpy as np
from rsa_pdf_reportes import impresion_reporte_sismo, impresion_reporte_acelerograma, hoja_seniales_

#from rsa_graficos_pdf import *
#from rsa_reportes_pdf import *
#from rsa_catalogo_pdf import *

from rsa_pdf_graficos import (mapa_configuracion,formato,mapa,
                              dibujo_sismos_,dibujar_lugar_geometrico_pdf,
                              caja_simbologia,estadistica_)


from metodos_gestion import parametros_estaciones,obtener_directorios

from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing, String
from reportlab.pdfgen import canvas
import csv
from reportlab.lib.pagesizes import A4

IDX_INDICE,IDX_ANIO,IDX_MES,IDX_DIA,IDX_HORA,IDX_MINUTO,IDX_SEGUNDO,\
IDX_LATITUD,IDX_LONGITUD,IDX_PROFUNDIDAD,IDX_RMS,IDX_E_X,IDX_E_Y,IDX_E_0,\
IDX_E_Z,IDX_MAGNITUD,IDX_UNIDAD_MAG,\
IDX_FUENTE,IDX_EVENTO,IDX_LUGAR = 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19

NUMERO_ESTACIONES=101

IDX_LONGITUD_MINIMA,IDX_LATITUD_MINIMA,IDX_LONGITUD_MAXIMA,IDX_LATITUD_MAXIMA=0,1,2,3
IDX_POSICION_X,IDX_POSICION_Y,IDX_ANCHO,IDX_ALTO,=0,1,2,3

# =========================
#  MODOS DE REPORTE (0–7)
# =========================
MODO_MAPA_ESPECIAL            = 0   # M0 – Portada cartográfica especial (Región, Fuentes, Reportes)
MODO_PERIODO_FRANJAS          = 1   # M1 – Período por franjas (00–12, 12–18, 18–24) – Control interno
MODO_DIARIO_REVISION          = 2   # M2 – Diario de revisión (día/ad-hoc) con detalle y dummies locales
MODO_OFICIAL_DETALLADO        = 3   # M3 – Oficial detallado (solo catálogo) + página/resumen de responsables
MODO_OFICIAL_RESUMEN          = 4   # M4 – Oficial resumen (solo catálogo, sin detalle)
MODO_FACULTAD_RESUMEN         = 5   # M5 – Facultad/resumen (redes sociales), sin detalle
MODO_INSTITUCIONAL_DETALLADO  = 6   # M6 – Institucional detallado (solo catálogo), sin extras ni responsables
MODO_INSTITUCIONAL_RESUMEN    = 7   # M7 – Institucional, sin detalle



def marcar_impresiones(lista_eventos,estaciones_informe,tipo_canal,mapa_):
    #Metodo que obtiene que estaciones se tienen que imprimir en los informes.
    # lista_eventos       lista de estaciones del evento marcado, a partir de la posicion 3
    # estaciones_informe  estaciones van en el informe
    # tipo_canal          tipo de estación, SISMICA O ACELEROGRAFICA
    # eventos_basico      Valor de retorno, lista con marcas de 1 con las señales a imprimir
    eventos_basico=[]
    for k in range(3,len(lista_eventos)):
        var_1=True if lista_eventos[k]!='-' else False  #Marca las estaciones que no esten con "-"
        var_2=True if str(k-3) in estaciones_informe  else False #Marca las estaciones dentro del informe
        if estaciones_informe==['', '']:  #Hay casos en los que se presenta esta forma
            var_2=True
        var_3=True if tipo_canal[k-3]=='ACELEROGRAFICO'  else False  #Marca las estaciones acelerograficas dentro en el archivo base.
        resultado_=(var_1 & ~var_2 & var_3) | (var_1 & var_2 & ~var_3) | (var_1 & var_2 & var_3)
        if resultado_:
            if len(lista_eventos[k])>4:
                if lista_eventos[k][5]=='1':
                    eventos_basico.append(1)
                else:
                    if mapa_==1 and tipo_canal[k-3]=='SISMICO':
                        eventos_basico.append(1)
                    else:
                        eventos_basico.append(0)
            else:
                eventos_basico.append(1)
        else:
            eventos_basico.append(0)
    return eventos_basico



def imprimir_catalogo(catalogo,arbol,lienzo,directorio,estaciones_informe,tipo_canal,mapa_,raiz,detalle,banderas=None):
    #########################################################################################
    #Método que imprime el catalogo completo sea de un día como de un periodo.
    #########################################################################################
    # catalogo           -   Catalogo a imprimir del mismo formato convencional de catalogo
    # arbol              -   Arbol xml de todo el reporte, aqui está toda la información de la base de datos. 
    # lienzo             -   Lienzo, o archivo pdf donde se imprime los diferentes graficos
    # directorio         -   Directorio de trabajo ..\DIA\
    # estaciones_informe -   estaciones que conformen los informes
    # tipo_canal         -   Tipo de canal
    # mapa_              -   Mapa al cual se va a imprimri
    # raiz               -   base de datos XML
    # detalle            -   Averiguar que no me acuerdo
    # banderas           -   Diccionario maestro de banderas del reporte (opcional)
    usar_todas_estaciones = (
        banderas.get('graficar_todas_estaciones_mseed', (mapa_ == 1))
        if isinstance(banderas, dict) else (mapa_ == 1)
    )
    maximos_reporte=[]
    indice=0
    while indice<len(catalogo): #Trabaja sobre el catalogo sísmico generado, incluyendo los reportes de otras redes.
        ####################################################################
        #### SISMOGRAMAS
        ####################################################################
        
        if catalogo[indice]==[] or catalogo[indice][IDX_EVENTO]=='ruta' or str(catalogo[indice][IDX_FUENTE]).strip() in ('Ruido', 'CONTROL'):
            indice=indice+1
            continue
        print("Graficando:  ",catalogo[indice][IDX_EVENTO])
        lienzo.drawString(50,850,'EVENTO: '+catalogo[indice][IDX_EVENTO])
        evento_catalogo=catalogo[indice]  #Variable que tiene la información principal del evento a imprimir, no importa la fuente ni si es reportado o no.
        ayuda=0
        evento_generar=[]   #Uno o mas vectores que tienen los datos para imprimir, sea la RSA, otras redes o los reportados.  Es para montar la información en un solo reporte
        if catalogo[indice][IDX_FUENTE]!='RSA':
            evento_generar.append([])#Si no es de la red, se incrementa un vacio en el generador de de eventos, esto para LA USGS o La IGPEN o los no reportados
            ayuda=1
        evento_generar.append(catalogo[indice])#EL evento a generar se toma del catalogo sísmico.
        evento_catalogo_sis=catalogo[indice][IDX_EVENTO]
        indice_evento=indice
        for j in range(indice+1, len(catalogo)):
            if catalogo[j]==[]:
                continue
            if evento_catalogo_sis==catalogo[j][IDX_EVENTO]:
                evento_generar.append(catalogo[j])
        indice=indice+len(evento_generar)-ayuda
        # En evento _generar se tiene los datos a desplegarse en el reporte, sean de la RSA como de otras redes.
        directorios=obtener_directorios(evento_catalogo_sis)
        archivo_csv=directorio+'/'+directorios['archivo_csv']
        eventos_a_graficar=[]
        evento_tipo_actual = ""
        with open(archivo_csv,newline='') as f:
            eventos_dia=csv.reader(f,delimiter=';',quotechar=';')
            for evento in eventos_dia:
                if evento[1]==evento_catalogo_sis:
                    evento_tipo_actual = str(evento[2]).strip() if len(evento) > 2 else ""
                    if usar_todas_estaciones:
                        #eventos_a_graficar - > marca todas las estaciones con señales mseed
                        eventos_a_graficar=[]
                        for i  in range(0,NUMERO_ESTACIONES):
                            if evento[i+3]!='-':
                                eventos_a_graficar.append(1)
                            else:
                                eventos_a_graficar.append(0)
                    else:
                        #eventos_a_graficar - > marca las estaciones habilitadas en el punto de interés                        
                        eventos_a_graficar=marcar_impresiones(evento,estaciones_informe,tipo_canal,mapa_)
                    break
        if evento_tipo_actual in ('Ruido', 'CONTROL'):
            continue
        trCanal=leer_mseed(directorio+directorios['archivo_referencia'],1)
        contador=0
        n=len(eventos_a_graficar)
        pagina_0 = [0] * n
        pagina_1=[]
        paginamiento_estaciones=[]     #paginamiento_estaciones ----- > Variable para poder graficar de 5 en 5 las hojas del pdf.
        for i in range(0,len(eventos_a_graficar)):
            contador=contador+eventos_a_graficar[i]
            pagina_1.append(eventos_a_graficar[i])
            if contador==5:
                contador=0
                pagina_1=pagina_1+pagina_0[i+1:]
                paginamiento_estaciones.append(pagina_1)
                pagina_1=pagina_0[:i+1]
        paginamiento_estaciones.append(pagina_1)
        
        for i in range(0,len(paginamiento_estaciones)):
            pagina=paginamiento_estaciones[i]
            if i==0:
                bandera_primera_hoja=1
            else:
                bandera_primera_hoja=0
            lienzo=hoja_seniales_(directorio,lienzo,evento_catalogo,evento_generar,evento,pagina,trCanal,raiz,mapa_,detalle,bandera_primera_hoja,banderas=banderas)
        ####################################################################
        #### ACELEROGRAMAS
        ####################################################################
        eventos_a_graficar=marcar_impresiones(evento,estaciones_informe,tipo_canal,mapa_)
        for i in range(0,len(eventos_a_graficar)):
            catalogo_=convertir_lista(catalogo[indice_evento])
            if trCanal[i] and len(trCanal[i]) > 0 and tipo_canal[i]=='ACELEROGRAFICO' and eventos_a_graficar[i]:
                lienzo,maximos=impresion_reporte_acelerograma(lienzo,trCanal[i],i,catalogo_,1)#lienzo,maximos
                if maximos!=[]:
                    xxx=[catalogo[indice_evento][IDX_EVENTO]]
                    xxx.append(maximos)
                maximos_reporte.append(xxx)            
    print("Maximos reporte:",maximos_reporte)
    return maximos_reporte


# ======================================================================================
# 3) Auxiliar: limpiar catálogo para oficiales (excluir dummies "No procesado" del M1)
# ======================================================================================
def _rango_horas_turno(horario: str):
    """
    Devuelve la tupla (hora_ini, hora_fin) cuando 'horario' corresponde a uno
    de los tres turnos operativos ('00:00 - 12:00', '12:00 - 18:00', '18:00 - 24:00').
    Si no aplica filtrado por turno, devuelve None.
    """
    h_limpio = (horario or "").strip()
    if h_limpio == "00:00 - 12:00":
        return 0, 12
    if h_limpio == "12:00 - 18:00":
        return 12, 18
    if h_limpio == "18:00 - 24:00":
        return 18, 24
    return None


def _extraer_hora_evento_sis(evento_id: str):
    """
    Extrae la hora (0..23) desde un identificador de archivo de evento con formato
    'AAMMDD_hhmmss.sis' (17 caracteres) o 'AAAAMMDD_hhmmss.sis' (19 caracteres).
    Usa el desplazamiento desde el final [-10:-8] (compatible con ambos formatos).
    """
    if not evento_id or not isinstance(evento_id, str):
        return None
    texto = Path(evento_id.strip()).name
    try:
        if texto.lower().endswith(".sis") and len(texto) >= 10:
            return int(texto[-10:-8])
        if "_" in texto:
            parte_hora = texto.split("_", 1)[1]
            return int(parte_hora[:2])
    except Exception:
        return None
    return None


def _extraer_hora_fila_catalogo(fila: list):
    """
    Extrae la hora (0..23) de una fila del catálogo priorizando el nombre del
    archivo .sis en fila[IDX_EVENTO] (consistente con la clasificación por turno)
    y usando fila[IDX_HORA] como respaldo.
    """
    if not fila or len(fila) <= IDX_EVENTO:
        return None
    hora_sis = _extraer_hora_evento_sis(str(fila[IDX_EVENTO]))
    if hora_sis is not None:
        return hora_sis
    try:
        return int(float(fila[IDX_HORA]))
    except Exception:
        return None


def _clave_orden_sis(evento_id: str):
    """
    Genera una clave entera cronológica normalizada (AAAAMMDDhhmmss) a partir de
    'AAMMDD_hhmmss.sis' o 'AAAAMMDD_hhmmss.sis' para inserción ordenada.
    """
    if not evento_id:
        return None
    nombre = Path(str(evento_id).strip()).name
    if nombre.lower().endswith(".sis"):
        nombre = nombre[:-4]
    limpio = nombre.replace("_", "").strip()
    if len(limpio) == 12 and limpio.isdigit():
        limpio = "20" + limpio
    try:
        return int(limpio)
    except Exception:
        return None


def construir_catalogo_temporal_turno(
    catalogo: list,
    eventos: list = None,
    horario: str = "",
    insertar_no_procesado: bool = False
) -> list:
    """
    Construye desde cero un catálogo temporal exclusivo para el período/turno
    indicado en 'horario' ('00:00 - 12:00', '12:00 - 18:00', '18:00 - 24:00'),
    sin alterar en ningún momento el catálogo acumulado del día (_cat.csv).

    Incluye:
      1) Únicamente los sismos procesados de 'catalogo' cuya hora pertenece al turno.
      2) Si 'insertar_no_procesado' es True, inserta en orden cronológico los
         eventos del turno en 'eventos' (FF, FC, TELESISMO, INDEFINIDO,
         Evento_local, CONTROL o SISMO pendiente) excluyendo 'Ruido'.
    """
    cabecera_default = [
        "Id", "anio", "mes", "dia", "hora", "min", "seg",
        "lat", "long", "prof", "rms", "e-x", "e-y", "e-0", "e-z",
        "Mag", "Tipo Mag", "Fuente", "ruta", "Ubicacion"
    ]
    if catalogo and len(catalogo) > 0 and isinstance(catalogo[0], list):
        catalogo_temporal = [list(catalogo[0])]
        filas_origen = catalogo[1:]
    else:
        catalogo_temporal = [cabecera_default]
        filas_origen = []

    rango_turno = _rango_horas_turno(horario)

    # 1) Agregar desde cero solo los sismos del turno (o todos si no hay filtro de turno)
    for fila in filas_origen:
        if not fila or len(fila) <= IDX_EVENTO:
            continue
        if rango_turno is not None:
            hora_fila = _extraer_hora_fila_catalogo(fila)
            if hora_fila is None or not (rango_turno[0] <= hora_fila < rango_turno[1]):
                continue
        catalogo_temporal.append(list(fila))

    # 2) Insertar eventos no procesados / no-sismo del turno si corresponde
    if insertar_no_procesado and eventos:
        hora_ini, hora_fin = rango_turno if rango_turno is not None else (0, 24)
        for evento_dia in eventos:
            if not evento_dia or len(evento_dia) < 3:
                continue
            evento_id = str(evento_dia[1]).strip()
            if evento_id in ("Fecha; Hora (UTC)", "Fecha Hora (UTC)", "ruta"):
                continue

            hora_evento = _extraer_hora_evento_sis(evento_id)
            if hora_evento is None or not (hora_ini <= hora_evento < hora_fin):
                continue

            tipo_evento = str(evento_dia[2]).strip()
            if tipo_evento in ("Ruido", "CONTROL"):
                continue

            # Verificar si ya existe en el catálogo temporal (comparando sufijo AAMMDD_hhmmss.sis)
            sufijo_ev = Path(evento_id).name[-17:]
            existe = False
            for fila in catalogo_temporal[1:]:
                if not fila or len(fila) <= IDX_EVENTO:
                    continue
                if fila[IDX_EVENTO] == evento_id or Path(str(fila[IDX_EVENTO])).name[-17:] == sufijo_ev:
                    existe = True
                    break

            if existe:
                continue

            ev_num = _clave_orden_sis(evento_id)
            if ev_num is None:
                continue

            dummy = [
                '00000000000000', '2025', '1', '1', '0', '0', '0',
                '-2.00', '-79.00', '0', 'rms', 'e-x', 'e-y', 'e-0', 'e-z',
                '0', ' ', tipo_evento, evento_id, ' , , '
            ]

            insertado = False
            for i in range(1, len(catalogo_temporal)):
                actual = _clave_orden_sis(catalogo_temporal[i][IDX_EVENTO])
                if actual is None:
                    continue
                if actual >= ev_num:
                    catalogo_temporal.insert(i, dummy)
                    insertado = True
                    break

            if not insertado:
                catalogo_temporal.append(dummy)

    return catalogo_temporal


def _filtrar_catalogo_oficial_sin_dummies(catalogo: list) -> list:
    """
    Devuelve el catálogo sin filas dummy 'No procesado' (id '00000000000000').
    Asume cabecera en catalogo[0].
    """
    if not catalogo:
        return catalogo
    filtrado = [catalogo[0]]
    for fila in catalogo[1:]:
        if not fila:
            continue
        # En tu dummy: fila[0] = '00000000000000'
        if str(fila[0]).strip() == '00000000000000':
            continue
        filtrado.append(fila)
    return filtrado


# ======================================================================================
# 4) Auxiliar: construir catalogo_dia (M2) con dummies locales si corresponde
# ======================================================================================

def _construir_catalogo_diario_para_detalle(catalogo: list, eventos: list) -> list:
    """
    Reproduce tu lógica: para cada 'evento_dia' arma las coincidencias en el catálogo,
    priorizando RSA. Si no hay coincidencias y el evento es FF/FC/INDEFINIDO, agrega dummy local.
    """
    catalogo_dia = []
    if not catalogo or not eventos:
        return catalogo_dia

    eventos_vistos = set()
    # Indices usados repetidamente
    # Asumo constantes ya definidas en tu módulo:
    # IDX_EVENTO, IDX_FUENTE
    for evento_dia in eventos:
        if not evento_dia or len(evento_dia) < 3:
            continue

        evento_id = str(evento_dia[1]).strip()
        if not evento_id.lower().endswith('.sis') or evento_id in eventos_vistos:
            continue
        eventos_vistos.add(evento_id)
        tipo_ev   = str(evento_dia[2]).strip()
        if tipo_ev in ('Ruido', 'CONTROL'):
            continue
        dummy = []
        if tipo_ev in ('FF', 'FC', 'INDEFINIDO'):
            # dummy local (NO contamina el catálogo maestro)
            dummy = ['00000000000000', '2025', '1', '1', '0', '0', '0',
                     '-2.00', '-79.00', '0', 'rms', 'e-x', 'e-y', 'e-0', 'e-z',
                     '0', ' ', 'No procesado', evento_id, ' , , ']

        coincidencias = []
        for fila in catalogo:
            if fila and fila[IDX_EVENTO] == evento_id:
                coincidencias.append(fila)

        if coincidencias:
            # Prioriza RSA primero, luego otras redes
            coincidencias.sort(key=lambda f: 0 if f[IDX_FUENTE] == 'RSA' else 1)
            catalogo_dia.extend(coincidencias)
        else:
            if dummy:
                catalogo_dia.append(dummy)

    return catalogo_dia


def responsables_tiempos_(lienzo, resumen_responsables, modo_reporte, banderas=None):
    """
    Renderiza el cuadro de tiempos por responsable según el modo / banderas:

      - M1 (1) / M2 (2) ('minutos_turno'): por cortes 12H/18H/24H, muestra T(min) por fila.
      - M3 (3) / M4 (4) ('horas_acumuladas'): agregado por responsable, muestra T(horas).
      - M0 / M5 / M6 / M7 ('ninguno'): no imprime nada.

    Estructura esperada en 'resumen_responsables' (una fila por responsable y corte):
      [RESP, CORTE(12H|18H|24H), TOT, SIS, FF, FC, Loc, TEL, IND, Ruido, c3, c4, c5, c6, c7, c8]
    """

    # ===== Robustez de entrada =====
    try:
        _ = iter(resumen_responsables)
    except Exception:
        return lienzo
    if not resumen_responsables:
        return lienzo

    unidad_resp = (
        banderas.get('unidad_responsables')
        if isinstance(banderas, dict) and 'unidad_responsables' in banderas
        else ('minutos_turno' if modo_reporte in (1, 2) else ('horas_acumuladas' if modo_reporte in (3, 4) else 'ninguno'))
    )

    # Modos institucionales o sin responsables no imprimen tiempos
    if unidad_resp == 'ninguno' or modo_reporte in (0, 5, 6, 7):
        return lienzo

    # ===== Único helper: minutos de trabajo a partir de contadores =====
    def calcular_minutos(valores_):
        """
        Política histórica (conservadora):
          T(min) = TOT*60 + c3*300 + c4*600 + c5*1200
        Índices dentro de valores_ (long. 14 esperada):
          0:TOT, 1:SIS, 2:FF, 3:FC, 4:Loc, 5:TEL, 6:IND, 7:Ruido, 8:c3, 9:c4, 10:c5, 11:c6, 12:c7, 13:c8
        """
        try:
            tot = int(valores_[0])
            c3  = int(valores_[8])  if len(valores_) > 8  else 0
            c4  = int(valores_[9])  if len(valores_) > 9  else 0
            c5  = int(valores_[10]) if len(valores_) > 10 else 0
        except Exception:
            return 0
        return tot*1 + c3*5 + c4*10 + c5*20

    # ===== Normalización mínima de filas a 16 columnas =====
    filas_norm = []
    for fila in resumen_responsables:
        base = list(fila)[:16] + ['0'] * max(0, 16 - len(fila))
        nombre = str(base[0]) if base[0] is not None else ''
        corte  = str(base[1]).upper() if isinstance(base[1], str) else str(base[1])
        # vectores numéricos (conversión segura a int)
        vals = []
        for v in base[2:16]:
            try:
                vals.append(int(v))
            except Exception:
                vals.append(0)
        filas_norm.append((nombre, corte, vals))  # (RESP, CORTE, [14 valores])

    # ===== M1/M2: por cortes 12H/18H/24H, en minutos =====
    if unidad_resp == 'minutos_turno' or modo_reporte in (1, 2):
        # Orden 12H→18H→24H
        orden_corte = {'12H': 0, '18H': 1, '24H': 2}
        filas_norm.sort(key=lambda r: (r[0], orden_corte.get(r[1], 99)))

        dibujo = Drawing(460, 180)
        dibujo.add(String(160, 155, 'Resumen de tiempos responsables:', fontSize=14))

        cabecera = ['RESPONSABLE', 'HORA', 'TOT.', 'SIS.', 'FF', 'FC', 'Loc.', 'TEL.', 'IND.', 'T(min)']
        xcols    = [45, 140, 205, 245, 275, 305, 335, 365, 395, 430]
        for j, txt in enumerate(cabecera):
            dibujo.add(String(xcols[j], 140, txt, fontSize=12))

        y = 128
        for nombre, corte, vals in filas_norm:
            tmin = calcular_minutos(vals)
            datos = [nombre, corte, vals[0], vals[1], vals[2], vals[3], vals[4], vals[5], vals[6], round(tmin, 1)]
            for j, item in enumerate(datos):
                dibujo.add(String(xcols[j], y, str(item), fontSize=12))
            y -= 12
            # Paginación simple
            if y < 20:
                dibujo.drawOn(lienzo, 15, 56)
                lienzo.showPage()
                dibujo = Drawing(460, 180)
                dibujo.add(String(160, 155, 'Resumen de tiempos responsables:', fontSize=14))
                for j, txt in enumerate(cabecera):
                    dibujo.add(String(xcols[j], 140, txt, fontSize=12))
                y = 128

        dibujo.drawOn(lienzo, 15, 56)
        return lienzo

    # ===== M3/M4: agregado por responsable, en horas =====
    if unidad_resp == 'horas_acumuladas' or modo_reporte in (3, 4):
        # Agregar por responsable
        acumulado_por_resp = {}  # resp -> ([sumas 14], minutos_totales)
        for nombre, corte, vals in filas_norm:
            tmin = calcular_minutos(vals)
            if nombre not in acumulado_por_resp:
                acumulado_por_resp[nombre] = ([0]*14, 0)
            sumas, tprev = acumulado_por_resp[nombre]
            acumulado_por_resp[nombre] = ([s+a for s, a in zip(sumas, vals)], tprev + tmin)

        dibujo = Drawing(520, 200)
        dibujo.add(String(160, 175, 'Resumen de tiempos invertidos:', fontSize=14))

        cabecera = ['RESPONSABLE', 'TOT.', 'SIS.', 'FF', 'FC', 'Loc.', 'TEL.', 'IND.', 'T(horas)']
        xcols    = [45, 205, 245, 275, 305, 335, 365, 395, 455]
        for j, txt in enumerate(cabecera):
            dibujo.add(String(xcols[j], 160, txt, fontSize=12))

        y = 148
        for nombre in sorted(acumulado_por_resp.keys()):
            vals_sum, tmin = acumulado_por_resp[nombre]
            thoras = round(tmin / 60.0, 2)
            datos = [nombre, vals_sum[0], vals_sum[1], vals_sum[2], vals_sum[3], vals_sum[4], vals_sum[5], vals_sum[6], thoras]
            for j, item in enumerate(datos):
                dibujo.add(String(xcols[j], y, str(item), fontSize=12))
            y -= 12
            # Paginación simple
            if y < 20:
                dibujo.drawOn(lienzo, 15, 400)
                lienzo.showPage()
                dibujo = Drawing(520, 200)
                dibujo.add(String(160, 175, 'Resumen de tiempos invertidos:', fontSize=14))
                for j, txt in enumerate(cabecera):
                    dibujo.add(String(xcols[j], 160, txt, fontSize=12))
                y = 148

        dibujo.drawOn(lienzo, 15, 400)
        return lienzo

    # Cualquier otro caso: no imprime
    return lienzo



# ==========================================================================================
# 5) NUEVA FUNCIÓN: reporte_resumen_modos (núcleo gobernado por 'modo_reporte')
#    - Reemplaza a tu 'reporte_resumen' actual (puedes renombrarla si lo prefieres).
#    - Firma explícita con 'modo_reporte', 'bandera_firma' y 'bandera_relleno' externos.
# ==========================================================================================

def reporte_resumen_modos(
    archivo_pdf: str,
    subtitulo_reporte: str,
    fecha_ini, fecha_fin,
    catalogo: list,
    resumen: list,
    mapa_: int,
    tipo_mapa: int,
    modo_reporte: int,
    estaciones,
    directorio: str,
    arbol,
    resumen_responsables: list,
    eventos: list,
    bandera_firma: bool,
    bandera_relleno: bool,
    horario: str = "",
    poligono_enjambre=None,
    sismo_principal=None
):

    # Mètodo que genera el reporte de resumen en pdf, pudiendo ser de un día o un período entero sin restricción del tiempo
    #
    #
    # archivo_pdf ---es el nombre en extención pdf del archivo ejemplo archivo.pdf
    # subtítulo -----variable string que define el subtítulo a imprimir
    # fecha_ini----- inicio del period del reporte
    # fecha_fin------ fecha de fin del reporte, si es diario, este valor es el mismo que fecha_ini
    # catalogo ------catalogo correspodiente al dia o al periodo                             .
    # resumen -------resumen del día o período, tiene dos formatos, el primero es:
    #                [['DIA', 'SISMO', 'FF', 'FC', 'TELESISMOS', 'Evento_local', 'INDEFINIDO', 'Ruido'],
    #                 ['Total:', 36, 44, 42, 15, 20, 44, 19],
    #                 ['2', '3', '2', '0', '1', '13', '6'],
    #                                   .
    #                                   .
    #                                   .
    #                 ['6', '7', '3', '0', '3', '2', '0']]
    #               
    #
    #                el sigueintes  es:
    #               [0 0 2...6]  donde los dos primeros valores son 0 y los sigueintes son el numero total de eventos procesados por día.
    # mapa_----------Varible para escoger el mapa dado por el archivo mapa.csv
    # tipo_mapa -------Tipo de mapa    0, 1 y 2 con basico, intermnedio y detallado respectivamente
    # banderas-------
    #                es_periodo     ---     bandera que habilita o deshabilita el cuadro resumen, permite usar el mismo método para hacer el reporte diario o el de período 
    #                                       en el reporte   0  no aparecen el cuadro reesumen ni las horas  1 aparece todo
    #                con_detalles   ---     bandera que permite la impresion de los detalles de los reportes. ()
    #                bandera_firma  ---     bandera que habilita o no la impresion para la firma (Nombre del responsable)
    #                
    # estaciones---- estaciones involucradas en le reporte diario, si es período este tiene valor de 0
    # directorio---- direcorio base donde se tomará la información de los días del reporte, usado en periodo.
    # arbol--------- base de datos en xml del periodo de reporte
    # resumen_responsables----
    # eventos        Todos los eventos generados en el día.
    # bandera_relleno Permite el rellono o no de los circulos de los eventos para cierto tipo de reportes.    
    
     
    # 1) BANDERAS MAESTRAS POR MODO + MAPA + OPCIONES DE INTERFAZ
    banderas = derivar_banderas_desde_modo(
        modo_reporte,
        mapa_=mapa_,
        bandera_firma=bandera_firma,
        bandera_relleno=bandera_relleno
    )

    print(
        f"[REPORTE PDF] Archivo: {archivo_pdf}\n"
        f"  -> Modo: {banderas.get('codigo_modo', modo_reporte)} ({banderas.get('nombre_modo', '')})\n"
        f"  -> Destinatario: {banderas.get('para_quien', '')}\n"
        f"  -> Mapa idx: {mapa_} ({banderas.get('nombre_perfil_mapa', '')}) | Subtítulo: {subtitulo_reporte}"
    )

    # 2) MAPA
    datos_mapa      = mapa_configuracion(mapa_, tipo_mapa)
    mapa_despliegue = datos_mapa[0]
    coordenadas     = datos_mapa[1]
    salto           = datos_mapa[2]
    titulo_hoja     = datos_mapa[3]
    estaciones_info = datos_mapa[4]

    # 3) LAYOUT FÍSICO (parche correcto usando tipo_institucional)
    layout = normalizar_layout_por_institucional(banderas['tipo_institucional'])
    tamanio    = layout['tamanio']
    marca_agua = layout['marca_agua']
    pos_x, pos_y = layout['pos_caja']
    tipo_formato = banderas.get('formato_portada', 0)

    # 4) CATÁLOGO DE TRABAJO TEMPORAL (por turno si horario está definido) Y VECTOR DE EVENTOS
    # Si se especifica un turno en 'horario' (M1), se construye un catálogo temporal desde cero
    # únicamente con los sismos de ese turno, sin alterar el catálogo acumulado del día.
    if _rango_horas_turno(horario) is not None:
        catalogo_trabajo = construir_catalogo_temporal_turno(
            catalogo,
            eventos=None,
            horario=horario,
            insertar_no_procesado=False
        )
    else:
        catalogo_trabajo = [list(f) for f in catalogo] if catalogo else []

    vector = []
    if catalogo_trabajo:
        for fila in catalogo_trabajo[1:]:
            if not fila:
                continue
            if str(fila[IDX_INDICE]).strip() == '00000000000000':
                continue
            try:
                lat = float(fila[IDX_LATITUD])
                lon = float(fila[IDX_LONGITUD])
                prf = -1.0 * float(fila[IDX_PROFUNDIDAD])
                mag = float(fila[IDX_MAGNITUD])
            except:
                continue

            ruta = fila[IDX_EVENTO]
            red = 0 if fila[IDX_FUENTE] == "RSA" else 1
            vector.append([lat, lon, prf, mag, red, ruta])

    # 5) CREAR LIENZO + PORTADA
    lienzo = canvas.Canvas(archivo_pdf, pagesize=A4)
    titulo_portada = "SISMICIDAD REGIONAL REGISTRADA"

    lienzo = formato(marca_agua, A4, titulo_portada, subtitulo_reporte, tipo_formato, lienzo)
    lienzo = mapa(lienzo, mapa_despliegue, tamanio, coordenadas, salto, 1)
    if poligono_enjambre is not None:
        lienzo = dibujar_lugar_geometrico_pdf(lienzo, poligono_enjambre, coordenadas, tamanio)
    lienzo = dibujo_sismos_(lienzo, vector, coordenadas, tamanio, mapa_, banderas['es_periodo'], bandera_relleno, banderas=banderas, sismo_principal=sismo_principal)
    lienzo = caja_simbologia(lienzo, resumen, vector, (pos_x, pos_y), mapa_, banderas['es_periodo'], bandera_relleno, banderas=banderas)

    # ========================================================
    #                RAMA PERIODO
    # ========================================================
    if banderas['es_periodo']:

        lienzo = estadistica_(lienzo, resumen, fecha_ini, mapa_, banderas['es_periodo'], banderas=banderas)

        if banderas['incluir_responsables']:
            lienzo.showPage()
            lienzo = responsables_tiempos_(lienzo, resumen_responsables, modo_reporte, banderas=banderas)

        if banderas['insertar_no_procesado'] and banderas['imprimir_detalle']:
            catalogo_trabajo = construir_catalogo_temporal_turno(
                catalogo_trabajo,
                eventos=eventos,
                horario=horario,
                insertar_no_procesado=True
            )

        if banderas['mostrar_tabla_resumen']:

            contador_linea = 0
            loc_centrada = (73,107,122,140,153,171,190,220,245,271,295,320,360)
            localizacion = (46,105,126,142,158,173,188,212,239,268,293,322,350)
            marca_agua_tabla = (120,450,400,200)

            for evento_catalogo in catalogo_trabajo:
                if not evento_catalogo:
                    continue
                if evento_catalogo[19] == ' ':
                    continue

                if contador_linea == 80:
                    contador_linea = 0
                contador_linea += 1
                contador_col = 0

                if contador_linea == 1:
                    lienzo.showPage()
                    lienzo = formato(marca_agua_tabla, A4, titulo_hoja, subtitulo_reporte, 0, lienzo)
                    lienzo.setFont('Helvetica', 7)

                try:
                    magv = float(evento_catalogo[IDX_MAGNITUD])
                    lienzo.setFillColor(colors.blue if magv > 4 else colors.black)
                except:
                    lienzo.setFillColor(colors.black)

                for idx in (0,1,2,3,4,5,6,7,8,9,15,17,19):
                    texto = evento_catalogo[idx]
                    if contador_linea == 1:
                        lienzo.drawString(loc_centrada[contador_col], 740 - contador_linea*8, catalogo_trabajo[0][idx])
                    else:
                        if 5 < contador_col < 9:
                            try:
                                texto = str(round(float(texto),2))
                            except:
                                pass
                        if contador_col == 10:
                            texto = texto + evento_catalogo[idx+1]
                        lienzo.drawString(localizacion[contador_col], 740 - contador_linea*8, texto)
                    contador_col += 1

            if contador_linea > 50:
                lienzo.showPage()
                lienzo = formato(marca_agua_tabla, A4, titulo_hoja, subtitulo_reporte, 0, lienzo)

            lienzo.setFont('Helvetica', 10)
            x, y = 100, 740 - (contador_linea + 20)*8

            if banderas.get('incluir_firma', False):
                lienzo.drawString(x, y, banderas.get('nombre_firmante', "Ing. Remigio Guevara"))

            lienzo.drawString(x, y-10, banderas.get('entidad_firmante', "Red Sísmica del Austro"))

        if banderas['imprimir_detalle']:
            lienzo.showPage()
            if banderas['solo_catalogo_oficial']:
                catalogo_para_detalle = _filtrar_catalogo_oficial_sin_dummies(catalogo_trabajo)
            else:
                catalogo_para_detalle = catalogo_trabajo

            mapa_detalle = mapa_ if banderas['extras_tecnicos'] else 0

            maximos_reporte = imprimir_catalogo(
                catalogo_para_detalle, arbol, lienzo, directorio,
                estaciones_info, parametros_estaciones()['SENSOR'],
                mapa_detalle, arbol.getroot(), tipo_mapa,
                banderas=banderas
            )
        else:
            maximos_reporte = []

    # ========================================================
    #                RAMA DIARIA (M2)
    # ========================================================
    else:

        if banderas['incluir_responsables']:
            lienzo = responsables_tiempos_(lienzo, resumen_responsables, modo_reporte, banderas=banderas)

        if banderas['imprimir_detalle']:
            catalogo_dia = _construir_catalogo_diario_para_detalle(catalogo_trabajo, eventos)

            lienzo.showPage()

            maximos_reporte = imprimir_catalogo(
                catalogo_dia, arbol, lienzo, directorio,
                estaciones_info, parametros_estaciones()['SENSOR'],
                mapa_, arbol.getroot(), tipo_mapa,
                banderas=banderas
            )
        else:
            maximos_reporte = []

    lienzo.save()
    return maximos_reporte


# ============================================================
# 2) Layout compacto vs general (solo posiciones y tamaños)
# ============================================================
def normalizar_layout_por_institucional(tipo_institucional: str):
    """
    Devuelve el layout físico (tamaño del mapa, marca de agua y posición de la
    caja de simbología) según el tipo de institución:

    - FACULTAD  → formato especial (tipo_formato = 2)
    - GADS / ELECAUSTRO / OTRO → formato general
    - NO-INST → formato general
    """

    # Formato general
    layout_general = {
        'tipo_formato': 0,
        'tamanio':      (90, 325, 400, 400),
        'marca_agua':   (200, 100, 200, 95),
        'pos_caja':     (55, 234),
    }

    # Formato Facultad (solo M5)
    layout_facultad = {
        'tipo_formato': 2,
        'tamanio':      (81, 216, 432, 432),
        'marca_agua':   (261, 66, 79, 36),
        'pos_caja':     (85, 109),
    }

    if tipo_institucional == "FACULTAD":
        return layout_facultad

    return layout_general



def normalizar_layout_por_institucional__(es_institucional: bool) -> dict:
    """
    Define posiciones físicas para el mapa, marca de agua y caja de simbología.
    No toca coordenadas de AOI ni estilo (eso viene de mapa_configuracion).
    """
    if not es_institucional:
        # Layout GENERAL (el que usas cuando antes mapa_ != 2/4)
        return {
            'tipo_formato': 0,
            'tamanio': (90, 325, 400, 400),       # xpos, ypos, ancho, alto
            'marca_agua': (200, 100, 200, 95),    # xpos, ypos, ancho, alto
            'pos_caja': (55, 234),                # leyenda/simbología
        }
    else:
        # Layout INSTITUCIONAL (el que usabas para 2/4)
        return {
            'tipo_formato': 2,
            'tamanio': (81, 216, 432, 432),
            'marca_agua': (261, 66, 79, 36),
            'pos_caja': (85, 109),
        }


# =============================================================================
# CATÁLOGO MAESTRO DE PERFILES DE REPORTE (M0 a M7) Y PERFILES DE MAPA/ZONA
# =============================================================================
# Esta tabla centraliza en un único lugar administrativo:
#   1. QUÉ SE IMPRIME (identificación del reporte y módulo de origen)
#   2. PARA QUIÉN SE EMITE (destinatario interno / institucional / difusión)
#   3. QUÉ CONTIENE (portada, estadística, tiempos de responsables, tabla de
#      catálogo, dummies no procesados, firma institucional y hojas de detalle)
#   4. NIVEL DE DIAGNÓSTICO TÉCNICO (cobertura de red, intentos de localización,
#      zoom de onda P, líneas rojas de fases P/S/Coda, cabecera RMS/operador y
#      selección de estaciones a graficar).
# =============================================================================

PERFILES_MODO_REPORTE = {
    # -------------------------------------------------------------------------
    # M0: Portada Cartográfica Especial (Región, Fuentes, Reportes)
    # -------------------------------------------------------------------------
    MODO_MAPA_ESPECIAL: {
        'codigo_modo': 'M0',
        'nombre_modo': 'Portada Cartográfica Especial',
        'para_quien': 'Análisis Cartográfico Interno RSA (Región / Fuentes / Reportes)',
        'origen_habitual': 'reporte_acumulado.py (Zonas: Region, Fuentes, Reportes)',
        'es_periodo': True,
        'tipo_institucional': 'NO-INST',
        'formato_portada': 0,
        'incluir_responsables': False,
        'unidad_responsables': 'ninguno',
        'mostrar_tabla_resumen': False,
        'insertar_no_procesado': False,
        'solo_catalogo_oficial': True,
        'permitir_firma': False,
        'imprimir_detalle': False,
        'extras_tecnicos': False,
    },

    # -------------------------------------------------------------------------
    # M1: Período por Franjas Horarias (00–12, 12–18, 18–24)
    # -------------------------------------------------------------------------
    MODO_PERIODO_FRANJAS: {
        'codigo_modo': 'M1',
        'nombre_modo': 'Control Operativo por Franja Horaria',
        'para_quien': 'Operador de Turno (Revisión pre-salida en Procesamiento Integrado)',
        'origen_habitual': 'procesamiento_integrado.py (Salir_)',
        'es_periodo': True,
        'tipo_institucional': 'NO-INST',
        'formato_portada': 0,
        'incluir_responsables': True,
        'unidad_responsables': 'minutos_turno',
        'mostrar_tabla_resumen': True,
        'insertar_no_procesado': True,
        'solo_catalogo_oficial': False,
        'permitir_firma': False,
        'imprimir_detalle': True,
        'extras_tecnicos': True,
    },

    # -------------------------------------------------------------------------
    # M2: Diario de Revisión Operativa
    # -------------------------------------------------------------------------
    MODO_DIARIO_REVISION: {
        'codigo_modo': 'M2',
        'nombre_modo': 'Reporte Diario de Revisión Sismológica',
        'para_quien': 'Analista / Revisor de la Red Sísmica del Austro (Control Interno)',
        'origen_habitual': 'reporte_diario.py (Guardar_)',
        'es_periodo': False,
        'tipo_institucional': 'NO-INST',
        'formato_portada': 0,
        'incluir_responsables': True,
        'unidad_responsables': 'minutos_turno',
        'mostrar_tabla_resumen': False,
        'insertar_no_procesado': False,
        'solo_catalogo_oficial': False,
        'permitir_firma': False,
        'imprimir_detalle': True,
        'extras_tecnicos': True,
    },

    # -------------------------------------------------------------------------
    # M3: Boletín Oficial Detallado RSA
    # -------------------------------------------------------------------------
    MODO_OFICIAL_DETALLADO: {
        'codigo_modo': 'M3',
        'nombre_modo': 'Boletín Oficial Detallado RSA',
        'para_quien': 'Archivo Técnico Oficial RSA (Catálogo + Responsables + Detalle Completo)',
        'origen_habitual': 'reporte_acumulado.py (Zona: Ecuador + Check Reporte)',
        'es_periodo': True,
        'tipo_institucional': 'NO-INST',
        'formato_portada': 0,
        'incluir_responsables': True,
        'unidad_responsables': 'horas_acumuladas',
        'mostrar_tabla_resumen': True,
        'insertar_no_procesado': False,
        'solo_catalogo_oficial': True,
        'permitir_firma': False,
        'imprimir_detalle': True,
        'extras_tecnicos': True,
    },

    # -------------------------------------------------------------------------
    # M4: Boletín Oficial Resumen RSA
    # -------------------------------------------------------------------------
    MODO_OFICIAL_RESUMEN: {
        'codigo_modo': 'M4',
        'nombre_modo': 'Boletín Oficial Resumen RSA',
        'para_quien': 'Dirección / Archivo Ejecutivo RSA (Catálogo + Responsables, Sin Detalle)',
        'origen_habitual': 'reporte_acumulado.py (Zona: Ecuador sin Check Reporte)',
        'es_periodo': True,
        'tipo_institucional': 'NO-INST',
        'formato_portada': 0,
        'incluir_responsables': True,
        'unidad_responsables': 'horas_acumuladas',
        'mostrar_tabla_resumen': True,
        'insertar_no_procesado': False,
        'solo_catalogo_oficial': True,
        'permitir_firma': False,
        'imprimir_detalle': False,
        'extras_tecnicos': False,
    },

    # -------------------------------------------------------------------------
    # M5: Boletín Resumen Facultad / Difusión
    # -------------------------------------------------------------------------
    MODO_FACULTAD_RESUMEN: {
        'codigo_modo': 'M5',
        'nombre_modo': 'Boletín Institucional Facultad y Redes Sociales',
        'para_quien': 'Facultad de Ingeniería / Difusión Pública y Redes Sociales',
        'origen_habitual': 'reporte_acumulado.py (Zona: Facultad)',
        'es_periodo': True,
        'tipo_institucional': 'FACULTAD',
        'formato_portada': 2,
        'incluir_responsables': False,
        'unidad_responsables': 'ninguno',
        'mostrar_tabla_resumen': False,
        'insertar_no_procesado': False,
        'solo_catalogo_oficial': True,
        'permitir_firma': False,
        'imprimir_detalle': False,
        'extras_tecnicos': False,
    },

    # -------------------------------------------------------------------------
    # M6: Informe Institucional Detallado (GADs / Proyectos / ElecAustro)
    # -------------------------------------------------------------------------
    MODO_INSTITUCIONAL_DETALLADO: {
        'codigo_modo': 'M6',
        'nombre_modo': 'Informe Técnico Institucional Detallado',
        'para_quien': 'Instituciones Externas / Proyectos (ElecAustro, GADs, Embalses)',
        'origen_habitual': 'reporte_acumulado.py (Zonas: Chanlud, Labrado, Austro, etc. + Check Reporte)',
        'es_periodo': True,
        'tipo_institucional': 'GADS',
        'formato_portada': 0,
        'incluir_responsables': False,
        'unidad_responsables': 'ninguno',
        'mostrar_tabla_resumen': True,
        'insertar_no_procesado': False,
        'solo_catalogo_oficial': True,
        'permitir_firma': True,
        'imprimir_detalle': True,
        'extras_tecnicos': False,
    },

    # -------------------------------------------------------------------------
    # M7: Informe Institucional Resumen (GADs / Proyectos / ElecAustro)
    # -------------------------------------------------------------------------
    MODO_INSTITUCIONAL_RESUMEN: {
        'codigo_modo': 'M7',
        'nombre_modo': 'Informe Ejecutivo Institucional Resumen',
        'para_quien': 'Instituciones Externas / Proyectos (Solo Catálogo y Estadística Zonal)',
        'origen_habitual': 'reporte_acumulado.py (Zonas: Chanlud, Labrado, Austro, etc. sin Check Reporte)',
        'es_periodo': True,
        'tipo_institucional': 'GADS',
        'formato_portada': 0,
        'incluir_responsables': False,
        'unidad_responsables': 'ninguno',
        'mostrar_tabla_resumen': True,
        'insertar_no_procesado': False,
        'solo_catalogo_oficial': True,
        'permitir_firma': True,
        'imprimir_detalle': False,
        'extras_tecnicos': False,
    },
}


# =============================================================================
# PERFILES VISUALES Y ESTADÍSTICOS SEGÚN EL MAPA ESCOGIDO (datos/mapas/mapas.csv)
# =============================================================================
# Al escoger el mapa (índice mapa_ en mapas.csv), se determinan las reglas
# cartográficas y de resumen de la portada:
#   - 0 (Region)   : Círculos a mitad de escala, matriz global (Procesados + FF)
#   - 1 (Ecuador)  : Círculos escala normal por profundidad, matriz global
#   - 2 (Facultad) : Todos los sismos en azul, caja compacta, sin gráfico de barras
#   - 3 (Fuentes)  : Halos difuminados concéntricos, matriz global
#   - 4 (Reportes) : Resumen vectorial filtrado, sin gráfico de barras
#   - >=5 (Proyectos: Chanlud, Labrado, Huascachaca, Soldados, Ocana, Austro, etc.):
#                    Círculos por profundidad, resumen vectorial filtrado a la zona
#                    (solo sismos localizados en el polígono) y gráfico de barras zonal.
# =============================================================================

PERFILES_MAPA_ZONA = {
    0: {
        'nombre_perfil_mapa': 'Region (Escala Regional)',
        'escala_circulos': 'mitad',               # r = 1*mag - 2.5
        'estilo_color_sismos': 'por_profundidad', # <40 rojo, 40-70 naranja, >70 azul
        'caja_simbologia_compacta': False,
        'tipo_resumen_estadistico': 'matriz_global',
        'mostrar_grafico_barras': True,
    },
    1: {
        'nombre_perfil_mapa': 'Ecuador (Nacional Oficial)',
        'escala_circulos': 'normal',              # r = 2*mag - 5
        'estilo_color_sismos': 'por_profundidad',
        'caja_simbologia_compacta': False,
        'tipo_resumen_estadistico': 'matriz_global',
        'mostrar_grafico_barras': True,
    },
    2: {
        'nombre_perfil_mapa': 'Facultad (Difusión Institucional)',
        'escala_circulos': 'normal',
        'estilo_color_sismos': 'azul_unico',      # Todos los eventos en azul
        'caja_simbologia_compacta': True,
        'tipo_resumen_estadistico': 'matriz_global',
        'mostrar_grafico_barras': False,
    },
    3: {
        'nombre_perfil_mapa': 'Fuentes Sísmicas (Halos de Energía)',
        'escala_circulos': 'normal',
        'estilo_color_sismos': 'halos_difuminados',
        'caja_simbologia_compacta': True,
        'tipo_resumen_estadistico': 'matriz_global',
        'mostrar_grafico_barras': False,
    },
    4: {
        'nombre_perfil_mapa': 'Reportes (Control Zonal)',
        'escala_circulos': 'normal',
        'estilo_color_sismos': 'por_profundidad',
        'caja_simbologia_compacta': False,
        'tipo_resumen_estadistico': 'vector_filtrado',
        'mostrar_grafico_barras': False,
    },
}

PERFIL_MAPA_PROYECTO_DEFAULT = {
    'nombre_perfil_mapa': 'Proyecto / Institución Zonal (mapas.csv >= 5)',
    'escala_circulos': 'normal',
    'estilo_color_sismos': 'por_profundidad',
    'caja_simbologia_compacta': False,
    'tipo_resumen_estadistico': 'vector_filtrado',
    'mostrar_grafico_barras': True,
}


def obtener_perfil_mapa(mapa_: int, es_periodo: bool = True) -> dict:
    """
    Retorna las banderas visuales y estadísticas asociadas al índice de mapa
    seleccionado en mapas.csv (0..N).
    """
    if mapa_ is None:
        perfil = dict(PERFILES_MAPA_ZONA[1])
    elif mapa_ in PERFILES_MAPA_ZONA:
        perfil = dict(PERFILES_MAPA_ZONA[mapa_])
    else:
        perfil = dict(PERFIL_MAPA_PROYECTO_DEFAULT)

    # En reporte diario (es_periodo == False), el resumen siempre viene como matriz del día
    # y se etiquetan magnitud/hora junto a cada epicentro en el mapa de portada.
    if not es_periodo:
        perfil['tipo_resumen_estadistico'] = 'matriz_global'
        perfil['etiquetar_magnitud_hora_mapa'] = True
    else:
        perfil['etiquetar_magnitud_hora_mapa'] = False

    return perfil


def resolver_modo_por_zona(nombre_zona: str, con_detalle: bool = False) -> int:
    """
    Determina el modo de reporte (M0..M7) en el momento en que el usuario
    escoge el mapa/zona (cmbx_zona) y el check de detalle (ck_box_reporte)
    en el módulo de informes acumulados:
      - 'Region', 'Fuentes', 'Reportes' -> MODO_MAPA_ESPECIAL (0)
      - 'Ecuador'                       -> M3 (con detalle) o M4 (resumen)
      - 'Facultad'                      -> M5 (resumen difusión Facultad)
      - Cualquier proyecto/institución ('Chanlud', 'Labrado', 'Austro', etc.)
                                        -> M6 (con detalle) o M7 (resumen)
    """
    zona_limpia = (nombre_zona or "").strip().lower()

    if zona_limpia in {"region", "región", "fuentes", "reportes"}:
        return MODO_MAPA_ESPECIAL

    if zona_limpia == "ecuador":
        return MODO_OFICIAL_DETALLADO if con_detalle else MODO_OFICIAL_RESUMEN

    if zona_limpia == "facultad":
        return MODO_FACULTAD_RESUMEN

    return MODO_INSTITUCIONAL_DETALLADO if con_detalle else MODO_INSTITUCIONAL_RESUMEN


def derivar_banderas_desde_modo(
    modo_reporte: int,
    mapa_: int = None,
    bandera_firma: bool = False,
    bandera_relleno: bool = True
) -> dict:
    """
    Construye y devuelve el diccionario maestro de banderas que gobierna de forma
    integral y trazable la emisión del reporte PDF.

    Combina:
      1) El perfil del modo de reporte (M0 a M7) desde PERFILES_MODO_REPORTE.
      2) El desglose explícito de las 6 sub-banderas de diagnóstico técnico
         (derivadas de 'extras_tecnicos', pero personalizables individualmente).
      3) El perfil cartográfico y estadístico del mapa escogido (obtener_perfil_mapa).
      4) Los controles interactivos de firma y relleno de símbolos.
    """
    # 1) Plantilla base por defecto (segura para modos no registrados)
    banderas = dict(PERFILES_MODO_REPORTE[MODO_MAPA_ESPECIAL])

    # 2) Aplicar perfil declarativo del modo solicitado
    if modo_reporte in PERFILES_MODO_REPORTE:
        banderas.update(PERFILES_MODO_REPORTE[modo_reporte])

    # 3) Desglose granular de 'extras_tecnicos' para las hojas de detalle de sismos
    #    Si un perfil define explícitamente alguna sub-bandera, se respeta su valor;
    #    de lo contrario, hereda automáticamente de banderas['extras_tecnicos'].
    extras = bool(banderas.get('extras_tecnicos', False))
    subbanderas_extras = (
        'mostrar_cobertura_red',           # Polígonos 50/150 km y triángulos de estaciones
        'mostrar_intentos_proc',           # Nube de intentos previos de localización (_proc.csv)
        'graficar_todas_estaciones_mseed', # Todas las trazas .mseed (True) vs. estaciones del mapa (False)
        'mostrar_zoom_seniales',           # 2 columnas derechas con zoom de onda P (cruda y filtrada)
        'mostrar_lineas_fases',            # Líneas verticales rojas de fases P, S y Coda
        'mostrar_cabecera_interna_rms',    # Cabecera con Responsable del turno y RMS del evento
    )
    for clave_sub in subbanderas_extras:
        banderas.setdefault(clave_sub, extras)

    # 4) Integrar reglas visuales y estadísticas del mapa escogido (mapas.csv)
    perfil_mapa = obtener_perfil_mapa(mapa_, es_periodo=banderas['es_periodo'])
    for clave_m, valor_m in perfil_mapa.items():
        banderas.setdefault(clave_m, valor_m)

    # 5) Opciones de firma institucional, relleno de epicentros y círculos concéntricos
    banderas['bandera_firma'] = bool(bandera_firma)
    banderas['incluir_firma'] = bool(banderas.get('permitir_firma', False) and bandera_firma)
    banderas['nombre_firmante'] = "Ing. Remigio Guevara"
    banderas['entidad_firmante'] = "Red Sísmica del Austro"
    if bandera_relleno in (2, 'concentricos', 'halos_difuminados') or banderas.get('estilo_color_sismos') == 'halos_difuminados':
        banderas['estilo_color_sismos'] = 'halos_difuminados'
        banderas['bandera_relleno'] = False
        # Círculos concéntricos imprime únicamente la primera hoja como en el informe para la Facultad
        banderas['codigo_modo'] = 'M0'
        banderas['nombre_modo'] = 'Portada Cartográfica Especial (Círculos Concéntricos)'
        banderas['es_periodo'] = True
        banderas['tipo_institucional'] = 'FACULTAD'
        banderas['formato_portada'] = 2
        banderas['caja_simbologia_compacta'] = True
        banderas['mostrar_grafico_barras'] = False
        banderas['incluir_responsables'] = False
        banderas['unidad_responsables'] = 'ninguno'
        banderas['mostrar_tabla_resumen'] = False
        banderas['insertar_no_procesado'] = False
        banderas['imprimir_detalle'] = False
        banderas['extras_tecnicos'] = False
        banderas['incluir_firma'] = False
        banderas['etiquetar_magnitud_hora_mapa'] = False
    else:
        banderas['bandera_relleno'] = bool(bandera_relleno)

    return banderas


# ==============================================================================
# 5) REPORTE ESPECIAL EN PDF POR ESTACIONES SELECCIONADAS (SECCIÓN 3)
# ==============================================================================
def imprimir_reporte_especial_estaciones(
    archivo_pdf: str,
    subtitulo_reporte: str,
    catalogo: list,
    tipo_evento_filtro: str,
    indices_estaciones_seleccionadas: list,
    directorio_trabajo: str,
    arbol,
    mapa_: int = 1,
    tipo_mapa: int = 1,
    progreso_callback=None,
    umbral_pga_min: float = 0.0,
    eventos: list = None,
) -> dict:
    """
    Genera un informe completo en PDF (ReportLab) enfocado en las estaciones seleccionadas
    mediante checkboxes en la Sección 3, filtrando los eventos del período que coincidan con
    'tipo_evento_filtro' y que hayan sido registrados por alguna de las estaciones seleccionadas.
    Soporta eventos locales (RSA), eventos de otras redes (IGEPN, USGS) y eventos regionales
    o lejanos clasificados como FF (Fuera de Foco / Franja) o FC (Foco Cercano regional).
    Si 'umbral_pga_min' > 0, filtra de manera estricta excluyendo sismos donde la aceleración
    máxima registrada por los acelerógrafos sea inferior a dicho límite (ej. 0.98 cm/s² = 0.01 g).
    """
    if not indices_estaciones_seleccionadas:
        return {
            'exito': False,
            'mensaje': "Debe seleccionar al menos una estación en los checkboxes.",
            'total_eventos': 0
        }

    indices_set = set(int(x) for x in indices_estaciones_seleccionadas)
    datos_est = parametros_estaciones()
    tipo_canal = datos_est.get('SENSOR', [])
    codigos_est = datos_est.get('CODIGO', [])
    n_estaciones = len(codigos_est)

    raiz = arbol.getroot() if hasattr(arbol, 'getroot') else arbol

    # 1. Agrupar e indexar soluciones del catálogo por sismo (RSA, IGEPN, USGS, etc.)
    mapa_soluciones = {}
    grupos_eventos = []
    evento_actual_sis = None
    grupo_actual = []
    for fila in catalogo[1:]:
        if not fila or len(fila) <= IDX_EVENTO:
            continue
        sis = fila[IDX_EVENTO]
        if sis != evento_actual_sis:
            if grupo_actual:
                grupos_eventos.append(grupo_actual)
            evento_actual_sis = sis
            grupo_actual = [fila]
        else:
            grupo_actual.append(fila)
    if grupo_actual:
        grupos_eventos.append(grupo_actual)

    for g in grupos_eventos:
        s_id = str(g[0][IDX_EVENTO]).strip()
        s_base = os.path.splitext(s_id)[0].replace('_', '')
        if s_base not in mapa_soluciones:
            mapa_soluciones[s_base] = g
        if s_id not in mapa_soluciones:
            mapa_soluciones[s_id] = g

    # 2. Construir lista unificada de candidatos combinando matriz diaria (eventos) y catálogo
    tipo_filtro_limpio = tipo_evento_filtro.strip().upper()
    candidatos = []
    vistos_sis = set()

    # Fuente A: Matriz acumulada de eventos diarios (AAAAMMDD000000.csv) si está disponible
    if eventos:
        for ev_row in eventos:
            if not ev_row or len(ev_row) < 3:
                continue
            sis_id = str(ev_row[1]).strip()
            if not sis_id.lower().endswith('.sis'):
                continue
            sis_base = os.path.splitext(sis_id)[0].replace('_', '')
            if sis_base in vistos_sis:
                continue
            vistos_sis.add(sis_base)

            tipo_ev_real = str(ev_row[2]).strip()
            if tipo_filtro_limpio != 'TODOS' and tipo_ev_real.upper() != tipo_filtro_limpio:
                continue

            grupo = mapa_soluciones.get(sis_base) or mapa_soluciones.get(sis_id)
            if not grupo:
                try:
                    utc_ev = obtencion_hora(sis_id)
                    anio_s = f"{utc_ev.year:04d}"
                    mes_s = f"{utc_ev.month:02d}"
                    dia_s = f"{utc_ev.day:02d}"
                    hora_s = f"{utc_ev.hour:02d}"
                    min_s = f"{utc_ev.minute:02d}"
                    seg_s = f"{utc_ev.second + utc_ev.microsecond / 1e6:04.1f}"
                except Exception:
                    anio_s, mes_s, dia_s, hora_s, min_s, seg_s = "2026", "01", "01", "00", "00", "0.0"

                fila_sintetica = [
                    sis_id,          # 0: IDX_INDICE
                    anio_s,          # 1: IDX_ANIO
                    mes_s,           # 2: IDX_MES
                    dia_s,           # 3: IDX_DIA
                    hora_s,          # 4: IDX_HORA
                    min_s,           # 5: IDX_MINUTO
                    seg_s,           # 6: IDX_SEGUNDO
                    "0.0",           # 7: IDX_LATITUD
                    "0.0",           # 8: IDX_LONGITUD
                    "0.0",           # 9: IDX_PROFUNDIDAD
                    "0.0",           # 10: IDX_RMS
                    "0.0",           # 11: IDX_E_X
                    "0.0",           # 12: IDX_E_Y
                    "0.0",           # 13: IDX_E_0
                    "0.0",           # 14: IDX_E_Z
                    "0.0",           # 15: IDX_MAGNITUD
                    "",              # 16: IDX_UNIDAD_MAG
                    tipo_ev_real,    # 17: IDX_FUENTE (FF, FC, etc.)
                    sis_id,          # 18: IDX_EVENTO
                    f"Evento {tipo_ev_real}" # 19: IDX_LUGAR
                ]
                grupo = [fila_sintetica]

            candidatos.append({
                'sis_id': sis_id,
                'grupo': grupo,
                'fila_csv': ev_row
            })

    # Fuente B: Catálogo hipocentral (para sismos no presentes en eventos o si eventos es None)
    for grupo in grupos_eventos:
        sis_id = grupo[0][IDX_EVENTO]
        sis_base = os.path.splitext(sis_id)[0].replace('_', '')
        if sis_base in vistos_sis:
            continue
        vistos_sis.add(sis_base)

        ruta_sismo = os.path.join(directorio_trabajo, sis_id)
        directorios = obtener_directorios(ruta_sismo)
        if not os.path.exists(directorios.get('Directorio_base', '')):
            ruta_sismo_dia = os.path.join(directorio_trabajo, 'DIA', sis_id)
            directorios_dia = obtener_directorios(ruta_sismo_dia)
            if os.path.exists(directorios_dia.get('Directorio_base', '')):
                directorios = directorios_dia
                ruta_sismo = ruta_sismo_dia

        cand_csv = [
            directorios.get('archivo_csv', ''),
            os.path.join(directorio_trabajo, os.path.basename(directorios.get('archivo_csv', ''))),
            os.path.join(directorio_trabajo, 'DIA', os.path.basename(directorios.get('archivo_csv', ''))),
            os.path.join(directorio_trabajo, directorios.get('archivo_csv', '').lstrip('/\\')),
            os.path.join(directorio_trabajo, 'DIA', directorios.get('archivo_csv', '').lstrip('/\\')),
        ]
        ruta_csv = None
        for c in cand_csv:
            if c and os.path.isfile(c):
                ruta_csv = c
                break
        if not ruta_csv:
            continue

        evento_csv_fila = None
        try:
            with open(ruta_csv, newline='', encoding='latin-1', errors='replace') as f:
                lector = csv.reader(f, delimiter=';')
                for row in lector:
                    if len(row) > 2:
                        id_fila = str(row[1]).strip()
                        id_fila_limpio = os.path.splitext(id_fila)[0].replace('_', '')
                        if id_fila == sis_id or id_fila_limpio == sis_base:
                            evento_csv_fila = row
                            break
        except Exception:
            continue

        if not evento_csv_fila:
            continue

        tipo_ev_real = str(evento_csv_fila[2]).strip()
        if tipo_filtro_limpio != 'TODOS' and tipo_ev_real.upper() != tipo_filtro_limpio:
            continue

        candidatos.append({
            'sis_id': sis_id,
            'grupo': grupo,
            'fila_csv': evento_csv_fila
        })

    # 3. Filtrar candidatos por aporte instrumental de estaciones seleccionadas y aceleración mínima
    eventos_calificados = []

    for cand in candidatos:
        sis_id = cand['sis_id']
        grupo = cand['grupo']
        evento_csv_fila = cand['fila_csv']

        # Identificar estaciones seleccionadas que aportaron ('1' en posición 5)
        candidatas_aporte = []
        for idx in indices_set:
            if idx + 3 < len(evento_csv_fila):
                token = evento_csv_fila[idx + 3].strip()
                if len(token) > 5 and token[5] == '1':
                    candidatas_aporte.append(idx)

        if not candidatas_aporte:
            continue

        # Resolver directorios completos del evento
        ruta_sismo = os.path.join(directorio_trabajo, sis_id)
        directorios = obtener_directorios(ruta_sismo)
        if not os.path.exists(directorios.get('Directorio_base', '')):
            ruta_sismo_dia = os.path.join(directorio_trabajo, 'DIA', sis_id)
            directorios_dia = obtener_directorios(ruta_sismo_dia)
            if os.path.exists(directorios_dia.get('Directorio_base', '')):
                directorios = directorios_dia
                ruta_sismo = ruta_sismo_dia

        # Si se especificó umbral_pga_min > 0, evaluar aceleración real de las estaciones acelerográficas
        estaciones_con_registro = []
        trCanal_precarga = None

        hay_acel_candidata = any(
            idx < len(tipo_canal) and tipo_canal[idx] == 'ACELEROGRAFICO'
            for idx in candidatas_aporte
        )

        if hay_acel_candidata and umbral_pga_min > 0.0:
            try:
                trCanal_precarga = leer_mseed(ruta_sismo, 1)
                if not any(trCanal_precarga):
                    trCanal_precarga = leer_mseed(os.path.join(directorio_trabajo, 'DIA', sis_id), 1)
            except Exception:
                trCanal_precarga = None

        if umbral_pga_min > 0.0:
            acel_que_superan = []
            for idx in candidatas_aporte:
                es_acel = (idx < len(tipo_canal) and tipo_canal[idx] == 'ACELEROGRAFICO')
                if es_acel:
                    pga_est = 0.0
                    if trCanal_precarga and idx < len(trCanal_precarga) and trCanal_precarga[idx]:
                        try:
                            factor = float(datos_est['FACTOR_MUL'][idx])
                        except Exception:
                            factor = 1.0
                        for ch in trCanal_precarga[idx][:3]:
                            try:
                                sen = correccion(ch, factor)
                                acel = sen[0]
                                if len(acel) > 0:
                                    max_c = max(abs(float(np.max(acel))), abs(float(np.min(acel))))
                                    if max_c > pga_est:
                                        pga_est = max_c
                            except Exception:
                                pass
                    if pga_est >= umbral_pga_min:
                        acel_que_superan.append(idx)

            # Si se activó el filtro de aceleración y ningún acelerógrafo superó el umbral, se descarta el sismo
            if not acel_que_superan:
                continue

            # Agregar acelerógrafos calificados y estaciones sísmicas aportantes
            for idx in candidatas_aporte:
                es_acel = (idx < len(tipo_canal) and tipo_canal[idx] == 'ACELEROGRAFICO')
                if es_acel:
                    if idx in acel_que_superan:
                        estaciones_con_registro.append(idx)
                else:
                    estaciones_con_registro.append(idx)
        else:
            estaciones_con_registro = list(candidatas_aporte)

        # Si ninguna estación cumplió el criterio en este evento, no se califica el sismo
        if estaciones_con_registro:
            eventos_calificados.append({
                'sis_id': sis_id,
                'grupo': grupo,
                'fila_csv': evento_csv_fila,
                'estaciones_registro': estaciones_con_registro,
                'directorios': directorios,
                'ruta_sismo': ruta_sismo,
                'trCanal': trCanal_precarga
            })

    if not eventos_calificados:
        detalle_umb = f" con aceleración ≥ {umbral_pga_min:.2f} cm/s²" if umbral_pga_min > 0 else ""
        return {
            'exito': False,
            'mensaje': (
                f"No se encontraron eventos clasificados como '{tipo_evento_filtro}' "
                f"donde las estaciones seleccionadas figuren como APORTANTES{detalle_umb}."
            ),
            'total_eventos': 0
        }

    # 3. Configurar banderas maestras en modo limpio para informe por estaciones
    banderas = {
        'codigo_modo': 'M_ESTACIONES',
        'nombre_modo': 'Reporte Especial por Estaciones',
        'es_periodo': True,
        'imprimir_detalle': True,
        'mostrar_cobertura_red': False,
        'mostrar_intentos_proc': False,
        'mostrar_zoom_seniales': False,        # Sin zoom P/S
        'mostrar_lineas_fases': False,         # Sin marcas de arribo P, S ni Coda
        'mostrar_cabecera_interna_rms': False, # Sin cabecera técnica con responsable ni RMS
        'graficar_todas_estaciones_mseed': False,
        'tipo_institucional': 'OFICIAL',
        'formato_portada': 1,
        'bandera_relleno': True,
    }

    # 4. Iniciar documento ReportLab
    os.makedirs(os.path.dirname(os.path.abspath(archivo_pdf)), exist_ok=True)
    lienzo = canvas.Canvas(archivo_pdf, pagesize=A4)

    # 5. Portada inicial con mapa cartográfico y lista de sismos calificados
    datos_mapa = mapa_configuracion(mapa_, tipo_mapa)
    mapa_despliegue = datos_mapa[0]
    coordenadas = datos_mapa[1]
    salto = datos_mapa[2]
    estaciones_info = datos_mapa[4]

    layout = normalizar_layout_por_institucional(banderas['tipo_institucional'])
    tamanio = layout['tamanio']
    marca_agua = layout['marca_agua']
    pos_x, pos_y = layout['pos_caja']

    vector_sismos = []
    for ev in eventos_calificados:
        fila_cat = ev['grupo'][0]
        try:
            lat = float(fila_cat[IDX_LATITUD])
            lon = float(fila_cat[IDX_LONGITUD])
            prf = -1.0 * float(fila_cat[IDX_PROFUNDIDAD])
            mag = float(fila_cat[IDX_MAGNITUD])
            red = 0 if fila_cat[IDX_FUENTE] == "RSA" else 1
            vector_sismos.append([lat, lon, prf, mag, red, fila_cat[IDX_EVENTO]])
        except (ValueError, IndexError):
            continue

    titulo_portada = "REPORTE SISMOLÓGICO ESPECIAL POR ESTACIONES"
    nombres_sel = [f"{codigos_est[i]}" for i in sorted(indices_set) if i < len(codigos_est)]
    subtitulo_completo = f"{subtitulo_reporte}  |  Estaciones: {', '.join(nombres_sel[:8])}{'...' if len(nombres_sel) > 8 else ''}"

    lienzo = formato(marca_agua, A4, titulo_portada, subtitulo_completo, 1, lienzo)
    lienzo = mapa(lienzo, mapa_despliegue, tamanio, coordenadas, salto, 1)
    if vector_sismos:
        lienzo = dibujo_sismos_(lienzo, vector_sismos, coordenadas, tamanio, mapa_, True, True, banderas=banderas)

    # Simbología oficial estándar en la portada
    resumen_caja = [
        ["DIA", "SISMO", "FF", "FC", "TELESISMO", "Evento Local", "INDEFINIDO", "Ruido"],
        ["Total:", len(vector_sismos), 0, 0, 0, 0, 0, 0]
    ]
    lienzo = caja_simbologia(lienzo, resumen_caja, vector_sismos, (pos_x, pos_y), mapa_, True, True, banderas=banderas)
    lienzo.showPage()

    # 5.1 Catálogo / Lista completa de sismos calificados (formato tabular estándar RSA)
    filas_por_pagina = 38
    total_eventos_calificados = len(eventos_calificados)
    total_paginas_lista = max(1, (total_eventos_calificados - 1) // filas_por_pagina + 1)
    marca_agua_tabla = (120, 450, 400, 200)

    for idx_fila, ev in enumerate(eventos_calificados):
        num_en_pag = idx_fila % filas_por_pagina
        if num_en_pag == 0:
            if idx_fila > 0:
                lienzo.showPage()
            pag_actual = (idx_fila // filas_por_pagina) + 1
            sub_tabla = f"{subtitulo_reporte}  (Página {pag_actual} de {total_paginas_lista})"
            lienzo = formato(marca_agua_tabla, A4, "CATÁLOGO DE EVENTOS SÍSMICOS REGISTRADOS", sub_tabla, 0, lienzo)

            # Encabezado de la tabla tabular
            y_enc = 740
            lienzo.setFillColor(colors.HexColor('#E8ECEF'))
            lienzo.rect(40, y_enc - 5, 515, 17, fill=True, stroke=False)

            lienzo.setFont('Helvetica-Bold', 7.5)
            lienzo.setFillColor(colors.HexColor('#1A2530'))
            lienzo.drawString(45, y_enc, "N°")
            lienzo.drawString(62, y_enc, "Identificador (.sis)")
            lienzo.drawString(155, y_enc, "Fecha (UTC)")
            lienzo.drawString(212, y_enc, "Hora (UTC)")
            lienzo.drawString(268, y_enc, "Lat (°)")
            lienzo.drawString(308, y_enc, "Lon (°)")
            lienzo.drawString(348, y_enc, "Prof(km)")
            lienzo.drawString(392, y_enc, "Mag(Md)")
            lienzo.drawString(435, y_enc, "Fuente")
            lienzo.drawString(475, y_enc, "Estaciones Aporte")

            lienzo.setStrokeColor(colors.HexColor('#4A6984'))
            lienzo.setLineWidth(0.8)
            lienzo.line(40, y_enc - 6, 555, y_enc - 6)

        y_pos = 722 - num_en_pag * 15.5
        f_cat = ev['grupo'][0]

        # Sombreado alternado de filas para máxima legibilidad
        if num_en_pag % 2 == 1:
            lienzo.setFillColor(colors.HexColor('#F8F9FA'))
            lienzo.rect(40, y_pos - 4, 515, 14.5, fill=True, stroke=False)

        # Destacar magnitud en azul si es relevante (>= 4.0) o guión si no aplica
        try:
            mag_num = float(f_cat[IDX_MAGNITUD])
            if mag_num > 0.0:
                color_mag = colors.blue if mag_num >= 4.0 else colors.black
                txt_mag = f"{mag_num:.1f}"
            else:
                color_mag = colors.black
                txt_mag = "-"
        except Exception:
            color_mag = colors.black
            txt_mag = "-"

        lienzo.setFont('Helvetica', 7.5)
        lienzo.setFillColor(colors.black)
        lienzo.drawString(45, y_pos, str(idx_fila + 1))
        lienzo.drawString(62, y_pos, str(f_cat[IDX_EVENTO])[:16])

        fecha_str = f"{f_cat[IDX_DIA]}/{f_cat[IDX_MES]}/{f_cat[IDX_ANIO]}"
        try:
            seg_f = round(float(f_cat[IDX_SEGUNDO]), 1)
            hora_str = f"{f_cat[IDX_HORA]}:{f_cat[IDX_MINUTO]}:{seg_f:04.1f}"
        except Exception:
            hora_str = f"{f_cat[IDX_HORA]}:{f_cat[IDX_MINUTO]}:{f_cat[IDX_SEGUNDO]}"

        lienzo.drawString(155, y_pos, fecha_str)
        lienzo.drawString(212, y_pos, hora_str)
        try:
            lat_f = float(f_cat[IDX_LATITUD])
            lon_f = float(f_cat[IDX_LONGITUD])
            prof_f = float(f_cat[IDX_PROFUNDIDAD])
            if abs(lat_f) > 0.001 or abs(lon_f) > 0.001:
                txt_lat = f"{lat_f:.3f}"
                txt_lon = f"{lon_f:.3f}"
                txt_prof = f"{prof_f:.1f}"
            else:
                txt_lat = "-"
                txt_lon = "-"
                txt_prof = "-"
        except Exception:
            txt_lat = "-"
            txt_lon = "-"
            txt_prof = "-"

        lienzo.drawString(268, y_pos, txt_lat)
        lienzo.drawString(308, y_pos, txt_lon)
        lienzo.drawString(348, y_pos, txt_prof)

        lienzo.setFillColor(color_mag)
        lienzo.drawString(392, y_pos, txt_mag)
        lienzo.setFillColor(colors.black)

        fuente_rep = str(f_cat[IDX_FUENTE]).strip()
        if not fuente_rep or fuente_rep == "No procesado":
            fuente_rep = str(ev['fila_csv'][2]).strip()
        lienzo.drawString(435, y_pos, fuente_rep)

        # Códigos de las estaciones seleccionadas que aportaron
        cods_aporte = [codigos_est[i] for i in ev['estaciones_registro'] if i < len(codigos_est)]
        str_est = ', '.join(cods_aporte[:4]) + ('...' if len(cods_aporte) > 4 else '')
        lienzo.drawString(475, y_pos, str_est)

    lienzo.showPage()

    # 6. Renderizar cada evento con ficha de sismo, señales limpias y acelerogramas
    total_ev = len(eventos_calificados)
    acelerogramas_recolectados = []
    for idx_ev, ev in enumerate(eventos_calificados):
        if progreso_callback:
            progreso_callback(idx_ev + 1, total_ev, ev['sis_id'])

        grupo = ev['grupo']
        evento_catalogo = grupo[0]
        evento_csv = ev['fila_csv']
        directorios = ev['directorios']
        estaciones_con_reg = ev['estaciones_registro']

        # Estructurar evento_generar (RSA + externas)
        evento_generar = []
        if evento_catalogo[IDX_FUENTE] != 'RSA':
            evento_generar.append([])
        evento_generar.extend(grupo)

        # Leer trazas mseed del evento (o reutilizar precarga si ya se leyó)
        trCanal = ev.get('trCanal')
        if not trCanal or not any(trCanal):
            ruta_sismo_mseed = ev.get('ruta_sismo') or os.path.join(directorio_trabajo, ev['sis_id'])
            try:
                trCanal = leer_mseed(ruta_sismo_mseed, 1)
                if not any(trCanal):
                    trCanal = leer_mseed(os.path.join(directorio_trabajo, 'DIA', ev['sis_id']), 1)
            except Exception:
                trCanal = [[] for _ in range(max(n_estaciones, NUMERO_ESTACIONES))]

        # Vector de máscara: solo 1 en las estaciones seleccionadas que fueron APORTANTES ('1') y tienen traza
        eventos_a_graficar = [0] * max(n_estaciones, NUMERO_ESTACIONES)
        for idx in estaciones_con_reg:
            if idx < len(eventos_a_graficar):
                token = evento_csv[idx + 3].strip() if idx + 3 < len(evento_csv) else ""
                if len(token) > 5 and token[5] == '1':
                    if trCanal and idx < len(trCanal) and trCanal[idx] and len(trCanal[idx]) > 0:
                        eventos_a_graficar[idx] = 1

        estaciones_sismicas = [
            i for i in range(len(eventos_a_graficar))
            if eventos_a_graficar[i] == 1 and i < len(tipo_canal) and tipo_canal[i] == 'SISMICO'
        ]
        estaciones_acelerograficas = [
            i for i in range(len(eventos_a_graficar))
            if eventos_a_graficar[i] == 1 and i < len(tipo_canal) and tipo_canal[i] == 'ACELEROGRAFICO'
        ]

        # Paginamiento de 5 en 5 para estaciones sísmicas
        paginamiento_seniales = []
        pagina_parcial = [0] * len(eventos_a_graficar)
        contador_pag = 0
        for i in estaciones_sismicas:
            pagina_parcial[i] = 1
            contador_pag += 1
            if contador_pag == 5:
                paginamiento_seniales.append(pagina_parcial)
                pagina_parcial = [0] * len(eventos_a_graficar)
                contador_pag = 0
        if contador_pag > 0:
            paginamiento_seniales.append(pagina_parcial)

        # Imprimir hojas de sismo y señales
        if paginamiento_seniales:
            for num_hoja, pag in enumerate(paginamiento_seniales):
                es_primera = 1 if num_hoja == 0 else 0
                lienzo = hoja_seniales_(
                    directorio_trabajo,
                    lienzo,
                    evento_catalogo,
                    evento_generar,
                    evento_csv,
                    pag,
                    trCanal,
                    raiz,
                    mapa_,
                    tipo_mapa,
                    es_primera,
                    banderas=banderas
                )
        else:
            # Si solo hubo estaciones acelerográficas, se imprime la ficha del sismo sola
            lienzo = impresion_reporte_sismo(
                lienzo,
                evento_generar,
                eventos_a_graficar,
                trCanal,
                1,
                directorio_trabajo,
                mapa_,
                banderas=banderas
            )
            lienzo.showPage()

        # Imprimir acelerogramas para las estaciones acelerográficas seleccionadas
        for idx_acel in estaciones_acelerograficas:
            catalogo_fila = convertir_lista(evento_catalogo)
            lienzo, maximos = impresion_reporte_acelerograma(
                lienzo,
                trCanal[idx_acel],
                idx_acel,
                catalogo_fila,
                1
            )
            if maximos and len(maximos) > 1:
                acelerogramas_recolectados.append([evento_catalogo[IDX_EVENTO], maximos])

    lienzo.save()

    # Generación complementaria del archivo CSV de aceleraciones máximas (_aceleraciones.csv)
    ruta_csv_aceleraciones = os.path.splitext(archivo_pdf)[0] + "_aceleraciones.csv"
    registro_acel = [
        ['Evento', 'Estación', 'Canal 0', '', '', 'Canal 1', '', '', 'Canal 2', '', ''],
        ['', '', 'Acel. max', 'Vel. max', 'Desp. max', 'Acel. max', 'Vel. max', 'Desp. max', 'Acel. max', 'Vel. max', 'Desp. max']
    ]
    for ev_acel in acelerogramas_recolectados:
        linea = [ev_acel[0]]
        for i, estacion_max in enumerate(ev_acel[1]):
            if i == 0:
                cod_est = codigos_est[estacion_max] if estacion_max < len(codigos_est) else str(estacion_max)
                linea.append(cod_est)
            else:
                for k in range(1, 4):
                    if isinstance(estacion_max, (list, tuple)) and k < len(estacion_max):
                        linea.append(str(estacion_max[k]))
                    else:
                        linea.append('')
        registro_acel.append(linea)

    csv_generado = None
    if len(registro_acel) > 2:
        try:
            with open(ruta_csv_aceleraciones, 'w', newline='', encoding='utf-8') as f_csv:
                escritor = csv.writer(f_csv, delimiter=';')
                for f in registro_acel:
                    escritor.writerow(f)
            csv_generado = ruta_csv_aceleraciones
        except Exception as e_csv:
            print(f"Error escribiendo CSV de aceleraciones: {e_csv}")

    return {
        'exito': True,
        'archivo_pdf': archivo_pdf,
        'total_eventos': total_ev,
        'ruta_csv_aceleraciones': csv_generado,
        'mensaje': f"Reporte PDF por estaciones generado exitosamente ({total_ev} eventos incluidos)."
    }








