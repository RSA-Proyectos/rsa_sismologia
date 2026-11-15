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
ruta_datos = os.path.abspath(os.path.join(ruta_proyecto,'datos'))
# Insertar la ruta al inicio del sys.path
if ruta_librerias not in sys.path:
    sys.path.insert(0, ruta_librerias)

import re
from PyQt5.QtWidgets import QMessageBox
import matplotlib
matplotlib.use('Qt5Agg')  # Asegúrate de que esto está antes de importar matplotlib.pyplot
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator    
import subprocess
from obspy import Trace, Stream
from datetime import datetime, timedelta
import sys
import os
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd

# metodos_rsa.py (archivo puente temporal)

#from rsa_io import leer_mseed,conversion_mseed,lectura_resumen,lectura_archivo,escritura_archivo,copiar_archivos,num_reportes,Guardar_dia,extraer_hasta_directorio,lectura_eventos
#from rsa_dominio import correccion,calidad_estacion,obtenerTraza,punto_fijo_a_punto_flotante,convertir_lista,decimal_a_hexadecimal,obtener_caracter_hexadecimal,intervalo_reporte
#from rsa_procesamiento import lectura_rsa,archivos_fast,verificar_coincidencias,guardar_intento,guardar_informacion_diaria,ordenar_y_eliminar_duplicados,extraer_dia,espectro_respuesta
#from rsa_utilidades import extraccion,codigos,loc_cabecera,binario_a_mseed,referencia_directorio_completa,ubicacion,agregar_evento,obtener_datos_reporte,generar_directorios_unidades_basicas,extraccion_dato

#from rsa_io import *
#from rsa_dominio import *
#from rsa_procesamiento import *

from rsa_io import leer_mseed,lectura_archivo,escritura_archivo
from rsa_procesamiento import lectura_rsa,ordenar_y_eliminar_duplicados
from metodos_gestion import parametros_estaciones,obtener_directorios
from rsa_utilidades import agregar_evento,ubicacion,extraccion_dato



IDX_INDICE,IDX_ANIO,IDX_MES,IDX_DIA,IDX_HORA,IDX_MINUTO,IDX_SEGUNDO,\
IDX_LATITUD,IDX_LONGITUD,IDX_PROFUNDIDAD,IDX_RMS,IDX_E_X,IDX_E_Y,IDX_E_0,\
IDX_E_Z,IDX_MAGNITUD,IDX_UNIDAD_MAG,\
IDX_FUENTE,IDX_EVENTO,IDX_LUGAR = 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19




def grafico_evento_int(visor, stLeido, t_inicio, t_final, estaciones_evento, hab_grafico, bandera_marcas, pagina):
    #visor   es la ventana donde se grafica
    #stLeido es la traza donde se encuetra el Mseed de la estaciòn
    #t_inicio----- incio del perido del grafico
    #t_final------ fin del perido del grafico
    #estaciones_evento---Estaciones que están marcadas con el contenido del evento en extraer  
    #hab_grafico---- Vector con la habilitacion de los graficos desde el archivo de configuracion 
    #bandera_marcas---- Permite ver las marcas para la extraccion
    #pagina-------- Variable que genera paginas para el despliegue, son de 6 en 6.
    # Limpiar la figura existente
    visor.clear()
    # Crear subplots dentro de la figura existente
    ax = [visor.add_subplot(6, 1, i+1) for i in range(6)]
    minorLocator = MultipleLocator(320)
    
    # Código original para preparar los datos y las marcas...

    parametros = parametros_estaciones()  # (nombre_canal_total_, nombre_canal, tipo_canal_, n_canales_, hab_canal, componente_canal, grafico_)
    estaciones_graficar = []
    st_graficar = []

    for kk in range(len(stLeido)):
        if stLeido[kk] != []:
            st_tiempo = stLeido[kk][0].stats.starttime
            break

    for i in range(pagina * 6, pagina * 6 + 6):
        if i < len(estaciones_evento):
            canal_ = int(estaciones_evento[i])
            comp_ = int(parametros['COMPONENTE'][canal_]) - 1
            estaciones_graficar.append(canal_)
            st_graficar.append(stLeido[canal_][comp_])

    t = st_graficar[0].stats.starttime  # Obtención de la referencia del tiempo
    if t == t_inicio:
        t_i = t_inicio
        t_f = t_final
    else:
        t_i = t + t_inicio
        t_f = t + t_final

    for i in range(len(st_graficar)):
        st_graficar[i].trim(t_i, t_f)  # Aquí la trama, sobre esta hay que trabajar filtros, corrección de línea de base, etc.
        st_graficar[i].detrend('linear')  # Hace la corrección de línea de base lineal

    anio_ = st_graficar[0].stats.starttime.year
    mes_ = st_graficar[0].stats.starttime.month
    dia_ = st_graficar[0].stats.starttime.day
    hora_ = st_graficar[0].stats.starttime.hour
    minuto_ = st_graficar[0].stats.starttime.minute
    segundo_ = st_graficar[0].stats.starttime.second
    tiempo_inicio = datetime(anio_, mes_, dia_, hora_, minuto_, segundo_)
    marca_1 = tiempo_inicio + timedelta(seconds=420)
    marca_2 = tiempo_inicio + timedelta(seconds=780)
    marca_0 = tiempo_inicio + timedelta(seconds=60)

    # Preparar los datos para el gráfico
    for i in range(6):
        try:
            canal_ = estaciones_graficar[5 - i]
            componente_graficar = int(parametros['COMPONENTE'][canal_]) - 1

            ax[i].plot(stLeido[canal_][componente_graficar].times("matplotlib"), st_graficar[5 - i].data, "b-", linewidth=0.8)
            ax[i].set_title(parametros['NOMBRE'][canal_], fontsize=8, pad=2)
            ax[i].tick_params(axis='both', which='major', labelsize=7, pad=1)
            if bandera_marcas:
                ax[i].axvline(marca_0, color="red")
                ax[i].axvline(marca_1, color="green")
                ax[i].axvline(marca_2, color="green")
            ax[i].xaxis.set_minor_locator(minorLocator)
            ax[i].get_yaxis().set_visible(False)
            ax[i].grid(which='minor')
            ax[i].grid(True)
            ax[i].xaxis_date()
        except IndexError:
            pass

    visor.autofmt_xdate()
    visor.subplots_adjust(left=0.04, right=0.98, top=0.94, bottom=0.10, hspace=0.40)

    # Redibujar el canvas para mostrar los gráficos actualizados
    visor.canvas.draw()






