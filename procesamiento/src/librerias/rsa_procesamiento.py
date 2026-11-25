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
ruta_datos = os.path.abspath(os.path.join(ruta_proyecto,'datos'))
# Insertar la ruta al inicio del sys.path
if ruta_librerias not in sys.path:
    sys.path.insert(0, ruta_librerias)

import numpy as np
import csv
from datetime import datetime, timedelta
import sys
import os
import xml.etree.ElementTree as ET
from metodos_gestion import obtener_directorios,VentanaProgreso
from rsa_io import lectura_archivo,escritura_archivo
from rsa_utilidades import extraccion,codigos,ubicacion,agregar_evento

IDX_INDICE,IDX_ANIO,IDX_MES,IDX_DIA,IDX_HORA,IDX_MINUTO,IDX_SEGUNDO,\
IDX_LATITUD,IDX_LONGITUD,IDX_PROFUNDIDAD,IDX_RMS,IDX_E_X,IDX_E_Y,IDX_E_0,\
IDX_E_Z,IDX_MAGNITUD,IDX_UNIDAD_MAG,\
IDX_FUENTE,IDX_EVENTO,IDX_LUGAR = 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19


def lectura_rsa(archivo, directorio_trabajo, usuario, archivo_rsa_detectado=''):
    # Método para obtener la información completa del sismo
    print("Lectura RSA")

    directorios = obtener_directorios(os.path.join(directorio_trabajo, archivo))
    eventos = lectura_archivo(directorios['archivo_csv'])

    archivos_evento = []
    base_evento = Path(archivo).stem.replace('_', '')

    if len(base_evento) == 12:  # AAMMDDhhmmss
        ss_evento = int(base_evento[10:12])
    else:  # AAAAMMDDhhmmss
        ss_evento = int(base_evento[12:14])

    # Si ya sé cuál RSA cambió en virtual, uso ese como prioritario
    if archivo_rsa_detectado:
        archivos_evento = archivos_fast(archivo, directorio_trabajo, usuario, modo_minuto_fast='auto')
        archivos_evento[2] = archivo_rsa_detectado

        nombre_rsa = Path(archivo_rsa_detectado).stem.rstrip('abc')
        mm_fast = nombre_rsa[0:2]
        dd_fast = nombre_rsa[2:4]
        hh_fast = nombre_rsa[4:6]
        minu_fast = nombre_rsa[6:8]

        dir_fast = os.path.dirname(archivo_rsa_detectado)
        archivos_evento[3] = os.path.join(dir_fast, f"Phase{dd_fast}{hh_fast[0]}.{hh_fast[1]}{minu_fast}")

        base_lp = f"{mm_fast}{dd_fast}{hh_fast}.{minu_fast}"
        archivos_evento[4] = os.path.join(dir_fast, base_lp + "L")
        archivos_evento[5] = os.path.join(dir_fast, base_lp + "P")
        archivos_evento[6] = os.path.join(dir_fast, base_lp + "S")

    else:
        archivos_evento = archivos_fast(archivo, directorio_trabajo, usuario, modo_minuto_fast='auto')

    # El sufijo solo aplica en host
    if usuario == '':
        archivos_evento = verificar_coincidencias(eventos, archivo, archivos_evento)

    archivo_fas = archivos_evento[1]
    archivo_rsa = archivos_evento[2]
    archivo_fase = archivos_evento[3]

    bandera_error = 0
    archivo_estaciones = os.path.join(directorio_trabajo, directorios["archivo_estaciones"])
    lectura_estaciones = lectura_archivo(archivo_estaciones)

    aux = len(archivo)
    if archivo[-11:-10] == "_":
        sismo_aux = archivo[-17:-11] + archivo[-10:aux]
    else:
        sismo_aux = archivo[-10:aux]

    lectura_fase = []
    auxiliar = ["Disp.", "t_pr.", "t_sec.", "marc.s", "t_cod."]
    lectura_fase.append(auxiliar)

    if os.path.exists(archivo_fase):
        with open(archivo_fase, newline='') as f_f:
            lectura_archivo_fase = csv.reader(f_f, delimiter='\n', quotechar=';')
            for lectura in lectura_archivo_fase:
                for v in lectura:
                    auxiliar = [v[4:8], v[19:24], v[31:36], v[36:40], v[70:75]]
                    lectura_fase.append(auxiliar)

    elif os.path.exists(archivo_fas):
        archivo_abrir = open(archivo_fas, 'rb')
        bandera_1 = 1
        auxiliar = []
        contador = 0

        while bandera_1:
            cabecera_0 = archivo_abrir.read(2)
            resultado = codigos(cabecera_0, archivo_abrir)

            if cabecera_0 == b'\x08\x00':
                if contador == 2:
                    auxiliar.append(resultado[0])
                    contador = 3
                if contador == 1:
                    auxiliar.append(resultado[0][:5])
                    auxiliar.append(resultado[0][-4:])
                    contador = 2
                if resultado[1] == 28:
                    auxiliar = []
                    if resultado[0][:4] != '    ':
                        if contador == 0:
                            auxiliar = [resultado[0][4:8], resultado[0][-5:]]
                            contador = 1
                if auxiliar != [] and contador == 3:
                    lectura_fase.append(auxiliar)
                    contador = 0

            if len(cabecera_0) == 0:
                bandera_1 = 0
                archivo_abrir.close()
    else:
        auxiliar = ['    ', '    ', '    ', '    ', '    ']
        lectura_fase.append(auxiliar)

    if os.path.exists(archivo_rsa):
        with open(archivo_rsa, newline='') as f_r:
            lectura_archivo_rsa = csv.reader(f_r, delimiter=' ', quotechar=';')
            estaciones_evento = ""
            lectura_total = []

            for lectura in lectura_archivo_rsa:
                datos_ = []
                for v in lectura:
                    if v == '' or v == ' ':
                        pass
                    else:
                        datos_.append(v)
                lectura_total.append(datos_)

            for i, datos_ in enumerate(lectura_total):
                try:
                    if len(datos_) > 0:
                        if datos_[0] == 'sta':
                            if lectura_total[i - 1] != []:
                                latitud = float(lectura_total[i - 1][0])
                                longitud = float(lectura_total[i - 1][1])
                                profundidad = round(float(lectura_total[i - 1][2]), 1)
                                segundo_sismo = float(lectura_total[i - 1][3])
                                datos_estaciones = []
                                auxiliar = lectura_estaciones[0][2:8] + datos_[1:] + lectura_fase[0]
                                datos_estaciones.append(auxiliar)
                                indice = i

                                while lectura_total[i] != []:
                                    i = i + 1
                                    if lectura_total[i] != []:
                                        estacion_ = lectura_total[i][0]
                                        lista_seleccionada = next(
                                            (lista for lista in lectura_estaciones if lista[2] == estacion_),
                                            None
                                        )

                                        if lista_seleccionada is None:
                                            if estacion_ == 'CALCULO':
                                                estaciones = ''
                                                for estacion in datos_estaciones:
                                                    if estacion != 'nombre':
                                                        estaciones = estaciones + estacion[0] + ' '
                                                return
                                            print("Estacion ", estacion_)
                                            return

                                        if len(lectura_fase) != 2:
                                            auxiliar_est = lista_seleccionada[2:8] + lectura_total[i][1:] + lectura_fase[i - indice]
                                        else:
                                            auxiliar_est = lista_seleccionada[2:8] + lectura_total[i][1:] + lectura_fase[1]

                                        datos_estaciones.append(auxiliar_est)

                        if datos_[0] == 'error':
                            ex = float(datos_[3])
                            ey = float(datos_[6])
                            e0 = float(datos_[10])

                        if datos_[0] == 'event':
                            id_sismo = '20' + sismo_aux[0:10] + '00'
                            anio_sismo = 2000 + int(datos_[3])
                            mes_sismo = int(datos_[4])
                            dia_sismo = int(datos_[5])
                            hora_sismo = int(datos_[6])
                            minuto_sismo = int(datos_[7])

                        if datos_[0] == 'rms=':
                            rms = float(datos_[1])
                            aux = len(lectura_total[i + 3][1])
                            ez = float(lectura_total[i + 3][1][0:aux - 2])
                            i = i + 3

                        if datos_[0] == 'Promedio':
                            if datos_[4] != 'No':
                                magnitud = float(datos_[4])
                            else:
                                magnitud = 0.0

                except ValueError:
                    bandera_error = 1

            if bandera_error:
                return 1
            else:
                ubicacion_sismo = ubicacion(latitud, longitud)
                ruta = archivo

                if segundo_sismo < 0:
                    segundo_sismo = 60 + segundo_sismo
                    minuto_sismo = minuto_sismo - 1
                    if minuto_sismo == -1:
                        minuto_sismo = 59
                        hora_sismo = hora_sismo - 1

                for ev in datos_estaciones:
                    if ev != [] and ev[0] != "sta" and ev[0] != '    ' and ev[0] != 'nombre':
                        estaciones_evento = estaciones_evento + ev[0] + " "

                datos_sismo = [
                    id_sismo, str(anio_sismo), str(mes_sismo), str(dia_sismo),
                    str(hora_sismo), str(minuto_sismo), str(segundo_sismo),
                    str(latitud), str(longitud), str(profundidad), str(rms),
                    str(ex), str(ey), str(e0), str(ez), str(magnitud),
                    'Md', 'RSA', ruta, ubicacion_sismo
                ]

                datos_estaciones = [sublista[:12] + sublista[13:15] + sublista[16:17] + sublista[19:] for sublista in datos_estaciones]

                return (datos_sismo, estaciones_evento, archivo_rsa, datos_estaciones)
    else:
        return

