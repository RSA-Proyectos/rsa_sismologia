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

import struct
import scipy.signal as signal
import numpy as np
from obspy import read

import sys
import os
import csv
import re
import xml.etree.ElementTree as ET
from metodos_gestion import obtener_directorios,obtencion_hora,parametros_estaciones
from rsa_io import conversion_mseed,lectura_archivo,escritura_archivo,lectura_resumen
from PyQt5.QtCore import QDate
from datetime import datetime, timedelta, date
import calendar

IDX_INDICE,IDX_ANIO,IDX_MES,IDX_DIA,IDX_HORA,IDX_MINUTO,IDX_SEGUNDO,\
IDX_LATITUD,IDX_LONGITUD,IDX_PROFUNDIDAD,IDX_RMS,IDX_E_X,IDX_E_Y,IDX_E_0,\
IDX_E_Z,IDX_MAGNITUD,IDX_UNIDAD_MAG,\
IDX_FUENTE,IDX_EVENTO,IDX_LUGAR = 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19


def extraccion(evento_auxiliar, solo_eventos, archivo, bandera_forzar):
    """
    evento_auxiliar : línea del AAMMDD_aux.csv 
    solo_eventos    : lista de eventos ya procesados del día (para evitar duplicados)
    archivo         : ruta base ..\DIA\AAMMDD000000
    bandera_forzar  : se mantiene por compatibilidad (no se usa para iterar)
    """
    estaciones_analogicas = lectura_archivo(os.path.join(ruta_datos, 'analogicas.csv'))
    directorios = obtener_directorios(archivo)
    parametros = parametros_estaciones()

    evento, tipo_evento = evento_auxiliar[1], evento_auxiliar[2]
    t_inicio, t_final = float(evento_auxiliar[4]), float(evento_auxiliar[5])
    print('Extrayendo ', evento)

    # Referencias de tiempo
    fecha_ = obtencion_hora(archivo)
    t_ini = fecha_ + t_inicio
    t_fin = fecha_ + t_final
    numero_de_muestras = int((t_fin - t_ini) * 64)

    # Nombres de salida
    nombre_sis = os.path.join(directorios['Directorio_dia'], t_ini.strftime('%Y%m%d_%H%M%S.sis'))
    hora_formateada = t_ini.strftime(" %H: %M: %S")

    # Rango de tiempo inválido
    if t_inicio > t_final:
        print("Advertencia:\n", "Hora incorrecta: Tiempo de inicio mayor a final")
        return

    # Evitar reprocesar eventos ya presentes
    if evento in solo_eventos:
        return

    # ------------------------------------------------------------------
    # Estaciones aportantes (tokens):
    # 1) CSV del día (preferente si existe la fila)
    # 2) Auxiliar (completa lo faltante)
    # ------------------------------------------------------------------
    # Tokens desde auxiliar (si vinieron)
    if len(evento_auxiliar) > 6 and evento_auxiliar[7].strip():
        tokens_aux = evento_auxiliar[7].split()
    else:
        tokens_aux = []

    # Tokens desde CSV del día (preferentes si existe la fila)
    fila_csv = None
    tokens_csv = []
    eventos_csv_dia = lectura_archivo(directorios['archivo_csv'])
    for fila_ev in eventos_csv_dia:
        if fila_ev[1] == evento_auxiliar[1]:
            fila_csv = fila_ev
            break
    if fila_csv:
        # columnas 3..N contienen tokens o '-'
        tokens_csv = [tok for tok in fila_csv[3:] if tok != '-']

    # ------------------------------------------------------------------
    # Extracción a .mseed por estación habilitada (si el evento no es "Ruido")
    # ------------------------------------------------------------------
    if tipo_evento != "Ruido":
        sismo_extraido = []
        estaciones_con_senial = []

        # Estaciones habilitadas con mseed del día disponible
        for numero_estacion, habil in enumerate(parametros['HAB_CANAL']):
            if habil == '1':
                archivo_mseed_dia = os.path.join(
                    directorios['Directorio_registros'],
                    parametros['CODIGO'][numero_estacion] + directorios['sufijo_mseed']
                )
                if os.path.exists(archivo_mseed_dia):
                    estaciones_con_senial.append(
                        (numero_estacion, parametros['NOMBRE'][numero_estacion], parametros['CODIGO'][numero_estacion])
                    )

        # Corte del intervalo y guardado del .mseed de evento por estación
        for numero_estacion, _, codigo_est in estaciones_con_senial:
            componente = int(parametros['COMPONENTE'][numero_estacion]) - 1
            archivo_mseed_dia = os.path.join(
                directorios['Directorio_registros'],
                parametros['CODIGO'][numero_estacion] + directorios['sufijo_mseed']
            )
            stcanal = read(archivo_mseed_dia, format="MSEED",
                           starttime=t_ini, endtime=t_fin, nearest_sample=False)
            if len(stcanal) == 0:
                continue
            stcanal = stcanal.copy()

            # Corrección de polaridad si aplica
            comp_idx = min(max(0, componente), len(stcanal) - 1)
            if parametros['POLARIDAD'][numero_estacion] == 'N':
                stcanal[comp_idx].data = stcanal[comp_idx].data * -1

            # Guardar .mseed de evento
            nombre_mseed_ev = os.path.join(
                directorios['Directorio_eventos'],
                codigo_est + t_ini.strftime('_%Y%m%d_%H%M%S.mseed')
            )
            stcanal.write(nombre_mseed_ev, format='MSEED', encoding='STEIM1', reclen=512)
            print('Grabando:', nombre_mseed_ev)

        # Construcción del archivo .sis (solo si es SISMO)
        if tipo_evento == "SISMO":
            # Conversión a “analógicas” (V2) y remuestreo a 64 Hz
            for estacion_analogica in estaciones_analogicas:
                if estacion_analogica[0] == 'ESTACION':
                    continue

                numero_estacion = int(estacion_analogica[0])
                componente = int(parametros['COMPONENTE'][numero_estacion]) - 1

                nombre_mseed_ev = os.path.join(
                    directorios['Directorio_eventos'],
                    parametros['CODIGO'][numero_estacion] + t_ini.strftime('_%Y%m%d_%H%M%S.mseed')
                )
                if not os.path.exists(nombre_mseed_ev):
                    sis_extraido = np.array([], dtype=np.int32)
                    sismo_extraido.append(sis_extraido)
                    continue

                try:
                    stcanal = read(nombre_mseed_ev)
                    stcanal = stcanal.copy()
                    stcanal.detrend("demean")
                    comp_idx = min(max(0, componente), len(stcanal) - 1)
                    stcanal[comp_idx].data = stcanal[comp_idx].data.astype('int32')

                    sis_extraido = stcanal[comp_idx].data
                    fs = stcanal[comp_idx].stats.sampling_rate

                    if fs != 64:
                        sis_extraido = signal.resample(sis_extraido, numero_de_muestras)
                        sis_extraido = np.rint(sis_extraido).astype(np.int32)

                    # Forzar tamaño exacto
                    if sis_extraido.size != numero_de_muestras:
                        if sis_extraido.size > numero_de_muestras:
                            sis_extraido = sis_extraido[:numero_de_muestras]
                        else:
                            faltantes = numero_de_muestras - sis_extraido.size
                            sis_extraido = np.pad(sis_extraido, (0, faltantes), mode='constant')

                    sismo_extraido.append(sis_extraido)
                except Exception as e:
                    print(f"Aviso al procesar analógica {nombre_mseed_ev}: {e}")
                    sismo_extraido.append(np.array([], dtype=np.int32))

            candidatos_cabecera = [
                os.path.join(directorios['Directorio_trabajo'], "cabecera_sismo"),
                os.path.join(ruta_datos, "cabecera_sismo"),
                "C:/DIA/cabecera_sismo",
                os.path.join(directorios.get('Directorio_base', ''), "cabecera_sismo"),
            ]
            archivo_cabecera = next((c for c in candidatos_cabecera if os.path.exists(c)), candidatos_cabecera[0])

            try:
                with open(archivo_cabecera, 'rb') as archivo_leer:

                    cabecera = b''
                    contador = 0
                    # Avanza dos etiquetas 0x0008
                    while contador < 2:
                        marcador = archivo_leer.read(2)
                        if marcador == b'\x08\x00':
                            cabecera_0 = archivo_leer.read(2)
                            num_caracteres = struct.unpack("<H", cabecera_0)[0]
                            archivo_leer.read(num_caracteres)
                            contador += 1
                    puntero = archivo_leer.tell()
                    archivo_leer.seek(0)
                    cabecera = (
                        archivo_leer.read(puntero) +
                        b'\x08\x00\x0B\x00' + hora_formateada.encode('utf-8') +
                        archivo_leer.read()
                    )

                with open(nombre_sis, 'wb') as archivo_escribir:
                    archivo_escribir.write(cabecera)

                    segundo_ = t_ini.hour * 3600 + t_ini.minute * 60 + t_ini.second
                    segundo_string = f'{segundo_:05}'
                    archivo_escribir.write(segundo_string.encode())

                    k = 0
                    for n in range(numero_de_muestras):
                        if k == 0:
                            archivo_escribir.write(
                                b'\x02\x20\x02\x00\x40\x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00'
                            )
                        k += 1
                        if k == 64:
                            k = 0

                        for i, estacion_analogica in enumerate(estaciones_analogicas):
                            if estacion_analogica[0] == 'ESTACION':
                                continue
                            m = i - 1
                            estacion = int(estacion_analogica[0])

                            if parametros['HAB_CANAL'][estacion] == "1" and sismo_extraido[m].size > 0:
                                valor = int(sismo_extraido[m][n])
                            else:
                                valor = 0

                            try:
                                archivo_escribir.write(valor.to_bytes(2, byteorder='little', signed=True))
                            except OverflowError:
                                print(valor)
                                valor = 0
                                archivo_escribir.write(valor.to_bytes(2, byteorder='little', signed=True))
            except FileNotFoundError:
                print("Cabecera binaria no encontrada:", archivo_cabecera)

    # ------------------------------------------------------------------
    # Construcción de la línea para el CSV de eventos (101 columnas)
    # ------------------------------------------------------------------
    if evento not in solo_eventos:
        lista_guiones = ['-'] * 101

        # Paso 2: tokens desde CSV del día
        for tok in tokens_csv:
            cod = tok[:4]
            try:
                idx = parametros['CODIGO'].index(cod)
                lista_guiones[idx] = tok
            except ValueError:
                pass

        # Paso 3: tokens desde auxiliar (solo si no fue ya rellenado)
        for tok in tokens_aux:
            cod = tok[:4]
            try:
                idx = parametros['CODIGO'].index(cod)
                if lista_guiones[idx] == '-':
                    lista_guiones[idx] = tok
            except ValueError:
                pass

        # Paso 4: generar token por existencia real de .mseed del evento
        timestamp_ev = t_ini.strftime('_%Y%m%d_%H%M%S.mseed')
        total_estaciones = min(101, len(parametros['CODIGO']))
        for idx in range(total_estaciones):
            if lista_guiones[idx] != '-':
                continue  # ya cubierto por CSV o AUX

            nombre_mseed_ev = os.path.join(
                directorios['Directorio_eventos'],
                parametros['CODIGO'][idx] + timestamp_ev
            )
            if os.path.exists(nombre_mseed_ev):
                cod = parametros['CODIGO'][idx]
                canal = str(parametros['COMPONENTE'][idx]) if str(parametros['COMPONENTE'][idx]) else '0'
                hab = '0'  # No aportante si no vino en CSV/AUX
                token_generado = f"{cod}{canal}{hab}000000"
                lista_guiones[idx] = token_generado

        evento = list(evento_auxiliar[:3]) + lista_guiones

    return evento