def imprimir_plt(archivo,trCanal1,ganancia,diezmado,factor_mult):   #Depurado
    #Método utilizado para la impresión de un archivo miniseed dado por la variabel trCanal hasta un archivo típicamente con extensión .plt
    #dentro de un archivo habierto dado en la variable archivo.  Como es referido al registro contínuo de la RSA, el dleta o variable de tiempo
    #es directamente 1/640.
    numero_muestras=trCanal1.stats.npts
    tiempo=trCanal1.stats.starttime
    f_muestreo=trCanal1.stats.sampling_rate
    hora=tiempo.hour
    minuto=tiempo.minute
    segundo=tiempo.second
    muestra_inicio=(hora*3600+minuto*60+segundo)*f_muestreo
    tiempo=trCanal1.stats.endtime
    n_muestras_maximo=int(86400*f_muestreo)
    hora=tiempo.hour
    minuto=tiempo.minute
    segundo=tiempo.second
    muestra_fin=(hora*3600+minuto*60+segundo)*f_muestreo
    promedio=0
    for i in range(0, int(f_muestreo*5)):
        promedio=promedio+trCanal1[i]
    promedio=int(promedio/(f_muestreo*5))
    if trCanal1.stats.npts>n_muestras_maximo:  #Se presentò un dia con mas de segundos en un dia 
        muestra_fin=n_muestras_maximo
    n_muestras=trCanal1.stats.npts
    muestra=0
    punto=0
    datos_linea=int(360*f_muestreo/diezmado)
    delta=diezmado/(10*f_muestreo)

    for j in range(0,241):#Numero total de segundos en un día /360 segundos (6 minutos por línea} mas 1)
        print("linea " ,j,"Punto",punto)
        if j>2 and j<240:
            promedio=0
            val_ini=int(muestra)
            num_muestras=int(f_muestreo*5)
            for k in range(0, num_muestras):
                if k+val_ini<numero_muestras:
                    promedio=promedio+trCanal1[k+val_ini]
                else:
                    break
            if k!=0:
                promedio=int(promedio/(k))
            else:
                promedio=trCanal1[val_ini-1]
        contador=0.
        if(j==0):
            archivo.write('SC 1.00 1.00\nRO 00\nFL 2\nSC 1.0 0.5\nSP 14\nTR 0.00 .00\n')
        else:
            archivo.write('SC 1.00 2.00\nRO 00\nFL 2\nSC 1.0 0.5\nSP 14\nTR 0.00 -0.10\n')
        for k in range(0, datos_linea): #360 segundos (6 minutos por línea) por la frecuencia de muestreo (64 mps)
            #los datos_lienea=23040 equivalen   a  6 minutos con 64 mps, es decir grafica un línea completa en el plt.
            punto+=diezmado
            valor=0.

            if punto>muestra_inicio and punto<muestra_fin:

                if(muestra<n_muestras):
                    valor=ganancia*(trCanal1[muestra]-promedio)/factor_mult# maximo fondo escala en entero con signo de 16 bits.
                    
                    muestra=muestra+diezmado
            if(k==0):
                archivo.write('MA .0  {:2.3}\n'.format(valor))#archivo.write('MA {:2.5}  {:2.3}\n'.format(contador, valor))
            else:
                contador_s=str(round(contador, 5))
                if(contador<1.):
                    aux=len(contador_s)
                    contador_s=contador_s[1:aux]

                archivo.write('PA {}  {:2.3}\n'.format(contador_s,valor))#archivo.write('PA {:2.5}  {:2.3}\n'.format(contador, valor))
                contador=contador+delta
    


import os


def filtro_evento(visor,stLeido,freqmin_,freqmax_,grado_,t_inicio,t_final,estaciones_eventos,hab_grafico,bandera_marcas,pagina,filtros_estaciones,estaciones_eventos_total,bandera_todos):
    #stLeido es la traza donde se encuetra el mseed de la estaciòn
    #freqmin_ Frecuencia mínima de cada estacion
    #freqmax_ Frecuencia máxima de cada estacion
    #grado_ de cada estacion
    #freqmin_frecuencia minima del filtro a implementar.  
    #freqmax_frecuencia màxima del filtro a implementar. 
    #grado_ grado del filtro a implementar.
    #t_inicio Tiempo de inicio del evento
    #t_final Tiempo final del evento
    #estaciones_eventos_total  Todas las estaciones presentes en el evento.
    #estaciones_eventos  Estaciones que forman parte del evento
    #hab_grafico  Estaciones que se muestran en el grafico, originalmente todos los que tienen registros mseed
    #bandera_marcas  Hay que avericuar 
    #pagina página del despleigue
    #filtros_estaciones    Todos los filtros estacion por estación
    #estaciones_eventos_total  Todas las estaciones que tienen registros mseed del evento
    #bandera_todos    Bandera para filtrar todos los canales con los parametros generales o con los filtros estacion por estación.

    num_canal = len(estaciones_eventos)
    for i in range(0, num_canal):
        indice = estaciones_eventos_total.index(estaciones_eventos[i])
        canal_ = int(estaciones_eventos[i])
        grado_i = grado_
        freqmin_i = freqmin_
        freqmax_i = freqmax_
        if bandera_todos and filtros_estaciones and indice < len(filtros_estaciones):
            f_est = filtros_estaciones[indice]
            if f_est and f_est != '000000':
                grado_i = int(f_est[0:2])
                freqmin_i = int(f_est[2:4])
                freqmax_i = int(f_est[4:6])
        if grado_i != 0:
            try:
                stLeido[canal_].filter("bandpass", freqmin=freqmin_i, freqmax=freqmax_i, corners=grado_i)
            except (ValueError, Exception):
                pass
    grafico_evento_int(visor, stLeido, t_inicio, t_final, estaciones_eventos, hab_grafico, bandera_marcas, pagina)



def cargar_evento(parametro,eventos_reporte,catalogo,eventos,canales_eventos_dia,directorio_trabajo,directorio_reporte):
    """
    Carga el evento para procesamiento o reporte
    Args:
        parametro(texto):       Texto desde un cmbx_text.currenttext.
        eventos_reporte (list):         Lista de eventos del día.
        catalogo (list):        Catalogo del día.
        eventos:                 Dato generado en cargar dia
        evento_canales:         Dato generado en cargar dia
        directorio_trabajo:     Directorio de trabajo de ..\\DIA\\
        directorio_reporte:     Directorio donde se guarda el reporte
    """
    if parametro=='':
        return
    ext=len(eventos_reporte)
    dato=parametro.split("  ")
    indice_local=int(dato[0])
    dato_escogido=eventos[indice_local-1] #evento desde el formato simple del día, solo número de evento y tipo
    evento_local=str(dato_escogido[1]).strip()
    parametros=parametros_estaciones()
    directorios=obtener_directorios(os.path.join(directorio_trabajo, evento_local))
    indice=0
    for i in range(0,ext):
        if (
            len(eventos_reporte[i]) > 1
            and str(eventos_reporte[i][0]).strip() == str(indice_local)
            and str(eventos_reporte[i][1]).strip() == evento_local
        ):
            indice=i
            break
    if indice == 0:
        for i in range(0,ext):
            if str(eventos_reporte[i][0]).strip() == str(indice_local):
                indice=i
                break
    ext=len(catalogo)
    indice_catalogo=max(0, ext - 1)
    for i in range(0,ext):
        if len(catalogo[i]) > 18 and evento_local==str(catalogo[i][18]).strip():
            indice_catalogo=i
            break
    evento_reporte_escogido=[]
    fila_rep_base = list(eventos_reporte[indice]) if indice < len(eventos_reporte) else [str(indice_local), evento_local, dato_escogido[2]]
    if len(fila_rep_base) > 1:
        fila_rep_base[1] = evento_local
    evento_reporte_escogido.append(fila_rep_base) #evento desde el reporte completo del día
    stem_evento = Path(dato_escogido[1]).stem.replace('_', '')
    archivo_escogido=os.path.join(directorio_trabajo, stem_evento) #Variable que tiene el nombre en el formato adecuado para la ubicación de los eventos.
    canales=canales_eventos_dia[indice_local-1]
    trCanal=leer_mseed(archivo_escogido,1)
    archivo_reporte=os.path.join(directorio_reporte, dato_escogido[1][:-4]+'_rep.pdf')
    estaciones_eventos=[]
    dir_eventos = directorios['Directorio_eventos']
    if not os.path.isabs(dir_eventos):
        dir_eventos = os.path.join(directorio_trabajo, dir_eventos)
    sufijo_ev = directorios.get('sufijo_mseed', '_' + evento_reporte_escogido[0][1][0:-4] + '.mseed')
    for i in range(0, len(parametros['CODIGO'])):#Verifica todos los archivos MSEED de registro continuo encontrados en la base de datos.
        nombreMseed_1 = os.path.join(dir_eventos, parametros['CODIGO'][i]+'_'+evento_reporte_escogido[0][1][0:-4]+".mseed")
        nombreMseed_2 = os.path.join(dir_eventos, parametros['CODIGO'][i]+sufijo_ev)
        if os.path.exists(nombreMseed_1) or os.path.exists(nombreMseed_2):
            estaciones_eventos.append(int(parametros['NUM_ESTACION'][i]))
            parametros['HAB_GRAFICO'][i]="1"
        else:
            parametros['HAB_GRAFICO'][i]="0"
    return (indice,indice_local,indice_catalogo,archivo_escogido,evento_reporte_escogido,canales,trCanal,archivo_reporte,parametros['HAB_GRAFICO'],estaciones_eventos)


    
