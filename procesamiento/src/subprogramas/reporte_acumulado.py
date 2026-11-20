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
ruta_modulos_externos = os.path.abspath(os.path.join(ruta_proyecto, 'modulos externos'))
# Insertar la ruta al inicio del sys.path
if ruta_librerias not in sys.path:
    sys.path.insert(0, ruta_librerias)
if ruta_datos not in sys.path:
    sys.path.insert(0, ruta_datos)
if ruta_modulos_externos not in sys.path:
    sys.path.insert(0, ruta_modulos_externos)

try:
    from generar_shape import generar_shapefile, metadatos_sugeridos, leer_csv as leer_csv_shape
except Exception:
    generar_shapefile = None
    metadatos_sugeridos = None
    leer_csv_shape = None


from rsa_io import lectura_resumen,lectura_archivo,escritura_archivo,Guardar_dia
from rsa_dominio import correccion
from rsa_utilidades import obtener_datos_reporte, generar_directorios_unidades_basicas, actualizar_periodos_emitidos_desde_fecha
from rsa_pdf_catalogo import (
    reporte_resumen_modos,
    resolver_modo_por_zona,
    obtener_perfil_mapa,
    MODO_MAPA_ESPECIAL,
    MODO_PERIODO_FRANJAS,
    MODO_DIARIO_REVISION,
    MODO_OFICIAL_DETALLADO,
    MODO_OFICIAL_RESUMEN,
    MODO_FACULTAD_RESUMEN,
    MODO_INSTITUCIONAL_DETALLADO,
    MODO_INSTITUCIONAL_RESUMEN,
)
from metodos_rsa import parametros_estaciones,cargar_dia,extraer_hasta_directorio
from metodos_gestion import obtener_directorios
from metodos_gis_rsa import widget_grafico_mpl, graficar_periodo_gis
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT

import csv
from PyQt5 import uic, QtWidgets#Importamos módulo uic y Qtwidgets
from datetime import datetime, time, timedelta
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtWidgets import ( QMainWindow, QMessageBox,QFileDialog)
import sys
import xml.etree.ElementTree as ET
import copy
from obspy import read
import calendar
import os
from PyQt5.QtCore import pyqtSignal
IDX_INDICE,IDX_ANIO,IDX_MES,IDX_DIA,IDX_HORA,IDX_MINUTO,IDX_SEGUNDO,\
IDX_LATITUD,IDX_LONGITUD,IDX_PROFUNDIDAD,IDX_RMS,IDX_E_X,IDX_E_Y,IDX_E_0,\
IDX_E_Z,IDX_MAGNITUD,IDX_UNIDAD_MAG,\
IDX_FUENTE,IDX_EVENTO,IDX_LUGAR = 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19

NUMERO_ESTACIONES=101

IDX_LONGITUD_MINIMA,IDX_LATITUD_MINIMA,IDX_LONGITUD_MAXIMA,IDX_LATITUD_MAXIMA=0,1,2,3
IDX_POSICION_X,IDX_POSICION_Y,IDX_ANCHO,IDX_ALTO,=0,1,2,3

###################################
#archivo es el nombre del archivo con el que se grabará el archivo pdf
#titulo es lo que aparecerácomo primera línea del pdf
#vector es la variable que contiene la información sísmica.
#resumen
#bandera_dia variable que habilita o no la impresión del reporte diario de eventos (esto es para deshabilitar en el reporte diario)

# =========================
#  MODOS DE REPORTE (1–7)
# =========================
MODO_PERIODO_FRANJAS          = 1   # M1 – Período por franjas (00–12, 12–18, 18–24) – Control interno
MODO_DIARIO_REVISION          = 2   # M2 – Diario de revisión (día/ad-hoc) con detalle y dummies locales
MODO_OFICIAL_DETALLADO        = 3   # M3 – Oficial detallado (solo catálogo) + página/resumen de responsables
MODO_OFICIAL_RESUMEN          = 4   # M4 – Oficial resumen (solo catálogo, sin detalle)
MODO_FACULTAD_RESUMEN         = 5   # M5 – Institucional resumen (Facultad/redes), sin detalle
MODO_INSTITUCIONAL_DETALLADO  = 6   # M6 – Institucional detallado (solo catálogo), sin extras ni responsables
MODO_INSTITUCIONAL_RESUMEN    = 7   # M7 – Institucional, sin detalle

class VentanaEstaciones(QtWidgets.QDialog):
    def __init__(self, parametros, parent=None):
        super(VentanaEstaciones, self).__init__(parent)
        self.setWindowTitle("Selector de Estaciones")
        self.parametros = parametros
        self.resize(600, 400)

        self.layout_principal = QtWidgets.QVBoxLayout(self)

        # Filtros por tipo de sensor
        self.filtro_sismicos = QtWidgets.QCheckBox("SISMICOS")
        self.filtro_acelerograficos = QtWidgets.QCheckBox("ACELEROGRAFICOS")
        self.filtro_sismicos.setChecked(True)
        self.filtro_acelerograficos.setChecked(True)

        filtro_layout = QtWidgets.QHBoxLayout()
        filtro_layout.addWidget(self.filtro_sismicos)
        filtro_layout.addWidget(self.filtro_acelerograficos)
        self.layout_principal.addLayout(filtro_layout)

        # Área de scroll para checkboxes de estaciones
        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_widget = QtWidgets.QWidget()
        self.layout_estaciones = QtWidgets.QVBoxLayout(self.scroll_widget)

        self.scroll_area.setWidget(self.scroll_widget)
        self.layout_principal.addWidget(self.scroll_area)

        # Botón de marcar/desmarcar
        self.btn_toggle_seleccion = QtWidgets.QPushButton("Marcar/Desmarcar todos")
        self.layout_principal.addWidget(self.btn_toggle_seleccion)

        # Botones de acción
        botones_layout = QtWidgets.QHBoxLayout()
        self.btn_ejecutar = QtWidgets.QPushButton("Ejecutar")
        self.btn_salir = QtWidgets.QPushButton("Salir")
        botones_layout.addWidget(self.btn_ejecutar)
        botones_layout.addWidget(self.btn_salir)
        self.layout_principal.addLayout(botones_layout)

        # Conexiones
        self.filtro_sismicos.stateChanged.connect(self.actualizar_estaciones)
        self.filtro_acelerograficos.stateChanged.connect(self.actualizar_estaciones)
        self.btn_toggle_seleccion.clicked.connect(self.toggle_todos)
        self.btn_salir.clicked.connect(self.close)

        self.checkboxes_estaciones = []
        self.actualizar_estaciones()

    def actualizar_estaciones(self):
        # Limpiar layout
        for i in reversed(range(self.layout_estaciones.count())):
            widget = self.layout_estaciones.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        self.checkboxes_estaciones.clear()

        for i in range(len(self.parametros['HAB_CANAL'])):
            if self.parametros['HAB_CANAL'][i] == "1":
                sensor = self.parametros['SENSOR'][i]
                mostrar = False
                if sensor == "SISMICO" and self.filtro_sismicos.isChecked():
                    mostrar = True
                elif sensor == "ACELEROGRAFICO" and self.filtro_acelerograficos.isChecked():
                    mostrar = True
                if mostrar:
                    nombre = self.parametros['NOMBRE'][i]
                    codigo = self.parametros['CODIGO'][i]
                    tipo = self.parametros['SENSOR'][i]
                    checkbox = QtWidgets.QCheckBox(f"{codigo} - {nombre} ({tipo})")
                    checkbox.setProperty("indice", i)
                    self.layout_estaciones.addWidget(checkbox)
                    self.checkboxes_estaciones.append(checkbox)

    def toggle_todos(self):
        """Marca o desmarca todos los checkboxes filtrados"""
        if not self.checkboxes_estaciones:
            return

        # Verificar si hay alguno desmarcado
        alguno_sin_marcar = any(not cb.isChecked() for cb in self.checkboxes_estaciones)
        for cb in self.checkboxes_estaciones:
            cb.setChecked(alguno_sin_marcar)

    def obtener_estaciones_seleccionadas(self):
        """Devuelve los índices de estaciones seleccionadas"""
        seleccionadas = []
        for cb in self.checkboxes_estaciones:
            if cb.isChecked():
                seleccionadas.append(cb.property("indice"))
        return seleccionadas