def codigos(opcion,archivo_abrir):
        def entero():
            dato_salida=str(struct.unpack("<H", archivo_abrir.read(2))[0])
            salida=4
            return (dato_salida,salida)
        def flotante():
            dato_salida=struct.unpack("<q", archivo_abrir.read(8))[0]
            #dato_salida=decimal_a_hexadecimal(struct.unpack("<Q", archivo_abrir.read(8))[0])
            #dato_salida=str(archivo_abrir.read(8))
            salida=10
            return (dato_salida,salida)
        def flotante1():
            dato_salida=struct.unpack("<q", archivo_abrir.read(8))[0]
            #dato_salida=decimal_a_hexadecimal(struct.unpack("<Q", archivo_abrir.read(8))[0])
            #dato_salida=str(archivo_abrir.read(8))
            salida=10
            return (dato_salida,salida)
        def cadena():
            dato_salida=""
            salida=0
            cabecera_0=archivo_abrir.read(2)
            numero_caracteres=struct.unpack("<H", cabecera_0)[0]
            if (numero_caracteres < 64 and numero_caracteres > 0 ): #numero_caracteres<32
                cabecera_0=archivo_abrir.read(numero_caracteres)
                try:
                    dato_salida=str(cabecera_0.decode())
                except UnicodeDecodeError:
                    dato_salida='SENOR PUNGO'
                salida=numero_caracteres+4
                if numero_caracteres==5:
                    cabecera_1=archivo_abrir.read(20)
                    if cabecera_1 == b'\x02\x20\x02\x00\x40\x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00':
                        numero_segundo=int(cabecera_0)
                        return (None,numero_segundo)
            else:
                numero_segundo=0
                return (None,numero_segundo)
                
            return (dato_salida,salida)
        def default():
            return ('',1)
#Dictionary mapping
        dict={
            b'\x02\x00': entero,
            b'\x05\x00': flotante1,
            b'\x06\x00': flotante,
            b'\x08\x00': cadena,
        }
        aux=dict.get(opcion,default)()    
        return(aux)#return(aux,numero_segundo)



def loc_cabecera(archivo_abrir):
    puntero=0
    bandera_1=1
    bandera_2=0
    dato=[]
    configuracion=[]
    numero_segundo=0
    contador=0
    #Ubica la posición de la cabecera en el registro continuo, sea de un sismo o del registro continuo.
    #global archivo_abrir
    while bandera_1:
        #input()
        archivo_abrir.seek(puntero)     # Ubica el puntero en cierta dirección del archivo
        cabecera_0=archivo_abrir.read(2)
        resultado=codigos(cabecera_0,archivo_abrir)
        if resultado[0]==None:
            numero_segundo=resultado[1]
            puntero=archivo_abrir.tell()
            bandera_1=0
            break
        else:
            if resultado[0]=='canal':
                bandera_2=1
        puntero=puntero+resultado[1]
        if bandera_2:
            dato.append(resultado[0])
            contador+=1
            if contador==9:
                configuracion.append(dato)
                dato=[]
                contador=0
        if len(cabecera_0) == 0:
            bandera_1=0
    archivo_abrir.seek(puntero) #Devuelve la ubicaciòn justo en donde está el numero de segundo.
    return(numero_segundo,configuracion,puntero-20)

def binario_a_mseed(archivo_binario):
    #archivo_binario    Archivo binario para la lectura, puede ser registro continuo o un evento .sis
    archivo=referencia_directorio_completa(archivo_binario)
    directorios=obtener_directorios(archivo)
    canal = [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]]   # canal Variable  para la lectura desde el archivo binario
    archivo_abrir = open(archivo_binario,'rb')
    numero_segundo,configuracion,puntero=loc_cabecera(archivo_abrir)  #return(numero_segundo,configuracion,puntero-20)
    archivo_abrir.close()
    escritura_archivo(directorios['archivo_estaciones'],configuracion)
    archivo_abrir = open(archivo_binario,'rb')
    bandera=1
    archivo_abrir.seek(puntero)
    while bandera:
        cabecera_1=archivo_abrir.read(20)
        if cabecera_1 == b'\x02\x20\x02\x00\x40\x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00':
            puntero=archivo_abrir.tell()
            cuerpo_=archivo_abrir.read(2048)
            if len(cuerpo_)<2048:
                bandera=0
                break
            archivo_abrir.seek(puntero)
            for k in range(0, 64):
                for m in range(0,16):
                    dato=struct.unpack("<h", archivo_abrir.read(2))
                    canal[m].append(dato[0])
        else:
            bandera=0
            break
    archivo_abrir.close()
    hab_canal=[]
    nombre_canal=[]
    fecha = obtencion_hora(archivo_binario)
    for i in range(0,16):
        hab_canal.append(configuracion[i+1][1])
        nombre_canal.append(configuracion[i+1][2])
    canal_np=np.asarray(canal)
    conversion_mseed(canal_np,hab_canal,nombre_canal,fecha,directorios['Directorio_eventos'])
    return nombre_canal

def referencia_directorio_completa(archivo) -> str:
    """
    Devuelve la ruta estándar …\DIA\AAAAMMDD000000.

    · Si la ruta ya es exactamente …\DIA\AAAAMMDD000000     → se devuelve tal cual.
    · Si la ruta es …\DIA\AAAAMMDD000000.[ext]              → se quita la extensión.
    · Para cualquier archivo bajo …\DIA\…                   →
      extrae la fecha de las carpetas o del nombre y devuelve …\DIA\AAAAMMDD000000.
    """
    ruta = Path(archivo).expanduser().resolve()
    partes = ruta.parts

    # ------------------------------------------------------------------ #
    # 1) Ubicar la carpeta “DIA” en la ruta.
    # ------------------------------------------------------------------ #
    try:
        idx_dia = next(i for i, p in enumerate(partes) if p.upper() == "DIA")
    except StopIteration:
        raise ValueError("La ruta no contiene un directorio 'DIA'.")

    directorio_dia = Path(*partes[:idx_dia + 1])       # …\DIA

    # ------------------------------------------------------------------ #
    # 2) CASO 1: la entrada YA tiene la forma …\DIA\AAAAMMDD000000 o
    #            …\DIA\AAAAMMDD000000.[ext]  → salir pronto.
    # ------------------------------------------------------------------ #
    if len(partes) == idx_dia + 2:
        nombre = Path(partes[-1]).stem
        if nombre.isdigit() and len(nombre) == 14 and nombre.endswith("000000"):
            return os.path.join(directorio_dia, nombre)

    # ------------------------------------------------------------------ #
    # 3) Intentar extraer la fecha (YYYYMMDD) del nombre de archivo
    # ------------------------------------------------------------------ #
    stem_limpio = ruta.stem.replace("_", "")
    m = re.search(r'(20\d{6})', stem_limpio)
    if m:
        return os.path.join(directorio_dia, f"{m.group(1)}000000")

    # ------------------------------------------------------------------ #
    # 4) Extraer de las carpetas bajo DIA (soporta YYYY_MM_DD con o sin AAAA)
    # ------------------------------------------------------------------ #
    for parte in reversed(partes[idx_dia + 1:]):
        sub = parte.split("_")
        if len(sub) == 3 and len(sub[0]) == 4 and len(sub[1]) == 2 and len(sub[2]) == 2:
            return os.path.join(directorio_dia, f"{sub[0]}{sub[1]}{sub[2]}000000")
        elif len(parte) == 8 and parte.isdigit():
            return os.path.join(directorio_dia, f"{parte}000000")

    # Fallback clásico
    try:
        anio = partes[idx_dia + 1]
        mes  = partes[idx_dia + 2].split("_")[1]
        dia  = partes[idx_dia + 3].split("_")[2]
        return os.path.join(directorio_dia, f"{anio}{mes}{dia}000000")
    except Exception:
        raise ValueError(
            f"No se pudo determinar la referencia del día para la ruta: {archivo}"
        )

def ubicacion(latitud,longitud):
    coordenadas=[]
    latitud=float(latitud)
    longitud=float(longitud)

    poblaciones=os.path.join(ruta_datos,"poblaciones.csv")
    coordenadas=lectura_archivo(poblaciones)
    auxiliar=len(coordenadas)
    distancia=pow(pow(longitud-float(coordenadas[1][0]),2)+pow(latitud-float(coordenadas[1][1]),2),0.5)
    indice=1
    for i in range(1,auxiliar):
        a=pow(longitud-float(coordenadas[i][0]),2)+pow(latitud-float(coordenadas[i][1]),2)
        d=pow(a,0.5)
        if d<distancia:
            distancia=d
            indice=i
    distancia=int(round(distancia*111.321,0))
    if coordenadas[indice][2]==" ":
        ubi_s="a "+str(distancia)+" Km. de "+coordenadas[indice][3]
    else:
        ubi_s="a "+str(distancia)+" Km. de "+coordenadas[indice][3]+" ("+coordenadas[indice][2]+")"
    if coordenadas[indice][4]=="parroquia":
        ubi_s=ubi_s+", cantón "+coordenadas[indice][6]
    if coordenadas[indice][4]=="Ciudad":
        ubi_s="a "+str(distancia)+" Km. de la Ciudad de "+coordenadas[indice][3]    
    ubi_s=ubi_s+", "+coordenadas[indice][5]
    return (ubi_s)