def cargar_dia(directorios):
    """
    Carga el dia para procesamiento o reporte
    Args:
        archivo_csv: Nombre del archivo para escoger el dian ia con formato AAMMDDhhmmss.
    """
    directorio_trabajo=directorios['Directorio_trabajo']
    if not(os.path.exists(directorios['Directorio_base'])):
        return [],[],[],[],[],[],[],[]
    eventos_reporte=[['0',"Fecha; Hora (UTC)","Evento","Magn.","Prof.(km)","Lat.","Long.","Ubicación"]]
    catalogo=[["Id","anio","mes","dia","hora","min","seg","lat","long","prof","rms","e-x","e-y","e-0","e-z","Mag","Tipo Mag","Fuente","ruta","Ubicacion"]]
    eventos=[]
    vector=[]
    canales_eventos_dia=[]
    contador_n_canales=[[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0]]#Tupla que contiene el número de estaciones por evento sísmico.
    root = ET.Element("sismo")
    lista_eventos=lectura_archivo(directorios['archivo_csv'])
    for evento_individual in lista_eventos:
            if evento_individual==[]:
                continue
            catalogo_grabar=[]#Variable donde se guarda lo que se va a grabar en el catalogo diario .csv
            evento_grabar=[]#Variable donde se guarda lo que se va a grabar en el resumen diario .csv
            canales_evento=[]#Variable que muestra los canales donde se tiene el evento con banderas 1 o 0
            vector_temporal=[]
            #self.cmbx_evento_escogido.addItem(str(self.evento_individual[0])+"  "+str(self.evento_individual[1])+"  "+str(self.evento_individual[2]))
            for i in range(0,101): # En vez de 100 16, numero de canales
                if evento_individual[i+3]=='-':
                    canales_evento.append(0)
                else:
                    canales_evento.append(1)
            evento_grabar.append(int(evento_individual[0]))
            evento_grabar.append(evento_individual[1])
            evento_grabar.append(evento_individual[2])
            if(evento_individual[2]=="SISMO"):
                catalogo_grabar=lectura_rsa(evento_individual[1],directorio_trabajo,'')
                if catalogo_grabar==None:
                    print("Evento pendiente de procesar:",evento_individual[1])
                    evento_grabar.append("revisar")
                    catalogo_grabar=[]
                elif catalogo_grabar==1:
                    print("Error en procesamiento:",evento_individual[1])
                    catalogo_grabar=[]
                else:
                    agregar_evento(root,catalogo_grabar[0],catalogo_grabar[3])
                    for i in(15,9,7,8,19):
                        evento_grabar.append(catalogo_grabar[0][i])
                    evento_grabar.append(catalogo_grabar[1])# catalogo_grabar[1] tiene la información de las estaciones que intervienen en la localización del evento.
                    estaciones__=catalogo_grabar[1]
                    n_estaciones=len(estaciones__.split(' '))-1#aux tiene el número de estaciones involucradas en el procesamiento.
                    n_hora=int(catalogo_grabar[0][0][8:14])
                    if(n_hora<120000):
                        n_periodo=0
                    elif (n_hora<180000):
                        n_periodo=1
                    else:
                        n_periodo=2
                    idx_est = min(max(0, n_estaciones - 3), 5)
                    contador_n_canales[n_periodo][idx_est]=contador_n_canales[n_periodo][idx_est]+1
                    for i in(7,8,9,15):
                        vector_temporal.append(catalogo_grabar[0][i])#Variable con datos del evento para desplegar en reporte diario.
                    vector_temporal.append(0)
                    vector_temporal.append(catalogo_grabar[0][18])
                    vector.append(vector_temporal)
                    catalogo_grabar=catalogo_grabar[0]
            if catalogo_grabar!=[]:
                catalogo.append(catalogo_grabar)
            eventos_reporte.append(evento_grabar)
            eventos.append(evento_individual)
            canales_eventos_dia.append(canales_evento)
    # Regenerar catálogo solo con eventos de otras redes (Id termina en != '00') manteniendo la cabecera 'Id'
    if os.path.exists(directorios['archivo_catalogo']):
            catalogo_existente = lectura_archivo(directorios['archivo_catalogo'])
            if catalogo_existente is not None:
                # 2.a) Desde el archivo existente
                for evento_existente in catalogo_existente:
                    if not evento_existente or len(evento_existente) < 19:
                        continue
                    if evento_existente[0] == 'Id':
                        continue
                    if str(evento_existente[0]).strip()[-2:] != '00':   # IGEPN (..01), USGS (..02) u otras no-RSA
                        catalogo.append(evento_existente)
                        try:
                            ruta_asoc = str(evento_existente[18]).strip()
                            ubic_ext = evento_existente[19] if len(evento_existente) > 19 else ""
                            insertado_rep = False
                            for j in range(1, len(eventos_reporte)):
                                if str(eventos_reporte[j][1]).strip() == ruta_asoc:
                                    fila_ext = [
                                        eventos_reporte[j][0],
                                        evento_existente[18],
                                        evento_existente[17],
                                        evento_existente[15],
                                        evento_existente[9],
                                        evento_existente[7],
                                        evento_existente[8],
                                        ubic_ext,
                                    ]
                                    eventos_reporte.insert(j + 1, fila_ext)
                                    insertado_rep = True
                                    break
                            if not insertado_rep:
                                num_hora = int(ruta_asoc[-10:-4])
                                for j in range(1, len(eventos_reporte)):
                                    otro_txt = str(eventos_reporte[j][1]).strip()
                                    if len(otro_txt) >= 10 and otro_txt[-10:-4].isdigit():
                                        otro_num = int(otro_txt[-10:-4])
                                        if otro_num > num_hora:
                                            orden_prev = eventos_reporte[j - 1][0] if j > 1 else 1
                                            fila_ext = [
                                                orden_prev,
                                                evento_existente[18],
                                                evento_existente[17],
                                                evento_existente[15],
                                                evento_existente[9],
                                                evento_existente[7],
                                                evento_existente[8],
                                                ubic_ext,
                                            ]
                                            eventos_reporte.insert(j, fila_ext)
                                            insertado_rep = True
                                            break
                            if not insertado_rep:
                                orden_ult = eventos_reporte[-1][0] if len(eventos_reporte) > 1 else 1
                                eventos_reporte.append([
                                    orden_ult,
                                    evento_existente[18],
                                    evento_existente[17],
                                    evento_existente[15],
                                    evento_existente[9],
                                    evento_existente[7],
                                    evento_existente[8],
                                    ubic_ext,
                                ])
                        except Exception:
                            pass
                catalogo = ordenar_y_eliminar_duplicados(catalogo, 0)
    try:
        catalogo, eventos_reporte, _ = sincronizar_otras_redes_dia(
            directorios,
            catalogo,
            eventos_reporte,
            eventos,
        )
    except Exception:
        pass
    indice_responsables=[0,0,0]
    cont_sismo=[0,0,0]
    cont_indefinido=[0,0,0]
    cont_FC=[0,0,0]
    cont_FF=[0,0,0]
    cont_ruido=[0,0,0]
    cont_local=[0,0,0]
    cont_tele=[0,0,0]
    hora_=['12H','18H','24H']
    for evento_ in eventos:
        h=int(evento_[1][-10:-8])
        if h<12:
            indice_hora=0
        elif h<18 and h>11:
            indice_hora=1
        else:
            indice_hora=2
        if evento_[2] == 'SISMO':
            cont_sismo[indice_hora]=cont_sismo[indice_hora]+1
        elif evento_[2] == 'FF':
            cont_FF[indice_hora]=cont_FF[indice_hora]+1
        elif evento_[2] == 'FC':
            cont_FC[indice_hora]=cont_FC[indice_hora]+1
        elif evento_[2] == 'INDEFINIDO':
            cont_indefinido[indice_hora]=cont_indefinido[indice_hora]+1
        elif evento_[2] == 'TELESISMO':
            cont_tele[indice_hora]=cont_tele[indice_hora]+1
        elif evento_[2] == 'Evento_local' or evento_[2] == 'CONTROL':
            cont_local[indice_hora]=cont_local[indice_hora]+1
        else:
            cont_ruido[indice_hora]=cont_ruido[indice_hora]+1
    responsables=lectura_archivo(directorios['archivo_tiempos'])
    aux=['','','']
    if not responsables or len(responsables) < 3:
        aux[0]=['RSA','']
        aux[1]=['RSA','']
        aux[2]=['RSA','']
        responsables=aux
        indice_responsables[0]=0
        indice_responsables[1]=1
        indice_responsables[2]=2
    else:
        aux=len(responsables)
        if aux==3:
            indice_responsables[0]=0#ind_0=0
            indice_responsables[1]=1#ind_1=1
            indice_responsables[2]=2#ind_2=2
        if aux==4:
            indice_responsables[0]=0#ind_0=0
            indice_responsables[1]=2#ind_1=2
            indice_responsables[2]=3#ind_2=3
        if aux==5:
            indice_responsables[0]=0#ind_0=0
            indice_responsables[1]=1#ind_1=1
            indice_responsables[2]=4#ind_2=4
        if aux==6:
            indice_responsables[0]=0#ind_0=0
            indice_responsables[1]=2#ind_1=2
            indice_responsables[2]=5#ind_2=5
    variable_responsables=[["RESPONSABLE","HORA","TOT.","SIS.","FF","FC","IND.","TEL.","Local_CONTROL.","Ruido","3 est","4 est","5 est","6 est","7 est","8 est"]]
    for i in range (0,3):
        total=cont_sismo[i]+cont_FF[i]+cont_FC[i]+cont_indefinido[i]+cont_tele[i]+cont_local[i]+cont_ruido[i]
        aux=[responsables[indice_responsables[i]][0],hora_[i],total,cont_sismo[i],cont_FF[i],cont_FC[i],cont_indefinido[i],cont_tele[i],cont_local[i],cont_ruido[i]]
        aux=aux+contador_n_canales[i]
        variable_responsables.append(aux)
    resumen=[["SISMO","FF","FC","TELESISMOS","Local_CONTROL","INDEFINIDO","Ruido"],[sum(cont_sismo),sum(cont_FF),sum(cont_FC),sum(cont_tele),sum(cont_local),sum(cont_indefinido),sum(cont_ruido)]]
    return eventos_reporte,catalogo,eventos,vector,canales_eventos_dia,root,variable_responsables,resumen