class Reporte_periodo(QMainWindow):
    cerrado = pyqtSignal()  # señal que se emitire al cerrar
    def __init__(self, archivo, directorio_trabajo, responsable, horario, parent=None):#Constructor de la clase
        super(Reporte_periodo,self).__init__(parent)
        QMainWindow.__init__(self)
        #Carga la configuración del archivo .ui en el objeto

        # Cargar la interfaz desde el archivo .ui directamente en esta instancia
        ruta_ui =  os.path.join(ruta_proyecto,"src", "ui", "reporte_mensual.ui")
        ruta_ui = os.path.abspath(ruta_ui)
        uic.loadUi(ruta_ui, self)
        
        self.directorio_trabajo = directorio_trabajo
        self.archivo=archivo
        self.responsable=responsable
        self.horario=horario
        
        
        self.Btn_Salir.clicked.connect(self.Salir_)
        self.Btn_guardar.clicked.connect(self.Guardar_)
        self.Btn_cargar_catalogo.clicked.connect(self.cargar_catalogo_guardado)
        self.btn_estaciones.clicked.connect(self.estaciones)
        self.btn_periodo.clicked.connect(self.periodo)
        self.btn_mes.clicked.connect(self.mes_)
        self.btn_anio.clicked.connect(self.anio_)
        self.btn_semana.clicked.connect(self.semana_)
        self.btn_selector_estaciones.clicked.connect(self.abrir_ventana_estaciones)
        self.estaciones_habilitadas=[]
        self.nombre_estaciones_habilitadas=[]
        self.btn_periodo_cat.clicked.connect(self.acumular_solo_catalogo)
        lista_estaciones=[]
        self.parametros=parametros_estaciones()
        for i in range (0,101):
            if self.parametros['HAB_CANAL'][i]=='1':
                lista_estaciones.append(self.parametros['NOMBRE'][i])
                self.estaciones_habilitadas.append(i)
                self.nombre_estaciones_habilitadas.append(self.parametros['CODIGO'][i])
        self.Cmb_bx_estacion.addItems(lista_estaciones)    
        self.inicializar_variables()

        lista_filtros = ["Ruido", "FF", "FC","TELESISMO","SISMO","INDEFINIDO","Evento_local",'CONTROL',"TODOS"]
        self.Cmb_bx_tipo_evento.addItems(lista_filtros)
        lista_anio=[]
        for i in range(1995,2050):
            lista_anio.append(str(i))
        lista_semana=[]
        for i in range(1,54):
            auxiliar=str(i)
            if i<10:
                auxiliar="0"+auxiliar
            lista_semana.append(auxiliar)
        self.comboBox_semana.addItems(lista_semana)
        lista_mes=["Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
        self.comboBox_mes.addItems(lista_mes)
        self.comboBox_anio.addItems(lista_anio)

        archivo =  os.path.join(ruta_proyecto,"datos", "mapas",'mapas.csv')
        archivo = os.path.abspath(archivo)

        with open(archivo,newline='') as mapas_csv:
            lista_mapas=csv.reader(mapas_csv,delimiter=';',quotechar=';')
            mapa=[]
            self.coordenadas=[]
            for x in lista_mapas:
                if x[0]!='nombre':
                    mapa.append(x[0])
                    self.coordenadas.append(x[1:7])
        self.cmbx_zona.addItems(mapa)
        self.cmbx_zona.setCurrentIndex(1)
        tipo_mapa=("1.Básico","1.Medio","3.Físico","4.Nidos","5.Fallas","6.Combinados")
        self.cmbx_mapa.addItems(tipo_mapa)
        magnitudes=("todos","2.5","3.0","3.5","4.0","4.5","5.0","5.5","6.0","6.5")
        self.cmbx_magnitud.addItems(magnitudes)
        estaciones_n=("todos","4","5","6","7")
        self.cmbx_n_estaciones.addItems(estaciones_n)
        profundidades=("Todos","Superficiales","Medios","Profundos","Sup. y Medios","Medios y prof.")
        self.cmbx_profundidad.addItems(profundidades)
        self.hoy=datetime.today()              #obtención de la fecha y hora actual
        d_ini = QDate(self.hoy.year, self.hoy.month,self.hoy.day-7)# obtención del año , mes y día en forma individual
        d_fin = QDate(self.hoy.year, self.hoy.month,self.hoy.day)# obtención del año , mes y día en forma individual
        self.dateEdit_ini.setDate(d_ini)    #Conficuración de los datos de fecha en el DataEdit
        self.dateEdit_fin.setDate(d_fin)
        semana = self.hoy.strftime("%U")
        hoy = QDate.currentDate()
        self.dateEdit_ini_cat.setDate(QDate(2000, 1, 1))
        self.dateEdit_fin_cat.setDate(QDate(hoy.year(), hoy.month(), 1))

        self.comboBox_semana.setCurrentIndex(max(0, int(semana) - 1))
        self.comboBox_anio.setCurrentIndex(int(self.hoy.year) - 1995)
        self.comboBox_mes.setCurrentIndex(int(self.hoy.month) - 1)

        # Corrección preventiva de fechas cuando el día del mes es <= 7
        d_fin_seguro = QDate.currentDate()
        d_ini_seguro = d_fin_seguro.addDays(-7)
        self.dateEdit_ini.setDate(d_ini_seguro)
        self.dateEdit_fin.setDate(d_fin_seguro)

        # Ampliar opciones de mínimo de estaciones para mecanismos focales
        if self.cmbx_n_estaciones.findText("8") == -1:
            self.cmbx_n_estaciones.addItems(["8", "10"])

        # =====================================================================
        # CONFIGURACIÓN DE GRUPOS DE RADIOBUTTONS EXCLUYENTES (ZONAS 1 y 2)
        # =====================================================================
        # 1A) Grupo excluyente para la unidad de período (Año, Mes, Semana o Rango de Fechas)
        self.grupo_rb_periodo = QtWidgets.QButtonGroup(self)
        if hasattr(self, 'rb_anio'):
            self.grupo_rb_periodo.addButton(self.rb_anio, 0)
            self.grupo_rb_periodo.addButton(self.rb_mes, 1)
            self.grupo_rb_periodo.addButton(self.rb_semana, 2)
            self.grupo_rb_periodo.addButton(self.rb_periodo, 3)
            self.grupo_rb_periodo.buttonClicked.connect(self._actualizar_controles_periodo)

        # 1B) Grupo excluyente para la fuente de consolidación (_cat.csv existente por defecto vs Día por día)
        self.grupo_rb_fuente = QtWidgets.QButtonGroup(self)
        if hasattr(self, 'rb_fuente_diaria'):
            self.grupo_rb_fuente.addButton(self.rb_fuente_catalogo, 1)
            self.grupo_rb_fuente.addButton(self.rb_fuente_diaria, 0)
            self.rb_fuente_catalogo.setChecked(True)

        # 1C) Botón unificado de carga de período
        if hasattr(self, 'btn_cargar_periodo'):
            self.btn_cargar_periodo.clicked.connect(self.cargar_periodo_unificado)

        # 2A) Grupo excluyente de modo de filtro de profundidad (Estratos vs Rango numérico km)
        self.grupo_rb_prof = QtWidgets.QButtonGroup(self)
        if hasattr(self, 'rb_prof_estratos'):
            self.grupo_rb_prof.addButton(self.rb_prof_estratos, 0)
            self.grupo_rb_prof.addButton(self.rb_prof_rango, 1)
            self.grupo_rb_prof.buttonClicked.connect(self._al_cambiar_controles_filtro)

        # 2B) Grupo excluyente de modo de filtro de magnitud (Umbral/Todas vs Rango numérico Md)
        self.grupo_rb_mag = QtWidgets.QButtonGroup(self)
        if hasattr(self, 'rb_mag_todos'):
            self.grupo_rb_mag.addButton(self.rb_mag_todos, 0)
            self.grupo_rb_mag.addButton(self.rb_mag_rango, 1)
            self.grupo_rb_mag.buttonClicked.connect(self._al_cambiar_controles_filtro)

        # 4A) Grupo excluyente de las 3 posibilidades de simbología de círculos en Zona 4
        #     (Círculos rellenos = 1, Círculos sin relleno = 0, Círculos concéntricos = 2)
        self.grupo_rb_simbologia = QtWidgets.QButtonGroup(self)
        if hasattr(self, 'rb_circulos_rellenos'):
            self.grupo_rb_simbologia.addButton(self.rb_circulos_rellenos, 1)
            self.grupo_rb_simbologia.addButton(self.rb_circulos_sin_relleno, 0)
            self.grupo_rb_simbologia.addButton(self.rb_circulos_concentricos, 2)
            self.grupo_rb_simbologia.buttonClicked.connect(self._al_cambiar_controles_filtro)

        # Conexiones de reactivación de catálogo respaldado ante cambios de región o filtros
        self._zona_previa = self.cmbx_zona.currentText().strip()
        self.cmbx_zona.currentIndexChanged.connect(self._al_cambiar_zona_mapa)
        self.cmbx_mapa.currentIndexChanged.connect(self._al_cambiar_controles_filtro)
        self.cmbx_magnitud.currentIndexChanged.connect(self._al_cambiar_controles_filtro)
        self.cmbx_profundidad.currentIndexChanged.connect(self._al_cambiar_controles_filtro)
        self.cmbx_n_estaciones.currentIndexChanged.connect(self._al_cambiar_controles_filtro)
        if hasattr(self, 'cmbx_filtro_red') and self.cmbx_filtro_red is not None:
            self.cmbx_filtro_red.currentIndexChanged.connect(self._al_cambiar_controles_filtro)

        for nombre_ctrl in (
            'ck_box_filtro', 'ck_prof_sup', 'ck_prof_med', 'ck_prof_pro',
            'ck_nest_catalogo', 'ck_box_reporte', 'ck_box_firma',
            'ck_box_relleno', 'ck_box_concentricos'
        ):
            ctrl = getattr(self, nombre_ctrl, None)
            if ctrl is not None:
                ctrl.stateChanged.connect(self._al_cambiar_controles_filtro)

        for nombre_spin in ('spin_prof_min', 'spin_prof_max', 'spin_mag_min', 'spin_mag_max'):
            sp = getattr(self, nombre_spin, None)
            if sp is not None:
                sp.valueChanged.connect(self._al_cambiar_controles_filtro)

        # =====================================================================
        # CONFIGURACIÓN DE VISTA PREVIA CARTOGRÁFICA GIS (ZONA 5)
        # =====================================================================
        if hasattr(self, 'contenedor_mapa_gis') and self.contenedor_mapa_gis is not None:
            self.layout_mapa_gis = QtWidgets.QVBoxLayout(self.contenedor_mapa_gis)
            self.layout_mapa_gis.setContentsMargins(0, 0, 0, 0)
            self.widget_mapa_gis = widget_grafico_mpl(self.contenedor_mapa_gis)
            self.layout_mapa_gis.addWidget(self.widget_mapa_gis)
        else:
            self.widget_mapa_gis = None

        self._ventana_emergente_gis = None
        self._widget_mapa_gis_emergente = None

        if hasattr(self, 'btn_actualizar_gis') and self.btn_actualizar_gis is not None:
            self.btn_actualizar_gis.clicked.connect(self.actualizar_vista_gis)
        if hasattr(self, 'btn_ampliar_gis') and self.btn_ampliar_gis is not None:
            self.btn_ampliar_gis.clicked.connect(self.abrir_ventana_emergente_gis)
        if hasattr(self, 'btn_exportar_gis') and self.btn_exportar_gis is not None:
            self.btn_exportar_gis.clicked.connect(self.exportar_imagen_gis)
        if hasattr(self, 'ck_gis_estaciones') and self.ck_gis_estaciones is not None:
            self.ck_gis_estaciones.stateChanged.connect(self.actualizar_vista_gis)

        self._actualizar_controles_periodo()
        self._actualizar_estado_visual_filtros()
        self.actualizar_vista_gis()
        self._registrar_bitacora(
            "Sistema listo. Seleccione un período en la Zona 1 (Año, Mes, Semana o Rango de Fechas),\n"
            "elija la fuente (Día por día o Reportes existentes _cat.csv) y pulse 'Cargar Período Seleccionado'."
        )

    def _obtener_estilo_circulos_mapa(self):
        """
        Evalúa las tres posibilidades excluyentes de simbología en el mapa:
          - True  : Círculos rellenos
          - False : Círculos sin relleno
          - 2     : Círculos concéntricos (solo el mapa principal, sin detalle adicional)
        """
        if hasattr(self, 'rb_circulos_concentricos') and self.rb_circulos_concentricos.isChecked():
            return 2
        if hasattr(self, 'rb_circulos_sin_relleno') and self.rb_circulos_sin_relleno.isChecked():
            return False
        if hasattr(self, 'rb_circulos_rellenos') and self.rb_circulos_rellenos.isChecked():
            return True
        if hasattr(self, 'ck_box_concentricos') and self.ck_box_concentricos.isChecked():
            return 2
        return bool(self.ck_box_relleno.isChecked()) if hasattr(self, 'ck_box_relleno') else True

    def resolver_modo_desde_controles(self) -> int:
        """
        Devuelve el MODO_* (M0..M7) delegando en el catálogo centralizado de modos (`rsa_pdf_catalogo.py`)
        en función de:
            - rb_circulos_concentricos: si está seleccionado, devuelve MODO_MAPA_ESPECIAL (0)
              porque solo requiere el mapa principal sin ningún detalle adicional.
            - cmbx_zona: 'Region', 'Ecuador', 'Facultad', 'Fuentes', 'Reportes', 'Chanlud', ...
            - ck_box_reporte: marcado = 'detallado', desmarcado = 'resumen' (cuando aplica)
        Nota: M1 y M2 no se generan aquí (período por franjas y diario de revisión).
        """
        if self._obtener_estilo_circulos_mapa() == 2:
            return MODO_MAPA_ESPECIAL
        zona = (self.cmbx_zona.currentText() if self.cmbx_zona else "").strip()
        reporte_marcado = bool(self.ck_box_reporte.isChecked()) if self.ck_box_reporte else False
        return resolver_modo_por_zona(zona, con_detalle=reporte_marcado)

    # =========================================================================
    # VISTA PREVIA CARTOGRÁFICA INTERACTIVA GIS (ZONA 5)
    # =========================================================================
    def actualizar_vista_gis(self):
        """
        Actualiza el mapa cartográfico interactivo GIS en la columna derecha (Zona 5)
        con el catálogo sísmico filtrado según los controles activos (Región, Profundidad,
        Magnitud, N° de Estaciones y Simbología).
        """
        if not hasattr(self, 'widget_mapa_gis') or self.widget_mapa_gis is None:
            return

        idx_zona = self.cmbx_zona.currentIndex() if hasattr(self, 'cmbx_zona') else 1
        coord_zona = self.coordenadas[idx_zona] if hasattr(self, 'coordenadas') and 0 <= idx_zona < len(self.coordenadas) else None
        zona_txt = self.cmbx_zona.currentText().strip() if hasattr(self, 'cmbx_zona') else 'Ecuador'
        estilo_circulos = self._obtener_estilo_circulos_mapa()
        mostrar_est = bool(self.ck_gis_estaciones.isChecked()) if hasattr(self, 'ck_gis_estaciones') else True
        periodo_txt = getattr(self, 'periodo_reporte', '').strip()
        titulo = f"VISTA PREVIA GIS — {zona_txt.upper()}" + (f" ({periodo_txt})" if periodo_txt else "")

        # Si hay catálogo en memoria, restaurar catálogo base y aplicar filtros activos
        if hasattr(self, 'catalogo_respaldo') and len(getattr(self, 'catalogo_respaldo', [])) > 1:
            self.Cargar_catalogo()
            self.filtros()
            catalogo_a_graficar = self.catalogo
        elif hasattr(self, 'catalogo') and len(self.catalogo) > 1:
            catalogo_a_graficar = self.catalogo
        else:
            catalogo_a_graficar = []

        stats = graficar_periodo_gis(
            widget=self.widget_mapa_gis,
            catalogo=catalogo_a_graficar,
            coordenadas_mapa=coord_zona,
            estilo_circulos=estilo_circulos,
            titulo_mapa=titulo,
            parametros_est=self.parametros,
            mostrar_estaciones=mostrar_est,
        )

        # Si la ventana emergente de ampliación GIS está abierta, sincronizarla en vivo
        if (
            getattr(self, '_ventana_emergente_gis', None) is not None
            and self._ventana_emergente_gis.isVisible()
            and getattr(self, '_widget_mapa_gis_emergente', None) is not None
        ):
            self._ventana_emergente_gis.setWindowTitle(f"Visor Cartográfico GIS Ampliado — {zona_txt} ({periodo_txt})")
            graficar_periodo_gis(
                widget=self._widget_mapa_gis_emergente,
                catalogo=catalogo_a_graficar,
                coordenadas_mapa=coord_zona,
                estilo_circulos=estilo_circulos,
                titulo_mapa=titulo,
                parametros_est=self.parametros,
                mostrar_estaciones=mostrar_est,
            )

        if hasattr(self, 'lbl_resumen_gis') and self.lbl_resumen_gis is not None:
            if stats['total'] > 0:
                txt_res = (
                    f"GIS ({zona_txt}): {stats['total']} sismos (RSA: {stats['rsa']} | Otras: {stats['otras']}) "
                    f"[Sup: {stats['sup']} | Med: {stats['med']} | Prof: {stats['pro']}]"
                )
            else:
                txt_res = f"GIS ({zona_txt}): 0 sismos en la región o filtros seleccionados."
            self.lbl_resumen_gis.setText(txt_res)

    def abrir_ventana_emergente_gis(self):
        """
        Abre el gráfico cartográfico GIS en una pantalla emergente independiente,
        redimensionable y maximizable, provista de barra de herramientas interactiva
        (Zoom, Pan, Vista Original y Guardado) para inspeccionar el mapa en detalle.
        """
        zona_txt = self.cmbx_zona.currentText().strip() if hasattr(self, 'cmbx_zona') else 'Ecuador'
        periodo_txt = getattr(self, 'periodo_reporte', '').strip()
        titulo_vent = f"Visor Cartográfico GIS Ampliado — {zona_txt}" + (f" ({periodo_txt})" if periodo_txt else "")

        if getattr(self, '_ventana_emergente_gis', None) is None:
            dlg = QtWidgets.QDialog(self)
            dlg.setWindowFlags(
                dlg.windowFlags()
                | Qt.WindowMinMaxButtonsHint
                | Qt.WindowMaximizeButtonHint
                | Qt.WindowCloseButtonHint
            )
            dlg.resize(1040, 820)
            layout_dlg = QtWidgets.QVBoxLayout(dlg)
            layout_dlg.setContentsMargins(6, 6, 6, 6)
            layout_dlg.setSpacing(4)

            visor_emergente = widget_grafico_mpl(dlg)
            barra_nav = NavigationToolbar2QT(visor_emergente.canvas, dlg)
            layout_dlg.addWidget(barra_nav)
            layout_dlg.addWidget(visor_emergente, stretch=1)

            self._ventana_emergente_gis = dlg
            self._widget_mapa_gis_emergente = visor_emergente

        self._ventana_emergente_gis.setWindowTitle(titulo_vent)
        self._ventana_emergente_gis.show()
        self._ventana_emergente_gis.raise_()
        self._ventana_emergente_gis.activateWindow()
        self.actualizar_vista_gis()

    def exportar_imagen_gis(self):
        """
        Exporta la vista cartográfica GIS activa a un archivo PNG de alta resolución (300 DPI)
        en el directorio de reportes de la región seleccionada.
        """
        if not hasattr(self, 'widget_mapa_gis') or self.widget_mapa_gis is None:
            return

        try:
            base_rep = str(getattr(self, 'directorio_reporte', '')).rstrip('/\\')
            zona_rep = self.cmbx_zona.currentText().strip() if hasattr(self, 'cmbx_zona') else 'Ecuador'
            if not base_rep:
                base_rep = os.path.join(self.directorio_trabajo, 'reportes')
            directorio_salida = os.path.join(base_rep, zona_rep)
            os.makedirs(directorio_salida, exist_ok=True)

            per_str = getattr(self, 'periodo_reporte', '')
            if per_str.startswith('Período: '):
                nombre_base = per_str[9:].replace('/', '_').strip()
            elif per_str:
                nombre_base = per_str[:10].strip()
            else:
                nombre_base = f"mapa_gis_{zona_rep}"

            ruta_png = os.path.join(directorio_salida, f"{nombre_base}_gis.png")
            self.widget_mapa_gis.figure.savefig(ruta_png, dpi=300, facecolor='#ffffff', bbox_inches='tight')

            msg_ok = f"✓ Mapa GIS exportado exitosamente:\n  • Archivo: {ruta_png}\n  • Resolución: 300 DPI"
            self._registrar_bitacora(msg_ok)
            QMessageBox.information(self, "Exportación Cartográfica Exitosa", msg_ok)
        except Exception as e:
            QMessageBox.critical(self, "Error al Exportar Mapa GIS", f"No se pudo guardar la imagen del mapa:\n{e}")

    def inicializar_variables(self):
        self.eventos=[]
        self.eventos_reporte=[["Nº","Fecha; Hora (UTC)","Evento","Magn.","Prof.(km)","Lat.","Long.","Ubicación"]]
        self.catalogo=[["Id","año","mes","día","hora","min","seg","lat","long","prof","rms","e-x","e-y","e-0","e-z","Mag","Tipo Mag","Fuente","ruta","Ubicación"]]
        self.reporte_total=[["RESPONSABLE","HORA","TOTAL","SISMO","FF","FC","TELESISMOS","Evento_local","INDEFINIDO","Ruido","3 est","4 est","5 est","6 est","7 est","8 est"]]
        self.resumen=[["DIA","SISMO","FF","FC","TELESISMO","Evento Local","INDEFINIDO","Ruido"]]
        # Cargar el primer archivo XML

        ruta_ =  os.path.join(ruta_datos, 'archivo.xml')
        archivo = os.path.abspath(ruta_)

        self.arbol = ET.parse(archivo)
        self.raiz = self.arbol.getroot()

    def Guardar_(self):
        if hasattr(self, 'catalogo_respaldo') and len(getattr(self, 'catalogo_respaldo', [])) > 1:
            self.Cargar_catalogo()
        self.filtros()
        if self.periodo_reporte[0:9]=='Período: ':
            #Por periodo
            nombre_=self.periodo_reporte[9:].replace('/', '_').strip()
        else:
            #semanal
            nombre_=self.periodo_reporte[:10].strip()
        base_rep = str(self.directorio_reporte).rstrip("/\\")
        zona_rep = self.cmbx_zona.currentText().strip()
        directorio_ = f"{base_rep}/{zona_rep}/"
        try:
            Path(directorio_).mkdir(parents=True, exist_ok=True)
        except OSError:
            pass    

        self.archivo_dat_men=directorio_+nombre_+"_rep.csv"
        self.archivo_reportes_total=directorio_+nombre_+"_rep_total.csv"
        self.archivo_cat_men=directorio_+nombre_+"_cat.csv"
        self.archivo_res_men=directorio_+nombre_+"_res.csv"
        self.archivo_responsables_=directorio_+nombre_+"_responsables.csv"#Archivo con el numero total de eventos por responsable
        self.archivo_est_men=directorio_+nombre_+"_est.csv"#Archivo con los resumenes
        self.archivo_1_pdf=directorio_+nombre_+"_pdf1.pdf"
        self.archivo_2_pdf=directorio_+nombre_+"_pdf2.pdf"
        self.archivo_3_pdf=directorio_+nombre_+"_pdf3.pdf"#Archivo de informe en pdf
        self.archivo_pro=directorio_+nombre_+"__rsa_pro.csv"
        self.archivo_med=directorio_+nombre_+"__rsa_med.csv"
        self.archivo_sup=directorio_+nombre_+"__rsa_sup.csv"
        self.archivo_or_pro=directorio_+nombre_+"__otr_pro.csv"
        self.archivo_or_med=directorio_+nombre_+"__otr_med.csv"
        self.archivo_or_sup=directorio_+nombre_+"__otr_sup.csv"
        self.archivo_xml_escritura=directorio_+nombre_+".xml"
        self.archivo_resumen_acelerografos=directorio_+nombre_+"_aceleraciones.csv"
        self.archivo_resumen_acelerografos_base=directorio_+nombre_+"_aceleraciones_base.csv"
        self.archivo_eventos_acelerografos=directorio_+nombre_+"_cat_aceleraciones.csv"
        even_rsa_sup=[["LAT","LONG","Prof.","Mag."]]
        even_rsa_int=[["LAT","LONG","Prof.","Mag."]]
        even_rsa_prof=[["LAT","LONG","Prof.","Mag."]]
        even_otr_sup=[["LAT","LONG","Prof.","Mag."]]
        even_otr_int=[["LAT","LONG","Prof.","Mag."]]
        even_otr_prof=[["LAT","LONG","Prof.","Mag."]]
        #evento_total=[]
        with open(self.archivo_cat_men, 'w', newline='') as archivo_grabar_2:
            escritor_csv_2 = csv.writer(archivo_grabar_2,delimiter=';')
            for i in range(0,len(self.catalogo)):
                if(len(self.catalogo[i])>0):
                    escritor_csv_2.writerow(self.catalogo[i])
        with open(self.archivo_dat_men, 'w', newline='') as archivo_grabar:
                escritor_csv = csv.writer(archivo_grabar,delimiter=';')
                for i in range(0,len(self.eventos_reporte)):
                    escritor_csv.writerow(self.eventos_reporte[i])
        with open(self.archivo_reportes_total, 'w', newline='') as archivo_grabar:
                escritor_csv = csv.writer(archivo_grabar,delimiter=';')
                for i in range(0,len(self.reporte_total)):
                    escritor_csv.writerow(self.reporte_total[i])
        cont_sismos=0
        cont_FF=0
        cont_FC=0
        cont_ind=0
        cont_tel=0
        cont_ev=0
        cont_ruido=0
        for i in range(0,len(self.eventos_reporte)):
            if(self.eventos_reporte[i][2]=="SISMO"):
                cont_sismos=cont_sismos+1
            if(self.eventos_reporte[i][2]=="FF"):
                cont_FF=cont_FF+1
            if(self.eventos_reporte[i][2]=="FC"):
                cont_FC=cont_FC+1
            if(self.eventos_reporte[i][2]=="TELESISMO"):
                cont_tel=cont_tel+1
            if(self.eventos_reporte[i][2]=="Evento_local"or self.eventos_reporte[i][2]=="CONTROL"):
                cont_ev=cont_ev+1
            if(self.eventos_reporte[i][2]=="Ruido"):
                cont_ruido=cont_ruido+1
            if(self.eventos_reporte[i][2]=="INDEFINIDO"):
                cont_ind=cont_ind+1
        # Consulta centralizada al perfil del mapa seleccionado (rsa_pdf_catalogo.py):
        # Si el mapa usa 'matriz_global' (0:Region, 1:Ecuador, 2:Facultad, 3:Fuentes),
        # se inserta la fila de totales globales por tipo de evento en self.resumen[1].
        perfil_mapa = obtener_perfil_mapa(self.cmbx_zona.currentIndex(), es_periodo=True)
        if perfil_mapa['tipo_resumen_estadistico'] == 'matriz_global':
            self.resumen.insert(1,["Total:",cont_sismos,cont_FF,cont_FC,cont_tel,cont_ev,cont_ind,cont_ruido])

##############################################################################################        
        #etapa de clasificacion de self.eventos_reporte

        #Evento total, tupla que contiene tuplas por día con la informacioón de los sismos[latitud, longitud, profundidad, magnitud,red], red:0 RSA, 1 otra red
##############################################################################################
        for i in range(1,len(self.catalogo)):  #-1 decia antes de cambiarlo
            x=float(self.catalogo[i][IDX_LATITUD])#Coordenada en x
            y=float(self.catalogo[i][IDX_LONGITUD])#Coordenada en y
            p=-1*float(self.catalogo[i][IDX_PROFUNDIDAD])#Profundidad
            mag=float(self.catalogo[i][IDX_MAGNITUD])#Magnitud
            #num=self.catalogo[i][18]
            evento_=[x,y,p,mag]

            if(p>-40):
                if(self.catalogo[i][IDX_FUENTE]=="RSA"):
                    even_rsa_sup.append(evento_)
                else:
                    even_otr_sup.append(evento_)
            else:
                if(p>-70):
                    if(self.catalogo[i][IDX_FUENTE]=="RSA"):
                        even_rsa_int.append(evento_)
                    else:
                        even_otr_int.append(evento_)
                else:
                    if(self.catalogo[i][IDX_FUENTE]=="RSA"):
                        even_rsa_prof.append(evento_)
                    else:
                        even_otr_prof.append(evento_)

#################################################################################
#               Reporte en pdf                   
#################################################################################

        if self.ck_box_firma.checkState()==2:
            bandera_firma=True
        else:
            bandera_firma=False
        bandera_relleno = self._obtener_estilo_circulos_mapa()
        modo_actual = self.resolver_modo_desde_controles()

        # Validación preventiva de existencia del archivo cartográfico <Zona>_<detalle>.emf
        zona_nombre = self.cmbx_zona.currentText().strip()
        indice_tipo_mapa = self.cmbx_mapa.currentIndex()
        ruta_emf_esperada = os.path.join(ruta_datos, 'mapas', f"{zona_nombre}_{indice_tipo_mapa}.emf")
        if not os.path.isfile(ruta_emf_esperada):
            # Buscar fallback seguro (_0.emf o _1.emf) para evitar FileNotFoundError en ReportLab
            for idx_alt in (0, 1, 2):
                ruta_alt = os.path.join(ruta_datos, 'mapas', f"{zona_nombre}_{idx_alt}.emf")
                if os.path.isfile(ruta_alt):
                    self._registrar_bitacora(
                        f"Aviso cartográfico: No existe '{zona_nombre}_{indice_tipo_mapa}.emf' en datos/mapas/. "
                        f"Se utilizará automáticamente '{zona_nombre}_{idx_alt}.emf'."
                    )
                    indice_tipo_mapa = idx_alt
                    break

        acelerogramas=reporte_resumen_modos(self.archivo_1_pdf,
                                      self.periodo_reporte,
                                      self.fecha_ini,
                                      self.fecha_fin, 
                                      self.catalogo,
                                      self.resumen,
                                      self.cmbx_zona.currentIndex(),
                                      indice_tipo_mapa,     
                                      modo_actual,
                                      0      ,  
                                      self.directorio_trabajo,
                                      self.arbol,
                                      self.reporte_total,
                                      self.eventos,
                                      bandera_firma,
                                      bandera_relleno)
        registro1=[]
        registro2=[]
        xxx=['Evento','Estación','Canal 0'  ,''        ,''         ,'Canal 1'  ,''        ,''         ,'Canal 2'  ,''         ,'']
        registro1.append(xxx)
        registro2.append(xxx)
        xxx=[''      ,''        ,'Acel. max','Vel. max','Desp. max','Acel. max','Vel. max','Desp. max','Acel. max','Vel. max','Desp. max']
        registro1.append(xxx)
        registro2.append(xxx)
        for evento in acelerogramas:
            linea=[]
            linea.append(evento[0])
            
            for i, estacion in enumerate(evento[1]):
                if i==0:
                    codigo_estacion=self.parametros['CODIGO'][estacion]
                    linea.append(codigo_estacion)
                else:
                    for k in range (1,4):
                        linea.append(str(estacion[k]))
            registro1.append(linea)
            if linea[1]=='CHAB':
                registro2.append(linea)
        escritura_archivo(self.archivo_resumen_acelerografos,registro1)
        escritura_archivo(self.archivo_resumen_acelerografos_base,registro2)
        xxx=['Id','año',	'mes',	'día',	'hora',	'min',	'seg',	'lat',	'long',	'prof',	'Mag',	'Fuente',	'ruta']
        catalogo_acelerometros=[]
        catalogo_acelerometros.append(xxx)
        for evento in registro2:
            for catalogo in self.catalogo:
                if evento[0]==catalogo[18]:
                    xxx=[catalogo[0],catalogo[1],catalogo[2],catalogo[3],catalogo[4],catalogo[5],catalogo[6],catalogo[7],catalogo[8],catalogo[9],catalogo[15]+catalogo[16],catalogo[17],catalogo[18]]
                    catalogo_acelerometros.append(xxx)
        escritura_archivo(self.archivo_eventos_acelerografos,catalogo_acelerometros)
            

        if perfil_mapa['tipo_resumen_estadistico'] == 'matriz_global':
    
#################################################################################
#               Escritura del archivo resumen                    
#################################################################################
            with open(self.archivo_res_men, 'w', newline='') as archivo_grabar:
                escritor_csv = csv.writer(archivo_grabar,delimiter=';')
                for i in range(0,len(self.resumen)):
                    if(i>1):
                        self.resumen[i].insert(0,i-1)
                    escritor_csv.writerow(self.resumen[i])

#################################################################################
#               Escritura del archivo eventos RSA superficial                    
#################################################################################                 

            with open(self.archivo_sup, 'w', newline='') as archivo_grabar:#archivo_pro,archivo_med,archivo_sup,archivo_or_pro,archivo_or_med,archivo_or_sup
                escritor_csv = csv.writer(archivo_grabar,delimiter=',')
                for i in range(0,len(even_rsa_sup)):
                    escritor_csv.writerow(even_rsa_sup[i])

#################################################################################
#               Escritura del archivo eventos RSA intermedios                    
#################################################################################

            with open(self.archivo_med, 'w', newline='') as archivo_grabar:#archivo_pro,archivo_med,archivo_sup,archivo_or_pro,archivo_or_med,archivo_or_sup
                escritor_csv = csv.writer(archivo_grabar,delimiter=',')
                for i in range(0,len(even_rsa_int)):
                    escritor_csv.writerow(even_rsa_int[i])         

#################################################################################
#               Escritura del archivo eventos RSA profundos                    
#################################################################################
                    
            with open(self.archivo_pro, 'w', newline='') as archivo_grabar:#archivo_pro,archivo_med,archivo_sup,archivo_or_pro,archivo_or_med,archivo_or_sup
                escritor_csv = csv.writer(archivo_grabar,delimiter=',')
                for i in range(0,len(even_rsa_prof)):
                    escritor_csv.writerow(even_rsa_prof[i])         

#################################################################################
#               Escritura del archivo eventos otras redes superficial                    
#################################################################################

            with open(self.archivo_or_sup, 'w', newline='') as archivo_grabar:#archivo_pro,archivo_med,archivo_sup,archivo_or_pro,archivo_or_med,archivo_or_sup
                escritor_csv = csv.writer(archivo_grabar,delimiter=',')
                for i in range(0,len(even_otr_sup)):
                    escritor_csv.writerow(even_otr_sup[i])

#################################################################################
#               Escritura del archivo eventos otras redes intermedio                    
#################################################################################

            with open(self.archivo_or_med, 'w', newline='') as archivo_grabar:#archivo_pro,archivo_med,archivo_sup,archivo_or_pro,archivo_or_med,archivo_or_sup
                escritor_csv = csv.writer(archivo_grabar,delimiter=',')
                for i in range(0,len(even_otr_int)):
                    escritor_csv.writerow(even_otr_int[i])         

#################################################################################
#               Escritura del archivo eventos otras redes profundo                    
#################################################################################
                    
            with open(self.archivo_or_pro, 'w', newline='') as archivo_grabar:#archivo_pro,archivo_med,archivo_sup,archivo_or_pro,archivo_or_med,archivo_or_sup
                escritor_csv = csv.writer(archivo_grabar,delimiter=',')
                for i in range(0,len(even_otr_prof)):
                    escritor_csv.writerow(even_otr_prof[i])


#################################################################################
#               Escritura del archivo eventos XML                    
#################################################################################


        # Guardar el archivo resultante
        self.nuevo_arbol.write(self.archivo_xml_escritura)

        # Generar automáticamente las capas Shapefile GIS (.shp, .shx, .dbf, .prj, .cpg, .metadata.json, .qmd)
        # junto al archivo <nombre>_cat.csv del reporte
        detalle_shape = self._generar_shapes_reporte(self.archivo_cat_men)

        self._registrar_bitacora(
            f"✓ Informe guardado exitosamente en:\n  {directorio_}\n"
            f"  • PDF: {os.path.basename(self.archivo_1_pdf)}\n"
            f"  • Catálogo filtrado: {max(0, len(self.catalogo) - 1)} sismos | XML: {os.path.basename(self.archivo_xml_escritura)}"
            + (f"\n  • {detalle_shape}" if detalle_shape else "")
        )
        QMessageBox.information(self,self.tr("Aviso"),self.tr("¡Archivo Guardado"))  
        self.inicializar_variables()
        self.Btn_guardar.setEnabled(False)

    def _generar_shapes_reporte(self, ruta_cat_csv: str) -> str:
        """
        Genera el set completo de archivos Shapefile GIS (EPSG:32717 UTM 17S:
        .shp, .shx, .dbf, .prj, .cpg, .metadata.json, .qmd) a partir del catálogo
        `*_cat.csv` recién guardado en el reporte mensual / de período.
        """
        if generar_shapefile is None or metadatos_sugeridos is None or leer_csv_shape is None:
            return ""
        if not ruta_cat_csv or not os.path.isfile(ruta_cat_csv):
            return ""
        try:
            ruta_path = Path(ruta_cat_csv)
            df_cat = leer_csv_shape(ruta_path)
            metadatos = metadatos_sugeridos(df_cat, ruta_path.stem)
            cantidad, archivos = generar_shapefile(ruta_path, metadatos)
            return f"Shapes GIS generados ({cantidad} eventos RSA, EPSG:32717): {ruta_path.stem}.shp (+6 archivos)"
        except ValueError as e_val:
            # Ejemplo: cuando el catálogo filtrado no contiene eventos con Fuente == 'RSA'
            print(f"Aviso omitiendo generación de Shapefile en {ruta_cat_csv}: {e_val}")
            return f"Shapes GIS omitidos ({e_val})"
        except Exception as e:
            print(f"Error generando Shapefile en {ruta_cat_csv}: {e}")
            return f"Aviso Shapes GIS: {e}"

    # =========================================================================
    # MÉTODOS DE COORDINACIÓN VISUAL DE ZONAS, RADIOBUTTONS Y BITÁCORA
    # =========================================================================
    def _registrar_bitacora(self, mensaje: str):
        """Muestra el estado actual del catálogo, filtros y archivos generados en el cuadro textEdit."""
        if hasattr(self, 'textEdit') and self.textEdit is not None:
            self.textEdit.setPlainText(mensaje)

    def _actualizar_controles_periodo(self, *_args):
        """
        Habilita únicamente el selector de fecha/unidad correspondiente al RadioButton
        activo en la Zona 1 (Año, Mes, Semana o Rango de Fechas) para evitar ambigüedad.
        """
        es_anio = getattr(self, 'rb_anio', None) is not None and self.rb_anio.isChecked()
        es_mes = getattr(self, 'rb_mes', None) is not None and self.rb_mes.isChecked()
        es_semana = getattr(self, 'rb_semana', None) is not None and self.rb_semana.isChecked()
        es_periodo = getattr(self, 'rb_periodo', None) is not None and self.rb_periodo.isChecked()

        if hasattr(self, 'comboBox_anio'):
            self.comboBox_anio.setEnabled(es_anio or es_mes or es_semana)
        if hasattr(self, 'comboBox_mes'):
            self.comboBox_mes.setEnabled(es_mes)
        if hasattr(self, 'comboBox_semana'):
            self.comboBox_semana.setEnabled(es_semana)
        if hasattr(self, 'dateEdit_ini'):
            self.dateEdit_ini.setEnabled(es_periodo)
        if hasattr(self, 'dateEdit_fin'):
            self.dateEdit_fin.setEnabled(es_periodo)

    def _actualizar_estado_visual_filtros(self):
        """
        Sincroniza la habilitación visual de los sub-grupos de filtros (Profundidad,
        Magnitud y N° de Estaciones) según la casilla maestra `ck_box_filtro` y los
        RadioButtons internos, y actualiza el resumen de impresión en la Zona 4.
        """
        filtro_activo = bool(self.ck_box_filtro.isChecked()) if hasattr(self, 'ck_box_filtro') else True

        for nombre_grp in ('grupo_filtro_prof', 'grupo_filtro_mag', 'grupo_filtro_nest'):
            grp = getattr(self, nombre_grp, None)
            if grp is not None:
                grp.setEnabled(filtro_activo)

        if filtro_activo:
            por_estratos = getattr(self, 'rb_prof_estratos', None) is not None and self.rb_prof_estratos.isChecked()
            for nom_ck in ('ck_prof_sup', 'ck_prof_med', 'ck_prof_pro'):
                ck = getattr(self, nom_ck, None)
                if ck is not None:
                    ck.setEnabled(por_estratos)
            for nom_sp in ('spin_prof_min', 'spin_prof_max'):
                sp = getattr(self, nom_sp, None)
                if sp is not None:
                    sp.setEnabled(not por_estratos)

            por_mag_rango = getattr(self, 'rb_mag_rango', None) is not None and self.rb_mag_rango.isChecked()
            if hasattr(self, 'cmbx_magnitud'):
                self.cmbx_magnitud.setEnabled(not por_mag_rango)
            for nom_sp_m in ('spin_mag_min', 'spin_mag_max'):
                spm = getattr(self, nom_sp_m, None)
                if spm is not None:
                    spm.setEnabled(por_mag_rango)

        # Evaluar las 3 posibilidades excluyentes: Círculos rellenos, Círculos sin relleno y Círculos concéntricos
        estilo_circulos = self._obtener_estilo_circulos_mapa()
        usar_concentricos = (estilo_circulos == 2)

        # Al escoger Círculos concéntricos es solo el mapa principal (no requiere detalle ni firma)
        if hasattr(self, 'ck_box_reporte') and self.ck_box_reporte is not None:
            self.ck_box_reporte.setEnabled(not usar_concentricos)
        if hasattr(self, 'ck_box_firma') and self.ck_box_firma is not None:
            self.ck_box_firma.setEnabled(not usar_concentricos)

        # Sincronizar controles ocultos de retrocompatibilidad
        if hasattr(self, 'ck_box_concentricos') and self.ck_box_concentricos is not None:
            self.ck_box_concentricos.blockSignals(True)
            self.ck_box_concentricos.setChecked(usar_concentricos)
            self.ck_box_concentricos.blockSignals(False)
        if hasattr(self, 'ck_box_relleno') and self.ck_box_relleno is not None:
            self.ck_box_relleno.blockSignals(True)
            self.ck_box_relleno.setChecked(estilo_circulos is True)
            self.ck_box_relleno.blockSignals(False)

        # Actualizar etiqueta de diagnóstico de impresión PDF en Zona 4
        if hasattr(self, 'lbl_resumen_impresion') and self.lbl_resumen_impresion is not None:
            modo_num = self.resolver_modo_desde_controles()
            zona_txt = self.cmbx_zona.currentText().strip() if hasattr(self, 'cmbx_zona') else 'Ecuador'
            if usar_concentricos:
                relleno_txt = "Círculos concéntricos (Solo mapa principal)"
            elif estilo_circulos:
                relleno_txt = "Círculos rellenos"
            else:
                relleno_txt = "Círculos sin relleno"
            nombres_modo = {
                0: "M0 — Solo Mapa Principal",
                3: "M3 — Boletín Oficial Detallado RSA",
                4: "M4 — Boletín Oficial Resumen RSA",
                5: "M5 — Boletín Institucional Facultad",
                6: f"M6 — Informe Institucional Detallado ({zona_txt})",
                7: f"M7 — Informe Institucional Resumen ({zona_txt})",
            }
            desc_modo = nombres_modo.get(modo_num, f"M{modo_num}")
            modo_red_idx = self.cmbx_filtro_red.currentIndex() if hasattr(self, 'cmbx_filtro_red') else 0
            nombres_red = {0: "Solo RSA", 1: "Todas las redes", 2: "Solo Otras redes"}
            txt_red = nombres_red.get(modo_red_idx, "Solo RSA")
            self.lbl_resumen_impresion.setText(f"Modo PDF: {desc_modo}  |  {relleno_txt}  |  Red: {txt_red}")

    def _al_cambiar_zona_mapa(self, *_args):
        """
        Cuando el usuario cambia la REGION (`cmbx_zona`), si selecciona 'Fuentes'
        activa automáticamente la opción `rb_circulos_concentricos` (solo mapa principal),
        y al salir de 'Fuentes' vuelve a `rb_circulos_rellenos`, permitiendo elegir
        cualquiera de las 3 posibilidades en cualquier región.
        """
        zona_nueva = self.cmbx_zona.currentText().strip() if hasattr(self, 'cmbx_zona') else ''
        zona_ant = getattr(self, '_zona_previa', '')
        self._zona_previa = zona_nueva
        if hasattr(self, 'rb_circulos_concentricos') and hasattr(self, 'rb_circulos_rellenos'):
            self.rb_circulos_concentricos.blockSignals(True)
            self.rb_circulos_rellenos.blockSignals(True)
            if zona_nueva.lower() == 'fuentes':
                self.rb_circulos_concentricos.setChecked(True)
            elif zona_ant.lower() == 'fuentes':
                self.rb_circulos_rellenos.setChecked(True)
            self.rb_circulos_concentricos.blockSignals(False)
            self.rb_circulos_rellenos.blockSignals(False)
        self._al_cambiar_controles_filtro()

    def _al_cambiar_controles_filtro(self, *_args):
        """
        Se dispara cuando el usuario modifica la Región, Capa de Mapa, Profundidad,
        Magnitud, N° de Estaciones, Red u opciones de impresión. Restaura el catálogo
        respaldado en memoria para permitir guardar múltiples reportes consecutivos
        y actualiza en tiempo real la vista cartográfica GIS.
        """
        self._actualizar_estado_visual_filtros()
        if hasattr(self, 'catalogo_respaldo') and len(getattr(self, 'catalogo_respaldo', [])) > 1:
            self.Cargar_catalogo()
            total_base = max(0, len(self.catalogo_respaldo) - 1)
            zona_txt = self.cmbx_zona.currentText().strip()
            dest_txt = self._ruta_destino_actual()
            modo_red_idx = self.cmbx_filtro_red.currentIndex() if hasattr(self, 'cmbx_filtro_red') else 0
            nombres_red = {0: "Solo RSA", 1: "Todas las redes", 2: "Solo Otras redes"}
            txt_red = nombres_red.get(modo_red_idx, "Solo RSA")
            self._registrar_bitacora(
                f"Período activo: {getattr(self, 'periodo_reporte', '')}\n"
                f"Sismos totales en respaldo: {total_base}  |  Región: {zona_txt}  |  Filtro Red: {txt_red}\n"
                f"Carpeta destino de guardado: {dest_txt}"
            )
        self.actualizar_vista_gis()

    def _ruta_destino_actual(self) -> str:
        """Devuelve la ruta de carpeta donde se guardará el reporte según el período y región activos."""
        base_rep = str(getattr(self, 'directorio_reporte', '')).rstrip('/\\')
        zona_txt = self.cmbx_zona.currentText().strip() if hasattr(self, 'cmbx_zona') else 'Ecuador'
        return f"{base_rep}/{zona_txt}/" if base_rep else ""

    def _obtener_tipo_periodo_activo(self):
        """
        Retorna el código de unidad de período seleccionado en la Zona 1:
        0 = Año, 1 = Mes, 2 = Semana ISO.
        Cuando está activo 'rb_periodo' (Rango de Fechas), retorna None para que
        `obtener_datos_reporte()` reconozca automáticamente si el rango seleccionado
        corresponde a un Año completo (0), Mes completo (1), Semana ISO completa (2)
        o Rango de Fechas arbitrario (3).
        """
        if hasattr(self, 'rb_anio') and self.rb_anio.isChecked():
            return 0
        if hasattr(self, 'rb_mes') and self.rb_mes.isChecked():
            return 1
        if hasattr(self, 'rb_semana') and self.rb_semana.isChecked():
            return 2
        return None

    def _obtener_rango_fechas_seleccionado(self):
        """
        Determina (fecha_ini, fecha_fin) según el RadioButton seleccionado en la Zona 1:
        Año entero, Mes del año, Semana ISO o Rango de Fechas (Inicio - Fin).
        """
        if hasattr(self, 'rb_anio') and self.rb_anio.isChecked():
            anio = int(self.comboBox_anio.currentText())
            return datetime(anio, 1, 1), datetime(anio, 12, 31)
        if hasattr(self, 'rb_mes') and self.rb_mes.isChecked():
            anio = int(self.comboBox_anio.currentText())
            mes = self.comboBox_mes.currentIndex() + 1
            return datetime(anio, mes, 1), datetime(anio, mes, calendar.monthrange(anio, mes)[1])
        if hasattr(self, 'rb_semana') and self.rb_semana.isChecked():
            anio = int(self.comboBox_anio.currentText())
            semana = int(self.comboBox_semana.currentText())
            f_ini = datetime.strptime(f'{anio}-W{semana}-1', '%G-W%V-%u')
            return f_ini, f_ini + timedelta(days=6)

        # Por defecto o cuando rb_periodo está seleccionado: Rango de fechas dateEdit_ini .. dateEdit_fin
        f_ini = datetime.combine(self.dateEdit_ini.date().toPyDate(), time(0, 0, 0))
        f_fin = datetime.combine(self.dateEdit_fin.date().toPyDate(), time(0, 0, 0))
        return f_ini, f_fin

    def cargar_periodo_unificado(self):
        """
        Punto de entrada único del botón 'Cargar Período Seleccionado' en la Zona 1:
          - Determina el período según el RadioButton activo (Año, Mes, Semana o Rango de Fechas).
          - Ejecuta la consolidación según la fuente elegida:
              * 'rb_fuente_diaria': Lee día por día las carpetas diarias (recopilacion).
              * 'rb_fuente_catalogo': Usa los reportes existentes (_cat.csv anuales/diarios).
        """
        usar_catalogo_existente = (
            hasattr(self, 'rb_fuente_catalogo') and self.rb_fuente_catalogo.isChecked()
        )
        f_ini, f_fin = self._obtener_rango_fechas_seleccionado()
        if f_ini > f_fin:
            QMessageBox.warning(
                self,
                "Rango de fechas inválido",
                "La fecha de INICIO no puede ser posterior a la fecha de FIN."
            )
            return

        # Sincronizar los dateEdit visuales con el rango efectivamente calculado
        self.dateEdit_ini.setDate(QDate(f_ini.year, f_ini.month, f_ini.day))
        self.dateEdit_fin.setDate(QDate(f_fin.year, f_fin.month, f_fin.day))

        if usar_catalogo_existente:
            self.ck_box_historico.setChecked(True)
            self.dateEdit_ini_cat.setDate(QDate(f_ini.year, f_ini.month, f_ini.day))
            self.dateEdit_fin_cat.setDate(QDate(f_fin.year, f_fin.month, f_fin.day))
            self.acumular_solo_catalogo(fecha_ini_explicita=f_ini, fecha_fin_explicita=f_fin)
        else:
            if hasattr(self, 'rb_anio') and self.rb_anio.isChecked():
                self.anio_()
            elif hasattr(self, 'rb_mes') and self.rb_mes.isChecked():
                self.mes_()
            elif hasattr(self, 'rb_semana') and self.rb_semana.isChecked():
                self.semana_()
            else:
                self.periodo()

    def anio_(self):
        self.inicializar_variables()
        anio=int(self.comboBox_anio.currentText())
        self.fecha_ini=datetime(anio,1,1)
        self.fecha_fin=datetime(anio,12,31)
        self.periodo_reporte, self.directorio_reporte,self.archivo_reporte=obtener_datos_reporte(
            self.fecha_ini, self.fecha_fin, self.directorio_trabajo, self.cmbx_zona.currentText(), tipo_forzado=0
        )
        self.recopilacion(self.fecha_ini,self.fecha_fin)
        self.Btn_guardar.setEnabled(True)
        dest_txt = self._ruta_destino_actual()
        self._registrar_bitacora(
            f"✓ Año {anio} cargado día por día ({self.periodo_reporte}).\n"
            f"  • Sismos en catálogo: {max(0, len(self.catalogo) - 1)}  |  Eventos totales: {len(self.eventos)}\n"
            f"  • Destino de guardado: {dest_txt}"
        )

    def mes_(self):
        self.inicializar_variables()
        anio=int(self.comboBox_anio.currentText())
        mes=self.comboBox_mes.currentIndex()+1
        self.fecha_ini=datetime(anio,mes,1)
        self.fecha_fin=datetime(anio,mes,calendar.monthrange(anio, mes)[1])
        
        self.periodo_reporte, self.directorio_reporte,self.archivo_reporte=obtener_datos_reporte(
            self.fecha_ini, self.fecha_fin, self.directorio_trabajo, self.cmbx_zona.currentText(), tipo_forzado=1
        )
        self.recopilacion(self.fecha_ini,self.fecha_fin)
        self.Btn_guardar.setEnabled(True)
        dest_txt = self._ruta_destino_actual()
        self._registrar_bitacora(
            f"✓ Mes cargado día por día ({self.periodo_reporte}).\n"
            f"  • Sismos en catálogo: {max(0, len(self.catalogo) - 1)}  |  Eventos totales: {len(self.eventos)}\n"
            f"  • Destino de guardado: {dest_txt}"
        )

    def semana_(self):
        self.inicializar_variables()
        anio=int(self.comboBox_anio.currentText())
        semana=int(self.comboBox_semana.currentText())
        self.fecha_ini = datetime.strptime(f'{anio}-W{semana}-1', '%G-W%V-%u')#.replace(hour=0, minute=0, second=0)
        self.fecha_fin = self.fecha_ini + timedelta(days=6)
        self.periodo_reporte, self.directorio_reporte,self.archivo_reporte=obtener_datos_reporte(
            self.fecha_ini, self.fecha_fin, self.directorio_trabajo, self.cmbx_zona.currentText(), tipo_forzado=2
        )
        self.recopilacion(self.fecha_ini,self.fecha_fin)
        self.Btn_guardar.setEnabled(True)
        dest_txt = self._ruta_destino_actual()
        self._registrar_bitacora(
            f"✓ Semana ISO {semana} del {anio} cargada día por día ({self.periodo_reporte}).\n"
            f"  • Sismos en catálogo: {max(0, len(self.catalogo) - 1)}  |  Eventos totales: {len(self.eventos)}\n"
            f"  • Destino de guardado: {dest_txt}"
        )

    def periodo(self):
        self.inicializar_variables()
        self.fecha_ini=self.dateEdit_ini.date().toPyDate() #Transforma el QdataEdit en formato date de python
        self.fecha_ini=datetime.combine(self.fecha_ini, time(0,0,0))#Transforma los datos tipo date a tipo datetime
        self.fecha_fin=self.dateEdit_fin.date().toPyDate()
        self.fecha_fin=datetime.combine(self.fecha_fin, time(0,0,0))#Transforma los datos tipo date a tipo datetime
        self.periodo_reporte, self.directorio_reporte,self.archivo_reporte=obtener_datos_reporte(
            self.fecha_ini, self.fecha_fin, self.directorio_trabajo, self.cmbx_zona.currentText(),
            tipo_forzado=self._obtener_tipo_periodo_activo()
        )
        self.recopilacion(self.fecha_ini,self.fecha_fin)
        self.Btn_guardar.setEnabled(True)
        dest_txt = self._ruta_destino_actual()
        self._registrar_bitacora(
            f"✓ Período cargado día por día ({self.periodo_reporte}).\n"
            f"  • Sismos en catálogo: {max(0, len(self.catalogo) - 1)}  |  Eventos totales: {len(self.eventos)}\n"
            f"  • Destino de guardado: {dest_txt}"
        )

    def estaciones(self):
        print('¡¡Recopilando informacion!!')
        self.inicializar_variables()
        f_ini_sel, f_fin_sel = self._obtener_rango_fechas_seleccionado()
        self.fecha_ini = f_ini_sel
        self.fecha_fin = f_fin_sel
        self.periodo_reporte, self.directorio_reporte,self.archivo_reporte=obtener_datos_reporte(
            self.fecha_ini, self.fecha_fin, self.directorio_trabajo, self.cmbx_zona.currentText(),
            tipo_forzado=self._obtener_tipo_periodo_activo()
        )
        self.recopilacion(self.fecha_ini,self.fecha_fin)
        eventos_escogidos=[]
        for eventos in self.eventos:
            
            #archivo=eventos[1][:6]+eventos[1][7:-4]
            #fecha_hora = obtencion_hora(archivo)
            #fecha_formateada = fecha_hora.strftime("%d/%m/%Y %H:%M:%S")
            aux=[]
            bandera_reporte=0
            if self.Cmb_bx_tipo_evento.currentText()=='TODOS':
                bandera_reporte=1
            else:
                if eventos[2]==self.Cmb_bx_tipo_evento.currentText():
                    print("Evento:",eventos[1],':',eventos[2])
                    aux.append(eventos[1])
                    bandera_reporte=1
            if  bandera_reporte:
                estacion_=self.Cmb_bx_estacion.currentText()
                indice_=self.parametros['NOMBRE'].index(estacion_)
                nombre_canal=self.parametros['CODIGO'][indice_]
                for i in range(0,len(self.catalogo)):
                    if eventos[1]==self.catalogo[i][IDX_EVENTO] :
                        directorio=obtener_directorios(eventos[1])['Directorio_eventos']
                        nombre_mseed=self.directorio_trabajo+directorio+'/'+nombre_canal+'_20'+eventos[1][:-3]+'mseed'
                        if len(eventos[indice_+3])<6:
                            bandera=0
                        else:
                            if eventos[indice_+3][5]=='1':
                                bandera=1
                            else:
                                bandera=0
                        if os.path.exists(nombre_mseed) and bandera:
                            aux.append(eventos[1])
                            aux.append(self.catalogo[i][IDX_LATITUD])
                            aux.append(self.catalogo[i][IDX_LONGITUD])
                            aux.append(self.catalogo[i][IDX_MAGNITUD])
                            aux.append(self.catalogo[i][IDX_FUENTE])
                            aux.append(self.catalogo[i][IDX_LUGAR])
                            st = read(nombre_mseed)
                            factor=float(self.parametros['FACTOR_MUL'][indice_])
                            canales=len(st)
                            for j in range(0,canales):
                                seniales=correccion(st[j],factor)
                                maximo=max(abs(max(seniales[0])),abs(min(seniales[0])))
                                aux.append(str(maximo))
                            #break
                        else:
                            print('No existe o no marcado')
            if aux!=[]:
                eventos_escogidos.append(aux)

                          
        directorio_=self.directorio_reporte+"/otros/"
        try:
            path = Path(directorio_)
            path.mkdir(parents=True)
        except FileExistsError:
            pass    
        aux_nombre=self.nombre_estaciones_habilitadas[self.Cmb_bx_estacion.currentIndex()]
        nombre_=directorio_+aux_nombre+'_'+self.Cmb_bx_tipo_evento.currentText()+'_rep.csv'
        escritura_archivo(nombre_,eventos_escogidos)
        print('Guardando en   ',nombre_)
        print('¡¡Terminado!!')
        self._registrar_bitacora(
            f"✓ Reporte de amplitudes por estación exportado:\n"
            f"  • Estación: {self.Cmb_bx_estacion.currentText()} ({aux_nombre}) | Tipo: {self.Cmb_bx_tipo_evento.currentText()}\n"
            f"  • Registros encontrados: {len(eventos_escogidos)}\n"
            f"  • Archivo: {nombre_}"
        )



    def recopilacion(self,fecha_inicio,fecha_fin):
#####################################################################################################################################################################################################        
#Carga los datos de los archivos diarios de catálogo (AAMMddhhmmss_cat.csv), datos(AAMMddhhmmss_dat.csv) y resumen(AAMMddhhmmss_res.csv)
# las tuplas self.catalogo, self.eventos_reporte y self.resumen tienen cabeceras que indican el tipo de variable, self.resumen tine una cabecera adicional correspondiente a la sumatoria de las variables.
#
###################################   
#self.catalogo   datos a partir de la posición 1
# 0  1   2   3    4   5   6   7    8   9   10   11 12  13  14  15     16      17    18     19    
#Id;año;mes;día;hora;min;seg;lat;long;prof;rms;e-x;e-y;e-0;e-z;Mag;Tipo Mag;Fuente;ruta;Ubicación
###################################
#self.eventos_reporte    datos a partir de la posición 1
# 0    1       2          3      4       5      6    7       8   
#Nº;"Fecha; Hora (UTC)";Evento;Magn.;Prof.(km);Lat.;Long.;Ubicación
###################################
#self.resumen    datos a partir de la posición 2
#  0     1   2  3     4          5           6        7  
# DIA;SISMO;FF;FC;TELESISMO;Evento Local;INDEFINIDO;Ruido
#Total:;     ;  ;  ;         ;            ;          ;     
        fecha=fecha_inicio
        dias_actualizados = 0
        cascadas_totales = set()
        while fecha <= fecha_fin:
            fecha_ = QDate(fecha.year, fecha.month, fecha.day)
            archivo = os.path.join(self.directorio_trabajo, fecha_.toString('yyyyMMdd000000'))
            self.directorios = obtener_directorios(archivo)
            if os.path.exists(self.directorios['Directorio_base']):
                (
                    eventos_reporte,
                    catalogo,
                    eventos,
                    vector,
                    canales_eventos_dia,
                    root_dia,
                    responsable_dia,
                    resumen_dia,
                ) = cargar_dia(self.directorios)

                # Persistencia en disco día por día (sin generar PDF) y actualización en cascada
                try:
                    Guardar_dia(
                        eventos_reporte,
                        catalogo,
                        eventos,
                        root_dia,
                        responsable_dia,
                        resumen_dia,
                        self.directorios,
                    )
                    act_cascada = actualizar_periodos_emitidos_desde_fecha(fecha, self.directorio_trabajo)
                    if act_cascada:
                        cascadas_totales.update(act_cascada)
                    dias_actualizados += 1
                except Exception as err_dia:
                    print(f"Aviso actualizando día {fecha}: {err_dia}")

                self.eventos = self.eventos + eventos
                self.catalogo = self.catalogo + catalogo[1:]
                self.eventos_reporte = self.eventos_reporte + eventos_reporte[1:]
                self.resumen = self.resumen + lectura_resumen(self.directorios['archivo_resumen'])
                self.reporte_total = self.reporte_total + lectura_resumen(self.directorios['archivo_responsables'])
                for child in root_dia:
                    self.raiz.append(child)
            fecha = fecha + timedelta(1)  # Suma a fecha actual 1 día
        self.Respaldar_catalogo()
        if dias_actualizados > 0 and cascadas_totales:
            print(f"✓ Cascada de períodos actualizada para {dias_actualizados} días: {', '.join(sorted(cascadas_totales))}")
        self.actualizar_vista_gis()

    # =========================================================================
    # MOTOR DE FILTRADO SISMOLÓGICO (PROFUNDIDAD, MAGNITUD, N° ESTACIONES Y REGIÓN)
    # =========================================================================
    def _cumple_filtro_profundidad(self, profundidad_km: float) -> bool:
        """
        Evalúa si una profundidad focal (en km, valor absoluto) cumple con la configuración
        activa en la Zona 2:
          - Modo 1 ('rb_prof_rango' activo): Rango numérico exacto [spin_prof_min .. spin_prof_max].
          - Modo 2 ('rb_prof_estratos' activo): Casillas por estrato estándar RSA:
              * Superficial (< 40 km)  -> ck_prof_sup
              * Medio (40 a 70 km)     -> ck_prof_med
              * Profundo (> 70 km)     -> ck_prof_pro
          - Fallback: Si se invoca sin los controles nuevos, usa el combo `cmbx_profundidad`.
        """
        prof = abs(float(profundidad_km))
        if hasattr(self, 'rb_prof_rango') and self.rb_prof_rango.isChecked():
            p_min = float(self.spin_prof_min.value())
            p_max = float(self.spin_prof_max.value())
            if p_min > p_max:
                p_min, p_max = p_max, p_min
            return p_min <= prof <= p_max

        if hasattr(self, 'rb_prof_estratos') and self.rb_prof_estratos.isChecked():
            inc_sup = bool(self.ck_prof_sup.isChecked()) if hasattr(self, 'ck_prof_sup') else True
            inc_med = bool(self.ck_prof_med.isChecked()) if hasattr(self, 'ck_prof_med') else True
            inc_pro = bool(self.ck_prof_pro.isChecked()) if hasattr(self, 'ck_prof_pro') else True
            if prof < 40.0:
                return inc_sup
            elif prof <= 70.0:
                return inc_med
            else:
                return inc_pro

        # Fallback por combo tradicional cmbx_profundidad
        prof_filtro = {
            'Todos': [0.0, 1000.0],
            'Superficiales': [0.0, 40.0],
            'Medios': [40.0, 70.0],
            'Profundos': [70.0, 1000.0],
            'Sup. y Medios': [0.0, 70.0],
            'Medios y prof.': [40.0, 1000.0]
        }
        rango = prof_filtro.get(self.cmbx_profundidad.currentText(), [0.0, 1000.0])
        return rango[0] <= prof <= rango[1]

    def _cumple_filtro_magnitud(self, magnitud_val: float) -> bool:
        """
        Evalúa si una magnitud cumple con la configuración activa en la Zona 2:
          - Modo 1 ('rb_mag_rango' activo): Rango numérico [spin_mag_min .. spin_mag_max].
          - Modo 2 ('rb_mag_todos' activo o por defecto): Evalúa el umbral rápido en `cmbx_magnitud`
            ('todos' acepta cualquier magnitud; un valor numérico exige magnitud >= umbral).
        """
        mag = float(magnitud_val)
        if hasattr(self, 'rb_mag_rango') and self.rb_mag_rango.isChecked():
            m_min = float(self.spin_mag_min.value())
            m_max = float(self.spin_mag_max.value())
            if m_min > m_max:
                m_min, m_max = m_max, m_min
            return m_min <= mag <= m_max

        try:
            umbral = float(self.cmbx_magnitud.currentText())
            return mag >= umbral
        except ValueError:
            return True

    def _cumple_filtro_red(self, fila_cat) -> bool:
        """
        Evalúa si un registro de catálogo cumple con la opción activa en `cmbx_filtro_red`:
          - Índice 0 ('Solo Red Sísmica (RSA)' - opción por defecto y habitual en reportes):
              Acepta únicamente sismos de la red RSA (Fuente == 'RSA' o Id con sufijo '00').
          - Índice 1 ('Todas las redes'):
              Acepta tanto sismos de la RSA como de otras redes (IGEPN, USGS, etc.).
          - Índice 2 ('Solo Otras redes'):
              Acepta exclusivamente sismos de otras redes (Fuente != 'RSA' y sin sufijo '00').
        """
        if not fila_cat or len(fila_cat) <= IDX_FUENTE:
            return True
        fuente = str(fila_cat[IDX_FUENTE]).strip().upper()
        id_ev = str(fila_cat[IDX_INDICE]).strip()
        es_rsa = (fuente == 'RSA' or (len(id_ev) >= 2 and id_ev.endswith('00')))

        modo_red = self.cmbx_filtro_red.currentIndex() if hasattr(self, 'cmbx_filtro_red') else 0
        if modo_red == 0:     # Solo RSA
            return es_rsa
        elif modo_red == 2:   # Solo Otras redes
            return not es_rsa
        return True           # Todas las redes

    def _cumple_filtro_red_xml(self, es_rsa_xml: bool) -> bool:
        """Aplica el mismo criterio de red al filtrado de nodos en el árbol XML."""
        modo_red = self.cmbx_filtro_red.currentIndex() if hasattr(self, 'cmbx_filtro_red') else 0
        if modo_red == 0:
            return es_rsa_xml
        elif modo_red == 2:
            return not es_rsa_xml
        return True

    def _construir_mapa_conteo_estaciones(self) -> dict:
        """
        Construye un diccionario {clave_evento: numero_estaciones} a partir del árbol XML
        (`self.raiz`) y de la matriz diaria (`self.eventos`) para clasificar con precisión
        qué sismos cumplen el mínimo de estaciones requerido para mecanismos focales.
        """
        conteo = {}
        if hasattr(self, 'raiz') and self.raiz is not None:
            for ev_xml in self.raiz.findall('.//Evento'):
                n_reg = len(list(ev_xml.iterfind("estaciones/estacion")))
                id_ev = (ev_xml.findtext('id_evento') or '').strip()
                ruta_ev = (ev_xml.findtext('ruta') or '').strip()
                if id_ev:
                    conteo[id_ev] = max(conteo.get(id_ev, 0), n_reg)
                if ruta_ev:
                    nom_sis = os.path.basename(ruta_ev)
                    conteo[nom_sis] = max(conteo.get(nom_sis, 0), n_reg)
                    conteo[ruta_ev] = max(conteo.get(ruta_ev, 0), n_reg)

        for fila_ev in getattr(self, 'eventos', []):
            if not fila_ev or len(fila_ev) < 4:
                continue
            ev_sis = str(fila_ev[1]).strip()
            n_activas = sum(1 for token in fila_ev[3:] if token and token != '-')
            if ev_sis and ev_sis not in conteo:
                conteo[ev_sis] = n_activas

        return conteo

    def filtros(self):
        """
        Aplica el recorte espacial de la `REGION` seleccionada (`cmbx_zona`) y, cuando la
        casilla `ck_box_filtro` está marcada, filtra tanto `self.catalogo` (Mapa PDF y _cat.csv)
        como `self.nuevo_arbol` (.xml) por:
          1. Profundidad (por estratos Superficial/Medio/Profundo o por rango numérico en km).
          2. Magnitud (por umbral rápido o por rango numérico Mín–Máx en Md).
          3. Número mínimo de estaciones caracterizadas (`cmbx_n_estaciones` para mecanismos focales).
        """
        self.nuevo_arbol = ET.ElementTree(ET.Element('sismo'))
        aplicar_filtros_sismologicos = (
            bool(self.ck_box_filtro.isChecked()) if hasattr(self, 'ck_box_filtro') else True
        )
        filtrar_nest_en_catalogo = (
            bool(self.ck_nest_catalogo.isChecked()) if hasattr(self, 'ck_nest_catalogo') else True
        )

        coord_ = self.coordenadas[self.cmbx_zona.currentIndex()]
        lat2 = float(coord_[1])
        lat1 = float(coord_[0])
        long2 = float(coord_[3])
        long1 = float(coord_[2])
        estaciones = coord_[5].split()

        try:
            n_est_ = float(self.cmbx_n_estaciones.currentText()) if aplicar_filtros_sismologicos else 0.0
        except ValueError:
            n_est_ = 0.0

        mapa_conteo_est = self._construir_mapa_conteo_estaciones() if n_est_ > 0 else {}

        eventos_filtrados = [self.catalogo[0]]
        n_eventos = len(self.catalogo)

        for i in range(1, n_eventos):
            fila_cat = self.catalogo[i]
            if not fila_cat:
                continue
            try:
                latitud = float(fila_cat[IDX_LATITUD])
                longitud = float(fila_cat[IDX_LONGITUD])
                profundidad = float(fila_cat[IDX_PROFUNDIDAD])
                magnitud = float(fila_cat[IDX_MAGNITUD])
            except (ValueError, IndexError):
                continue

            # Filtro por Red Sísmica / Origen (Solo RSA por defecto vs Todas las redes vs Solo Otras redes)
            if not self._cumple_filtro_red(fila_cat):
                continue

            # Verificar filtros de Profundidad, Magnitud y N° de Estaciones cuando están activos
            if aplicar_filtros_sismologicos:
                if not self._cumple_filtro_profundidad(profundidad):
                    continue
                if not self._cumple_filtro_magnitud(magnitud):
                    continue
                if n_est_ > 0 and filtrar_nest_en_catalogo:
                    id_cat = str(fila_cat[IDX_INDICE]).strip()
                    ruta_cat = str(fila_cat[IDX_EVENTO]).strip()
                    n_est_ev = max(
                        mapa_conteo_est.get(id_cat, 0),
                        mapa_conteo_est.get(ruta_cat, 0),
                        mapa_conteo_est.get(os.path.basename(ruta_cat), 0)
                    )
                    # Si tenemos conteo registrado para ese sismo y es menor a n_est_, se descarta
                    if n_est_ev > 0 and n_est_ev < n_est_:
                        continue

            # Verificar pertenencia al recorte geográfico de la REGION
            if lat1 <= latitud <= lat2 and long1 <= longitud <= long2:
                eventos_filtrados.append(fila_cat)
            else:
                modo_red = self.cmbx_filtro_red.currentIndex() if hasattr(self, 'cmbx_filtro_red') else 0
                fuente_cat = str(fila_cat[IDX_FUENTE]).strip().upper()
                id_cat_ev = str(fila_cat[IDX_INDICE]).strip()
                es_rsa_ev = (fuente_cat == 'RSA' or (len(id_cat_ev) >= 2 and id_cat_ev.endswith('00')))
                if modo_red in (1, 2) and not es_rsa_ev:
                    directorios = obtener_directorios(fila_cat[IDX_EVENTO])
                    for estacion in estaciones:
                        evento_mseed = (
                            self.directorio_trabajo + '/' + directorios['Directorio_eventos'] +
                            '/' + self.parametros['CODIGO'][int(estacion)] + directorios['sufijo_mseed']
                        )
                        print(evento_mseed)
                    eventos_filtrados.append(fila_cat)

        self.catalogo = eventos_filtrados
        numero_dias = self.fecha_fin - self.fecha_ini

        # Si el perfil del mapa seleccionado es 'vector_filtrado' (4:Reportes y >=5:Proyectos/GADs),
        # self.resumen se convierte en un vector diario con el conteo exclusivo de sismos RSA dentro del polígono.
        perfil_mapa = obtener_perfil_mapa(self.cmbx_zona.currentIndex(), es_periodo=True)
        if perfil_mapa['tipo_resumen_estadistico'] == 'vector_filtrado':
            self.resumen = []
            for i in range(0, numero_dias.days + 3):
                self.resumen.append(0)
            for evento in self.catalogo:
                if evento[IDX_INDICE] != 'Id' and evento[IDX_FUENTE] == 'RSA':
                    fecha_it = datetime(
                        int(evento[IDX_INDICE][0:4]),
                        int(evento[IDX_INDICE][4:6]),
                        int(evento[IDX_INDICE][6:8])
                    )
                    contador = fecha_it - self.fecha_ini
                    if 0 <= contador.days + 2 < len(self.resumen):
                        self.resumen[contador.days + 2] = self.resumen[contador.days + 2] + 1

        # Filtrado consistente del árbol XML (Región + Red + Profundidad + Magnitud + N° Mínimo de Estaciones)
        for evento in self.raiz.findall('.//Evento'):
            try:
                longitud = float(evento.find('longitud').text)
                latitud = float(evento.find('latitud').text)
                magnitud = float(evento.find('magnitud').text)
                prof_texto = evento.findtext('profundidad')
                profundidad_xml = float(prof_texto) if prof_texto is not None else 0.0
                id_ev_xml = (evento.findtext('id_evento') or '').strip()
                fuente_xml = (evento.findtext('fuente') or '').strip().upper()
                es_rsa_xml = (fuente_xml == 'RSA' or not fuente_xml or id_ev_xml.endswith('00'))
            except (AttributeError, ValueError, TypeError):
                continue

            if not self._cumple_filtro_red_xml(es_rsa_xml):
                continue

            registros = list(evento.iterfind("estaciones/estacion"))
            numero_registros = len(registros)

            if not (long1 <= longitud <= long2 and lat1 <= latitud <= lat2):
                continue

            if aplicar_filtros_sismologicos:
                if not self._cumple_filtro_profundidad(profundidad_xml):
                    continue
                if not self._cumple_filtro_magnitud(magnitud):
                    continue
                if numero_registros < n_est_:
                    continue

            nuevo_evento = ET.SubElement(self.nuevo_arbol.getroot(), 'Evento')
            for child in evento:
                nuevo_evento.append(copy.deepcopy(child))


    def Cargar_catalogo(self):
        self.catalogo=copy.deepcopy(self.catalogo_respaldo)
        self.eventos_reporte=copy.deepcopy(self.eventos_reporte_respaldo)
        self.resumen=copy.deepcopy(self.resumen_respaldo)
        self.reporte_total=copy.deepcopy(self.reporte_total_respaldo)
        self.arbol=self.arbol_respaldo
        self.Btn_guardar.setEnabled(True)


    def Respaldar_catalogo(self):
        self.catalogo_respaldo= copy.deepcopy(self.catalogo)
        self.eventos_reporte_respaldo=copy.deepcopy(self.eventos_reporte)
        self.resumen_respaldo=copy.deepcopy(self.resumen)
        self.arbol_respaldo=copy.deepcopy(self.arbol)
        self.reporte_total_respaldo=copy.deepcopy(self.reporte_total)


    def cargar_catalogo_guardado(self):
        carpeta = QFileDialog.getExistingDirectory(self, "Selecciona la carpeta del catálogo (debe terminar en 'Ecuador')")
        if not carpeta:
            return

        if Path(carpeta).name != "Ecuador":
            QMessageBox.critical(self, "Carga no permitida", "Solo puedes cargar catálogos desde una carpeta que se llame exactamente 'Ecuador'.")
            return

        try:
            self.directorio_trabajo=extraer_hasta_directorio(carpeta, 'DIA')

            lista_archivos = os.listdir(carpeta)
            base = None

            for archivo in lista_archivos:
                if archivo.endswith("_cat.csv"):
                    base = archivo[:-8]  # Quitar '_cat.csv'
                    break

            if not base:
                QMessageBox.warning(self, "Error", "No se encontró ningún archivo *_cat.csv en la carpeta.")
                return

            # Determinar el rango de fechas según el nombre del archivo
            try:
                if " a " in base:
                    # Formato: 01_01_2001 a 31_12_2024
                    fecha_str_ini, _, fecha_str_fin = base.partition(" a ")
                    self.fecha_ini = datetime.strptime(fecha_str_ini, "%d_%m_%Y")
                    self.fecha_fin = datetime.strptime(fecha_str_fin, "%d_%m_%Y")
                elif base.isdigit() and len(base) == 4:
                    # Formato: 2010
                    anio = int(base)
                    self.fecha_ini = datetime(anio, 1, 1)
                    self.fecha_fin = datetime(anio, 12, 31)
                else:
                    # Intentar parsear formato tipo "Enero del 2025"
                    meses = {
                        "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
                        "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
                        "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12
                    }
                    base_minus = base.lower()
                    for mes_nombre, mes_num in meses.items():
                        if mes_nombre in base_minus:
                            anio = int(''.join(filter(str.isdigit, base_minus)))
                            self.fecha_ini = datetime(anio, mes_num, 1)
                            ultimo_dia = calendar.monthrange(anio, mes_num)[1]
                            self.fecha_fin = datetime(anio, mes_num, ultimo_dia)
                            break
                    else:
                        raise ValueError(f"No se pudo interpretar la fecha desde el nombre del archivo: {base}")
            except Exception as e:
                raise ValueError(f"No se pudieron extraer fechas del nombre base '{base}': {e}")

            # Selección de zona 'Ecuador' en el combo
            index_ecuador = self.cmbx_zona.findText("Ecuador")
            if index_ecuador != -1:
                self.cmbx_zona.setCurrentIndex(index_ecuador)
            else:
                QMessageBox.warning(self, "Aviso", "No se encontró 'Ecuador' en la lista de zonas.")
                return

            self.periodo_reporte, self.directorio_reporte, self.archivo_reporte = obtener_datos_reporte(
                self.fecha_ini, self.fecha_fin, self.directorio_trabajo, "Ecuador"
            )

            # Cargar archivos asociados
            self.catalogo = lectura_archivo(os.path.join(carpeta, base + "_cat.csv"))
            self.eventos_reporte = lectura_archivo(os.path.join(carpeta, base + "_rep.csv"))
            self.resumen = lectura_archivo(os.path.join(carpeta, base + "_res.csv"))
            self.reporte_total = lectura_archivo(os.path.join(carpeta, base + "_rep_total.csv"))
            self.arbol = ET.parse(os.path.join(carpeta, base + ".xml"))
            self.raiz = self.arbol.getroot()
            self.Respaldar_catalogo()
            self.actualizar_vista_gis()
            self.dateEdit_ini.setDate(QDate(self.fecha_ini.year, self.fecha_ini.month, self.fecha_ini.day))
            self.dateEdit_fin.setDate(QDate(self.fecha_fin.year, self.fecha_fin.month, self.fecha_fin.day))
            self.Btn_guardar.setEnabled(True)
            self._registrar_bitacora(
                f"✓ Catálogo cargado directamente desde carpeta 'Ecuador':\n"
                f"  • Período: {self.periodo_reporte}\n"
                f"  • Total de sismos en catálogo: {max(0, len(self.catalogo) - 1)}"
            )
            QMessageBox.information(
                self,
                "Catálogo cargado",
                f"Catálogo cargado correctamente para el periodo:\n{self.periodo_reporte}"
            )

        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar el catálogo:\n{str(e)}")


    def acumular_solo_catalogo(self, fecha_ini_explicita=None, fecha_fin_explicita=None):
        """
        Algoritmo inteligente de consolidación rápida basado en unidades básicas (`_cat.csv`):
          - Descompone el intervalo [fecha_ini, fecha_fin] en la secuencia jerárquica:
                días -> semanas -> meses -> años -> meses -> semanas -> días
            usando `generar_directorios_unidades_basicas(..., verificar_existencia=True, detallar=True)`.
          - Para cada unidad mayor existente en `Ecuador` (Año, Mes o Semana ISO), carga su
            `_cat.csv` y archivos compañeros (`_rep.csv`, `_res.csv`, `_rep_total.csv`, `.xml`)
            en una sola lectura, descendiendo automáticamente a niveles más finos solo cuando
            un bloque consolidado aún no existe en disco.
          - Inicializa formalmente `self.fecha_ini`, `self.fecha_fin`, `self.periodo_reporte`
            y `self.directorio_reporte` para que `Guardar_()` funcione sin errores.
        """
        if fecha_ini_explicita is None and not self.ck_box_historico.isChecked():
            return

        try:
            self.inicializar_variables()
            if fecha_ini_explicita is not None and fecha_fin_explicita is not None:
                fecha_ini_dt = fecha_ini_explicita
                fecha_fin_dt = fecha_fin_explicita
            else:
                f_i = self.dateEdit_ini_cat.date().toPyDate()
                f_f = self.dateEdit_fin_cat.date().toPyDate()
                fecha_ini_dt = datetime.combine(f_i, time(0, 0, 0))
                fecha_fin_dt = datetime.combine(f_f, time(0, 0, 0))

            self.fecha_ini = fecha_ini_dt
            self.fecha_fin = fecha_fin_dt
            self.periodo_reporte, self.directorio_reporte, self.archivo_reporte = obtener_datos_reporte(
                self.fecha_ini, self.fecha_fin, self.directorio_trabajo, self.cmbx_zona.currentText(),
                tipo_forzado=self._obtener_tipo_periodo_activo()
            )

            unidades = generar_directorios_unidades_basicas(
                fecha_ini_dt,
                fecha_fin_dt,
                self.directorio_trabajo,
                verificar_existencia=True,
                detallar=True,
            )

            conteo_unidades = {'PERIODO': 0, 'ANIO': 0, 'MES': 0, 'SEMANA': 0, 'DIA': 0}

            for unidad in unidades:
                tipo_u = unidad['tipo']
                prefijo = unidad['prefijo']
                ruta_cat = f"{prefijo}_cat.csv"

                if not os.path.isfile(ruta_cat):
                    continue

                try:
                    datos = lectura_archivo(ruta_cat)
                    if datos and datos[0][0] == "Id":
                        self.catalogo.extend(datos[1:])
                    elif datos:
                        self.catalogo.extend(datos)

                    if tipo_u in ('PERIODO', 'ANIO', 'MES', 'SEMANA'):
                        ruta_rep = f"{prefijo}_rep.csv"
                        ruta_res = f"{prefijo}_res.csv"
                        ruta_rtot = f"{prefijo}_rep_total.csv"
                        ruta_xml = f"{prefijo}.xml"

                        if os.path.isfile(ruta_rep):
                            d_rep = lectura_archivo(ruta_rep)
                            self.eventos_reporte.extend(
                                d_rep[1:] if d_rep and d_rep[0][0] == "Nº" else (d_rep or [])
                            )
                        if os.path.isfile(ruta_res):
                            d_res = lectura_resumen(ruta_res)
                            for fila_r in (d_res or []):
                                if not fila_r or fila_r[0] in ("DIA", "Total:"):
                                    continue
                                # Normalizar a 7 columnas diarias si el consolidado incluye columna 'DIA' al inicio
                                self.resumen.append(fila_r[-7:] if len(fila_r) >= 8 else fila_r)
                        if os.path.isfile(ruta_rtot):
                            d_rtot = lectura_resumen(ruta_rtot)
                            self.reporte_total.extend(
                                [r for r in (d_rtot or []) if r and r[0] != "RESPONSABLE"]
                            )
                        if os.path.isfile(ruta_xml):
                            raiz_u = ET.parse(ruta_xml).getroot()
                            for child in raiz_u:
                                self.raiz.append(child)

                        conteo_unidades[tipo_u] += 1
                        print(f"✓ Se cargó unidad [{tipo_u}] existente: {ruta_cat}")
                    else:
                        # Unidad DIA individual (AAMMDD000000)
                        ruta_dat = f"{prefijo}_rep.csv"
                        if not os.path.isfile(ruta_dat):
                            ruta_dat = f"{prefijo}_dat.csv"
                        ruta_res = f"{prefijo}_res.csv"
                        carpeta_dia = os.path.dirname(prefijo)
                        stem_dia = os.path.basename(prefijo)
                        pref_fecha_dia = stem_dia[:-6] if stem_dia.endswith("000000") else stem_dia[:6]
                        ruta_resp = os.path.join(carpeta_dia, "reportes", f"{pref_fecha_dia}_resp.csv")
                        if not os.path.isfile(ruta_resp):
                            ruta_resp = f"{prefijo}_responsables.csv"
                        ruta_xml = f"{prefijo}.xml"

                        if os.path.isfile(ruta_dat):
                            d_dat = lectura_archivo(ruta_dat)
                            self.eventos_reporte.extend(d_dat[1:] if d_dat else [])
                        if os.path.isfile(ruta_res):
                            self.resumen.extend(lectura_resumen(ruta_res))
                        if os.path.isfile(ruta_resp):
                            self.reporte_total.extend(lectura_resumen(ruta_resp))
                        if os.path.isfile(ruta_xml):
                            raiz_d = ET.parse(ruta_xml).getroot()
                            for child in raiz_d:
                                self.raiz.append(child)

                        conteo_unidades['DIA'] += 1
                except Exception as e:
                    print(f"Error al leer unidad [{tipo_u}] en {ruta_cat}: {e}")

            self.Respaldar_catalogo()
            self.actualizar_vista_gis()
            self.Btn_guardar.setEnabled(True)
            dest_txt = self._ruta_destino_actual()
            partes_res = []
            if conteo_unidades['PERIODO'] > 0:
                partes_res.append(f"Período emitido: {conteo_unidades['PERIODO']}")
            partes_res.extend([
                f"Años: {conteo_unidades['ANIO']}",
                f"Meses: {conteo_unidades['MES']}",
                f"Semanas: {conteo_unidades['SEMANA']}",
                f"Días: {conteo_unidades['DIA']}",
            ])
            resumen_unidades = " | ".join(partes_res)
            self._registrar_bitacora(
                f"✓ Catálogo consolidado por unidades básicas (_cat.csv):\n"
                f"  • Período: {self.periodo_reporte}\n"
                f"  • Unidades cargadas -> {resumen_unidades}\n"
                f"  • Total de sismos cargados: {max(0, len(self.catalogo) - 1)}\n"
                f"  • Destino de guardado: {dest_txt}"
            )

            QMessageBox.information(
                self,
                "Catálogo acumulado (_cat.csv)",
                f"Se acumularon eventos desde {fecha_ini_dt.strftime('%d/%m/%Y')} hasta {fecha_fin_dt.strftime('%d/%m/%Y')}.\n"
                f"Unidades consolidadas ({resumen_unidades}).\n"
                f"Total de sismos cargados: {max(0, len(self.catalogo) - 1)}"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Ocurrió un error al acumular el catálogo:\n{str(e)}"
            )

    def abrir_ventana_estaciones(self):
        self.ventana_estaciones = VentanaEstaciones(self.parametros)
        self.ventana_estaciones.btn_ejecutar.clicked.connect(self.ejecutar_con_estaciones)
        self.ventana_estaciones.exec_()



    def ejecutar_con_estaciones(self):
        self.estaciones_seleccionadas = self.ventana_estaciones.obtener_estaciones_seleccionadas()
        self.ventana_estaciones.close()

        self.reporte = []

        for evento_catalogo in self.catalogo[1:]:  # Omitimos cabecera
            evento_id = evento_catalogo[IDX_EVENTO]  # Ej: "240505_153312.sis"
            evento_sin_extension = evento_id[:-4]  # "240505_153312"
            evento_sin_guion = evento_sin_extension.replace("_", "")  # "240505153312"

            ruta_evento = os.path.join(self.directorio_trabajo, evento_sin_guion)
            directorios = obtener_directorios(ruta_evento)

            self.eventos = lectura_archivo(directorios['archivo_csv'])
            print(directorios['archivo_csv'])

            for evento in self.eventos[1:]:
                if evento[1] == evento_id:
                    linea_evento = [evento_id]
                    for idx_estacion in self.estaciones_seleccionadas:
                        if evento[idx_estacion + 3] != "-":
                            codigo = self.parametros['CODIGO'][idx_estacion]
                            nombre_mseed = codigo + directorios['sufijo_mseed']
                            linea_evento.append(nombre_mseed)
                    if len(linea_evento) > 1:
                        self.reporte.append(linea_evento)
                    break  # Ya encontramos el evento
                        
        # Mostrar resultado final en consola y en la bitácora de la pantalla
        print("📄 Contenido de self.reporte:")
        lineas_txt = [f"✓ Archivos .mseed encontrados para las {len(self.estaciones_seleccionadas)} estaciones seleccionadas ({len(self.reporte)} eventos):"]
        for linea in self.reporte:
            print(linea)
            lineas_txt.append(f"  • {linea[0]}: {', '.join(linea[1:])}")
        self._registrar_bitacora("\n".join(lineas_txt))




    def Salir_(self):
        print('Saliendo desde boton:')
        self.close()

    def limpiar_estado(self):
        """Limpia figuras, visores, hilos, timers, etc., antes de cerrar."""
        try:
            if hasattr(self, 'canvas') and self.canvas is not None:
                self.canvas.deleteLater()
                self.canvas = None
            if hasattr(self, 'visor') and self.visor is not None:
                self.visor.clf()
                self.visor = None
            if hasattr(self, '_ventana_emergente_gis') and self._ventana_emergente_gis is not None:
                try:
                    self._ventana_emergente_gis.close()
                    self._ventana_emergente_gis.deleteLater()
                    self._ventana_emergente_gis = None
                    self._widget_mapa_gis_emergente = None
                except Exception:
                    pass
            if hasattr(self, 'widget_mapa_gis') and self.widget_mapa_gis is not None:
                try:
                    self.widget_mapa_gis.figure.clf()
                    self.widget_mapa_gis.canvas.deleteLater()
                    self.widget_mapa_gis.deleteLater()
                    self.widget_mapa_gis = None
                except Exception:
                    pass
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
        print("Saliendo de Reporte  - closeEvent ejecutado")
    
        # Limpiar estado antes de emitir señal
        self.limpiar_estado()
        
        # Emitir señal una sola vez
        self.cerrado.emit()
    
        # Aceptar el evento de cierre
        event.accept()
    
        print("closeEvent completado - señal cerrado emitida")




        