##return((id_sismo,anio_sismo,mes_sismo,dia_sismo,hora_sismo,minuto_sismo,segundo_sismo,latitud,longitud,profundidad,rms,ex,ey,e0,ez,magnitud,'Md','RSA',ruta,ubicacion_sismo),estaciones_evento,archivo_rsa,datos_estaciones)
def agregar_evento(root,sismo,estaciones_sismo):
    sismo_campos=['id_evento', 'anio', 'mes', 'dia', 'hora', 'minuto', 'segundo', 'latitud', 'longitud', 'profundidad', 'rms', 'e_x', 'e_y', 'e_0', 'e_z', 'magnitud', 'tipo_magnitud', 'fuente', 'ruta', 'ubicacion']


# Creación del elemento Evento
    evento = ET.SubElement(root, "Evento")
    
# Creación de los elementos hijo del elemento Evento

    for i, nombre_campo in enumerate(sismo_campos):
        campo_estacion = ET.SubElement(evento, nombre_campo)
        campo_estacion.text = str(sismo[i])

# Añadir las estaciones como sub-elementos de "sismo"
    estaciones = ET.SubElement(evento, "estaciones")

    for i,est in enumerate(estaciones_sismo):
        if i==0:
            estaciones_campos=est
        else:
            estacion = ET.SubElement(estaciones, "estacion")
            for j, campo in enumerate(est):
                nombre_campo = estaciones_campos[j]
                campo_estacion = ET.SubElement(estacion, nombre_campo)
                campo_estacion.text = str(campo)
    return root
        

def obtener_datos_reporte(fecha_ini, fecha_fin, directorio_trabajo, mapa_="Ecuador", tipo_forzado=None):
    """
    Retorna:
        - periodo_reporte (str): Texto descriptivo del período
        - directorio_reporte (str): Ruta base unificada donde se guardará el reporte
        - archivo_reporte (str): Prefijo de ruta completo incluyendo región y nombre base

    Estructura unificada de directorios bajo `directorio_trabajo` (DIA):
        - Tipo 0 (Anual)   : DIA/<AAAA>/reportes/<Región>/<AAAA>_*
        - Tipo 1 (Mensual) : DIA/<AAAA>/<AAAA_MM>/reporte/<Región>/<Mes> del <AAAA>_*
        - Tipo 2 (Semanal) : DIA/<AAAA_fin>/reportes/semanal/semana<WW>/<Región>/Semana <WW>_*
        - Tipo 3 (Período) : DIA/<AAAA_fin>/reportes/periodos/<AAAA_MM_DD_ini>_<AAAA_MM_DD_fin>/<Región>/<dd_mm_aaaa a dd_mm_aaaa>_*
    """

    def dias_mes(anio, mes):
        """Retorna el último día del mes, considerando años bisiestos."""
        return calendar.monthrange(anio, mes)[1]

    def deducir_tipo(f_ini, f_fin):
        """Deducción automática del tipo de reporte cuando no se especifica `tipo_forzado`."""
        if f_ini > f_fin:
            f_ini, f_fin = f_fin, f_ini

        # Año completo
        if (f_ini.month, f_ini.day) == (1, 1) and (f_fin.month, f_fin.day) == (12, 31) and f_ini.year == f_fin.year:
            return 0

        # Mes completo
        ultimo_dia = dias_mes(f_ini.year, f_ini.month)
        if (f_ini.day == 1 and
            f_ini.year == f_fin.year and
            f_ini.month == f_fin.month and
            f_fin.day == ultimo_dia):
            return 1

        # Semana completa (lunes a domingo)
        delta = f_fin - f_ini
        if delta.days == 6 and f_ini.weekday() == 0 and f_fin.weekday() == 6:
            return 2

        return 3  # Rango de fechas (Período inicio - fin)

    # --- Inicialización ---
    fecha_ini = fecha_ini.date() if isinstance(fecha_ini, datetime) else fecha_ini
    fecha_fin = fecha_fin.date() if isinstance(fecha_fin, datetime) else fecha_fin
    if fecha_ini > fecha_fin:
        fecha_ini, fecha_fin = fecha_fin, fecha_ini

    meses_es = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    tipo = int(tipo_forzado) if tipo_forzado is not None else deducir_tipo(fecha_ini, fecha_fin)
    anio = str(fecha_ini.year)
    anio_fin = str(fecha_fin.year)
    mes = meses_es[fecha_ini.month - 1]  # Nombre del mes
    semana = f"{fecha_ini.isocalendar()[1]:02d}"  # Número de semana ISO
    fecha_q_ini = QDate(fecha_ini.year, fecha_ini.month, fecha_ini.day)
    fecha_q_fin = QDate(fecha_fin.year, fecha_fin.month, fecha_fin.day)
    base_trabajo = str(directorio_trabajo).rstrip('/\\')

    # --- Generación del período y ruta unificada según tipo ---
    if tipo == 0:
        periodo_reporte = f"Período: {anio}"
        directorio_reporte = f"{base_trabajo}/{anio}/reportes"

    elif tipo == 1:
        periodo_reporte = f"Período: {mes} del {anio}"
        directorio_reporte = base_trabajo + fecha_q_ini.toString('/yyyy/yyyy_MM/reporte')

    elif tipo == 2:
        periodo_reporte = (
            f"Semana {semana} del {anio}: del {fecha_q_ini.toString('dd/MM/yyyy')} "
            f"al /{fecha_q_fin.toString('dd/MM/yyyy')}"
        )
        directorio_reporte = f"{base_trabajo}/{anio_fin}/reportes/semanal/semana{semana}"

    elif tipo == 3:
        periodo_reporte = (
            f"Período: {fecha_q_ini.toString('dd/MM/yyyy')} a {fecha_q_fin.toString('dd/MM/yyyy')}"
        )
        rango_carpeta = (
            f"{fecha_q_ini.toString('yyyy_MM_dd')}_{fecha_q_fin.toString('yyyy_MM_dd')}"
        )
        directorio_reporte = f"{base_trabajo}/{anio_fin}/reportes/periodos/{rango_carpeta}"

    else:
        periodo_reporte = ""
        directorio_reporte = ""

    if periodo_reporte.startswith("Período: "):
        nombre_archivo = periodo_reporte[9:].replace('/', '_')
    else:
        nombre_archivo = periodo_reporte[:10].strip()
    archivo_reporte = f"{directorio_reporte}/{mapa_}/{nombre_archivo}"
    return periodo_reporte, directorio_reporte, archivo_reporte