def insertar_evento_otras_redes(catalogo,indice_catalogo,eventos_reporte,red_,magnitud_,tipo_magnitud,texto,texto2,evento_reporte_escogido,indice,indice_local):
    #red_:          cmbx_red.currentIndex
    #magnitud_:     cmbx_tipo_mag.currentIndex
    #tipo_magnitud: cmbx_tipo_mag.currentText
    #texto:         textEdit.toPlainText
    eventos_temp=[" "," "," "," "," "," "," "," "]
    catalogo_temp=[" "," "," "," "," "," "," "," "," "," "," "," "," "," "," "," "," "," "," "," "]
    if red_ == 0:
        QMessageBox.information(None, "Error", '¡Falta la Red!')
        return catalogo, eventos_reporte
    if texto == "":
        QMessageBox.information(None, "Error", '¡Falta información del sismo!')
        return catalogo, eventos_reporte
    if red_ != 1 and magnitud_ == 0:
        QMessageBox.information(None, "Error", '¡Falta tipo de magnitud!')
        return catalogo, eventos_reporte

    lectura = extraccion_dato(texto, "\n")
    es_formato_igepn = 'Tiempo UTC:' in lectura

    if red_ == 1 or (red_ == 3 and es_formato_igepn):  # Cuando la red es IGEPN (o formato IGEPN en Otras redes)
        try:
            sufijo_id = "01" if red_ == 1 else "03"
            nombre_fuente = "IGEPN" if red_ == 1 else "Otras redes"
            indice_utc = lectura.index('Tiempo UTC:')
            fecha_utc = lectura[indice_utc + 1].strip()
            anio, mes, dia = fecha_utc[:10].split('-')
            hora, minuto, segundo = fecha_utc[11:].split(':')
            valor_formateado = f"{anio}{mes}{dia}{hora}{minuto}{sufijo_id}"
            catalogo_temp[0] = valor_formateado     # ID
            catalogo_temp[1] = str(int(anio))       # año
            catalogo_temp[2] = str(int(mes))        # mes
            catalogo_temp[3] = str(int(dia))        # dia
            catalogo_temp[4] = str(int(hora))       # hora
            catalogo_temp[5] = str(int(minuto))     # min
            catalogo_temp[6] = str(int(float(segundo)))  # seg
            indice_localizacion = lectura.index('Localización:')
            localizacion = lectura[indice_localizacion + 1]
            partes = localizacion.split()
            latitud = float(partes[0].replace('°', '')) * (-1 if partes[1] == 'S' else 1)
            longitud = float(partes[2].replace('°', '')) * (-1 if partes[3] == 'W' else 1)
            catalogo_temp[7] = str(latitud)         # Latitud (IDX_LATITUD = 7)
            catalogo_temp[8] = str(longitud)        # Longitud (IDX_LONGITUD = 8)
            indice_profundidad = lectura.index('Profundidad:')
            profundidad_str = lectura[indice_profundidad + 1]
            profundidad = float(profundidad_str.replace(' km', '').replace('km', '').strip())
            catalogo_temp[9] = str(profundidad)
            indice_magnitud = lectura.index('Magnitud:')
            magnitud_str = lectura[indice_magnitud + 1].strip()
            partes_mag = magnitud_str.split()
            valor_magnitud = float(partes_mag[0])
            tipo_mag_final = partes_mag[1] if len(partes_mag) > 1 else (tipo_magnitud.strip() or "M")
            if magnitud_ != 0 and tipo_magnitud.strip():
                tipo_mag_final = tipo_magnitud.strip()
            catalogo_temp[15] = str(valor_magnitud)                 # Magnitud
            catalogo_temp[16] = tipo_mag_final                      # Tipo de Magnitud
            catalogo_temp[17] = nombre_fuente                       # Fuente
            catalogo_temp[18] = str(evento_reporte_escogido[0][1]).strip()  # Ruta (.sis)
            catalogo_temp[19] = ubicacion(latitud, longitud)        # Ubicacion
            eventos_temp[0] = indice_local
            eventos_temp[1] = anio + "/" + mes + "/" + dia + "_" + hora + ":" + minuto + ":" + segundo
            eventos_temp[2] = nombre_fuente                         # Evento
            eventos_temp[3] = str(valor_magnitud)                   # Magnitud
            eventos_temp[4] = str(profundidad)                      # Profundidad
            eventos_temp[5] = str(latitud)                          # Latitud
            eventos_temp[6] = str(longitud)                         # Longitud
            eventos_temp[7] = catalogo_temp[19]                     # Ubicacion
        except Exception as e:
            QMessageBox.information(None, str(e), '¡Revise la información del sismo en la página de la IGEPN!')
            return catalogo, eventos_reporte

    elif red_ in (2, 3):  # Cuando la red es USGS (o formato USGS en Otras redes)
        try:
            sufijo_id = "02" if red_ == 2 else "03"
            nombre_fuente = "USGS" if red_ == 2 else "Otras redes"
            if 'Time' not in lectura:
                QMessageBox.information(None, "Error", '¡¡Revise la información del sismo en la página de la USGS!')
                return catalogo, eventos_reporte
            tiempo = lectura[1].strip()
            localizacion = lectura[2].strip()
            profundidad = lectura[3].strip()
            magnitud = extraccion_dato(lectura[0], " ")
            catalogo_temp[0] = tiempo[0:4] + tiempo[5:7] + tiempo[8:10] + tiempo[11:13] + tiempo[14:16] + sufijo_id
            catalogo_temp[1] = str(int(tiempo[0:4]))    # año
            catalogo_temp[2] = str(int(tiempo[5:7]))    # mes
            catalogo_temp[3] = str(int(tiempo[8:10]))   # dia
            catalogo_temp[4] = str(int(tiempo[11:13]))  # hora
            catalogo_temp[5] = str(int(tiempo[14:16]))  # min
            catalogo_temp[6] = str(int(tiempo[17:19]))  # seg
            partes_loc = extraccion_dato(localizacion, " ")
            str_lat = partes_loc[0]
            str_lon = partes_loc[1]
            signo_lat = -1 if str_lat.upper().endswith('S') else 1
            signo_lon = -1 if str_lon.upper().endswith('W') else 1
            val_lat = signo_lat * float(str_lat[:-2])
            val_lon = signo_lon * float(str_lon[:-2])
            catalogo_temp[7] = str(val_lat)             # Latitud (IDX_LATITUD = 7)
            catalogo_temp[8] = str(val_lon)             # Longitud (IDX_LONGITUD = 8)
            profundidad_partes = extraccion_dato(profundidad, " ")
            catalogo_temp[9] = str(float(profundidad_partes[0]))
            catalogo_temp[15] = str(float(magnitud[1]))  # Magnitud
            catalogo_temp[16] = tipo_magnitud.strip()    # Tipo de Magnitud
            catalogo_temp[17] = nombre_fuente            # Fuente
            catalogo_temp[18] = str(evento_reporte_escogido[0][1]).strip()  # Ruta (.sis)
            catalogo_temp[19] = ubicacion(val_lat, val_lon)  # Ubicacion
            eventos_temp[0] = indice_local
            eventos_temp[1] = tiempo[0:4] + "/" + tiempo[5:7] + "/" + tiempo[8:10] + "_" + tiempo[11:13] + ":" + tiempo[14:16]
            eventos_temp[2] = nombre_fuente
            eventos_temp[3] = catalogo_temp[15]          # Magnitud
            eventos_temp[4] = catalogo_temp[9]           # Profundidad
            eventos_temp[5] = catalogo_temp[7]           # Latitud
            eventos_temp[6] = catalogo_temp[8]           # Longitud
            eventos_temp[7] = catalogo_temp[19]          # Ubicacion
        except Exception as e:
            QMessageBox.information(None, str(e), '¡¡Revise la información del sismo en la página de la USGS!')
            return catalogo, eventos_reporte

    # Si el evento cuenta con localización RSA (..00), alinear los primeros 12 dígitos del Id
    # manteniendo el sufijo de la otra red (01 = IGEPN, 02 = USGS, 03 = Otras redes)
    nombre_sis_asoc = str(catalogo_temp[18]).strip()
    sufijo_red = str(catalogo_temp[0]).strip()[-2:]
    for f in catalogo:
        if (
            f and len(f) > 18 and f[0] != 'Id'
            and str(f[18]).strip() == nombre_sis_asoc
            and (str(f[17]).strip() == 'RSA' or str(f[0]).strip().endswith('00'))
            and len(str(f[0]).strip()) >= 12
        ):
            catalogo_temp[0] = str(f[0]).strip()[:12] + sufijo_red
            break

    # Si ya existía un registro para la misma red y evento, actualizarlo sin duplicar
    catalogo = [
        f for f in catalogo
        if not (
            f and len(f) > 18 and f[0] != 'Id'
            and str(f[17]).strip() == str(catalogo_temp[17]).strip()
            and str(f[18]).strip() == str(catalogo_temp[18]).strip()
        )
    ]
    eventos_reporte = [
        f for f in eventos_reporte
        if not (
            f and len(f) > 2 and str(f[0]).strip() == str(indice_local).strip()
            and str(f[2]).strip() == str(eventos_temp[2]).strip()
        )
    ]

    pos_cat = min(max(1, indice_catalogo + 1), len(catalogo))
    catalogo.insert(pos_cat, catalogo_temp)
    catalogo = ordenar_y_eliminar_duplicados(catalogo, 0)

    pos_rep = min(max(1, indice + 1), len(eventos_reporte))
    eventos_reporte.insert(pos_rep, eventos_temp)
    return catalogo, eventos_reporte