def archivos_fast(evento, dir_trabajo, usuario, retornar_validaciones=False, modo_minuto_fast='auto'):
    """
    Genera rutas para archivos FASTHYPO.
    
    modo_minuto_fast:
        'real'      -> fuerza minuto exacto
        'siguiente' -> fuerza minuto + 1
        'auto'      -> busca archivos existentes o usa ss>=50 si no existen
    """
    info = obtener_directorios(evento)
    dir_dia = os.path.join(dir_trabajo, info['Directorio_dia'])
    dir_fast = os.path.join(dir_trabajo, info['Directorio_fastHypo'])

    if usuario:
        csv_path = os.path.join(ruta_datos, "responsables.csv")
        for fila in lectura_archivo(csv_path):
            if fila and fila[0].strip() == usuario.strip():
                dir_dia, dir_fast = fila[1], fila[2]
                break

    base = Path(evento).stem

    if len(base) == 13:      # AAMMDD_hhmmss
        yy = 2000 + int(base[:2])
        mm = base[2:4]
        dd = base[4:6]
        hh = base[7:9]
        minu = base[9:11]
        ss = base[11:13]
        sisfas_base = base
    else:                    # AAAAMMDD_hhmmss
        yy = int(base[:4])
        mm = base[4:6]
        dd = base[6:8]
        hh = base[9:11]
        minu = base[11:13]
        ss = base[13:15]
        sisfas_base = base if usuario == '' else base[2:]

    archivo_sis = os.path.join(dir_dia, f"{sisfas_base}.sis")
    archivo_fas = os.path.join(dir_dia, f"{sisfas_base}.fas")

    segundo_evento = int(ss)
    dt_evento = datetime(yy, int(mm), int(dd), int(hh), int(minu), segundo_evento)
    dt_siguiente = dt_evento + timedelta(minutes=1)

    def generar_rutas_fast(dt):
        mm_fast = dt.strftime("%m")
        dd_fast = dt.strftime("%d")
        hh_fast = dt.strftime("%H")
        minu_fast = dt.strftime("%M")

        rsa_nom = f"{mm_fast}{dd_fast}{hh_fast}{minu_fast}.rsa"
        archivo_rsa = os.path.join(dir_fast, rsa_nom)

        phase_nom = f"Phase{dd_fast}{hh_fast[0]}.{hh_fast[1]}{minu_fast}"
        archivo_phase = os.path.join(dir_fast, phase_nom)

        base_lp = f"{mm_fast}{dd_fast}{hh_fast}.{minu_fast}"
        archivo_L = os.path.join(dir_fast, base_lp + "L")
        archivo_P = os.path.join(dir_fast, base_lp + "P")
        archivo_S = os.path.join(dir_fast, base_lp + "S")

        return [archivo_rsa, archivo_phase, archivo_L, archivo_P, archivo_S]

    rutas_fast_real = generar_rutas_fast(dt_evento)
    rutas_fast_siguiente = generar_rutas_fast(dt_siguiente)

    if modo_minuto_fast == 'real':
        rutas_fast_elegidas = rutas_fast_real
    elif modo_minuto_fast == 'siguiente':
        rutas_fast_elegidas = rutas_fast_siguiente
    else:
        existe_real = os.path.exists(rutas_fast_real[0])
        existe_siguiente = os.path.exists(rutas_fast_siguiente[0])

        if existe_real or os.path.exists(rutas_fast_real[1]):
            rutas_fast_elegidas = rutas_fast_real
        elif existe_siguiente or os.path.exists(rutas_fast_siguiente[1]):
            rutas_fast_elegidas = rutas_fast_siguiente
        else:
            if segundo_evento >= 50:
                rutas_fast_elegidas = rutas_fast_siguiente
            else:
                rutas_fast_elegidas = rutas_fast_real

    rutas = [
        archivo_sis,
        archivo_fas,
        rutas_fast_elegidas[0],
        rutas_fast_elegidas[1],
        rutas_fast_elegidas[2],
        rutas_fast_elegidas[3],
        rutas_fast_elegidas[4]
    ]

    if retornar_validaciones:
        etiquetas = ['.sis', '.fas', '.rsa', 'Phase', '.L', '.P', '.S']
        existe = {etq: os.path.isfile(ruta) for etq, ruta in zip(etiquetas, rutas)}
        faltantes = [etq for etq, ok in existe.items() if not ok]
        return rutas, existe, faltantes

    return rutas