def generar_directorios_unidades_basicas(
    fecha_ini,
    fecha_fin,
    directorio_trabajo="G:/Mi unidad/DIA",
    verificar_existencia=False,
    detallar=False,
    nivel_maximo="ANIO",
):
    """
    Descompone jerárquicamente el intervalo [fecha_ini, fecha_fin] en unidades básicas
    siguiendo la estructura telescópica:
        días -> semanas -> meses -> años -> meses -> semanas -> días

    Jerarquía de consolidación:
      1. Años completos (01/01/AAAA al 31/12/AAAA)
      2. Meses completos (01/MM/AAAA al último día del mes)
      3. Semanas ISO completas (Lunes a Domingo, 7 días)
      4. Días individuales (AAMMDD000000)

    Si `verificar_existencia=True`, cada bloque mayor (Año, Mes, Semana o Período exacto)
    solo se selecciona si su archivo `<prefijo>_cat.csv` ya existe en disco (bajo la
    carpeta `Ecuador`); de lo contrario, ese sub-intervalo desciende automáticamente
    al siguiente nivel más fino (Año -> Mes -> Semana -> Día).

    Parámetros:
        fecha_ini (date | datetime): Fecha inicial del rango.
        fecha_fin (date | datetime): Fecha final del rango.
        directorio_trabajo (str): Ruta base del directorio de trabajo (`DIA`).
        verificar_existencia (bool): Si True, valida en disco la existencia de `<prefijo>_cat.csv`.
        detallar (bool): Si True, retorna diccionarios con metadatos de cada unidad;
                         si False, retorna la lista de prefijos de ruta (`List[str]`).
        nivel_maximo (str): Nivel máximo de consolidación ('ANIO', 'MES', 'SEMANA' o 'DIA').

    Retorna:
        List[str] | List[dict]: Lista ordenada cronológicamente de unidades básicas.
    """
    f_ini = fecha_ini.date() if isinstance(fecha_ini, datetime) else fecha_ini
    f_fin = fecha_fin.date() if isinstance(fecha_fin, datetime) else fecha_fin
    if f_ini > f_fin:
        f_ini, f_fin = f_fin, f_ini

    base_trabajo = str(directorio_trabajo).rstrip('/\\')

    def _unidad_valida(u_ini, u_fin, tipo_forzado):
        _, _, prefijo = obtener_datos_reporte(
            u_ini, u_fin, base_trabajo, mapa_="Ecuador", tipo_forzado=tipo_forzado
        )
        if not verificar_existencia:
            return prefijo
        if os.path.isfile(f"{prefijo}_cat.csv"):
            return prefijo
        return None

    def _descomponer_anio(ini, fin):
        for anio in range(ini.year, fin.year + 1):
            ini_anio = date(anio, 1, 1)
            fin_anio = date(anio, 12, 31)
            if ini_anio >= ini and fin_anio <= fin:
                prefijo = _unidad_valida(ini_anio, fin_anio, tipo_forzado=0)
                if prefijo is not None:
                    izquierda = _descomponer_anio(ini, ini_anio - timedelta(days=1)) if ini < ini_anio else []
                    centro = [{
                        'tipo': 'ANIO',
                        'fecha_ini': ini_anio,
                        'fecha_fin': fin_anio,
                        'prefijo': prefijo,
                    }]
                    derecha = _descomponer_anio(fin_anio + timedelta(days=1), fin) if fin_anio < fin else []
                    return izquierda + centro + derecha
        return _descomponer_mes(ini, fin)

    def _descomponer_mes(ini, fin):
        anio_act, mes_act = ini.year, ini.month
        while (anio_act, mes_act) <= (fin.year, fin.month):
            ini_mes = date(anio_act, mes_act, 1)
            ult_dia = calendar.monthrange(anio_act, mes_act)[1]
            fin_mes = date(anio_act, mes_act, ult_dia)
            if ini_mes >= ini and fin_mes <= fin:
                prefijo = _unidad_valida(ini_mes, fin_mes, tipo_forzado=1)
                if prefijo is not None:
                    izquierda = _descomponer_mes(ini, ini_mes - timedelta(days=1)) if ini < ini_mes else []
                    centro = [{
                        'tipo': 'MES',
                        'fecha_ini': ini_mes,
                        'fecha_fin': fin_mes,
                        'prefijo': prefijo,
                    }]
                    derecha = _descomponer_mes(fin_mes + timedelta(days=1), fin) if fin_mes < fin else []
                    return izquierda + centro + derecha
            if mes_act == 12:
                anio_act += 1
                mes_act = 1
            else:
                mes_act += 1
        return _descomponer_semana(ini, fin)

    def _descomponer_semana(ini, fin):
        dias_hasta_lunes = (7 - ini.weekday()) % 7
        ini_sem = ini + timedelta(days=dias_hasta_lunes)
        while ini_sem + timedelta(days=6) <= fin:
            fin_sem = ini_sem + timedelta(days=6)
            prefijo = _unidad_valida(ini_sem, fin_sem, tipo_forzado=2)
            if prefijo is not None:
                izquierda = _descomponer_semana(ini, ini_sem - timedelta(days=1)) if ini < ini_sem else []
                centro = [{
                    'tipo': 'SEMANA',
                    'fecha_ini': ini_sem,
                    'fecha_fin': fin_sem,
                    'prefijo': prefijo,
                }]
                derecha = _descomponer_semana(fin_sem + timedelta(days=1), fin) if fin_sem < fin else []
                return izquierda + centro + derecha
            ini_sem += timedelta(days=7)
        return _descomponer_dia(ini, fin)

    def _descomponer_dia(ini, fin):
        unidades_dia = []
        actual = ini
        while actual <= fin:
            anio_s = f"{actual.year:04d}"
            mes_s = f"{actual.year:04d}_{actual.month:02d}"
            dia_s = f"{actual.year:04d}_{actual.month:02d}_{actual.day:02d}"
            carpeta_dia = f"{base_trabajo}/{anio_s}/{mes_s}/{dia_s}"
            prefijo_2d = f"{str(actual.year)[2:]:0>2}{actual.month:02d}{actual.day:02d}000000"
            prefijo_4d = f"{actual.year:04d}{actual.month:02d}{actual.day:02d}000000"
            ruta_2d = f"{carpeta_dia}/{prefijo_2d}"
            ruta_4d = f"{carpeta_dia}/{prefijo_4d}"
            if not os.path.isfile(f"{ruta_2d}_cat.csv") and os.path.isfile(f"{ruta_4d}_cat.csv"):
                ruta_prefijo = ruta_4d
            else:
                ruta_prefijo = ruta_2d
            unidades_dia.append({
                'tipo': 'DIA',
                'fecha_ini': actual,
                'fecha_fin': actual,
                'prefijo': ruta_prefijo,
            })
            actual += timedelta(days=1)
        return unidades_dia

    nivel_norm = str(nivel_maximo or "ANIO").upper()
    if nivel_norm == "DIA":
        unidades = _descomponer_dia(f_ini, f_fin)
    elif nivel_norm == "SEMANA":
        unidades = _descomponer_semana(f_ini, f_fin)
    elif nivel_norm == "MES":
        unidades = _descomponer_mes(f_ini, f_fin)
    else:
        # Si el reporte exacto del período completo [f_ini, f_fin] ya fue emitido en Ecuador,
        # tomarlo directamente por defecto antes de descomponer en sub-unidades
        prefijo_exacto = _unidad_valida(f_ini, f_fin, tipo_forzado=None) if verificar_existencia else None
        if prefijo_exacto is not None and f_ini != f_fin:
            if (f_ini.month, f_ini.day) == (1, 1) and (f_fin.month, f_fin.day) == (12, 31) and f_ini.year == f_fin.year:
                tipo_ex = 'ANIO'
            elif (
                f_ini.day == 1
                and f_ini.year == f_fin.year
                and f_ini.month == f_fin.month
                and f_fin.day == calendar.monthrange(f_ini.year, f_ini.month)[1]
            ):
                tipo_ex = 'MES'
            elif (f_fin - f_ini).days == 6 and f_ini.weekday() == 0 and f_fin.weekday() == 6:
                tipo_ex = 'SEMANA'
            else:
                tipo_ex = 'PERIODO'
            unidades = [{
                'tipo': tipo_ex,
                'fecha_ini': f_ini,
                'fecha_fin': f_fin,
                'prefijo': prefijo_exacto,
            }]
        else:
            unidades = _descomponer_anio(f_ini, f_fin)

    if detallar:
        return unidades
    return [u['prefijo'] for u in unidades]