def extraer_datetime_evento_rsa(nombre_sis, catalogo=None):
    """
    Obtiene el datetime UTC de un evento de la RSA priorizando la hora origen
    del catálogo (_cat.csv) si existe solución RSA, o el nombre del archivo .sis
    (AAMMDD_hhmmss.sis o AAAAMMDD_hhmmss.sis) en caso contrario (ej. FF o FC).
    """
    nombre_limpio = Path(str(nombre_sis).strip()).name
    if catalogo:
        for fila in catalogo:
            if (
                fila and len(fila) > 18 and fila[0] != 'Id'
                and Path(str(fila[18]).strip()).name == nombre_limpio
                and (str(fila[17]).strip() == 'RSA' or str(fila[0]).strip().endswith('00'))
            ):
                try:
                    return datetime(
                        int(fila[1]), int(fila[2]), int(fila[3]),
                        int(fila[4]), int(fila[5]), int(float(fila[6]))
                    )
                except (ValueError, TypeError):
                    pass

    base = Path(nombre_limpio).stem.strip()
    for fmt in ("%y%m%d_%H%M%S", "%Y%m%d_%H%M%S", "%y%m%d%H%M%S", "%Y%m%d%H%M%S"):
        try:
            return datetime.strptime(base, fmt)
        except ValueError:
            continue
    return None


def _normalizar_tipo_magnitud_rsa(tipo_raw):
    """Normaliza la etiqueta de tipo de magnitud al conjunto estándar de la RSA."""
    t = str(tipo_raw or "").strip()
    if not t:
        return "M"
    t_low = t.lower()
    if t_low.startswith("ml"):
        return "MLv"
    if t_low.startswith("mw"):
        return "Mw"
    if t_low.startswith("mb"):
        return "Mb"
    if t_low.startswith("md"):
        return "Md"
    if t_low.startswith("mc"):
        return "Mc"
    if t in ("M", "MLv", "Md", "Mc", "Mw", "Mb"):
        return t
    return "M"


