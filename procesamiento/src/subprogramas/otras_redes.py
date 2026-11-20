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

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from rsa_io import lectura_archivo,escritura_archivo,Guardar_dia
from rsa_procesamiento import ordenar_y_eliminar_duplicados

from metodos_rsa import cargar_dia, extraer_datetime_evento_rsa
from metodos_gestion import obtener_directorios
from rsa_utilidades import ubicacion, actualizar_periodos_emitidos_desde_fecha

from PyQt5 import uic
from PyQt5.QtWidgets import (QMainWindow)
from datetime import datetime, timezone 

from PyQt5.QtCore import pyqtSignal

IDX_INDICE,IDX_ANIO,IDX_MES,IDX_DIA,IDX_HORA,IDX_MINUTO,IDX_SEGUNDO,\
IDX_LATITUD,IDX_LONGITUD,IDX_PROFUNDIDAD,IDX_RMS,IDX_E_X,IDX_E_Y,IDX_E_0,\
IDX_E_Z,IDX_MAGNITUD,IDX_UNIDAD_MAG,\
IDX_FUENTE,IDX_EVENTO,IDX_LUGAR = 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19

class Otras_redes(QMainWindow):
    cerrado = pyqtSignal()  # señal que se emitire al cerrar
    def __init__(self, archivo, directorio_trabajo, responsable, periodo, red, parent=None):#Constructor de la clase
        super(Otras_redes,self).__init__(parent)
        QMainWindow.__init__(self)
        #Carga la configuración del archivo .ui en el objeto

        # Cargar la interfaz desde el archivo .ui directamente en esta instancia
        ruta_ui =  os.path.join(ruta_proyecto,"src", "ui", 'otras_redes.ui')
        ruta_ui = os.path.abspath(ruta_ui)
        uic.loadUi(ruta_ui, self)

        #QtWidgets.QMainWindow.__init__(self)#Constructor
        #Ui_MainWindow.__init__(self)#Constructor
        self.visor = Figure(figsize=(8, 4), dpi=100)
        self.canvas = FigureCanvas(self.visor)
        self.archivo, self.directorio_trabajo, self.responsable, self.periodo,self.red=archivo, directorio_trabajo, responsable, periodo,red
        lista_filtros = [" ","IGEPN", "USGS", "Otras redes"]
        self.cmbx_red.addItems(lista_filtros)
        
        self.redes_diccionario = {
            "IGEPN": {"indice": 1, "ancho": 13,"hora":11,"latitud":5,"longitud":6,"profundidad":7,"magnitud":2,"tipo":3,"ubicacion":9,"divisor":'\n'},
            "USGS":  {"indice": 2, "ancho": 21,"hora":0,"latitud":1,"longitud":2,"profundidad":3,"magnitud":4,"tipo":5,"ubicacion":13,"divisor":'\n'}
            }
        self.n_columnas=self.redes_diccionario[self.red]["ancho"]                   
        self.spinBox.setValue(self.n_columnas)   
        self.cmbx_red.setCurrentIndex(self.redes_diccionario[self.red]["indice"])

        self.textEdit.resize(1200, 400)
        
        self.Btn_Leer.clicked.connect(self.leer_datos)
        self.Btn_Salir.clicked.connect(self.Salir_)


    def leer_datos(self):
        catalogo_otras_redes = self.leer_qtextedit_como_matriz(self.textEdit)
        dias_modificados = set()
        for evento_otras_redes in catalogo_otras_redes:
            hora_otras_redes = self.lectura_hora(evento_otras_redes[IDX_EVENTO])
            if hora_otras_redes is None:
                continue
            archivo = os.path.join(
                self.directorio_trabajo,
                evento_otras_redes[IDX_EVENTO].split(".", 1)[0].replace("_", "")
            )
            directorios = obtener_directorios(archivo)
            if not os.path.exists(directorios["archivo_catalogo"]) and not os.path.exists(directorios["archivo_csv"]):
                continue

            catalogo = lectura_archivo(directorios["archivo_catalogo"]) if os.path.exists(directorios["archivo_catalogo"]) else []
            eventos = lectura_archivo(directorios["archivo_csv"]) if os.path.exists(directorios["archivo_csv"]) else []

            mejor_delta_seg = None
            mejor_fila_cat = None
            mejor_evento_sis = None

            # 1) Búsqueda prioritaria en función del catálogo de la Red Sísmica (_cat.csv)
            for fila_cat in catalogo:
                if not fila_cat or len(fila_cat) <= IDX_EVENTO or fila_cat[0] == "Id":
                    continue
                if str(fila_cat[IDX_FUENTE]).strip() != "RSA" and not str(fila_cat[IDX_INDICE]).strip().endswith("00"):
                    continue
                hora_cat = extraer_datetime_evento_rsa(fila_cat[IDX_EVENTO], catalogo)
                if hora_cat is None:
                    continue
                delta_seg = abs((hora_cat - hora_otras_redes).total_seconds())
                if (mejor_delta_seg is None) or (delta_seg < mejor_delta_seg):
                    mejor_delta_seg = delta_seg
                    mejor_fila_cat = fila_cat
                    mejor_evento_sis = fila_cat[IDX_EVENTO]

            # 2) Respaldo sobre eventos FF / FC / SISMO del archivo diario AAAAMMDD000000.csv
            if mejor_delta_seg is None or mejor_delta_seg >= 60:
                for evento in eventos:
                    if not evento or len(evento) < 3:
                        continue
                    if evento[2] not in ("SISMO", "FC", "FF"):
                        continue
                    hora_evento = extraer_datetime_evento_rsa(evento[1], catalogo)
                    if hora_evento is None:
                        continue
                    delta_seg = abs((hora_evento - hora_otras_redes).total_seconds())
                    if (mejor_delta_seg is None) or (delta_seg < mejor_delta_seg):
                        mejor_delta_seg = delta_seg
                        mejor_fila_cat = None
                        mejor_evento_sis = evento[1]

            # Resultado por cada evento de otras redes que coincida (< 60 s)
            if mejor_delta_seg is not None and mejor_delta_seg < 60 and mejor_evento_sis:
                if mejor_fila_cat is not None:
                    evento_otras_redes[IDX_INDICE] = (
                        str(mejor_fila_cat[IDX_INDICE]).strip()[:-2]
                        + str(evento_otras_redes[IDX_INDICE]).strip()[-2:]
                    )
                    evento_otras_redes[IDX_EVENTO] = str(mejor_fila_cat[IDX_EVENTO]).strip()
                else:
                    evento_otras_redes[IDX_EVENTO] = str(mejor_evento_sis).strip()

                try:
                    evento_otras_redes[IDX_LUGAR] = ubicacion(
                        float(evento_otras_redes[IDX_LATITUD]),
                        float(evento_otras_redes[IDX_LONGITUD]),
                    )
                except Exception:
                    pass

                catalogo = [
                    f for f in catalogo
                    if not (
                        f and len(f) > IDX_EVENTO and f[0] != "Id"
                        and str(f[IDX_FUENTE]).strip() == str(evento_otras_redes[IDX_FUENTE]).strip()
                        and str(f[IDX_EVENTO]).strip() == str(evento_otras_redes[IDX_EVENTO]).strip()
                    )
                ]
                catalogo.append(evento_otras_redes)
                catalogo = ordenar_y_eliminar_duplicados(catalogo, 0)
                print("Ingresando evento", evento_otras_redes[IDX_EVENTO], evento_otras_redes[IDX_FUENTE])
                escritura_archivo(directorios["archivo_catalogo"], catalogo)
                dias_modificados.add(directorios["archivo_csv"])

        self.textEdit.clear()
        for archivo_csv_dia in sorted(dias_modificados):
            directorios_dia = obtener_directorios(archivo_csv_dia)
            (
                eventos_reporte,
                catalogo,
                eventos,
                vector,
                evento_canales,
                root,
                responsables,
                resumen,
            ) = cargar_dia(directorios_dia)
            Guardar_dia(eventos_reporte, catalogo, eventos, root, responsables, resumen, directorios_dia)
            actualizar_periodos_emitidos_desde_fecha(archivo_csv_dia, self.directorio_trabajo)

    def lectura_hora(self, evento):
        return extraer_datetime_evento_rsa(evento)
        
        
        


    def leer_qtextedit_como_matriz(self,textedit):
        """
        Lee el contenido de un QTextEdit y lo convierte en una matriz (lista de listas).
        Soporta tablas separadas por TABs o por columnas alineadas con 2+ espacios.
        """
        texto = textedit.toPlainText()
        
        variables=texto.split(self.redes_diccionario[self.red]["divisor"])  
        filas=[]
        if self.red=='IGEPN':
           
            variables = [x for x in variables if x != '']
            print(variables)
            for i in range(0,len(variables),self.n_columnas):
                filas.append(variables[i:i+self.n_columnas])
        else:
            for variable in variables:
                filas.append(variable.split(','))
        catalogo=[]

        for evento_otras_redes in filas[1:]:
            cadena=evento_otras_redes[self.redes_diccionario[self.red]["hora"]]
            if self.red=='IGEPN':
                dt = datetime.strptime(cadena, "%Y-%m-%d %H:%M:%S")
            else:
                dt = datetime.fromisoformat(cadena.replace("Z", "+00:00")).astimezone(timezone.utc)
            anio, mes, dia = dt.year, dt.month, dt.day
            hora, minuto, segundo = dt.hour, dt.minute, dt.second
            id_evento = dt.strftime("%Y%m%d%H%M")+str(self.redes_diccionario[self.red]["indice"]).zfill(2)
            latitud=evento_otras_redes[self.redes_diccionario[self.red]["latitud"]]
            factor=1
            if latitud[-3:]=='° S':
                factor=-1
            latitud=float(latitud[:-3])*factor
            longitud=evento_otras_redes[self.redes_diccionario[self.red]["longitud"]]
            longitud=float(longitud[:-3])*(-1)
            profundidad=float(evento_otras_redes[self.redes_diccionario[self.red]["profundidad"]])
            magnitud=evento_otras_redes[self.redes_diccionario[self.red]["magnitud"]]
            tipo=evento_otras_redes[self.redes_diccionario[self.red]["tipo"]]
            ruta=dt.strftime("%Y%m%d_%H%M%S") + ".sis"
            ubicacion=evento_otras_redes[self.redes_diccionario[self.red]["ubicacion"]]
            evento=[id_evento,str(anio),str(mes),str(dia),str(hora),str(minuto),str(segundo),str(latitud),str(longitud),str(profundidad),'','','','','',str(magnitud),tipo,self.red,ruta,ubicacion]
            catalogo.append(evento)
        print(catalogo)
        return catalogo





    def Salir_(self):
        print('Saliendo desde boton:')
        self.close()


    def limpiar_estado(self):
        """Limpia figuras, visores, hilos, timers, etc., antes de cerrar."""
        try:
            if hasattr(self, 'canvas'):
                self.canvas.deleteLater()
                self.canvas = None
            if hasattr(self, 'visor'):
                self.visor.clf()
                self.visor = None
            # Limpieza de listas, buffers o datos
            if hasattr(self, 'stLeido'):
                del self.stLeido
            if hasattr(self, 'lista_eventos'):
                self.lista_eventos.clear()
        except Exception as e:
            print(f"Error en limpieza de Reporte_diario: {e}")


    def closeEvent(self, event):
        """
        Emite la señal de cerrado para notificar a la ventana principal y realiza limpieza.
        """
        print("Saliendo de Reporte diario - closeEvent ejecutado")
    
        # Limpiar estado antes de emitir señal
        self.limpiar_estado()
        
        # Emitir señal una sola vez
        self.cerrado.emit()
    
        # Aceptar el evento de cierre
        event.accept()
    
        print("closeEvent completado - señal cerrado emitida")
        
        