def consolidar_archivos_periodo_ecuador(
    fecha_ini,
    fecha_fin,
    directorio_trabajo="G:/Mi unidad/DIA",
    tipo_forzado=None,
    nivel_maximo="DIA",
):
    """
    Reconstruye y guarda todos los archivos de datos consolidados de un período
    (Semana, Mes o Año) en la carpeta `Ecuador` SIN generar archivos PDF:
      - `<prefijo>_cat.csv`
      - `<prefijo>_rep.csv`
      - `<prefijo>_rep_total.csv`
      - `<prefijo>_res.csv`
      - `<prefijo>.xml`
      - `<prefijo>__rsa_sup/med/pro.csv` y `<prefijo>__otr_sup/med/pro.csv`
    """
    f_ini = fecha_ini.date() if isinstance(fecha_ini, datetime) else fecha_ini
    f_fin = fecha_fin.date() if isinstance(fecha_fin, datetime) else fecha_fin
    if f_ini > f_fin:
        f_ini, f_fin = f_fin, f_ini

    _, _, prefijo_salida = obtener_datos_reporte(
        f_ini, f_fin, directorio_trabajo, mapa_="Ecuador", tipo_forzado=tipo_forzado
    )
    Path(os.path.dirname(prefijo_salida)).mkdir(parents=True, exist_ok=True)

    unidades = generar_directorios_unidades_basicas(
        f_ini,
        f_fin,
        directorio_trabajo=directorio_trabajo,
        verificar_existencia=True,
        detallar=True,
        nivel_maximo=nivel_maximo,
    )

    catalogo = [[
        "Id", "año", "mes", "día", "hora", "min", "seg", "lat", "long", "prof",
        "rms", "e-x", "e-y", "e-0", "e-z", "Mag", "Tipo Mag", "Fuente", "ruta", "Ubicación"
    ]]
    eventos_reporte = [[
        "Nº", "Fecha Hora (UTC)", "Evento", "Magn.", "Prof.(km)", "Lat.", "Long.", "Ubicación"
    ]]
    resumen = [["DIA", "SISMO", "FF", "FC", "TELESISMO", "Evento Local", "INDEFINIDO", "Ruido"]]
    reporte_total = [[
        "RESPONSABLE", "HORA", "TOT.", "SIS.", "FF", "FC", "IND.", "TEL.",
        "Local_CONTROL.", "Ruido", "3 est", "4 est", "5 est", "6 est", "7 est", "8 est"
    ]]
    raiz_xml = ET.Element("sismo")

    for unidad in unidades:
        tipo_u = unidad['tipo']
        prefijo = unidad['prefijo']
        ruta_cat = f"{prefijo}_cat.csv"

        if os.path.isfile(ruta_cat):
            datos_cat = lectura_archivo(ruta_cat)
            if datos_cat and datos_cat[0][0] == "Id":
                catalogo.extend(datos_cat[1:])
            elif datos_cat:
                catalogo.extend(datos_cat)

        if tipo_u in ('ANIO', 'MES', 'SEMANA'):
            ruta_rep = f"{prefijo}_rep.csv"
            ruta_res = f"{prefijo}_res.csv"
            ruta_rtot = f"{prefijo}_rep_total.csv"
            ruta_xml = f"{prefijo}.xml"

            if os.path.isfile(ruta_rep):
                d_rep = lectura_archivo(ruta_rep)
                if d_rep and d_rep[0][0] in ("Nº", "0"):
                    eventos_reporte.extend(d_rep[1:])
                elif d_rep:
                    eventos_reporte.extend(d_rep)
            if os.path.isfile(ruta_res):
                d_res = lectura_resumen(ruta_res)
                for fila_r in (d_res or []):
                    if not fila_r or fila_r[0] in ("DIA", "Total:"):
                        continue
                    resumen.append(list(fila_r[-7:]) if len(fila_r) >= 8 else list(fila_r))
            if os.path.isfile(ruta_rtot):
                d_rtot = lectura_resumen(ruta_rtot)
                reporte_total.extend(
                    [list(r) for r in (d_rtot or []) if r and r[0] != "RESPONSABLE"]
                )
            if os.path.isfile(ruta_xml):
                try:
                    raiz_u = ET.parse(ruta_xml).getroot()
                    for child in raiz_u:
                        raiz_xml.append(child)
                except Exception:
                    pass
        else:
            # Unidad DIA individual
            ruta_rep = f"{prefijo}_rep.csv"
            if not os.path.isfile(ruta_rep):
                ruta_rep = f"{prefijo}_dat.csv"
            ruta_res = f"{prefijo}_res.csv"
            carpeta_dia = os.path.dirname(prefijo)
            stem_dia = os.path.basename(prefijo)
            pref_fecha_dia = stem_dia[:-6] if stem_dia.endswith("000000") else stem_dia[:6]
            ruta_resp = os.path.join(carpeta_dia, "reportes", f"{pref_fecha_dia}_resp.csv")
            if not os.path.isfile(ruta_resp):
                ruta_resp = f"{prefijo}_responsables.csv"
            ruta_xml = f"{prefijo}.xml"

            if os.path.isfile(ruta_rep):
                d_rep = lectura_archivo(ruta_rep)
                if d_rep and d_rep[0][0] in ("Nº", "0"):
                    eventos_reporte.extend(d_rep[1:])
                elif d_rep:
                    eventos_reporte.extend(d_rep)
            if os.path.isfile(ruta_res):
                for fila_r in (lectura_resumen(ruta_res) or []):
                    if fila_r and fila_r[0] not in ("DIA", "Total:", "SISMO"):
                        resumen.append(list(fila_r[-7:]) if len(fila_r) >= 8 else list(fila_r))
            if os.path.isfile(ruta_resp):
                for fila_rt in (lectura_resumen(ruta_resp) or []):
                    if fila_rt and fila_rt[0] != "RESPONSABLE":
                        reporte_total.append(list(fila_rt))
            if os.path.isfile(ruta_xml):
                try:
                    raiz_d = ET.parse(ruta_xml).getroot()
                    for child in raiz_d:
                        raiz_xml.append(child)
                except Exception:
                    pass

    # Eliminar posibles duplicados por Id manteniendo cabecera
    vistos_id = set()
    catalogo_unico = [catalogo[0]]
    for fila_c in catalogo[1:]:
        if not fila_c:
            continue
        clave_id = str(fila_c[0]).strip()
        if clave_id not in vistos_id:
            vistos_id.add(clave_id)
            catalogo_unico.append(fila_c)
    catalogo = sorted(catalogo_unico[1:], key=lambda x: str(x[0]))
    catalogo.insert(0, catalogo_unico[0])

    # Contabilizar totales globales del período para `<prefijo>_res.csv`
    cont_sismos = 0
    cont_FF = 0
    cont_FC = 0
    cont_tel = 0
    cont_ev = 0
    cont_ind = 0
    cont_ruido = 0
    for fila_ev in eventos_reporte[1:]:
        if len(fila_ev) < 3:
            continue
        tipo_ev = fila_ev[2]
        if tipo_ev == "SISMO":
            cont_sismos += 1
        elif tipo_ev == "FF":
            cont_FF += 1
        elif tipo_ev == "FC":
            cont_FC += 1
        elif tipo_ev == "TELESISMO":
            cont_tel += 1
        elif tipo_ev in ("Evento_local", "CONTROL"):
            cont_ev += 1
        elif tipo_ev == "Ruido":
            cont_ruido += 1
        elif tipo_ev == "INDEFINIDO":
            cont_ind += 1

    resumen_salida = [list(r) for r in resumen]
    resumen_salida.insert(
        1,
        ["Total:", cont_sismos, cont_FF, cont_FC, cont_tel, cont_ev, cont_ind, cont_ruido],
    )
    for idx_r in range(2, len(resumen_salida)):
        resumen_salida[idx_r].insert(0, idx_r - 1)

    # Clasificar eventos del catálogo por estrato de profundidad y red para CSVs SIG
    even_rsa_sup = [["LAT", "LONG", "Prof.", "Mag."]]
    even_rsa_int = [["LAT", "LONG", "Prof.", "Mag."]]
    even_rsa_prof = [["LAT", "LONG", "Prof.", "Mag."]]
    even_otr_sup = [["LAT", "LONG", "Prof.", "Mag."]]
    even_otr_int = [["LAT", "LONG", "Prof.", "Mag."]]
    even_otr_prof = [["LAT", "LONG", "Prof.", "Mag."]]

    for fila_c in catalogo[1:]:
        try:
            lat_c = float(fila_c[IDX_LATITUD])
            lon_c = float(fila_c[IDX_LONGITUD])
            prof_c = -1.0 * float(fila_c[IDX_PROFUNDIDAD])
            mag_c = float(fila_c[IDX_MAGNITUD])
            es_rsa = (fila_c[IDX_FUENTE] == "RSA")
            ev_sig = [lat_c, lon_c, prof_c, mag_c]
            if prof_c > -40.0:
                (even_rsa_sup if es_rsa else even_otr_sup).append(ev_sig)
            elif prof_c > -70.0:
                (even_rsa_int if es_rsa else even_otr_int).append(ev_sig)
            else:
                (even_rsa_prof if es_rsa else even_otr_prof).append(ev_sig)
        except (ValueError, IndexError):
            continue

    # Escritura de todos los archivos consolidados en la carpeta Ecuador
    escritura_archivo(f"{prefijo_salida}_cat.csv", catalogo)
    escritura_archivo(f"{prefijo_salida}_rep.csv", eventos_reporte)
    escritura_archivo(f"{prefijo_salida}_rep_total.csv", reporte_total)
    escritura_archivo(f"{prefijo_salida}_res.csv", resumen_salida)

    pares_sig = [
        (f"{prefijo_salida}__rsa_sup.csv", even_rsa_sup),
        (f"{prefijo_salida}__rsa_med.csv", even_rsa_int),
        (f"{prefijo_salida}__rsa_pro.csv", even_rsa_prof),
        (f"{prefijo_salida}__otr_sup.csv", even_otr_sup),
        (f"{prefijo_salida}__otr_med.csv", even_otr_int),
        (f"{prefijo_salida}__otr_pro.csv", even_otr_prof),
    ]
    for ruta_sig, datos_sig in pares_sig:
        with open(ruta_sig, "w", newline="", encoding="utf-8") as f_sig:
            escritor_sig = csv.writer(f_sig, delimiter=",")
            for fila_sig in datos_sig:
                escritor_sig.writerow(fila_sig)

    ET.ElementTree(raiz_xml).write(
        f"{prefijo_salida}.xml", encoding="utf-8", xml_declaration=True
    )
    return prefijo_salida


def _pertenece_fila_cat_a_fecha(fila: list, fecha_d: date) -> bool:
    """Determina si una fila de `_cat.csv` pertenece a la fecha `fecha_d`."""
    if not fila or len(fila) < 19 or fila[0] == "Id":
        return False
    pref_8 = fecha_d.strftime("%Y%m%d")
    pref_6 = fecha_d.strftime("%y%m%d")
    id_str = str(fila[0]).strip()
    if id_str.startswith(pref_8):
        return True
    ruta_nom = os.path.basename(str(fila[18]).strip())
    if ruta_nom.startswith(f"{pref_6}_") or ruta_nom.startswith(f"{pref_8}_"):
        return True
    try:
        return (int(fila[1]), int(fila[2]), int(fila[3])) == (fecha_d.year, fecha_d.month, fecha_d.day)
    except (ValueError, TypeError, IndexError):
        return False


def _extraer_fecha_fila_rep(fila: list):
    """Extrae un `date` desde la columna 1 de una fila de `_rep.csv` si es posible."""
    if not fila or len(fila) < 2 or fila[0] in ("Nº", "0"):
        return None
    txt = os.path.basename(str(fila[1]).strip())
    m_barra = re.match(r"^(20\d{2})/(\d{2})/(\d{2})", txt)
    if m_barra:
        try:
            return date(int(m_barra.group(1)), int(m_barra.group(2)), int(m_barra.group(3)))
        except ValueError:
            return None
    m8 = re.match(r"^(20\d{2})(\d{2})(\d{2})[_]", txt)
    if m8:
        try:
            return date(int(m8.group(1)), int(m8.group(2)), int(m8.group(3)))
        except ValueError:
            return None
    m6 = re.match(r"^(\d{2})(\d{2})(\d{2})[_]", txt)
    if m6:
        try:
            return date(2000 + int(m6.group(1)), int(m6.group(2)), int(m6.group(3)))
        except ValueError:
            return None
    return None