def consultar_sismos_igepn_web(timeout=6):
    """
    Consulta la tabla HTML de Últimos Sismos del IGEPN
    (https://www.igepn.edu.ec/portal/sismos/index2.html) y devuelve una lista
    de diccionarios normalizados con fecha/hora UTC, coordenadas, magnitud y
    texto formateado compatible con insertar_evento_otras_redes.
    """
    import urllib.request
    urls = [
        "https://www.igepn.edu.ec/portal/sismos/index2.html",
        "https://www.igepn.edu.ec/portal/eventos/informes-ultimos-sismosC.html",
    ]
    resultados = []
    for url in urls:
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
            filas_tr = re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.S | re.I)
            for tr in filas_tr:
                celdas = [
                    re.sub(r"<[^>]+>", "", td).strip()
                    for td in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S | re.I)
                ]
                if len(celdas) < 12:
                    continue
                try:
                    mag_val = float(celdas[2].replace(",", "."))
                    tipo_mag = _normalizar_tipo_magnitud_rsa(celdas[3] or "MLv")
                    lat_raw = celdas[5].strip()
                    lon_raw = celdas[6].strip()
                    lat_partes = lat_raw.replace("°", " ").split()
                    lon_partes = lon_raw.replace("°", " ").split()
                    lat_val = float(lat_partes[0]) * (-1 if len(lat_partes) > 1 and lat_partes[1].upper().startswith("S") else 1)
                    lon_val = float(lon_partes[0]) * (-1 if len(lon_partes) > 1 and lon_partes[1].upper().startswith("W") else 1)
                    prof_val = float(celdas[7].lower().replace("km", "").strip())
                    fecha_utc_str = celdas[11].strip()
                    dt_utc = datetime.strptime(fecha_utc_str, "%Y-%m-%d %H:%M:%S")
                    hemi_lat = "S" if lat_val < 0 else "N"
                    hemi_lon = "W" if lon_val < 0 else "E"
                    texto_igepn = (
                        f"Tiempo UTC:\n{fecha_utc_str}\n"
                        f"Localización:\n{abs(lat_val):.3f}° {hemi_lat} {abs(lon_val):.3f}° {hemi_lon}\n"
                        f"Profundidad:\n{prof_val:.1f} km\n"
                        f"Magnitud:\n{mag_val} {tipo_mag}"
                    )
                    resultados.append({
                        "fuente": "IGEPN",
                        "sufijo_id": "01",
                        "dt_utc": dt_utc,
                        "latitud": round(lat_val, 4),
                        "longitud": round(lon_val, 4),
                        "profundidad": round(prof_val, 2),
                        "magnitud": round(mag_val, 2),
                        "tipo_mag": tipo_mag,
                        "texto_formateado": texto_igepn,
                    })
                except (ValueError, IndexError):
                    continue
            if resultados:
                break
        except Exception:
            continue
    return resultados


def consultar_sismos_usgs_api(dt_inicio_utc, dt_fin_utc, timeout=6):
    """
    Consulta la API FDSN GeoJSON de la USGS en el rango [dt_inicio_utc, dt_fin_utc]
    para la región del Ecuador y alrededores, devolviendo diccionarios normalizados.
    """
    import urllib.request
    import json
    resultados = []
    try:
        t_ini = dt_inicio_utc.strftime("%Y-%m-%dT%H:%M:%S")
        t_fin = dt_fin_utc.strftime("%Y-%m-%dT%H:%M:%S")
        url = (
            "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson"
            f"&starttime={t_ini}&endtime={t_fin}"
            "&minlatitude=-12.0&maxlatitude=6.0&minlongitude=-93.0&maxlongitude=-70.0"
        )
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            datos = json.loads(resp.read().decode("utf-8", errors="ignore"))
        for feat in datos.get("features", []):
            try:
                props = feat.get("properties", {})
                geom = feat.get("geometry", {})
                coords = geom.get("coordinates", [])
                if len(coords) < 3 or props.get("mag") is None or props.get("time") is None:
                    continue
                lon_val = float(coords[0])
                lat_val = float(coords[1])
                prof_val = float(coords[2])
                mag_val = float(props["mag"])
                tipo_mag = _normalizar_tipo_magnitud_rsa(props.get("magType") or "M")
                dt_utc = datetime.utcfromtimestamp(float(props["time"]) / 1000.0)
                hemi_lat = "S" if lat_val < 0 else "N"
                hemi_lon = "W" if lon_val < 0 else "E"
                fecha_utc_str = dt_utc.strftime("%Y-%m-%d %H:%M:%S")
                lugar_usgs = str(props.get("place") or "Ecuador")
                texto_usgs = (
                    f"M {mag_val} - {lugar_usgs}\n"
                    f"{fecha_utc_str} (UTC)\n"
                    f"{abs(lat_val):.3f}°{hemi_lat} {abs(lon_val):.3f}°{hemi_lon}\n"
                    f"{prof_val:.1f} km depth\n"
                    "Time"
                )
                resultados.append({
                    "fuente": "USGS",
                    "sufijo_id": "02",
                    "dt_utc": dt_utc,
                    "latitud": round(lat_val, 4),
                    "longitud": round(lon_val, 4),
                    "profundidad": round(prof_val, 2),
                    "magnitud": round(mag_val, 2),
                    "tipo_mag": tipo_mag,
                    "texto_formateado": texto_usgs,
                })
            except (ValueError, TypeError, KeyError):
                continue
    except Exception:
        pass
    return resultados


def buscar_evento_otra_red_en_linea(nombre_sis, catalogo, red_nombre, tolerancia_seg=180):
    """
    Busca en línea (web IGEPN o API USGS) un evento particular de la RSA
    identificado por 'nombre_sis' dentro de una ventana de ±tolerancia_seg.
    Retorna el diccionario con los datos y 'texto_formateado', o None si no hay coincidencia.
    """
    dt_rsa = extraer_datetime_evento_rsa(nombre_sis, catalogo)
    if dt_rsa is None:
        return None

    red_norm = str(red_nombre).strip().upper()
    candidatos = []
    if red_norm == "IGEPN":
        candidatos = consultar_sismos_igepn_web(timeout=6)
    elif red_norm == "USGS":
        candidatos = consultar_sismos_usgs_api(
            dt_rsa - timedelta(seconds=tolerancia_seg + 60),
            dt_rsa + timedelta(seconds=tolerancia_seg + 60),
            timeout=6,
        )

    mejor = None
    mejor_delta = None
    for cand in candidatos:
        delta = abs((cand["dt_utc"] - dt_rsa).total_seconds())
        if delta <= tolerancia_seg and (mejor_delta is None or delta < mejor_delta):
            mejor_delta = delta
            mejor = cand
    return mejor


def _construir_filas_otra_red_para_evento(sismo_ext, nombre_sis, indice_local, catalogo):
    """
    Construye la tupla (fila_catalogo_20_col, fila_reporte_8_col) para un sismo externo
    asociado al evento RSA 'nombre_sis', respetando el prefijo del ID del catálogo RSA
    cuando el evento tiene localización RSA.
    """
    dt_utc = sismo_ext["dt_utc"]
    sufijo = sismo_ext["sufijo_id"]
    fuente = sismo_ext["fuente"]
    nombre_limpio = str(nombre_sis).strip()

    prefijo_id = dt_utc.strftime("%Y%m%d%H%M")
    if catalogo:
        for f in catalogo:
            if (
                f and len(f) > 18 and f[0] != "Id"
                and str(f[18]).strip() == nombre_limpio
                and (str(f[17]).strip() == "RSA" or str(f[0]).strip().endswith("00"))
                and len(str(f[0]).strip()) >= 12
            ):
                prefijo_id = str(f[0]).strip()[:12]
                break

    id_completo = f"{prefijo_id}{sufijo}"
    lat_val = float(sismo_ext["latitud"])
    lon_val = float(sismo_ext["longitud"])
    prof_val = float(sismo_ext["profundidad"])
    mag_val = float(sismo_ext["magnitud"])
    tipo_mag = str(sismo_ext["tipo_mag"]).strip() or "M"
    ubic_str = ubicacion(lat_val, lon_val)

    fila_cat = [
        id_completo,
        str(dt_utc.year),
        str(dt_utc.month),
        str(dt_utc.day),
        str(dt_utc.hour),
        str(dt_utc.minute),
        str(dt_utc.second),
        str(lat_val),
        str(lon_val),
        str(prof_val),
        " ", " ", " ", " ", " ",
        str(mag_val),
        tipo_mag,
        fuente,
        nombre_limpio,
        ubic_str,
    ]
    if fuente == "IGEPN":
        fecha_rep = dt_utc.strftime("%Y/%m/%d_%H:%M:%S")
    else:
        fecha_rep = dt_utc.strftime("%Y/%m/%d_%H:%M")

    fila_rep = [
        indice_local,
        fecha_rep,
        fuente,
        str(mag_val),
        str(prof_val),
        str(lat_val),
        str(lon_val),
        ubic_str,
    ]
    return fila_cat, fila_rep