def verificar_coincidencias(eventos, evento_procesar, rutas_fast):
    print("verificar_coincidencias")
    contador = 0
    sufijo = ['', 'a', 'b', 'c']

    base_evento = Path(evento_procesar).stem.replace('_', '')
    if len(base_evento) == 12:  # AAMMDDhhmmss
        yy = 2000 + int(base_evento[:2])
        mm = int(base_evento[2:4])
        dd = int(base_evento[4:6])
        hh = int(base_evento[6:8])
        minu = int(base_evento[8:10])
        ss = int(base_evento[10:12])
    else:  # AAAAMMDDhhmmss
        yy = int(base_evento[:4])
        mm = int(base_evento[4:6])
        dd = int(base_evento[6:8])
        hh = int(base_evento[8:10])
        minu = int(base_evento[10:12])
        ss = int(base_evento[12:14])

    dt_evento = datetime(yy, mm, dd, hh, minu, ss)
    if ss >= 50:
        dt_evento = dt_evento + timedelta(minutes=1)

    clave_minuto = dt_evento.strftime("%Y%m%d%H%M")
    if rutas_fast and len(rutas_fast) > 2 and rutas_fast[2]:
        stem_rsa = Path(rutas_fast[2]).stem.rstrip('abc')
        if len(stem_rsa) >= 8 and stem_rsa[:8].isdigit():
            mm_f, dd_f, hh_f, mi_f = int(stem_rsa[0:2]), int(stem_rsa[2:4]), int(stem_rsa[4:6]), int(stem_rsa[6:8])
            clave_minuto = datetime(yy, mm_f, dd_f, hh_f, mi_f).strftime("%Y%m%d%H%M")

    for evento in eventos:
        tipo_evento = evento[2]
        if tipo_evento != 'SISMO':
            continue

        base_actual = Path(evento[1]).stem.replace('_', '')
        if len(base_actual) == 12:  # AAMMDDhhmmss
            yy_a = 2000 + int(base_actual[:2])
            mm_a = int(base_actual[2:4])
            dd_a = int(base_actual[4:6])
            hh_a = int(base_actual[6:8])
            minu_a = int(base_actual[8:10])
            ss_a = int(base_actual[10:12])
        else:  # AAAAMMDDhhmmss
            yy_a = int(base_actual[:4])
            mm_a = int(base_actual[4:6])
            dd_a = int(base_actual[6:8])
            hh_a = int(base_actual[8:10])
            minu_a = int(base_actual[10:12])
            ss_a = int(base_actual[12:14])

        dt_actual = datetime(yy_a, mm_a, dd_a, hh_a, minu_a, ss_a)
        if ss_a >= 50:
            dt_actual = dt_actual + timedelta(minutes=1)

        clave_actual = dt_actual.strftime("%Y%m%d%H%M")

        if clave_actual == clave_minuto:
            if base_actual == base_evento:
                break
            contador += 1

    if contador >= len(sufijo):
        contador = len(sufijo) - 1

    suf = sufijo[contador]
    if not suf:
        return rutas_fast

    if rutas_fast[2].lower().endswith('.rsa'):
        rutas_fast[2] = rutas_fast[2][:-4] + suf + '.rsa'

    for i in range(3, 7):
        if rutas_fast[i]:
            rutas_fast[i] = rutas_fast[i] + suf

    return rutas_fast


def guardar_intento(archivo, directorio, responsables, procesamiento, archivo_rsa_detectado=''):
    print("guardar_intento")

    resultado = lectura_rsa(
        archivo,
        directorio,
        responsables,
        archivo_rsa_detectado
    )

    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    indice = str(len(procesamiento) - 1)

    if resultado is None:
        fila = [indice, ahora, "Fallido", " ", " ", " ", " "]
        procesamiento.append(fila)
        return procesamiento

    if resultado == 1:
        fila = [indice, ahora, "Fallido", "Error de conversion", " ", " ", " "]
        procesamiento.append(fila)
        return procesamiento

    datos_sismo = resultado[0]

    try:
        profundidad = datos_sismo[9]
        magnitud = datos_sismo[15]
        latitud = datos_sismo[7]
        longitud = datos_sismo[8]
        rms = datos_sismo[10]
        fila = [indice, ahora, profundidad, magnitud, latitud, longitud, rms]
    except Exception:
        fila = [indice, ahora, "Fallido", " ", " ", " ", " "]

    procesamiento.append(fila)
    return procesamiento






