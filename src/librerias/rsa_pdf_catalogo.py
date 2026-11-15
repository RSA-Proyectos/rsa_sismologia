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
ruta_proyecto=extraer_hasta_directorio(ruta_librerias, 'rsa_sismologia')
ruta_librerias = os.path.abspath(os.path.join(ruta_proyecto, 'src','librerias'))
ruta_datos = os.path.abspath(os.path.join(ruta_proyecto, 'datos'))

# Insertar la ruta al inicio del sys.path
if ruta_librerias not in sys.path:
    sys.path.insert(0, ruta_librerias)
if ruta_datos not in sys.path:
    sys.path.insert(0, ruta_datos)

from rsa_io import leer_mseed
from rsa_dominio import convertir_lista
from rsa_pdf_reportes import impresion_reporte_acelerograma,hoja_seniales_

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