def sincronizar_otras_redes_dia(directorios, catalogo, eventos_reporte, eventos, tolerancia_seg=180):
    """
    Sincroniza de forma automática y transparente los eventos del día de la RSA
    ('SISMO', 'FF', 'FC', 'TELESISMO', 'INDEFINIDO') contra la tabla web del IGEPN (01)
    y la API de la USGS (02).
    Si no hay conexión a internet o no hay coincidencias nuevas, retorna sin error.

    Retorna:
        (catalogo, eventos_reporte, hubo_cambios)
    """
    if not eventos:
        return catalogo, eventos_reporte, False

    eventos_candidatos = []
    for ev in eventos:
        if not ev or len(ev) < 3:
            continue
        tipo_ev = str(ev[2]).strip()
        if tipo_ev in ("SISMO", "FF", "FC", "TELESISMO", "INDEFINIDO"):
            dt_ev = extraer_datetime_evento_rsa(ev[1], catalogo)
            if dt_ev is not None:
                eventos_candidatos.append((ev[0], str(ev[1]).strip(), tipo_ev, dt_ev))

    if not eventos_candidatos:
        return catalogo, eventos_reporte, False

    fechas_dt = [x[3] for x in eventos_candidatos]
    dt_min = min(fechas_dt) - timedelta(seconds=tolerancia_seg + 60)
    dt_max = max(fechas_dt) + timedelta(seconds=tolerancia_seg + 60)

    sismos_igepn = consultar_sismos_igepn_web(timeout=5)
    sismos_usgs = consultar_sismos_usgs_api(dt_min, dt_max, timeout=5)
    if not sismos_igepn and not sismos_usgs:
        return catalogo, eventos_reporte, False

    hubo_cambios = False
    for indice_local, nombre_sis, _tipo_ev, dt_ev in eventos_candidatos:
        for lista_red, nombre_fuente in ((sismos_igepn, "IGEPN"), (sismos_usgs, "USGS")):
            if not lista_red:
                continue
            ya_existe = any(
                f and len(f) > 18 and f[0] != "Id"
                and str(f[17]).strip() == nombre_fuente
                and str(f[18]).strip() == nombre_sis
                for f in catalogo
            )
            if ya_existe:
                continue

            mejor = None
            mejor_delta = None
            for cand in lista_red:
                delta = abs((cand["dt_utc"] - dt_ev).total_seconds())
                if delta <= tolerancia_seg and (mejor_delta is None or delta < mejor_delta):
                    mejor_delta = delta
                    mejor = cand

            if mejor is not None:
                fila_cat, fila_rep = _construir_filas_otra_red_para_evento(
                    mejor, nombre_sis, indice_local, catalogo
                )
                catalogo.append(fila_cat)
                ya_en_rep = any(
                    r and len(r) > 2
                    and str(r[0]).strip() == str(indice_local).strip()
                    and str(r[2]).strip() == nombre_fuente
                    for r in eventos_reporte
                )
                if not ya_en_rep:
                    pos_insercion = len(eventos_reporte)
                    for idx_r, r in enumerate(eventos_reporte):
                        if r and str(r[0]).strip() == str(indice_local).strip():
                            pos_insercion = idx_r + 1
                    eventos_reporte.insert(pos_insercion, fila_rep)
                hubo_cambios = True

    if hubo_cambios:
        catalogo = ordenar_y_eliminar_duplicados(catalogo, 0)
        if isinstance(directorios, dict):
            if directorios.get("archivo_catalogo"):
                escritura_archivo(directorios["archivo_catalogo"], catalogo)
            if directorios.get("archivo_reporte"):
                escritura_archivo(directorios["archivo_reporte"], eventos_reporte)

    return catalogo, eventos_reporte, hubo_cambios


def guardar_seniales_csv(archivo_csv, seniales_ascii, stats):
    """
    Guarda los datos de las señales en un archivo CSV con cabecera de estadísticas.

    Parámetros:
    archivo_csv (str): Nombre del archivo CSV de salida.
    seniales_ascii (list): Lista con las señales y sus etiquetas.
    stats (dict): Diccionario con la información estadística del archivo trcanal.
    """

    # Extraer dinámicamente los nombres de las señales y sus datos
    etiquetas = [seniales_ascii[0].strip(), seniales_ascii[2].strip(), seniales_ascii[4].strip()]
    datos_seniales = [seniales_ascii[1][0], seniales_ascii[3][0], seniales_ascii[5][0]]

    # Determinar la longitud máxima de las señales para alinear los datos
    max_len = max(len(datos_seniales[0]), len(datos_seniales[1]), len(datos_seniales[2]))

    # Rellenar con NaN para igualar las longitudes
    columnas = {}
    for etiqueta, datos in zip(etiquetas, datos_seniales):
        columnas[etiqueta] = pd.Series(datos).reindex(range(max_len))

    # Crear el DataFrame con las etiquetas dinámicas
    df = pd.DataFrame(columnas)

    # Abrir el archivo y escribir la cabecera con los datos de stats
    with open(archivo_csv, 'w', encoding='utf-8') as f:
        f.write("# Información de estadísticas:\n")
        for clave, valor in stats.items():
            f.write(f"# {clave}: {valor}\n")
        f.write("\n")

    # Guardar los datos de las señales debajo de la cabecera
    df.to_csv(archivo_csv, mode='a', index=False)
   
    
def incrementar_catalogo_eventos(directorio_trabajo,eventos,eventos_catalogo):
    """
    eventos:   Eventos tomados de AAAAMMDD_000000.csv
    eventos_catalogo:  Eventos tomados del catálogo 
    """
    for evento in eventos:
        directorios=obtener_directorios(evento[1])
        archivo_procesamiento=directorio_trabajo+directorios['archivo_procesamiento']
        aux=['00000000000000', '2025', '1', '1', '0', '0', '0', '-2.00', '-79.00', '0', 'rms', 'e-x', 'e-y', 'e-0', 'e-z', '0', ' ', 'No procesado', evento[1],' , , ']
        if os.path.exists(archivo_procesamiento):
            lectura=lectura_archivo(archivo_procesamiento)
            if len(lectura)==1:
                #os.remove(archivo_procesamiento)
                continue
            else:
                for k in range(len(lectura),1,-1):
                    pass
        evento_buscado =int(evento[1].replace('_', '')[:-4])
        tamanio_catalogo=len(eventos_catalogo)
        indice=1
        for i in range(indice,tamanio_catalogo):
            evento_analizado=int(eventos_catalogo[i][IDX_EVENTO].replace('_', '')[:-4])
            if evento_buscado==evento_analizado:
                break
            if evento_analizado>evento_buscado:
                eventos_catalogo.insert(i,aux)
                break
    return eventos_catalogo