def guardar_informacion_diaria(archivo,directorio_trabajo,catalogo_anterior,eventos):
    #archivo:          Archivo del día con formato AAMMDD_hhmmss.csv
    #directorio_trabajo:   Directorio del drive de trabajo
    #catalogo_anterior:    Catalogo encontrado en el día para cargar la información de otras redes.
    print("guardar_informacion_diaria")
    ruta_entrada = archivo if os.path.isabs(str(archivo)) else os.path.join(directorio_trabajo, str(archivo))
    directorios = obtener_directorios(ruta_entrada)
    archivo_csv = directorios['archivo_csv']
    catalogo=[["Id","anio","mes","dia","hora","min","seg","lat","long","prof","rms","e-x","e-y","e-0","e-z","Mag","Tipo Mag","Fuente","ruta","Ubicacion"]]
    eventos_reporte=[['0',"Fecha Hora (UTC)","Evento","Magn.","Prof.(km)","Lat.","Long.","Ubicación"]]
    archivo_xml = directorios['archivo_xml']
    archivo_dat = directorios['archivo_reporte']
    archivo_cat = directorios['archivo_catalogo']
    archivo_res = directorios['archivo_resumen']
    archivo_responsables = directorios['archivo_tiempos']
    rep_responsables = directorios['archivo_responsables']
    contador_n_canales=[[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0]]#Tupla que contiene el número de estaciones por evento sísmico.
    indice_responsables=[0,0,0]
    root = ET.Element("sismo")
    for evento_individual in eventos:
        catalogo_grabar=[]#Variable donde se guarda lo que se va a grabar en el catalogo diario .csv
        evento_grabar=[]#Variable donde se guarda lo que se va a grabar en el resumen diario .csv
        evento_canales=[]#Variable que muestra los canales donde se tiene el evento con banderas 1 o 0
        for i in range(0,101): # En vez de 100 16, numero de canales
            if evento_individual[i+3]=='-':
                evento_canales.append(0)
            else:
                evento_canales.append(1)
        evento_grabar.append(evento_individual[0])
        evento_grabar.append(evento_individual[1])
        evento_grabar.append(evento_individual[2])
        if(evento_individual[2]=="SISMO"):
            catalogo_grabar=lectura_rsa(evento_individual[1],directorio_trabajo,'')
            if catalogo_grabar==None or catalogo_grabar==1:
                evento_grabar.append("revisar")
                catalogo_grabar=[]
            else:
                agregar_evento(root,catalogo_grabar[0],catalogo_grabar[3])
                for i in(15,9,7,8,19):
                    evento_grabar.append(str(catalogo_grabar[0][i]))
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
                catalogo_grabar=catalogo_grabar[0]
        if catalogo_grabar!=[]:
            catalogo.append(catalogo_grabar)
        eventos_reporte.append(evento_grabar)
        evento_canales.append(evento_canales)
        
        ############################################################################
        #Rutina para cargar el número de eventos y los responsables del día procesado
    if os.path.exists(archivo_responsables):
            with open(archivo_responsables) as archivo_leer:
                lector_csv = csv.reader(archivo_leer)
                lectura=[]
                for row in lector_csv:
                    lectura.append(row)
                aux=len(lectura)
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
            with open(rep_responsables, 'w', newline='') as archivo_grabar:
                escritor_csv = csv.writer(archivo_grabar,delimiter=';')
                escritor_csv.writerow(["RESPONSABLE","HORA","TOT.","SIS.","FF","FC","IND.","TEL.","Local_CONTROL.","Ruido","3 est","4 est","5 est","6 est","7 est","8 est"])
                responsable=[]
                for i in range (0,3):
                    aux=lectura[indice_responsables[i]][0].split(';')+contador_n_canales[i]
                    escritor_csv.writerow(aux)
                    responsable.append(aux[0])
    else:
            pass
    # Recolectar eventos de otras redes desde catalogo_anterior y desde archivo_cat en disco
    filas_otras_redes = []
    claves_otras_redes = set()
    fuentes_previas = [catalogo_anterior or []]
    if os.path.exists(archivo_cat):
        cat_disco = lectura_archivo(archivo_cat)
        if cat_disco:
            fuentes_previas.append(cat_disco)

    for fuente_cat in fuentes_previas:
        for fila_prev in fuente_cat:
            if not fila_prev or len(fila_prev) < 19:
                continue
            id_ev = str(fila_prev[0]).strip()
            if id_ev == 'Id' or id_ev[-2:] == '00':
                continue
            clave_ext = (id_ev, str(fila_prev[17]).strip(), str(fila_prev[18]).strip())
            if clave_ext not in claves_otras_redes:
                claves_otras_redes.add(clave_ext)
                filas_otras_redes.append(fila_prev)

    for evento_otras_redes in filas_otras_redes:
        id_evento = str(evento_otras_redes[0]).strip()
        insertado_cat = False
        try:
            numero = int(id_evento)
            for j in range(1, len(catalogo)):
                if not catalogo[j]:
                    continue
                otro_numero = int(catalogo[j][0])
                if otro_numero > numero:
                    catalogo.insert(j, evento_otras_redes)
                    insertado_cat = True
                    break
        except Exception:
            pass
        if not insertado_cat:
            catalogo.append(evento_otras_redes)

        ubic_ext = evento_otras_redes[19] if len(evento_otras_redes) > 19 else ""
        ruta_asociada = str(evento_otras_redes[18]).strip()
        insertado_rep = False
        try:
            for j in range(1, len(eventos_reporte)):
                if str(eventos_reporte[j][1]).strip() == ruta_asociada:
                    variable = [
                        eventos_reporte[j][0],
                        evento_otras_redes[18],
                        evento_otras_redes[17],
                        evento_otras_redes[15],
                        evento_otras_redes[9],
                        evento_otras_redes[7],
                        evento_otras_redes[8],
                        ubic_ext,
                    ]
                    eventos_reporte.insert(j + 1, variable)
                    insertado_rep = True
                    break
            if not insertado_rep:
                numero = int(ruta_asociada[-10:-4])
                for j in range(1, len(eventos_reporte)):
                    otro_txt = str(eventos_reporte[j][1]).strip()
                    if len(otro_txt) >= 10 and otro_txt[-10:-4].isdigit():
                        otro_numero = int(otro_txt[-10:-4])
                        if otro_numero > numero:
                            orden_prev = eventos_reporte[j - 1][0] if j > 1 else 1
                            variable = [
                                orden_prev,
                                evento_otras_redes[18],
                                evento_otras_redes[17],
                                evento_otras_redes[15],
                                evento_otras_redes[9],
                                evento_otras_redes[7],
                                evento_otras_redes[8],
                                ubic_ext,
                            ]
                            eventos_reporte.insert(j, variable)
                            insertado_rep = True
                            break
        except Exception:
            pass
        if not insertado_rep:
            orden_ult = eventos_reporte[-1][0] if len(eventos_reporte) > 1 else 1
            eventos_reporte.append([
                orden_ult,
                evento_otras_redes[18],
                evento_otras_redes[17],
                evento_otras_redes[15],
                evento_otras_redes[9],
                evento_otras_redes[7],
                evento_otras_redes[8],
                ubic_ext,
            ])

    catalogo=ordenar_y_eliminar_duplicados(catalogo,0)
    escritura_archivo(archivo_cat,catalogo)
    escritura_archivo(archivo_dat,eventos_reporte)
    cont_sismos=0
    cont_FF=0
    cont_FC=0
    cont_tel=0
    cont_ev=0
    cont_ruido=0
    cont_indefinido=0
    for i in range(0,len(eventos)):
            if(eventos[i][2]=="SISMO"):
                cont_sismos=cont_sismos+1
            if(eventos[i][2]=="FF"or eventos[i][2]=="REVISION" ):
                cont_FF=cont_FF+1
            if(eventos[i][2]=="FC"):
                cont_FC=cont_FC+1
            if(eventos[i][2]=="TELESISMO"):
                cont_tel=cont_tel+1
            if(eventos[i][2]=="Evento_local" or eventos[i][2]=="CONTROL" ):
                cont_ev=cont_ev+1
            if(eventos[i][2]=="Ruido"):
                cont_ruido=cont_ruido+1
            if(eventos[i][2]=="INDEFINIDO"):
                cont_indefinido=cont_indefinido+1    

    with open(archivo_res, 'w', newline='') as archivo_grabar:
                escritor_csv = csv.writer(archivo_grabar,delimiter=';')
                escritor_csv.writerow(["SISMO",     "FF",   "FC","TELESISMOS","Local_CONTROL","INDEFINIDO","Ruido"])
                escritor_csv.writerow([cont_sismos,cont_FF,cont_FC,cont_tel,cont_ev,      cont_indefinido,cont_ruido])
    tree = ET.ElementTree(root)
        # Escribir el archivo XML
    tree.write(archivo_xml, encoding="utf-8", xml_declaration=True)
    return catalogo,eventos_reporte




def ordenar_y_eliminar_duplicados(catalogo, indice, bandera=True):
    """
    Ordena una lista de listas o tuplas y elimina duplicados.

    Args:
        catalogo: Lista de listas o tuplas donde la primera sublista contiene los encabezados.
        indice: Índice de la columna por la que se ordenará.
        bandera:   True es catalogo, False es cualquier archivo
    Returns:
        Lista ordenada y sin duplicados.
    """    
    print(" ordenar_y_eliminar_duplicados")
    if bandera:
        
        if not catalogo or not isinstance(catalogo, list):
            raise ValueError("El catálogo debe ser una lista no vacía.")

        encabezado = catalogo[0]
        datos = [fila for fila in catalogo[1:] if fila]  # Eliminar filas vacías

        # Validar índice
        if not all(len(fila) > indice for fila in datos):
            raise IndexError(f"El índice {indice} es inválido para algunas filas.")

    else:
        
        datos=catalogo

    # Eliminar duplicados
    vistos = set()
    sin_duplicados = []
    for fila in datos:
        clave = tuple(fila)  # Convertimos a tupla para poder agregar al set
        if clave not in vistos:
            vistos.add(clave)
            sin_duplicados.append(fila)

    # Ordenar por el índice especificado, convirtiendo el elemento a str temporalmente
    sin_duplicados.sort(key=lambda x: x[indice])
    if bandera:    
        # Agregar el encabezado
        sin_duplicados.insert(0, encabezado)
    else:
        for i, evento in enumerate(sin_duplicados):
            if isinstance(evento, list):
                evento[0] = str(i + 1)
            elif isinstance(evento, tuple):
                sin_duplicados[i] = [str(i + 1)] + list(evento[1:])


    return sin_duplicados