def _reemplazar_dia_en_periodo_emitido(
    prefijo_salida: str,
    fecha_d: date,
    fecha_ini_periodo: date,
    directorio_trabajo: str = "G:/Mi unidad/DIA",
) -> bool:
    """
    Abre los archivos ya emitidos de una unidad de tiempo mayor (Semana ISO, Mes o Año)
    en `Ecuador` y reemplaza quirúrgicamente los registros correspondientes a `fecha_d`
    con los nuevos datos del día, sin necesidad de re-escanear todos los demás días
    del período ni regenerar PDFs.
    """
    ruta_cat_per = f"{prefijo_salida}_cat.csv"
    if not os.path.isfile(ruta_cat_per):
        return False

    info_dia = obtener_directorios(
        os.path.join(directorio_trabajo, fecha_d.strftime("%Y%m%d000000"))
    )
    ruta_cat_dia = info_dia["archivo_catalogo"]
    ruta_rep_dia = info_dia["archivo_reporte"]
    ruta_res_dia = info_dia["archivo_resumen"]
    ruta_xml_dia = info_dia["archivo_xml"]

    # 1) Abrir `_cat.csv` del período y reemplazar las filas de `fecha_d`
    cat_per = lectura_archivo(ruta_cat_per) or []
    cabecera_cat = (
        cat_per[0]
        if cat_per and cat_per[0] and cat_per[0][0] == "Id"
        else [
            "Id", "año", "mes", "día", "hora", "min", "seg", "lat", "long", "prof",
            "rms", "e-x", "e-y", "e-0", "e-z", "Mag", "Tipo Mag", "Fuente", "ruta", "Ubicación"
        ]
    )
    filas_cat_conservadas = [
        f for f in (cat_per[1:] if cat_per and cat_per[0][0] == "Id" else cat_per)
        if f and not _pertenece_fila_cat_a_fecha(f, fecha_d)
    ]

    cat_dia = lectura_archivo(ruta_cat_dia) if os.path.isfile(ruta_cat_dia) else []
    filas_cat_nuevas = [
        f for f in (cat_dia[1:] if cat_dia and cat_dia[0][0] == "Id" else (cat_dia or []))
        if f and len(f) >= 19 and str(f[0]).strip() not in ("Id", "00000000000000")
    ]

    combinadas_cat = filas_cat_conservadas + filas_cat_nuevas
    vistos_cat = set()
    unicas_cat = []
    for f in combinadas_cat:
        clave = (str(f[0]).strip(), str(f[17]).strip(), str(f[18]).strip())
        if clave not in vistos_cat:
            vistos_cat.add(clave)
            unicas_cat.append(f)
    unicas_cat.sort(key=lambda x: str(x[0]).strip())
    catalogo_actualizado = [cabecera_cat] + unicas_cat
    escritura_archivo(ruta_cat_per, catalogo_actualizado)

    # Actualizar también los 6 archivos SIG (__rsa_sup/med/pro.csv y __otr_sup/med/pro.csv)
    even_rsa_sup = [["LAT", "LONG", "Prof.", "Mag."]]
    even_rsa_int = [["LAT", "LONG", "Prof.", "Mag."]]
    even_rsa_prof = [["LAT", "LONG", "Prof.", "Mag."]]
    even_otr_sup = [["LAT", "LONG", "Prof.", "Mag."]]
    even_otr_int = [["LAT", "LONG", "Prof.", "Mag."]]
    even_otr_prof = [["LAT", "LONG", "Prof.", "Mag."]]
    for fila_c in unicas_cat:
        try:
            lat_c = float(fila_c[IDX_LATITUD])
            lon_c = float(fila_c[IDX_LONGITUD])
            prof_c = -1.0 * float(fila_c[IDX_PROFUNDIDAD])
            mag_c = float(fila_c[IDX_MAGNITUD])
            es_rsa = (str(fila_c[IDX_FUENTE]).strip() == "RSA")
            ev_sig = [lat_c, lon_c, prof_c, mag_c]
            if prof_c > -40.0:
                (even_rsa_sup if es_rsa else even_otr_sup).append(ev_sig)
            elif prof_c > -70.0:
                (even_rsa_int if es_rsa else even_otr_int).append(ev_sig)
            else:
                (even_rsa_prof if es_rsa else even_otr_prof).append(ev_sig)
        except (ValueError, IndexError):
            continue

    for ruta_sig, datos_sig in (
        (f"{prefijo_salida}__rsa_sup.csv", even_rsa_sup),
        (f"{prefijo_salida}__rsa_med.csv", even_rsa_int),
        (f"{prefijo_salida}__rsa_pro.csv", even_rsa_prof),
        (f"{prefijo_salida}__otr_sup.csv", even_otr_sup),
        (f"{prefijo_salida}__otr_med.csv", even_otr_int),
        (f"{prefijo_salida}__otr_pro.csv", even_otr_prof),
    ):
        try:
            with open(ruta_sig, "w", newline="", encoding="utf-8") as f_sig:
                escritor_sig = csv.writer(f_sig, delimiter=",")
                for fila_sig in datos_sig:
                    escritor_sig.writerow(fila_sig)
        except Exception:
            pass

    # 2) Abrir `_rep.csv` del período y reemplazar las filas de `fecha_d` en orden cronológico
    ruta_rep_per = f"{prefijo_salida}_rep.csv"
    if os.path.isfile(ruta_rep_per) and os.path.isfile(ruta_rep_dia):
        try:
            rep_per = lectura_archivo(ruta_rep_per) or []
            cabecera_rep = (
                rep_per[0]
                if rep_per and rep_per[0] and rep_per[0][0] in ("Nº", "0")
                else ["Nº", "Fecha Hora (UTC)", "Evento", "Magn.", "Prof.(km)", "Lat.", "Long.", "Ubicación"]
            )
            filas_rep_orig = rep_per[1:] if rep_per and rep_per[0][0] in ("Nº", "0") else rep_per
            rep_dia = lectura_archivo(ruta_rep_dia) or []
            filas_rep_dia = rep_dia[1:] if rep_dia and rep_dia[0][0] in ("Nº", "0") else rep_dia

            antes_rep = []
            despues_rep = []
            en_despues = False
            for f_r in filas_rep_orig:
                f_fecha = _extraer_fecha_fila_rep(f_r)
                if f_fecha == fecha_d:
                    en_despues = True
                    continue
                if f_fecha is not None and f_fecha > fecha_d:
                    en_despues = True
                if not en_despues:
                    antes_rep.append(f_r)
                else:
                    despues_rep.append(f_r)

            escritura_archivo(ruta_rep_per, [cabecera_rep] + antes_rep + filas_rep_dia + despues_rep)
        except Exception:
            pass

    # 3) Abrir `_res.csv` del período y reemplazar la fila del día + recalcular 'Total:'
    ruta_res_per = f"{prefijo_salida}_res.csv"
    if os.path.isfile(ruta_res_per) and os.path.isfile(ruta_res_dia):
        try:
            res_per = lectura_archivo(ruta_res_per) or []
            res_dia = lectura_archivo(ruta_res_dia) or []
            valores_dia = res_dia[1] if len(res_dia) > 1 else (res_dia[0] if res_dia else None)
            idx_dia_periodo = (fecha_d - fecha_ini_periodo).days + 1
            if valores_dia and len(valores_dia) >= 7 and len(res_per) >= 2:
                reemplazado_res = False
                for i_r in range(2, len(res_per)):
                    if res_per[i_r] and str(res_per[i_r][0]).strip() == str(idx_dia_periodo):
                        res_per[i_r] = [str(idx_dia_periodo)] + [str(x) for x in valores_dia[:7]]
                        reemplazado_res = True
                        break
                if reemplazado_res:
                    totales = [0] * 7
                    for i_r in range(2, len(res_per)):
                        if res_per[i_r] and len(res_per[i_r]) >= 8:
                            for col_idx in range(7):
                                try:
                                    totales[col_idx] += int(float(res_per[i_r][col_idx + 1]))
                                except (ValueError, TypeError):
                                    pass
                    res_per[1] = ["Total:"] + [str(t) for t in totales]
                    escritura_archivo(ruta_res_per, res_per)
        except Exception:
            pass

    # 4) Abrir `.xml` del período y reemplazar los nodos `<Evento>` de `fecha_d`
    ruta_xml_per = f"{prefijo_salida}.xml"
    if os.path.isfile(ruta_xml_per) and os.path.isfile(ruta_xml_dia):
        try:
            pref_8 = fecha_d.strftime("%Y%m%d")
            pref_6 = fecha_d.strftime("%y%m%d")
            arbol_per = ET.parse(ruta_xml_per)
            raiz_per = arbol_per.getroot()
            nodos_conservados = []
            for ev_node in list(raiz_per.findall("Evento")):
                id_ev = (ev_node.findtext("id_evento") or "").strip()
                ruta_ev = os.path.basename((ev_node.findtext("ruta") or "").strip())
                if id_ev.startswith(pref_8) or ruta_ev.startswith(f"{pref_6}_") or ruta_ev.startswith(f"{pref_8}_"):
                    continue
                nodos_conservados.append(ev_node)

            raiz_dia = ET.parse(ruta_xml_dia).getroot()
            nodos_nuevos = list(raiz_dia.findall("Evento"))
            todos_nodos = nodos_conservados + nodos_nuevos
            todos_nodos.sort(key=lambda n: (n.findtext("id_evento") or "").strip())

            nueva_raiz = ET.Element("sismo")
            for n_ev in todos_nodos:
                nueva_raiz.append(n_ev)
            ET.ElementTree(nueva_raiz).write(ruta_xml_per, encoding="utf-8", xml_declaration=True)
        except Exception:
            pass

    return True


def actualizar_periodos_emitidos_desde_fecha(fecha_referencia, directorio_trabajo="G:/Mi unidad/DIA"):
    """
    Propaga automáticamente en cascada (Semana ISO -> Mes -> Año) cualquier cambio
    ocurrido en `fecha_referencia`, abriendo los catálogos y archivos ya emitidos en
    la carpeta `Ecuador` y reemplazando los registros del día modificado con los
    nuevos datos (sin regenerar PDFs).

    Parámetros:
        fecha_referencia (date | datetime | str): Fecha del día modificado o ruta de archivo del día.
        directorio_trabajo (str): Ruta base del directorio de trabajo (`DIA`).

    Retorna:
        List[str]: Lista descriptiva de los períodos consolidados que fueron actualizados.
    """
    if isinstance(fecha_referencia, datetime):
        fecha_d = fecha_referencia.date()
    elif isinstance(fecha_referencia, date):
        fecha_d = fecha_referencia
    else:
        texto = str(fecha_referencia)
        m8 = re.search(r'(20\d{2})[_]?(\d{2})[_]?(\d{2})', texto)
        if m8:
            fecha_d = date(int(m8.group(1)), int(m8.group(2)), int(m8.group(3)))
        else:
            m6 = re.search(r'(\d{2})(\d{2})(\d{2})000000', texto)
            if m6:
                fecha_d = date(2000 + int(m6.group(1)), int(m6.group(2)), int(m6.group(3)))
            else:
                return []

    actualizados = []

    # 1. Semana ISO correspondiente (Lunes a Domingo): abre y reemplaza los datos del día
    ini_semana = fecha_d - timedelta(days=fecha_d.weekday())
    fin_semana = ini_semana + timedelta(days=6)
    per_sem, _, pref_sem = obtener_datos_reporte(
        ini_semana, fin_semana, directorio_trabajo, mapa_="Ecuador", tipo_forzado=2
    )
    if os.path.isfile(f"{pref_sem}_cat.csv"):
        try:
            _reemplazar_dia_en_periodo_emitido(pref_sem, fecha_d, ini_semana, directorio_trabajo)
            actualizados.append(f"Semana ({per_sem})")
            print(f"✓ Catálogo semanal actualizado (reemplazo del día {fecha_d}): {pref_sem}_cat.csv")
        except Exception as e:
            print(f"Error actualizando catálogo semanal {pref_sem}: {e}")

    # 2. Mes correspondiente: abre y reemplaza los datos del día
    ini_mes = date(fecha_d.year, fecha_d.month, 1)
    fin_mes = date(fecha_d.year, fecha_d.month, calendar.monthrange(fecha_d.year, fecha_d.month)[1])
    per_mes, _, pref_mes = obtener_datos_reporte(
        ini_mes, fin_mes, directorio_trabajo, mapa_="Ecuador", tipo_forzado=1
    )
    if os.path.isfile(f"{pref_mes}_cat.csv"):
        try:
            _reemplazar_dia_en_periodo_emitido(pref_mes, fecha_d, ini_mes, directorio_trabajo)
            actualizados.append(f"Mes ({per_mes})")
            print(f"✓ Catálogo mensual actualizado (reemplazo del día {fecha_d}): {pref_mes}_cat.csv")
        except Exception as e:
            print(f"Error actualizando catálogo mensual {pref_mes}: {e}")

    # 3. Año correspondiente: abre y reemplaza los datos del día
    ini_anio = date(fecha_d.year, 1, 1)
    fin_anio = date(fecha_d.year, 12, 31)
    per_anio, _, pref_anio = obtener_datos_reporte(
        ini_anio, fin_anio, directorio_trabajo, mapa_="Ecuador", tipo_forzado=0
    )
    if os.path.isfile(f"{pref_anio}_cat.csv"):
        try:
            _reemplazar_dia_en_periodo_emitido(pref_anio, fecha_d, ini_anio, directorio_trabajo)
            actualizados.append(f"Año ({per_anio})")
            print(f"✓ Catálogo anual actualizado (reemplazo del día {fecha_d}): {pref_anio}_cat.csv")
        except Exception as e:
            print(f"Error actualizando catálogo anual {pref_anio}: {e}")

    return actualizados