def recolectar_evt(directorio_base):
    archivos_evt = []

    # Función para verificar formato AAAAMMDD
    def es_formato_aaaammdd(nombre):
        return re.fullmatch(r"\d{8}", nombre) is not None

    # Función para verificar formato AAMMDD
    def es_formato_aammdd(nombre):
        return re.fullmatch(r"\d{6}", nombre) is not None

    # Revisar el contenido del directorio base
    print("Revisando en directorio ",directorio_base )
    subdirectorios_encontrados=os.listdir(directorio_base)
    print("Subdirectorios encontrados:",subdirectorios_encontrados)
    for subdirectorio in subdirectorios_encontrados:
        print("Trabajando sobre ",subdirectorio)
        ruta_subdirectorio = os.path.join(directorio_base, subdirectorio)
        if os.path.isfile(ruta_subdirectorio):
            if subdirectorio.lower().endswith(".evt"):
                archivos_evt.append(ruta_subdirectorio)
        elif os.path.isdir(ruta_subdirectorio) and es_formato_aaaammdd(subdirectorio):
            # Directorio tipo AAAAMMDD encontrado
            for subdirectorio_fecha in os.listdir(ruta_subdirectorio):
                ruta_subdirectorio_fecha = os.path.join(ruta_subdirectorio, subdirectorio_fecha)

                if os.path.isdir(ruta_subdirectorio_fecha) and es_formato_aammdd(subdirectorio_fecha):
                    # Subdirectorio tipo AAMMDD encontrado
                    for archivo in os.listdir(ruta_subdirectorio_fecha):
                        ruta_archivo = os.path.join(ruta_subdirectorio_fecha, archivo)
                        if os.path.isfile(ruta_archivo) and archivo.lower().endswith(".evt"):
                            archivos_evt.append(ruta_archivo)

    return archivos_evt




from scipy.stats import kurtosis, skew
from scipy.fft import rfft, rfftfreq

def clasificar_evento_sismico(traza):
    """
    Analiza un evento sísmico segmentado (con múltiples componentes) y determina si alguna componente
    muestra evidencia de un evento sísmico real. Si encuentra una positiva, retorna esa; si no, retorna
    la última con clasificación falsa.

    Parámetros:
    -----------
    traza : obspy.Stream
        Objeto Stream que contiene una o más trazas (componentes).

    Retorna:
    --------
    dict con métricas del evento y clasificación (de la componente que cumpla o la última).
    """

    # Umbrales de decisión (ajustables)
    umbrales = {
        "duracion_min": 0.8,         # segundos
        "rms_min": 100,              # depende del instrumento
        "kurtosis_min": 2.5,         # picos
        "frecuencia_max": 20         # Hz
    }

    resultado_final = {}

    for tr in traza:
        fs = tr.stats.sampling_rate
        datos = tr.data

        # Preprocesamiento
        tr.detrend("demean")
        tr.filter("bandpass", freqmin=1.0, freqmax=20.0)

        # Estadísticas
        rms = np.sqrt(np.mean(datos ** 2))
        duracion = len(datos) / fs
        kurt = kurtosis(datos)
        sesgo = skew(datos)

        # Espectro
        N = len(datos)
        fft_vals = np.abs(rfft(datos))
        freqs = rfftfreq(N, d=1/fs)
        frecuencia_dominante = freqs[np.argmax(fft_vals)]

        es_evento = (
            duracion >= umbrales["duracion_min"] and
            rms >= umbrales["rms_min"] and
            kurt >= umbrales["kurtosis_min"] and
            frecuencia_dominante <= umbrales["frecuencia_max"]
        )

        resultado = {
            "componente": tr.stats.channel,
            "duracion_s": round(duracion, 2),
            "rms": round(rms, 2),
            "kurtosis": round(kurt, 2),
            "skewness": round(sesgo, 2),
            "frecuencia_dominante_Hz": round(frecuencia_dominante, 2),
            "evento_sismico_probable": es_evento
        }

        # Si ya se detectó un evento, lo retornamos inmediatamente
        if es_evento:
            return resultado

        # Si no es evento, seguimos pero guardamos el último por si todas fallan
        resultado_final = resultado

    # Ninguna componente clasificó como evento verdadero
    return resultado_final






def extraer_kinemetrics_evt(ruta_shd_txt):
    """
    Extrae metadatos de un archivo EVT convertido a texto (.SHD)
    y devuelve un diccionario tipo kinemetrics_evt.
    """
    evt_dict = {
        'nombre_estacion': None,
        'latitud': None,
        'longitud': None,
        'altura': None,
        'profundiad': None,
        'numero_serie_sensor': None,
        'sensitividad': None,
        'unidades': None,
        'modelo': None,
        'serialnumber': None,
        'canales':None,
        'muestreo':None,
        'pre_evento':None,
        'post_evento':None,
        'tiempo_incicio':None,
        'tiempo_disparo':None,
        'duracion':None,
        'frames':None,
        'scans':None,
        'instrument':None,
        'comment': ''

    }
    with open(ruta_shd_txt, "r", encoding="latin1") as f:
        cabecera = f.read().splitlines()

    evt_dict['nombre_estacion'] = cabecera[2].split()[2]
    evt_dict['latitud'] = None
    evt_dict['longitud'] = None
    evt_dict['altura'] = None
    evt_dict['profundiad'] = None
    evt_dict['numero_serie_sensor'] = None
    evt_dict['sensitividad'] = None
    evt_dict['unidades'] = None 
    evt_dict['modelo'] = None 
    evt_dict['serialnumber'] = cabecera[1].split()[-1] 
    evt_dict['canales'] = cabecera[3].split()[2] 
    evt_dict['muestreo'] = cabecera[3].split()[-1] 
    evt_dict['pre_evento'] = cabecera[4].split()[1] 
    evt_dict['post_evento'] = cabecera[4].split()[3] 
    evt_dict['tiempo_incicio'] = cabecera[6].split()[2] + "T" + cabecera[6].split()[4]
    evt_dict['tiempo_disparo'] = cabecera[7].split()[2] + "T" + cabecera[7].split()[4]
    evt_dict['duracion'] = cabecera[8].split()[1]
    evt_dict['frames'] = cabecera[8].split()[3]
    evt_dict['scans'] = cabecera[8].split()[-2] 
    evt_dict['instrument'] = None 
    evt_dict['comment'] = None 
    return evt_dict

def ejecutar_en_vm(evt_path,virtual_path):
        try:
            usuario = "vbox"
            password = "rsa"

            comando = [
                "VBoxManage", "guestcontrol", "RSA1", "run",
                "--username", usuario,
                "--password", password,
                "--exe", "C:\\Windows\\System32\\cmd.exe",
                "--timeout", "10000",
                "--", "cmd.exe", "/c", "C:\\DIA\\KINEMETRICS\\ejecutar_kw2asc.bat"
            ]
            subprocess.run(comando, capture_output=True, text=True)
            nombre_base = evt_path.stem
            archivos_txt = [virtual_path  / f"{nombre_base}.00{i+1}" for i in range(3)]
            archivo_shd = virtual_path  / f"{nombre_base}.SHD"
            datos_evt=extraer_kinemetrics_evt(archivo_shd)
            with open(archivo_shd, "r", encoding="latin1") as f:
                cabecera = f.read().splitlines()
            estacion = datos_evt['nombre_estacion']
            sampling_rate=float(datos_evt['muestreo'])
            linea_tiempo = cabecera[6].split()
            fecha_str = linea_tiempo[2] + "T" + linea_tiempo[4]
            starttime = datetime.strptime(fecha_str, '%m/%d/%YT%H:%M:%S.%f')
            canales = ["Z", "N", "E"]
            stream = Stream()
            for path, comp in zip(archivos_txt, canales):
                with open(path, "r") as f:
                    datos = np.array([float(x) for x in f.read().split()], dtype=np.float32)
                tr = Trace(data=datos)
                tr.stats.station = estacion
                tr.stats.channel = comp
                tr.stats.starttime = starttime
                tr.stats.sampling_rate = sampling_rate
                tr.stats.kinemetrics_evt = datos_evt
                stream += tr

            for ext in [".001", ".002", ".003", ".SHD"]:
                archivo = virtual_path / f"{nombre_base}{ext}"
                if archivo.exists():
                    os.remove(archivo)
            return stream
        except Exception as e:
            print(e)
            return None