def extraer_dia(archivo, responsable, bandera_todo):
    """
    Procesa el día indicado por 'archivo':
      - Selecciona el archivo fuente (AAAAMMDD_aux.csv si existe, caso contrario AAAAMMDD000000.csv)
      - Lee eventos y actualiza los conteos por tramos (0–11, 12–17, 18–23)
      - Actualiza/crea archivo de tiempos (archivo_tiempos)
      - Recorre eventos_auxiliar, ejecuta 'extraccion' y consolida en el CSV principal
    Asume que todos los archivos son generados por el sistema (sin cabeceras y con formato estable).
    """
    # ----------------------------------------------------------------------
    # 1) Selección de archivo fuente y lecturas base
    # ----------------------------------------------------------------------
    print("Entro a extraer dia")
    directorios = obtener_directorios(archivo)

    # Elegimos primero el archivo correcto y recién luego leemos (evita desfasajes)
    nombre_archivo = directorios["archivo_auxiliar"]
    if not os.path.exists(nombre_archivo):
        nombre_archivo = directorios["archivo_csv"]

    # Lecturas de listas (sin cabeceras, según tu pipeline)
    eventos_auxiliar = lectura_archivo(nombre_archivo) or []   # base para iterar en extraccion()

    # Respaldar primero las clasificaciones y filas existentes de AAAAMMDD000000.csv
    # para no perder reclasificaciones manuales que no se reflejaron en _aux.csv
    eventos_csv_previos = lectura_archivo(directorios["archivo_csv"]) if os.path.exists(directorios["archivo_csv"]) else []
    clasificaciones_csv = {}
    filas_csv_previas_por_clave = {}
    for fila_csv in (eventos_csv_previos or []):
        if fila_csv and len(fila_csv) >= 3:
            clave_csv = _normalizar_clave_evento_reconstruccion(fila_csv[1])
            if clave_csv:
                clasificaciones_csv[clave_csv] = str(fila_csv[2]).strip()
                filas_csv_previas_por_clave[clave_csv] = list(fila_csv)

    # Aplicar en memoria la clasificación oficial de AAAAMMDD000000.csv sobre eventos_auxiliar
    claves_en_aux = set()
    for fila_aux in eventos_auxiliar:
        if fila_aux and len(fila_aux) >= 3:
            clave_aux = _normalizar_clave_evento_reconstruccion(fila_aux[1])
            if clave_aux:
                claves_en_aux.add(clave_aux)
                if clave_aux in clasificaciones_csv:
                    fila_aux[2] = clasificaciones_csv[clave_aux]

    lista_eventos = eventos_auxiliar                           # base para conteos por tramo (con clasificación oficial)

    # Archivo donde se guardan conteos
    archivo_guardar = directorios["archivo_tiempos"]

    # Si existe, se usa; caso contrario se crea con 3 filas (12H, 18H, 24H)
    if os.path.exists(archivo_guardar):
        datos_tiempo = lectura_archivo(archivo_guardar)
    else:
        datos_tiempo = [
            ["RSA", "12H", "0", "0", "0", "0", "0", "0", "0", "0"],
            ["RSA", "18H", "0", "0", "0", "0", "0", "0", "0", "0"],
            ["RSA", "24H", "0", "0", "0", "0", "0", "0", "0", "0"],
        ]
        escritura_archivo(archivo_guardar, datos_tiempo)

    # ----------------------------------------------------------------------
    # 2) Conteos por tramo y por tipo de evento (sin validaciones adicionales)
    #    Tramos: 0 = 00–11, 1 = 12–17, 2 = 18–23
    # ----------------------------------------------------------------------
    # Estructura: cada clave tiene una lista [c0, c1, c2]
    contadores = {
        "sismo":       [0, 0, 0],
        "ff":          [0, 0, 0],
        "fc":          [0, 0, 0],
        "indefinido":  [0, 0, 0],
        "tele":        [0, 0, 0],
        "local":       [0, 0, 0],
        "ruido":       [0, 0, 0],
    }
    # Etiquetas de salida para datos_tiempo (coinciden con tus columnas)
    etiquetas_tramo = [12, 18, 24]  # Semántico: 12H, 18H, 24H (tramo 18–23)
    responsable_por_tramo = ["", "", ""]

    # Recorremos eventos tal como vienen (tolerando AAAAMMDD_hhmmss y AAMMDD_hhmmss)
    for fila in lista_eventos:
        if not fila or len(fila) < 3:
            continue
        h = _extraer_hora_tramo(fila[1])

        # Tramo según la hora
        if h < 12:
            idx = 0
        elif h < 18:
            idx = 1
        else:
            idx = 2

        if len(fila) > 6 and str(fila[6]).strip() not in ("", "RSA") and not responsable_por_tramo[idx]:
            responsable_por_tramo[idx] = str(fila[6]).strip()

        # Tipo exacto (según tu pipeline)
        tipo = fila[2]

        # Suma por tipo, con tus equivalencias para 'local'
        if tipo == 'SISMO':
            contadores["sismo"][idx] += 1
        elif tipo == 'FF':
            contadores["ff"][idx] += 1
        elif tipo == 'FC':
            contadores["fc"][idx] += 1
        elif tipo == 'INDEFINIDO':
            contadores["indefinido"][idx] += 1
        elif tipo == 'TELESISMO':
            contadores["tele"][idx] += 1
        elif tipo == 'Evento_local' or tipo == 'CONTROL':
            contadores["local"][idx] += 1
        else:
            contadores["ruido"][idx] += 1

    # ----------------------------------------------------------------------
    # 3) Actualización de datos_tiempo (respetando responsables previos por turno)
    # ----------------------------------------------------------------------
    for i in (0, 1, 2):
        total = (
            contadores["sismo"][i] + contadores["ff"][i] + contadores["fc"][i] +
            contadores["indefinido"][i] + contadores["tele"][i] +
            contadores["local"][i] + contadores["ruido"][i]
        )

        # Si hay eventos en el tramo y la fila está vacía o sin responsable individual,
        # asignar el responsable (preservando el propietario si ya existía uno distinto de RSA)
        if total != 0:
            resp_actual_fila = str(datos_tiempo[i][0]).strip() if datos_tiempo[i] else ""
            if datos_tiempo[i][2] in ("0", "") or resp_actual_fila in ("", "RSA"):
                if responsable and responsable != "RSA":
                    datos_tiempo[i][0] = responsable
                elif responsable_por_tramo[i]:
                    datos_tiempo[i][0] = responsable_por_tramo[i]
                elif not resp_actual_fila:
                    datos_tiempo[i][0] = responsable or "RSA"
            datos_tiempo[i][1] = f"{etiquetas_tramo[i]}H"

        # Si la fila ya está “abierta” (o la acabamos de abrir), escribir conteos
        if datos_tiempo[i][2] != "" or total != 0:
            datos_tiempo[i][2] = str(total)
            datos_tiempo[i][3] = str(contadores["sismo"][i])
            datos_tiempo[i][4] = str(contadores["ff"][i])
            datos_tiempo[i][5] = str(contadores["fc"][i])
            datos_tiempo[i][6] = str(contadores["indefinido"][i])
            datos_tiempo[i][7] = str(contadores["tele"][i])
            datos_tiempo[i][8] = str(contadores["local"][i])
            datos_tiempo[i][9] = str(contadores["ruido"][i])

    escritura_archivo(archivo_guardar, datos_tiempo)

    # ----------------------------------------------------------------------
    # 4) Extracción y consolidación en el CSV principal
    #     - La barra de progreso usa el tamaño real de 'eventos_auxiliar'
    #     - 'bandera_todo' vacía 'eventos' para reprocesar todo preservando
    #       las clasificaciones y eventos exclusivos del CSV previo
    # ----------------------------------------------------------------------
    eventos = list(eventos_csv_previos or [])

    # La barra debe reflejar lo que realmente vamos a iterar
    maximo = len(eventos_auxiliar)
    ventana = VentanaProgreso("Extrayendo eventos...", maximo)

    try:
        if bandera_todo:
            eventos = []

        # Lista de claves ya existentes (columna 1 = AAAAMMDD_hhmmss)
        solo_eventos = [fila[1] for fila in eventos]

        for i, evento_auxiliar in enumerate(eventos_auxiliar):
            ventana.actualizar(i + 1)
            evento = extraccion(evento_auxiliar, solo_eventos, archivo, False)
            if evento is not None:
                eventos.append(evento)

        # Preservar eventos que estaban en AAAAMMDD000000.csv pero no tenían fila en _aux.csv
        if bandera_todo and filas_csv_previas_por_clave:
            for clave_prev, fila_prev in filas_csv_previas_por_clave.items():
                if clave_prev not in claves_en_aux:
                    eventos.append(fila_prev)

        # Consolidación final (según tu convención: clave en la columna 1)
        eventos = ordenar_y_eliminar_duplicados(eventos, 1, False)
        escritura_archivo(directorios['archivo_csv'], eventos)

    finally:
        # Asegura cierre de la ventana incluso si hay una excepción intermedia
        ventana.cerrar()