def extraccion_dato(dato,separador):
    salida=[]
    xxx=dato.split(separador)
    for i in range(0,len(xxx)):
        if(len(xxx[i])>0):
            salida.append(xxx[i])
    return(salida)


# ==============================================================================
# PRECARGA LOCAL DEL PC (MEMORIA DEL EQUIPO) Y CONTROL DE TURNOS / RESPONSABLES
# ==============================================================================
import json
import socket

TURNOS_PARCIALES_DIA = ("00:00 - 12:00", "12:00 - 18:00", "18:00 - 24:00")
OPCION_TODO_EL_DIA = "Todo el día"
OPCIONES_PERIODO_DIARIO = TURNOS_PARCIALES_DIA + (OPCION_TODO_EL_DIA,)


def obtener_ruta_config_local_pc() -> str:
    """
    Retorna la ruta absoluta del archivo local de configuración del PC
    (`config_local_pc.json` en la raíz del proyecto).
    Nota: `*.json` está excluido en `.gitignore`, por lo que este archivo
    pertenece únicamente al PC donde se trabaja y nunca se sincroniza con el repositorio.
    """
    raiz = ruta_proyecto if ruta_proyecto else os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    return os.path.abspath(os.path.join(raiz, "config_local_pc.json"))


def cargar_config_local_pc() -> dict:
    """
    Carga la configuración de precarga local del PC desde `config_local_pc.json`.
    Si el archivo no existe o está corrupto, lo crea automáticamente con valores
    por defecto seguros para el equipo actual.
    """
    ruta_cfg = obtener_ruta_config_local_pc()
    try:
        nombre_pc = socket.gethostname()
    except Exception:
        nombre_pc = "PC_RSA"

    config_defecto = {
        "nombre_equipo": nombre_pc,
        "responsable_habitual": "RSA",
        "directorio_trabajo": "G:/Mi unidad/DIA/",
        "ultimo_dia_procesado": datetime.today().strftime("%Y-%m-%d"),
        "ultimo_periodo_procesado": "00:00 - 12:00",
        "pc_autorizado_config": True,
        "pc_administrador": False,
        "usuarios_autorizados_config": ["RSA"],
        "clave_administrador": "RSA",
        "actualizado_en": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    if os.path.isfile(ruta_cfg):
        try:
            with open(ruta_cfg, "r", encoding="utf-8") as f_cfg:
                leido = json.load(f_cfg)
            if isinstance(leido, dict):
                for k, v in config_defecto.items():
                    leido.setdefault(k, v)
                if not isinstance(leido.get("usuarios_autorizados_config"), list):
                    leido["usuarios_autorizados_config"] = ["RSA"]
                if "RSA" not in leido["usuarios_autorizados_config"]:
                    leido["usuarios_autorizados_config"].insert(0, "RSA")
                return leido
        except Exception as e:
            print(f"Aviso leyendo config_local_pc.json ({e}). Se restaurará configuración base.")

    guardar_config_local_pc(config_defecto)
    return config_defecto


def guardar_config_local_pc(datos_nuevos: dict) -> dict:
    """
    Actualiza y persiste en disco el archivo `config_local_pc.json` con la memoria
    operativa del PC actual (responsable habitual, directorio de trabajo, último
    día y período procesado, y permisos de administración de configuración).
    """
    ruta_cfg = obtener_ruta_config_local_pc()
    actual = {}
    if os.path.isfile(ruta_cfg):
        try:
            with open(ruta_cfg, "r", encoding="utf-8") as f_cfg:
                leido = json.load(f_cfg)
                if isinstance(leido, dict):
                    actual.update(leido)
        except Exception:
            pass

    try:
        nombre_pc = socket.gethostname()
    except Exception:
        nombre_pc = "PC_RSA"

    actual.setdefault("nombre_equipo", nombre_pc)
    actual.setdefault("responsable_habitual", "RSA")
    actual.setdefault("directorio_trabajo", "G:/Mi unidad/DIA/")
    actual.setdefault("ultimo_dia_procesado", datetime.today().strftime("%Y-%m-%d"))
    actual.setdefault("ultimo_periodo_procesado", "00:00 - 12:00")
    actual.setdefault("pc_autorizado_config", True)
    actual.setdefault("usuarios_autorizados_config", ["RSA"])
    actual.setdefault("clave_administrador", "RSA")

    if isinstance(datos_nuevos, dict):
        for k, v in datos_nuevos.items():
            if v is not None:
                actual[k] = v

    if not isinstance(actual.get("usuarios_autorizados_config"), list):
        actual["usuarios_autorizados_config"] = ["RSA"]
    if "RSA" not in actual["usuarios_autorizados_config"]:
        actual["usuarios_autorizados_config"].insert(0, "RSA")

    actual["actualizado_en"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        with open(ruta_cfg, "w", encoding="utf-8") as f_cfg:
            json.dump(actual, f_cfg, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Aviso guardando config_local_pc.json: {e}")

    return actual


def obtener_responsables_turnos_dia(archivo_dia: str) -> list:
    """
    Inspecciona el archivo de tiempos/responsables del día (`<AAMMDD>_tiempos.csv` o
    `<AAMMDD>_resp.csv`) y retorna una lista de 3 diccionarios correspondientes a los
    3 turnos del día:
      0 -> '00:00 - 12:00' (12H)
      1 -> '12:00 - 18:00' (18H)
      2 -> '18:00 - 24:00' (24H)
    Cada elemento contiene:
      {'indice': i, 'periodo': str, 'etiqueta': '12H'|'18H'|'24H',
       'responsable': str, 'total': int, 'procesado': bool}
    """
    turnos_info = [
        {"indice": 0, "periodo": "00:00 - 12:00", "etiqueta": "12H", "responsable": "", "total": 0, "procesado": False},
        {"indice": 1, "periodo": "12:00 - 18:00", "etiqueta": "18H", "responsable": "", "total": 0, "procesado": False},
        {"indice": 2, "periodo": "18:00 - 24:00", "etiqueta": "24H", "responsable": "", "total": 0, "procesado": False},
    ]
    if not archivo_dia:
        return turnos_info

    try:
        directorios = obtener_directorios(archivo_dia)
    except Exception:
        return turnos_info

    ruta_tiempos = directorios.get("archivo_tiempos", "")
    ruta_resp = directorios.get("archivo_responsables", "")
    ruta_csv = directorios.get("archivo_csv", "")
    ruta_aux = directorios.get("archivo_auxiliar", "")

    filas = []
    if ruta_tiempos and os.path.isfile(ruta_tiempos):
        try:
            filas = lectura_archivo(ruta_tiempos) or []
        except Exception:
            filas = []

    if not filas and ruta_resp and os.path.isfile(ruta_resp):
        try:
            filas_r = lectura_archivo(ruta_resp) or []
            filas = [f for f in filas_r if f and str(f[0]).strip().upper() != "RESPONSABLE"]
        except Exception:
            filas = []

    mapa_etiquetas = {"12": 0, "12H": 0, "18": 1, "18H": 1, "24": 2, "24H": 2}
    for pos, fila in enumerate(filas):
        if not fila or len(fila) < 3:
            continue
        etiq_fila = str(fila[1]).strip().upper()
        idx_t = mapa_etiquetas.get(etiq_fila)
        if idx_t is None and len(filas) == 3 and pos < 3:
            idx_t = pos
        if idx_t is None:
            continue
        resp_str = str(fila[0]).strip()
        try:
            tot_val = int(float(str(fila[2]).strip()))
        except (ValueError, TypeError):
            tot_val = 0
        procesado = tot_val > 0
        turnos_info[idx_t]["responsable"] = resp_str if procesado else (resp_str if resp_str not in ("", "RSA") else "")
        turnos_info[idx_t]["total"] = tot_val
        turnos_info[idx_t]["procesado"] = procesado

    # Conteo directo y exacto de eventos por período desde archivo_csv (o archivo_auxiliar)
    ruta_eventos = ruta_csv if (ruta_csv and os.path.isfile(ruta_csv)) else (
        ruta_aux if (ruta_aux and os.path.isfile(ruta_aux)) else ""
    )
    if ruta_eventos:
        try:
            filas_ev = lectura_archivo(ruta_eventos) or []
            conteos_ev = [0, 0, 0]
            resp_ev = ["", "", ""]
            for fila_ev in filas_ev:
                if not fila_ev or len(fila_ev) < 2:
                    continue
                texto_fecha = str(fila_ev[1]).strip()
                try:
                    if "_" in texto_fecha:
                        hora = int(texto_fecha.split("_", 1)[1][:2])
                    elif len(texto_fecha) >= 10 and texto_fecha[:8].isdigit():
                        hora = int(texto_fecha[8:10])
                    else:
                        continue
                except (ValueError, IndexError):
                    continue
                if not (0 <= hora <= 23):
                    continue
                idx_p = 0 if hora < 12 else (1 if hora < 18 else 2)
                conteos_ev[idx_p] += 1
                if len(fila_ev) > 6:
                    r_ev = str(fila_ev[6]).strip()
                    if r_ev not in ("", "RSA") and not resp_ev[idx_p]:
                        resp_ev[idx_p] = r_ev

            for idx_p in (0, 1, 2):
                turnos_info[idx_p]["total"] = conteos_ev[idx_p]
                turnos_info[idx_p]["procesado"] = conteos_ev[idx_p] > 0
                if conteos_ev[idx_p] > 0 and turnos_info[idx_p]["responsable"] in ("", "RSA"):
                    if resp_ev[idx_p]:
                        turnos_info[idx_p]["responsable"] = resp_ev[idx_p]
                    elif not turnos_info[idx_p]["responsable"]:
                        turnos_info[idx_p]["responsable"] = "RSA"
        except Exception:
            pass

    return turnos_info


def sugerir_siguiente_periodo_dia(archivo_dia: str, es_fecha_hoy: bool = True) -> str:
    """
    Determina automáticamente el período sugerido al seleccionar una fecha en `Inicio`:
    - Si la fecha seleccionada NO corresponde al día actual (`not es_fecha_hoy`),
      selecciona por defecto `'Todo el día'` (ideal para procesar días anteriores/fines
      de semana completos o realizar revisiones integrales).
    - Si la fecha seleccionada ES el día actual (`es_fecha_hoy`), busca el siguiente
      período pendiente del día en orden cronológico (`00:00 - 12:00` -> `12:00 - 18:00`
      -> `18:00 - 24:00`). Si los 3 turnos ya cuentan con eventos extraídos/procesados,
      sugiere `'Todo el día'`.
    """
    if not es_fecha_hoy:
        return OPCION_TODO_EL_DIA

    turnos = obtener_responsables_turnos_dia(archivo_dia)
    for info in turnos:
        if not info["procesado"]:
            return info["periodo"]
    return OPCION_TODO_EL_DIA


def validar_permiso_responsable_turno(
    archivo_dia: str,
    responsable_activo: str,
    periodo_seleccionado: str,
) -> tuple:
    """
    Verifica si `responsable_activo` tiene autorización para abrir/trabajar en el
    `periodo_seleccionado` del día `archivo_dia`:
    - El usuario maestro `'RSA'` tiene acceso total a todos los turnos y a `'Todo el día'`.
    - Un operador individual puede trabajar libremente en:
        a) Turnos aún no procesados (`total == 0`) o asignados a `'RSA'`.
        b) Turnos cuyo responsable registrado en el día sea él mismo.
    - Si el turno (o alguno de los turnos ya procesados cuando se escoge `'Todo el día'`)
      pertenece a otro responsable distinto, se bloquea el acceso indicando que debe
      seleccionarse el usuario `'RSA'` para acceder a todos los turnos.

    Retorna:
        tuple[bool, str]: `(permitido, mensaje_detalle)`
    """
    resp_act = (responsable_activo or "").strip()
    if resp_act == "RSA":
        return True, ""

    turnos = obtener_responsables_turnos_dia(archivo_dia)
    per_sel = (periodo_seleccionado or "").strip()

    if per_sel in TURNOS_PARCIALES_DIA:
        idx = TURNOS_PARCIALES_DIA.index(per_sel)
        info = turnos[idx]
        resp_turno = info["responsable"]
        if info["procesado"] and resp_turno not in ("", "RSA", resp_act):
            msg = (
                f"El período {per_sel} ({info['etiqueta']}) ya se encuentra registrado "
                f"a nombre del responsable «{resp_turno}» ({info['total']} eventos).\n\n"
                f"El usuario actual («{resp_act}») solo puede trabajar en sus propios "
                f"períodos o en turnos libres.\n"
                f"Para acceder o revisar períodos de todos los responsables, seleccione "
                f"el usuario «RSA»."
            )
            return False, msg
        return True, ""

    # Caso 'Todo el día' (o período general en modo diario)
    conflictos = []
    for info in turnos:
        resp_turno = info["responsable"]
        if info["procesado"] and resp_turno not in ("", "RSA", resp_act):
            conflictos.append(f"• {info['periodo']} ({info['etiqueta']}): {resp_turno} ({info['total']} ev.)")

    if conflictos:
        detalle_conf = "\n".join(conflictos)
        msg = (
            f"No es posible abrir «{OPCION_TODO_EL_DIA}» con el responsable «{resp_act}» "
            f"porque existen turnos de este día asignados a otro(s) responsable(s):\n\n"
            f"{detalle_conf}\n\n"
            f"Seleccione su turno específico o cambie el responsable a «RSA» para "
            f"acceder a todo el día."
        )
        return False, msg

    return True, ""


def verificar_permiso_configuracion_pc(usuario_actual: str = None) -> tuple:
    """
    Verifica si el equipo actual y el usuario activo cuentan con autorización del
    Administrador (`RSA`) en `config_local_pc.json` para modificar los archivos
    maestros de configuración del sistema (`estaciones.csv`, `analogicas.csv`,
    `digitales.csv`, `responsables.csv`, `mapas.csv`).

    Retorna:
        tuple[bool, str, str, str]: `(autorizado, usuario_resuelto, nombre_pc, mensaje)`
    """
    cfg = cargar_config_local_pc()
    nombre_pc = str(cfg.get("nombre_equipo") or "PC_RSA").strip()
    usuario = str(usuario_actual or cfg.get("responsable_habitual") or "RSA").strip()
    pc_autorizado = bool(cfg.get("pc_autorizado_config", True))
    autorizados = [str(u).strip() for u in (cfg.get("usuarios_autorizados_config") or ["RSA"])]

    if not pc_autorizado:
        return (
            False,
            usuario,
            nombre_pc,
            f"El equipo «{nombre_pc}» tiene deshabilitada la edición de configuración en config_local_pc.json.",
        )

    if usuario == "RSA":
        return True, usuario, nombre_pc, f"Administrador «RSA» activo en equipo «{nombre_pc}»."

    if usuario in autorizados:
        return (
            True,
            usuario,
            nombre_pc,
            f"Usuario «{usuario}» autorizado por el Administrador en el equipo «{nombre_pc}».",
        )

    return (
        False,
        usuario,
        nombre_pc,
        f"El usuario activo en este PC («{usuario}») no tiene permisos de edición de configuración.\n"
        f"Solo el Administrador («RSA») o un usuario autorizado por el Administrador en este equipo "
        f"pueden guardar cambios en los archivos maestros.",
    )


def verificar_permiso_respaldo_pc() -> tuple:
    """
    Verifica en `config_local_pc.json` si el equipo actual corresponde a la
    computadora del Administrador (`pc_administrador: true`) para habilitar el
    módulo de respaldo y restauración del programa.

    Retorna:
        tuple[bool, str, str]: `(autorizado, nombre_pc, mensaje)`
    """
    cfg = cargar_config_local_pc()
    nombre_pc = str(cfg.get("nombre_equipo") or "PC_RSA").strip()
    es_pc_admin = bool(cfg.get("pc_administrador", False))
    pc_autorizado = bool(cfg.get("pc_autorizado_config", True))

    if es_pc_admin and pc_autorizado:
        return True, nombre_pc, f"Equipo administrador autorizado («{nombre_pc}»)."

    return (
        False,
        nombre_pc,
        f"El equipo «{nombre_pc}» no está configurado como computadora del Administrador "
        f"en config_local_pc.json (pc_administrador: false).",
    )


def escritura_segura_configuracion(ruta_destino: str, filas: list) -> str:
    """
    Guarda de forma atómica y con respaldo automático (`datos/respaldos_config/`)
    cualquier archivo maestro de configuración (`estaciones.csv`, `analogicas.csv`,
    `digitales.csv`, `responsables.csv`, `mapas.csv`):
      1. Crea una copia de respaldo con marca de tiempo antes de tocar el archivo original.
      2. Escribe primero en un archivo temporal `.tmp` en la misma carpeta y verifica
         que se haya escrito íntegramente.
      3. Reemplaza atómicamente el archivo destino mediante `os.replace`.
    """
    import shutil

    if not filas:
        raise ValueError("No se puede guardar un archivo de configuración vacío.")

    ruta_abs = os.path.abspath(ruta_destino)
    carpeta_padre = os.path.dirname(ruta_abs)
    nombre_arch = os.path.basename(ruta_abs)
    stem_arch = Path(ruta_abs).stem

    # 1. Crear respaldo previo si el archivo ya existe
    ruta_respaldo = ""
    if os.path.isfile(ruta_abs):
        raiz = ruta_proyecto if ruta_proyecto else os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        dir_respaldos = os.path.join(raiz, "datos", "respaldos_config")
        os.makedirs(dir_respaldos, exist_ok=True)
        sello = datetime.now().strftime("%Y%m%d_%H%M%S")
        ruta_respaldo = os.path.join(dir_respaldos, f"{stem_arch}_{sello}.bak.csv")
        shutil.copy2(ruta_abs, ruta_respaldo)

        # Conservar únicamente los últimos 20 respaldos de ese archivo para orden limpio
        try:
            existentes = sorted(
                [
                    os.path.join(dir_respaldos, f)
                    for f in os.listdir(dir_respaldos)
                    if f.startswith(f"{stem_arch}_") and f.endswith(".bak.csv")
                ]
            )
            while len(existentes) > 20:
                antiguo = existentes.pop(0)
                try:
                    os.remove(antiguo)
                except Exception:
                    pass
        except Exception:
            pass

    # 2. Escribir primero en archivo temporal (.tmp) y verificar integridad
    os.makedirs(carpeta_padre, exist_ok=True)
    ruta_tmp = ruta_abs + ".tmp"
    escritura_archivo(ruta_tmp, filas)
    if not os.path.isfile(ruta_tmp) or os.path.getsize(ruta_tmp) == 0:
        raise IOError(f"Fallo de verificación al escribir archivo temporal: {ruta_tmp}")

    # 3. Reemplazo atómico
    os.replace(ruta_tmp, ruta_abs)
    return ruta_respaldo