def _normalizar_clave_evento_reconstruccion(nombre_evento: str) -> str:
    """
    Normaliza el identificador de evento (.sis) a 14 dígitos (AAAAMMDDhhmmss)
    para cruzar de forma segura AAAAMMDD_aux.csv con AAAAMMDD000000.csv
    incluso en días históricos con nombres de 2 dígitos de año (AAMMDD_hhmmss.sis).
    """
    base = Path(str(nombre_evento).strip()).stem.replace('_', '')
    if len(base) == 12 and base.isdigit():
        return '20' + base
    return base


def _extraer_hora_tramo(nombre_evento: str) -> int:
    """Devuelve la hora (0..23) desde un nombre de evento AAAAMMDD_hhmmss.sis o AAMMDD_hhmmss.sis."""
    clave = _normalizar_clave_evento_reconstruccion(nombre_evento)
    if len(clave) >= 10 and clave[8:10].isdigit():
        return int(clave[8:10])
    return 0


def reconstruir_eventos_dia(
    archivo,
    responsable='RSA',
    sobrescribir_existentes=True,
    solo_presentes_en_csv=True,
    reconstruir_sis=False,
    parametros=None,
    estaciones_analogicas=None,
    progreso_callback=None,
    cancelar_callback=None,
):
    """
    Reconstruye los eventos de un día a partir de los registros continuos (.mseed en
    mseed/registros/), tomando las ventanas de tiempo [t_inicio, t_final] desde
    AAAAMMDD_aux.csv y aplicando la clasificación oficial y tokens existentes desde
    AAAAMMDD000000.csv.

    - Si falta AAAAMMDD_aux.csv, AAAAMMDD000000.csv o no hay registros continuos en
      mseed/registros/, el día se omite de forma segura sin error.
    - Preserva los eventos presentes en AAAAMMDD000000.csv que no figuren en _aux.csv
      (por ejemplo eventos EVT o de otras redes) y conserva todos los tokens EEEECBFFIISS
      previamente procesados.
    """
    import struct
    from obspy import read as obspy_read
    from scipy import signal
    from metodos_gestion import parametros_estaciones, obtencion_hora

    directorios = obtener_directorios(archivo)
    ruta_aux = directorios.get('archivo_auxiliar', '')
    ruta_csv = directorios.get('archivo_csv', '')
    dir_registros = directorios.get('Directorio_registros', '')
    dir_eventos = directorios.get('Directorio_eventos', '')
    dir_dia = directorios.get('Directorio_dia', '')

    resumen = {
        'estado': 'omitido',
        'motivo': '',
        'fecha_base': os.path.basename(directorios.get('Directorio_base', '')),
        'total_aux': 0,
        'eventos_reconstruidos': 0,
        'mseed_generados': 0,
        'sis_generados': 0,
        'ruido_omitidos': 0,
        'sin_match_csv': 0,
    }

    if not ruta_aux or not os.path.isfile(ruta_aux):
        resumen['motivo'] = 'No existe archivo AAAAMMDD_aux.csv'
        return resumen
    if not ruta_csv or not os.path.isfile(ruta_csv):
        resumen['motivo'] = 'No existe archivo AAAAMMDD000000.csv'
        return resumen
    if not dir_registros or not os.path.isdir(dir_registros):
        resumen['motivo'] = 'No existe carpeta mseed/registros'
        return resumen

    filas_aux = lectura_archivo(ruta_aux) or []
    filas_csv = lectura_archivo(ruta_csv) or []
    if not filas_aux:
        resumen['motivo'] = 'Archivo AAAAMMDD_aux.csv vacío'
        return resumen

    if parametros is None:
        parametros = parametros_estaciones()
    if estaciones_analogicas is None:
        estaciones_analogicas = lectura_archivo(os.path.join(ruta_datos, 'analogicas.csv')) or []

    # Verificar estaciones habilitadas que tengan registro continuo .mseed en este día
    fecha_ = obtencion_hora(archivo)
    sufijo_4d = fecha_.strftime('_%Y%m%d_%H%M%S.mseed')
    sufijo_2d = fecha_.strftime('_%y%m%d_%H%M%S.mseed')

    estaciones_con_senial = []
    for num_est, habil in enumerate(parametros['HAB_CANAL']):
        if habil != '1':
            continue
        cod_est = parametros['CODIGO'][num_est]
        cand_4d = os.path.join(dir_registros, cod_est + sufijo_4d)
        cand_2d = os.path.join(dir_registros, cod_est + sufijo_2d)
        if os.path.isfile(cand_4d):
            estaciones_con_senial.append((num_est, parametros['NOMBRE'][num_est], cod_est, cand_4d))
        elif os.path.isfile(cand_2d):
            estaciones_con_senial.append((num_est, parametros['NOMBRE'][num_est], cod_est, cand_2d))

    if not estaciones_con_senial:
        resumen['motivo'] = 'No hay registros continuos .mseed en mseed/registros'
        return resumen

    os.makedirs(dir_eventos, exist_ok=True)
    os.makedirs(dir_dia, exist_ok=True)

    # Indexar AAAAMMDD000000.csv por clave normalizada (preservando clasificación y tokens)
    mapa_csv = {}
    for fila_ev in filas_csv:
        if not fila_ev or len(fila_ev) < 3:
            continue
        clave = _normalizar_clave_evento_reconstruccion(fila_ev[1])
        if clave:
            mapa_csv[clave] = list(fila_ev)

    # Resolver cabecera binaria .sis una sola vez para el día
    candidatos_cabecera = [
        os.path.join(directorios['Directorio_trabajo'], "cabecera_sismo"),
        os.path.join(ruta_datos, "cabecera_sismo"),
        "C:/DIA/cabecera_sismo",
        os.path.join(directorios.get('Directorio_base', ''), "cabecera_sismo"),
    ]
    archivo_cabecera = next((c for c in candidatos_cabecera if os.path.exists(c)), candidatos_cabecera[0])

    # Índice rápido de códigos de estación
    mapa_cod_idx = {cod: idx for idx, cod in enumerate(parametros['CODIGO'])}
    total_estaciones = min(101, len(parametros['CODIGO']))

    # Mapa de filas consolidadas (arranca con todo lo que ya existía en AAAAMMDD000000.csv
    # para no perder eventos que no tengan entrada en _aux.csv)
    eventos_por_clave = dict(mapa_csv)
    claves_aux_procesadas = set()
    resumen['total_aux'] = len(filas_aux)

    for idx_aux, fila_aux in enumerate(filas_aux):
        if cancelar_callback and cancelar_callback():
            resumen['estado'] = 'cancelado'
            resumen['motivo'] = 'Cancelado por el usuario'
            return resumen

        if not fila_aux or len(fila_aux) < 6:
            continue

        nombre_ev_aux = str(fila_aux[1]).strip()
        clave_ev = _normalizar_clave_evento_reconstruccion(nombre_ev_aux)
        if not clave_ev or clave_ev in claves_aux_procesadas:
            continue
        claves_aux_procesadas.add(clave_ev)

        if progreso_callback:
            progreso_callback(idx_aux + 1, len(filas_aux), nombre_ev_aux)

        fila_csv_oficial = mapa_csv.get(clave_ev)
        if fila_csv_oficial is None:
            resumen['sin_match_csv'] += 1
            if solo_presentes_en_csv:
                continue
            tipo_evento = str(fila_aux[2]).strip()
            nombre_ev_final = nombre_ev_aux
            tokens_csv = []
        else:
            # Clasificación definitiva tomada de AAAAMMDD000000.csv
            tipo_evento = str(fila_csv_oficial[2]).strip()
            nombre_ev_final = str(fila_csv_oficial[1]).strip()
            tokens_csv = [tok for tok in fila_csv_oficial[3:] if tok and tok != '-']

        try:
            t_inicio = float(fila_aux[4])
            t_final = float(fila_aux[5])
        except (ValueError, TypeError):
            continue

        if t_inicio >= t_final:
            continue

        t_ini = fecha_ + t_inicio
        t_fin = fecha_ + t_final
        numero_de_muestras = int((t_fin - t_ini) * 64)
        timestamp_ev = t_ini.strftime('_%Y%m%d_%H%M%S.mseed')

        tokens_aux = []
        if len(fila_aux) > 7 and str(fila_aux[7]).strip():
            tokens_aux = str(fila_aux[7]).split()

        if tipo_evento.upper() == 'RUIDO':
            resumen['ruido_omitidos'] += 1
        else:
            # 1) Extraer .mseed por cada estación habilitada con registro continuo
            for num_est, _, cod_est, ruta_mseed_dia in estaciones_con_senial:
                nombre_mseed_ev = os.path.join(dir_eventos, cod_est + timestamp_ev)
                if not sobrescribir_existentes and os.path.isfile(nombre_mseed_ev):
                    continue
                try:
                    componente = int(parametros['COMPONENTE'][num_est]) - 1
                    stcanal = obspy_read(
                        ruta_mseed_dia,
                        format="MSEED",
                        starttime=t_ini,
                        endtime=t_fin,
                        nearest_sample=False,
                    )
                    if len(stcanal) == 0:
                        continue
                    stcanal = stcanal.copy()
                    comp_idx = min(max(0, componente), len(stcanal) - 1)
                    if parametros['POLARIDAD'][num_est] == 'N':
                        stcanal[comp_idx].data = stcanal[comp_idx].data * -1
                    stcanal.write(nombre_mseed_ev, format='MSEED', encoding='STEIM1', reclen=512)
                    resumen['mseed_generados'] += 1
                except Exception as e_ms:
                    print(f"Aviso reconstruyendo {cod_est}{timestamp_ev}: {e_ms}")

            # 2) Si está habilitada la reconstrucción de .sis y la clasificación definitiva es SISMO
            if reconstruir_sis and tipo_evento.upper() == 'SISMO':
                nombre_sis = os.path.join(dir_dia, t_ini.strftime('%Y%m%d_%H%M%S.sis'))
                if sobrescribir_existentes or not os.path.isfile(nombre_sis):
                    sismo_extraido = []
                    for estacion_analogica in estaciones_analogicas:
                        if not estacion_analogica or estacion_analogica[0] == 'ESTACION':
                            continue
                        num_est_an = int(estacion_analogica[0])
                        comp_an = int(parametros['COMPONENTE'][num_est_an]) - 1
                        ruta_ev_an = os.path.join(dir_eventos, parametros['CODIGO'][num_est_an] + timestamp_ev)
                        if not os.path.isfile(ruta_ev_an):
                            sismo_extraido.append(np.array([], dtype=np.int32))
                            continue
                        try:
                            st_an = obspy_read(ruta_ev_an).copy()
                            st_an.detrend("demean")
                            comp_idx = min(max(0, comp_an), len(st_an) - 1)
                            st_an[comp_idx].data = st_an[comp_idx].data.astype('int32')
                            sis_arr = st_an[comp_idx].data
                            fs = st_an[comp_idx].stats.sampling_rate
                            if fs != 64 and numero_de_muestras > 0:
                                sis_arr = signal.resample(sis_arr, numero_de_muestras)
                                sis_arr = np.rint(sis_arr).astype(np.int32)
                            if sis_arr.size != numero_de_muestras:
                                if sis_arr.size > numero_de_muestras:
                                    sis_arr = sis_arr[:numero_de_muestras]
                                else:
                                    sis_arr = np.pad(sis_arr, (0, numero_de_muestras - sis_arr.size), mode='constant')
                            sismo_extraido.append(sis_arr)
                        except Exception as e_an:
                            print(f"Aviso analógica {ruta_ev_an}: {e_an}")
                            sismo_extraido.append(np.array([], dtype=np.int32))

                    if os.path.isfile(archivo_cabecera) and numero_de_muestras > 0:
                        try:
                            hora_formateada = t_ini.strftime(" %H: %M: %S")
                            with open(archivo_cabecera, 'rb') as f_cab:
                                contador_cab = 0
                                while contador_cab < 2:
                                    marcador = f_cab.read(2)
                                    if not marcador:
                                        break
                                    if marcador == b'\x08\x00':
                                        cab_len = struct.unpack("<H", f_cab.read(2))[0]
                                        f_cab.read(cab_len)
                                        contador_cab += 1
                                puntero = f_cab.tell()
                                f_cab.seek(0)
                                cabecera = (
                                    f_cab.read(puntero)
                                    + b'\x08\x00\x0B\x00'
                                    + hora_formateada.encode('utf-8')
                                    + f_cab.read()
                                )

                            with open(nombre_sis, 'wb') as f_sis:
                                f_sis.write(cabecera)
                                segundo_ = t_ini.hour * 3600 + t_ini.minute * 60 + t_ini.second
                                f_sis.write(f'{segundo_:05}'.encode())
                                k = 0
                                for n in range(numero_de_muestras):
                                    if k == 0:
                                        f_sis.write(
                                            b'\x02\x20\x02\x00\x40\x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00'
                                        )
                                    k += 1
                                    if k == 64:
                                        k = 0
                                    for i_an, est_an in enumerate(estaciones_analogicas):
                                        if not est_an or est_an[0] == 'ESTACION':
                                            continue
                                        m_an = i_an - 1
                                        est_idx = int(est_an[0])
                                        if (
                                            parametros['HAB_CANAL'][est_idx] == "1"
                                            and m_an < len(sismo_extraido)
                                            and sismo_extraido[m_an].size > 0
                                        ):
                                            valor = int(sismo_extraido[m_an][n])
                                        else:
                                            valor = 0
                                        try:
                                            f_sis.write(valor.to_bytes(2, byteorder='little', signed=True))
                                        except OverflowError:
                                            f_sis.write((0).to_bytes(2, byteorder='little', signed=True))
                            resumen['sis_generados'] += 1
                        except Exception as e_sis:
                            print(f"Aviso generando binario .sis {nombre_sis}: {e_sis}")

        # 3) Actualizar tokens en la fila de AAAAMMDD000000.csv preservando tokens previos
        lista_guiones = ['-'] * 101
        for tok in tokens_csv:
            idx_c = mapa_cod_idx.get(tok[:4])
            if idx_c is not None and idx_c < 101:
                lista_guiones[idx_c] = tok
        for tok in tokens_aux:
            idx_c = mapa_cod_idx.get(tok[:4])
            if idx_c is not None and idx_c < 101 and lista_guiones[idx_c] == '-':
                lista_guiones[idx_c] = tok
        if tipo_evento.upper() != 'RUIDO':
            for idx_e in range(total_estaciones):
                if lista_guiones[idx_e] != '-':
                    continue
                ruta_ev_check = os.path.join(dir_eventos, parametros['CODIGO'][idx_e] + timestamp_ev)
                if os.path.isfile(ruta_ev_check):
                    cod = parametros['CODIGO'][idx_e]
                    canal = str(parametros['COMPONENTE'][idx_e]) if str(parametros['COMPONENTE'][idx_e]) else '0'
                    lista_guiones[idx_e] = f"{cod}{canal}0000000"

        prefijo_idx = str(fila_csv_oficial[0]) if fila_csv_oficial else str(fila_aux[0])
        eventos_por_clave[clave_ev] = [prefijo_idx, nombre_ev_final, tipo_evento] + lista_guiones
        resumen['eventos_reconstruidos'] += 1

    # 4) Guardar AAAAMMDD000000.csv consolidado, ordenado y deduplicado
    eventos_consolidados = list(eventos_por_clave.values())
    eventos_consolidados = ordenar_y_eliminar_duplicados(eventos_consolidados, 1, False)
    escritura_archivo(ruta_csv, eventos_consolidados)

    # 5) Actualizar archivo_tiempos con la clasificación oficial consolidada
    archivo_tiempos = directorios.get('archivo_tiempos', '')
    if archivo_tiempos:
        try:
            os.makedirs(os.path.dirname(archivo_tiempos), exist_ok=True)
            if os.path.isfile(archivo_tiempos):
                datos_tiempo = lectura_archivo(archivo_tiempos)
            else:
                datos_tiempo = [
                    ["RSA", "12H", "0", "0", "0", "0", "0", "0", "0", "0"],
                    ["RSA", "18H", "0", "0", "0", "0", "0", "0", "0", "0"],
                    ["RSA", "24H", "0", "0", "0", "0", "0", "0", "0", "0"],
                ]
            contadores = {
                "sismo": [0, 0, 0], "ff": [0, 0, 0], "fc": [0, 0, 0],
                "indefinido": [0, 0, 0], "tele": [0, 0, 0], "local": [0, 0, 0], "ruido": [0, 0, 0],
            }
            for fila_ev in eventos_consolidados:
                if not fila_ev or len(fila_ev) < 3:
                    continue
                h = _extraer_hora_tramo(fila_ev[1])
                idx_t = 0 if h < 12 else (1 if h < 18 else 2)
                tipo_t = str(fila_ev[2]).strip()
                if tipo_t == 'SISMO':
                    contadores["sismo"][idx_t] += 1
                elif tipo_t == 'FF':
                    contadores["ff"][idx_t] += 1
                elif tipo_t == 'FC':
                    contadores["fc"][idx_t] += 1
                elif tipo_t == 'INDEFINIDO':
                    contadores["indefinido"][idx_t] += 1
                elif tipo_t == 'TELESISMO':
                    contadores["tele"][idx_t] += 1
                elif tipo_t in ('Evento_local', 'CONTROL'):
                    contadores["local"][idx_t] += 1
                else:
                    contadores["ruido"][idx_t] += 1

            etiquetas_tramo = [12, 18, 24]
            for i_t in (0, 1, 2):
                if i_t >= len(datos_tiempo):
                    datos_tiempo.append([responsable or "RSA", f"{etiquetas_tramo[i_t]}H"] + ["0"] * 8)
                total_t = sum(contadores[k][i_t] for k in contadores)
                if total_t != 0 or datos_tiempo[i_t][2] != "":
                    datos_tiempo[i_t][1] = f"{etiquetas_tramo[i_t]}H"
                    datos_tiempo[i_t][2] = str(total_t)
                    datos_tiempo[i_t][3] = str(contadores["sismo"][i_t])
                    datos_tiempo[i_t][4] = str(contadores["ff"][i_t])
                    datos_tiempo[i_t][5] = str(contadores["fc"][i_t])
                    datos_tiempo[i_t][6] = str(contadores["indefinido"][i_t])
                    datos_tiempo[i_t][7] = str(contadores["tele"][i_t])
                    datos_tiempo[i_t][8] = str(contadores["local"][i_t])
                    datos_tiempo[i_t][9] = str(contadores["ruido"][i_t])
            escritura_archivo(archivo_tiempos, datos_tiempo)
        except Exception as e_t:
            print(f"Aviso actualizando archivo_tiempos: {e_t}")

    resumen['estado'] = 'ok'
    resumen['motivo'] = 'Reconstruido exitosamente'
    return resumen

def espectro_respuesta(acelerograma, dt,factor,directorio):
    """
    Calcula el espectro de respuesta de un sistema de un grado de libertad (SDOF)
    usando el método de Newmark a partir de un archivo mseed.

    Args:
        acelerogrma:  Datos desde el mseed
        dt:Delta t del acelerograma
        factor: factor de conversión par avolverlo en g

    Returns:
        tuple: (T, Spa, Spv, Sd, Sa, Sv)
            - T: Periodos del espectro.
            - Spa: Pseudoaceleración (GAL).
            - Spv: Pseudovelocidad (cm/s).
            - Sd: Desplazamiento máximo (cm).
            - Sa: Aceleración máxima (cm/s²).
            - Sv: Velocidad máxima (cm/s).
    """
    
    damp=0.05   #damp (float): Amortiguamiento adimensional. Default: 0.05 (5%).
    Tmin=0.02   #Tmin (float): Periodo mínimo para el espectro (s). Default: 0.02.
    Tmax=4.0    #Tmax (float): Periodo máximo para el espectro (s). Default: 4.0.
    Ax_g = acelerograma * factor/980.  # Suponemos que el factor convierte a m/s²

    # Convertir a fuerza externa
    m = 1  # Masa normalizada
    p = -m * Ax_g

    # Selección del método según dt
    beta = 1/4 if dt > 0.005 else 1/6
    gamma = 0.5  # Método de aceleración promedio

    # Definir periodos T
    deltaT = 0.05
    T = np.arange(Tmin, Tmax + deltaT, deltaT)

    # Inicialización de resultados
    nT = len(T)
    ls = len(Ax_g)
    Sd = np.zeros(nT)
    Sv = np.zeros(nT)
    Sa = np.zeros(nT)
    Spd = np.zeros(nT)
    Spv = np.zeros(nT)
    Spa = np.zeros(nT)

    # Cálculo para cada periodo T
    for j in range(nT):
        wn = 2 * np.pi / T[j]
        k = m * wn**2
        c = 2 * m * wn * damp

        # Inicializar variables del oscilador
        u = np.zeros(ls)
        udot = np.zeros(ls)
        uddot = np.zeros(ls)

        # Calcular parámetros para Newmark
        khat = k + gamma / beta / dt * c + m / beta / dt**2
        a = m / beta / dt + gamma * c / beta
        b = m / (2 * beta) + dt * (gamma / (2 * beta) - 1) * c

        # Resolver la ecuación para cada paso de tiempo
        for i in range(1, ls):
            dp = p[i] - p[i - 1]
            du = (dp + a * udot[i - 1] + b * uddot[i - 1]) / khat
            dudot = gamma / beta / dt * du - gamma / beta * udot[i - 1] + dt * (1 - gamma / (2 * beta)) * uddot[i - 1]
            duddot = du / (beta * dt**2) - udot[i - 1] / (beta * dt) - uddot[i - 1] / (2 * beta)

            # Actualizar variables
            u[i] = u[i - 1] + du
            udot[i] = udot[i - 1] + dudot
            uddot[i] = uddot[i - 1] + duddot

        # Calcular valores máximos
        Sd[j] = np.max(np.abs(u))
        Sv[j] = np.max(np.abs(udot))
        Sa[j] = np.max(np.abs(uddot))

        # Cálculo de pseudocantidades
        Spd[j] = Sd[j]
        Spv[j] = 2 * np.pi * Spd[j] / T[j]
        Spa[j] = 2 * np.pi * Spv[j] / T[j]

    return T, Spa, Spv, Sd, Sa, Sv




