import copy
import csv
import math
import os
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, time, timedelta
from pathlib import Path

from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import QDate, Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication,
    QButtonGroup,
    QFileDialog,
    QHBoxLayout,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT
from shapely.geometry import Point


def extraer_hasta_directorio(ruta_completa, nombre_directorio):
    partes = Path(ruta_completa).parts
    if nombre_directorio in partes:
        indice = partes.index(nombre_directorio)
        ruta_recortada = Path(*partes[: indice + 1])
        return str(ruta_recortada) + "/"
    return ""


ruta_librerias = os.path.dirname(__file__)
ruta_proyecto = extraer_hasta_directorio(ruta_librerias, "procesamiento")
if not ruta_proyecto:
    ruta_proyecto = os.path.abspath(os.path.join(ruta_librerias, "..", ".."))
ruta_librerias = os.path.abspath(os.path.join(ruta_proyecto, "src", "librerias"))
ruta_datos = os.path.abspath(os.path.join(ruta_proyecto, "datos"))

if ruta_librerias not in sys.path:
    sys.path.insert(0, ruta_librerias)

from rsa_io import (
    Guardar_dia,
    escritura_archivo,
    lectura_archivo,
    lectura_resumen,
)
from rsa_utilidades import (
    actualizar_periodos_emitidos_desde_fecha,
    generar_directorios_unidades_basicas,
    obtener_datos_reporte,
)
from metodos_gestion import obtener_directorios
from metodos_gis_rsa import (
    construir_poligono_lugar_geometrico,
    graficar_periodo_gis,
    widget_grafico_mpl,
)
from metodos_rsa import (
    cargar_dia,
    parametros_estaciones,
)
from rsa_pdf_catalogo import (
    MODO_INSTITUCIONAL_DETALLADO,
    MODO_INSTITUCIONAL_RESUMEN,
    MODO_MAPA_ESPECIAL,
    obtener_perfil_mapa,
    reporte_resumen_modos,
)

IDX_INDICE = 0
IDX_ANIO = 1
IDX_MES = 2
IDX_DIA = 3
IDX_HORA = 4
IDX_MINUTO = 5
IDX_SEGUNDO = 6
IDX_LATITUD = 7
IDX_LONGITUD = 8
IDX_PROFUNDIDAD = 9
IDX_RMS = 10
IDX_E_X = 11
IDX_E_Y = 12
IDX_E_0 = 13
IDX_E_Z = 14
IDX_MAGNITUD = 15
IDX_UNIDAD_MAG = 16
IDX_FUENTE = 17
IDX_EVENTO = 18
IDX_LUGAR = 19

archivo_ui = os.path.abspath(
    os.path.join(ruta_proyecto, "src", "ui", "reporte_enjambre.ui")
)
Ui_FormReporteEnjambre, QtBaseClass = uic.loadUiType(archivo_ui)


class Reporte_enjambre(QWidget, Ui_FormReporteEnjambre):
    """
    Subprograma interactivo para delimitación espacial y temporal de enjambres
    sísmicos (por Círculo, Rectángulo o Polígono libre sobre el mapa GIS) y
    generación de boletines en PDF mediante las herramientas de ReportLab.
    """

    cerrado = pyqtSignal()

    def __init__(
        self,
        archivo="",
        directorio_trabajo="G:/Mi unidad/DIA/",
        responsable="RSA",
        horario=0,
        parent=None,
    ):
        super().__init__(parent)
        self.setupUi(self)

        self.archivo = archivo
        self.directorio_trabajo = directorio_trabajo or "G:/Mi unidad/DIA/"
        self.responsable = responsable
        self.horario = horario

        self._sincronizando_fechas = False
        self._modo_dibujo_activo = False
        self._puntos_dibujo_temp = []
        self.vertices_poligono = []
        self._cid_click_gis = None
        self._cid_move_gis = None
        self.sismo_principal_actual = None
        self._id_sismo_principal_forzado = None
        self._actualizando_combo_principal = False

        self.parametros = parametros_estaciones()
        self.inicializar_variables()

        # Cargar lista de mapas base desde datos/mapas/mapas.csv
        ruta_mapas_csv = os.path.abspath(
            os.path.join(ruta_proyecto, "datos", "mapas", "mapas.csv")
        )
        self.coordenadas = []
        nombres_mapas = []
        with open(ruta_mapas_csv, newline="", encoding="utf-8", errors="ignore") as f_map:
            lector = csv.reader(f_map, delimiter=";", quotechar=";")
            for fila in lector:
                if fila and fila[0] != "nombre":
                    nombres_mapas.append(fila[0])
                    self.coordenadas.append(fila[1:7])
        self.cmbx_zona.addItems(nombres_mapas)
        idx_austro = self.cmbx_zona.findText("Austro")
        self.cmbx_zona.setCurrentIndex(idx_austro if idx_austro != -1 else 1)

        self.cmbx_mapa.addItems(
            ("1.Básico", "2.Medio", "3.Físico", "4.Nidos", "5.Fallas", "6.Combinados")
        )
        self.cmbx_magnitud.addItems(
            ("todos", "1.5", "2.0", "2.5", "3.0", "3.5", "4.0", "4.5", "5.0")
        )

        # Grupos de RadioButtons
        self.grupo_rb_fuente = QButtonGroup(self)
        self.grupo_rb_fuente.addButton(self.rb_fuente_catalogo)
        self.grupo_rb_fuente.addButton(self.rb_fuente_diaria)

        self.grupo_rb_simbologia = QButtonGroup(self)
        self.grupo_rb_simbologia.addButton(self.rb_circulos_rellenos)
        self.grupo_rb_simbologia.addButton(self.rb_circulos_sin_relleno)
        self.grupo_rb_simbologia.addButton(self.rb_circulos_concentricos)

        self.grupo_rb_modo_secuencia = QButtonGroup(self)
        if hasattr(self, "rb_modo_enjambre") and hasattr(self, "rb_modo_replicas"):
            self.grupo_rb_modo_secuencia.addButton(self.rb_modo_enjambre)
            self.grupo_rb_modo_secuencia.addButton(self.rb_modo_replicas)

        # Fechas iniciales (últimos 7 días)
        hoy_dt = datetime.today()
        ini_dt = hoy_dt - timedelta(days=6)
        self._sincronizando_fechas = True
        self.dateEdit_ini.setDate(QDate(ini_dt.year, ini_dt.month, ini_dt.day))
        self.dateEdit_fin.setDate(QDate(hoy_dt.year, hoy_dt.month, hoy_dt.day))
        self.spin_duracion_dias.setValue(7)
        self._sincronizando_fechas = False
        self._actualizar_etiqueta_dias()

        # Inicializar visor GIS interactivo en contenedor_mapa_gis
        self.widget_mapa_gis = None
        self._ventana_emergente_gis = None
        self._widget_mapa_gis_emergente = None
        if hasattr(self, "contenedor_mapa_gis"):
            layout_gis = QVBoxLayout(self.contenedor_mapa_gis)
            layout_gis.setContentsMargins(0, 0, 0, 0)
            self.widget_mapa_gis = widget_grafico_mpl(self.contenedor_mapa_gis)
            layout_gis.addWidget(self.widget_mapa_gis)
            self._cid_click_gis = self.widget_mapa_gis.canvas.mpl_connect(
                "button_press_event", self._al_hacer_clic_en_mapa_gis
            )

        # Conexiones de señales
        self.Btn_Salir.clicked.connect(self.Salir_)
        self.Btn_guardar.clicked.connect(self.Guardar_)
        self.btn_cargar_periodo.clicked.connect(self.cargar_sismicidad_periodo)
        self.btn_dibujar_lugar.clicked.connect(self.alternar_modo_dibujo_mapa)
        self.btn_limpiar_lugar.clicked.connect(self.restablecer_lugar_al_mapa_base)
        self.btn_actualizar_gis.clicked.connect(self.actualizar_vista_gis)
        self.btn_ampliar_gis.clicked.connect(self.abrir_ventana_emergente_gis)
        self.btn_exportar_gis.clicked.connect(self.exportar_imagen_gis)
        self.ck_gis_estaciones.stateChanged.connect(self.actualizar_vista_gis)

        self.dateEdit_ini.dateChanged.connect(self._al_cambiar_fechas_calendario)
        self.dateEdit_fin.dateChanged.connect(self._al_cambiar_fechas_calendario)
        self.spin_duracion_dias.valueChanged.connect(self._al_cambiar_spin_duracion)

        self.cmbx_zona.currentIndexChanged.connect(self._al_cambiar_mapa_base)
        self.cmbx_tipo_lugar.currentIndexChanged.connect(
            self._al_cambiar_tipo_lugar_geometrico
        )
        if hasattr(self, "cmbx_sismo_principal"):
            self.cmbx_sismo_principal.currentIndexChanged.connect(
                self._al_seleccionar_sismo_principal
            )
        if hasattr(self, "btn_centrar_en_principal"):
            self.btn_centrar_en_principal.clicked.connect(
                self.centrar_lugar_en_sismo_principal
            )

        controles_reactivacion = (
            self.cmbx_mapa,
            self.cmbx_filtro_red,
            self.cmbx_magnitud,
            self.spin_lat_centro,
            self.spin_lon_centro,
            self.spin_radio_km,
            self.spin_lat_min,
            self.spin_lat_max,
            self.spin_lon_min,
            self.spin_lon_max,
            self.spin_prof_min,
            self.spin_prof_max,
            self.ck_dibujar_contorno_pdf,
            self.ck_box_reporte,
            self.ck_box_firma,
            self.rb_circulos_rellenos,
            self.rb_circulos_sin_relleno,
            self.rb_circulos_concentricos,
            getattr(self, "rb_modo_enjambre", None),
            getattr(self, "rb_modo_replicas", None),
            getattr(self, "ck_solo_posteriores", None),
        )
        for ctrl in controles_reactivacion:
            if ctrl is None:
                continue
            if hasattr(ctrl, "currentIndexChanged"):
                ctrl.currentIndexChanged.connect(self._al_cambiar_parametros_filtro)
            elif hasattr(ctrl, "valueChanged"):
                ctrl.valueChanged.connect(self._al_cambiar_parametros_filtro)
            elif hasattr(ctrl, "toggled"):
                ctrl.toggled.connect(self._al_cambiar_parametros_filtro)
            elif hasattr(ctrl, "stateChanged"):
                ctrl.stateChanged.connect(self._al_cambiar_parametros_filtro)

        self.restablecer_lugar_al_mapa_base()
        self._actualizar_visibilidad_controles_lugar()
        self._registrar_bitacora(
            f"Directorio de trabajo: {self.directorio_trabajo}\n"
            "1) Seleccione el período en días y pulse '1. Cargar Sismicidad del Período'.\n"
            "2) Delimite el lugar geométrico en el mapa GIS y pulse '2. Generar Informe PDF'."
        )

    # =========================================================================
    # INICIALIZACIÓN Y GESTIÓN DE PERÍODO EN DÍAS
    # =========================================================================
    def inicializar_variables(self):
        self.eventos = []
        self.eventos_reporte = [
            [
                "Nº",
                "Fecha; Hora (UTC)",
                "Evento",
                "Magn.",
                "Prof.(km)",
                "Lat.",
                "Long.",
                "Ubicación",
            ]
        ]
        self.catalogo = [
            [
                "Id",
                "año",
                "mes",
                "día",
                "hora",
                "min",
                "seg",
                "lat",
                "long",
                "prof",
                "rms",
                "e-x",
                "e-y",
                "e-0",
                "e-z",
                "Mag",
                "Tipo Mag",
                "Fuente",
                "ruta",
                "Ubicación",
            ]
        ]
        self.reporte_total = [
            [
                "RESPONSABLE",
                "HORA",
                "TOTAL",
                "SISMO",
                "FF",
                "FC",
                "TELESISMOS",
                "Evento_local",
                "INDEFINIDO",
                "Ruido",
                "3 est",
                "4 est",
                "5 est",
                "6 est",
                "7 est",
                "8 est",
            ]
        ]
        self.resumen = [
            [
                "DIA",
                "SISMO",
                "FF",
                "FC",
                "TELESISMO",
                "Evento Local",
                "INDEFINIDO",
                "Ruido",
            ]
        ]
        ruta_xml_base = os.path.abspath(
            os.path.join(ruta_proyecto, "datos", "archivo.xml")
        )
        self.arbol = ET.parse(ruta_xml_base)
        self.raiz = self.arbol.getroot()

    def _al_cambiar_fechas_calendario(self):
        if self._sincronizando_fechas:
            return
        self._sincronizando_fechas = True
        try:
            f_i = self.dateEdit_ini.date().toPyDate()
            f_f = self.dateEdit_fin.date().toPyDate()
            if f_f < f_i:
                self.dateEdit_fin.setDate(self.dateEdit_ini.date())
                f_f = f_i
            dias = (f_f - f_i).days + 1
            self.spin_duracion_dias.setValue(max(1, dias))
            self._actualizar_etiqueta_dias()
        finally:
            self._sincronizando_fechas = False

    def _al_cambiar_spin_duracion(self, valor_dias: int):
        if self._sincronizando_fechas:
            return
        self._sincronizando_fechas = True
        try:
            f_i = self.dateEdit_ini.date().toPyDate()
            f_f = f_i + timedelta(days=max(0, int(valor_dias) - 1))
            self.dateEdit_fin.setDate(QDate(f_f.year, f_f.month, f_f.day))
            self._actualizar_etiqueta_dias()
        finally:
            self._sincronizando_fechas = False

    def _actualizar_etiqueta_dias(self):
        f_i = self.dateEdit_ini.date().toPyDate()
        f_f = self.dateEdit_fin.date().toPyDate()
        dias = max(1, (f_f - f_i).days + 1)
        self.lbl_resumen_dias.setText(
            f"Período: {dias} {'día' if dias == 1 else 'días'} ({f_i.strftime('%d/%m/%Y')}–{f_f.strftime('%d/%m/%Y')})"
        )

    # =========================================================================
    # DEFINICIÓN Y TRAZADO INTERACTIVO DEL LUGAR GEOMÉTRICO EN EL MAPA GIS
    # =========================================================================
    def _obtener_definicion_lugar_actual(self):
        """
        Retorna el diccionario con la definición geométrica activa según `cmbx_tipo_lugar`:
          0: Círculo (lat, lon, radio_km)
          1: Rectángulo (lat_min, lat_max, lon_min, lon_max)
          2: Polígono libre (lista de vértices [(lon, lat), ...])
          3: Todo el Mapa Base (None -> usa solo el recorte del mapa base)
        """
        modo_lugar = self.cmbx_tipo_lugar.currentIndex()
        if modo_lugar == 0:
            return {
                "tipo": "circulo",
                "lat": float(self.spin_lat_centro.value()),
                "lon": float(self.spin_lon_centro.value()),
                "radio_km": float(self.spin_radio_km.value()),
            }
        elif modo_lugar == 1:
            return {
                "tipo": "rectangulo",
                "lat_min": float(self.spin_lat_min.value()),
                "lat_max": float(self.spin_lat_max.value()),
                "lon_min": float(self.spin_lon_min.value()),
                "lon_max": float(self.spin_lon_max.value()),
            }
        elif modo_lugar == 2:
            if len(self.vertices_poligono) >= 3:
                return {
                    "tipo": "poligono",
                    "vertices": list(self.vertices_poligono),
                }
            return None
        return None

    def _actualizar_visibilidad_controles_lugar(self):
        modo_lugar = self.cmbx_tipo_lugar.currentIndex()
        es_circulo = (modo_lugar == 0)
        es_rect = (modo_lugar == 1)
        es_poly = (modo_lugar == 2)

        for w in (self.lbl_lat_centro, self.spin_lat_centro, self.lbl_lon_centro, self.spin_lon_centro, self.lbl_radio_km, self.spin_radio_km):
            w.setEnabled(es_circulo)
        for w in (self.lbl_lat_rango, self.spin_lat_min, self.spin_lat_max, self.lbl_lon_rango, self.spin_lon_min, self.spin_lon_max):
            w.setEnabled(es_rect)

        self.lbl_estado_poligono.setText(
            f"Vértices: {len(self.vertices_poligono)}" if es_poly else ""
        )
        self.btn_dibujar_lugar.setEnabled(modo_lugar in (0, 1, 2))

        usar_concentricos = self.rb_circulos_concentricos.isChecked()
        self.ck_box_reporte.setEnabled(not usar_concentricos)
        self.ck_box_firma.setEnabled(not usar_concentricos)

        es_replicas = (
            hasattr(self, "rb_modo_replicas") and self.rb_modo_replicas.isChecked()
        )
        for nombre_w in (
            "lbl_sismo_principal",
            "cmbx_sismo_principal",
            "btn_centrar_en_principal",
            "ck_solo_posteriores",
        ):
            w_rep = getattr(self, nombre_w, None)
            if w_rep is not None:
                w_rep.setEnabled(es_replicas)

    def _al_seleccionar_sismo_principal(self, idx_combo: int):
        if self._actualizando_combo_principal or not hasattr(self, "cmbx_sismo_principal"):
            return
        dato = self.cmbx_sismo_principal.itemData(idx_combo)
        self._id_sismo_principal_forzado = None if dato in (None, "AUTO") else str(dato)
        self._al_cambiar_parametros_filtro()

    def centrar_lugar_en_sismo_principal(self):
        """
        Centra el círculo o rectángulo del lugar geométrico en las coordenadas
        del Sismo Principal activo (o del evento de mayor magnitud del período cargado).
        """
        sismo_ref = self.sismo_principal_actual
        if sismo_ref is None and hasattr(self, "catalogo_respaldo") and len(self.catalogo_respaldo) > 1:
            mejor_fila = None
            mejor_mag = -999.0
            for f in self.catalogo_respaldo[1:]:
                try:
                    m = float(f[IDX_MAGNITUD])
                    if m > mejor_mag:
                        mejor_mag = m
                        mejor_fila = f
                except Exception:
                    pass
            if mejor_fila is not None:
                sismo_ref = {
                    "lat": float(mejor_fila[IDX_LATITUD]),
                    "lon": float(mejor_fila[IDX_LONGITUD]),
                }
        if not isinstance(sismo_ref, dict):
            return

        lat_c = round(float(sismo_ref["lat"]), 4)
        lon_c = round(float(sismo_ref["lon"]), 4)
        for sp in (
            self.spin_lat_centro,
            self.spin_lon_centro,
            self.spin_lat_min,
            self.spin_lat_max,
            self.spin_lon_min,
            self.spin_lon_max,
        ):
            sp.blockSignals(True)

        self.spin_lat_centro.setValue(lat_c)
        self.spin_lon_centro.setValue(lon_c)
        delta_deg = max(0.05, round(float(self.spin_radio_km.value()) / 111.0, 4))
        self.spin_lat_min.setValue(round(lat_c - delta_deg, 4))
        self.spin_lat_max.setValue(round(lat_c + delta_deg, 4))
        self.spin_lon_min.setValue(round(lon_c - delta_deg, 4))
        self.spin_lon_max.setValue(round(lon_c + delta_deg, 4))

        for sp in (
            self.spin_lat_centro,
            self.spin_lon_centro,
            self.spin_lat_min,
            self.spin_lat_max,
            self.spin_lon_min,
            self.spin_lon_max,
        ):
            sp.blockSignals(False)

        self._al_cambiar_parametros_filtro()

    def _al_cambiar_tipo_lugar_geometrico(self):
        self._cancelar_modo_dibujo()
        self._actualizar_visibilidad_controles_lugar()
        self._al_cambiar_parametros_filtro()

    def _al_cambiar_mapa_base(self):
        self.restablecer_lugar_al_mapa_base()

    def restablecer_lugar_al_mapa_base(self):
        """
        Ajusta por defecto los parámetros del círculo y rectángulo al centro
        y sub-cuadrante de la región seleccionada en `cmbx_zona`.
        """
        self._cancelar_modo_dibujo()
        idx_z = self.cmbx_zona.currentIndex()
        if 0 <= idx_z < len(self.coordenadas):
            coord = self.coordenadas[idx_z]
            try:
                lat_min = float(coord[0])
                lat_max = float(coord[1])
                lon_min = float(coord[2])
                lon_max = float(coord[3])
                lat_c = round((lat_min + lat_max) / 2.0, 4)
                lon_c = round((lon_min + lon_max) / 2.0, 4)
                span_lat = max(0.1, lat_max - lat_min)
                span_lon = max(0.1, lon_max - lon_min)
                radio_def = round(min(span_lat, span_lon) * 111.0 * 0.25, 1)

                for sp in (
                    self.spin_lat_centro,
                    self.spin_lon_centro,
                    self.spin_radio_km,
                    self.spin_lat_min,
                    self.spin_lat_max,
                    self.spin_lon_min,
                    self.spin_lon_max,
                ):
                    sp.blockSignals(True)

                self.spin_lat_centro.setValue(lat_c)
                self.spin_lon_centro.setValue(lon_c)
                self.spin_radio_km.setValue(max(2.0, radio_def))

                self.spin_lat_min.setValue(round(lat_c - span_lat * 0.25, 4))
                self.spin_lat_max.setValue(round(lat_c + span_lat * 0.25, 4))
                self.spin_lon_min.setValue(round(lon_c - span_lon * 0.25, 4))
                self.spin_lon_max.setValue(round(lon_c + span_lon * 0.25, 4))

                self.vertices_poligono = [
                    (round(lon_c - span_lon * 0.22, 4), round(lat_c - span_lat * 0.22, 4)),
                    (round(lon_c + span_lon * 0.22, 4), round(lat_c - span_lat * 0.22, 4)),
                    (round(lon_c + span_lon * 0.22, 4), round(lat_c + span_lat * 0.22, 4)),
                    (round(lon_c - span_lon * 0.22, 4), round(lat_c + span_lat * 0.22, 4)),
                ]

                for sp in (
                    self.spin_lat_centro,
                    self.spin_lon_centro,
                    self.spin_radio_km,
                    self.spin_lat_min,
                    self.spin_lat_max,
                    self.spin_lon_min,
                    self.spin_lon_max,
                ):
                    sp.blockSignals(False)
            except (ValueError, IndexError):
                pass
        self._actualizar_visibilidad_controles_lugar()
        self._al_cambiar_parametros_filtro()

    def alternar_modo_dibujo_mapa(self):
        """
        Activa o finaliza la captura interactiva de clics sobre el mapa GIS
        para trazar el lugar geométrico directamente con el ratón.
        """
        if self._modo_dibujo_activo:
            # Si estaba trazando un polígono con >=3 puntos, lo cierra y aplica
            if self.cmbx_tipo_lugar.currentIndex() == 2 and len(self._puntos_dibujo_temp) >= 3:
                self.vertices_poligono = list(self._puntos_dibujo_temp)
            self._cancelar_modo_dibujo()
            self._al_cambiar_parametros_filtro()
            return

        modo_lugar = self.cmbx_tipo_lugar.currentIndex()
        if modo_lugar == 3:
            return

        self._modo_dibujo_activo = True
        self._puntos_dibujo_temp = []
        self.btn_dibujar_lugar.setText("Finalizar Dibujo en Mapa")
        self.btn_dibujar_lugar.setStyleSheet(
            "background-color: #d97706; color: white; border-radius: 4px; padding: 3px;"
        )

        if modo_lugar == 0:
            self.lbl_instruccion_dibujo.setText(
                "MODO CÍRCULO: 1º clic en el epicentro central, 2º clic en el borde del radio."
            )
        elif modo_lugar == 1:
            self.lbl_instruccion_dibujo.setText(
                "MODO RECTÁNGULO: 1º clic en una esquina, 2º clic en la esquina opuesta."
            )
        elif modo_lugar == 2:
            self.lbl_instruccion_dibujo.setText(
                "MODO POLÍGONO: Clic izquierdo añade vértices; clic derecho cierra el polígono."
            )

    def _cancelar_modo_dibujo(self):
        self._modo_dibujo_activo = False
        self._puntos_dibujo_temp = []
        self.btn_dibujar_lugar.setText("Dibujar Lugar en el Mapa")
        self.btn_dibujar_lugar.setStyleSheet(
            "background-color: #0284c7; color: white; border-radius: 4px; padding: 3px;"
        )
        self.lbl_instruccion_dibujo.setText(
            'Use "Dibujar Lugar en el Mapa" o ajuste las coordenadas para aislar el enjambre.'
        )

    def _al_hacer_clic_en_mapa_gis(self, event):
        """
        Captura los clics del usuario sobre el mapa GIS cuando el modo de dibujo
        está activo para definir interactivamente Círculo, Rectángulo o Polígono.
        """
        if not self._modo_dibujo_activo or event.inaxes is None:
            return
        if event.xdata is None or event.ydata is None:
            return

        lon_clic = round(float(event.xdata), 4)
        lat_clic = round(float(event.ydata), 4)
        modo_lugar = self.cmbx_tipo_lugar.currentIndex()

        # MODO 0: CÍRCULO (1º clic = centro, 2º clic = radio)
        if modo_lugar == 0:
            self._puntos_dibujo_temp.append((lon_clic, lat_clic))
            if len(self._puntos_dibujo_temp) == 1:
                self.spin_lat_centro.blockSignals(True)
                self.spin_lon_centro.blockSignals(True)
                self.spin_lat_centro.setValue(lat_clic)
                self.spin_lon_centro.setValue(lon_clic)
                self.spin_lat_centro.blockSignals(False)
                self.spin_lon_centro.blockSignals(False)
                self.lbl_instruccion_dibujo.setText(
                    f"Centro fijado en ({lat_clic:.3f}°, {lon_clic:.3f}°). Haga 2º clic para fijar el radio."
                )
                self.actualizar_vista_gis()
            elif len(self._puntos_dibujo_temp) >= 2:
                lon_c, lat_c = self._puntos_dibujo_temp[0]
                d_lat_km = (lat_clic - lat_c) * 110.574
                d_lon_km = (
                    (lon_clic - lon_c)
                    * 111.320
                    * math.cos(math.radians((lat_c + lat_clic) / 2.0))
                )
                radio_km = max(0.5, round(math.hypot(d_lat_km, d_lon_km), 1))
                self.spin_radio_km.blockSignals(True)
                self.spin_radio_km.setValue(radio_km)
                self.spin_radio_km.blockSignals(False)
                self._cancelar_modo_dibujo()
                self._al_cambiar_parametros_filtro()

        # MODO 1: RECTÁNGULO (1º clic = esquina 1, 2º clic = esquina 2)
        elif modo_lugar == 1:
            self._puntos_dibujo_temp.append((lon_clic, lat_clic))
            if len(self._puntos_dibujo_temp) == 1:
                self.lbl_instruccion_dibujo.setText(
                    f"Esquina 1 fijada ({lat_clic:.3f}°, {lon_clic:.3f}°). Haga 2º clic en la esquina opuesta."
                )
            elif len(self._puntos_dibujo_temp) >= 2:
                lon1, lat1 = self._puntos_dibujo_temp[0]
                for sp in (self.spin_lat_min, self.spin_lat_max, self.spin_lon_min, self.spin_lon_max):
                    sp.blockSignals(True)
                self.spin_lat_min.setValue(min(lat1, lat_clic))
                self.spin_lat_max.setValue(max(lat1, lat_clic))
                self.spin_lon_min.setValue(min(lon1, lon_clic))
                self.spin_lon_max.setValue(max(lon1, lon_clic))
                for sp in (self.spin_lat_min, self.spin_lat_max, self.spin_lon_min, self.spin_lon_max):
                    sp.blockSignals(False)
                self._cancelar_modo_dibujo()
                self._al_cambiar_parametros_filtro()

        # MODO 2: POLÍGONO LIBRE (clics izquierdos agregan vértices; clic derecho cierra)
        elif modo_lugar == 2:
            if event.button == 1:
                self._puntos_dibujo_temp.append((lon_clic, lat_clic))
                self.vertices_poligono = list(self._puntos_dibujo_temp)
                self.lbl_estado_poligono.setText(f"Vértices: {len(self.vertices_poligono)}")
                self.lbl_instruccion_dibujo.setText(
                    f"Vértice {len(self.vertices_poligono)} añadido. Clic derecho (o botón Finalizar) para cerrar."
                )
                if len(self.vertices_poligono) >= 3:
                    self._al_cambiar_parametros_filtro(preservar_modo_dibujo=True)
            elif event.button == 3 and len(self._puntos_dibujo_temp) >= 3:
                self.vertices_poligono = list(self._puntos_dibujo_temp)
                self._cancelar_modo_dibujo()
                self._al_cambiar_parametros_filtro()

    # =========================================================================
    # CARGA DE SISMICIDAD DEL PERÍODO (CATÁLOGOS _CAT.CSV O DÍA POR DÍA)
    # =========================================================================
    def cargar_sismicidad_periodo(self):
        f_i = self.dateEdit_ini.date().toPyDate()
        f_f = self.dateEdit_fin.date().toPyDate()
        if f_i > f_f:
            QMessageBox.warning(
                self,
                "Rango inválido",
                "La Fecha Inicio no puede ser posterior a la Fecha Fin.",
            )
            return

        self.inicializar_variables()
        self.fecha_ini = datetime.combine(f_i, time(0, 0, 0))
        self.fecha_fin = datetime.combine(f_f, time(0, 0, 0))
        self.periodo_reporte, self.directorio_reporte, self.archivo_reporte = (
            obtener_datos_reporte(
                self.fecha_ini,
                self.fecha_fin,
                self.directorio_trabajo,
                self.cmbx_zona.currentText(),
                tipo_forzado=3,
            )
        )

        if self.rb_fuente_catalogo.isChecked():
            self._cargar_desde_unidades_basicas(self.fecha_ini, self.fecha_fin)
        else:
            self._cargar_dia_por_dia(self.fecha_ini, self.fecha_fin)

        self.Respaldar_catalogo()
        self.Btn_guardar.setEnabled(True)
        self._al_cambiar_parametros_filtro()

    def _cargar_desde_unidades_basicas(self, fecha_ini_dt, fecha_fin_dt):
        unidades = generar_directorios_unidades_basicas(
            fecha_ini_dt,
            fecha_fin_dt,
            self.directorio_trabajo,
            verificar_existencia=True,
            detallar=True,
        )
        for unidad in unidades:
            tipo_u = unidad["tipo"]
            prefijo = unidad["prefijo"]
            ruta_cat = f"{prefijo}_cat.csv"
            if not os.path.isfile(ruta_cat):
                continue
            try:
                datos = lectura_archivo(ruta_cat)
                if datos and datos[0][0] == "Id":
                    self.catalogo.extend(datos[1:])
                elif datos:
                    self.catalogo.extend(datos)

                if tipo_u in ("PERIODO", "ANIO", "MES", "SEMANA"):
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
                        for fila_r in d_res or []:
                            if not fila_r or fila_r[0] in ("DIA", "Total:"):
                                continue
                            self.resumen.append(
                                fila_r[-7:] if len(fila_r) >= 8 else fila_r
                            )
                    if os.path.isfile(ruta_rtot):
                        d_rtot = lectura_resumen(ruta_rtot)
                        self.reporte_total.extend(
                            [r for r in (d_rtot or []) if r and r[0] != "RESPONSABLE"]
                        )
                    if os.path.isfile(ruta_xml):
                        raiz_u = ET.parse(ruta_xml).getroot()
                        for child in raiz_u:
                            self.raiz.append(child)
                else:
                    ruta_dat = f"{prefijo}_rep.csv"
                    if not os.path.isfile(ruta_dat):
                        ruta_dat = f"{prefijo}_dat.csv"
                    ruta_res = f"{prefijo}_res.csv"
                    carpeta_dia = os.path.dirname(prefijo)
                    stem_dia = os.path.basename(prefijo)
                    pref_fecha = (
                        stem_dia[:-6] if stem_dia.endswith("000000") else stem_dia[:6]
                    )
                    ruta_resp = os.path.join(
                        carpeta_dia, "reportes", f"{pref_fecha}_resp.csv"
                    )
                    if not os.path.isfile(ruta_resp):
                        ruta_resp = f"{prefijo}_resp.csv"
                    ruta_xml = f"{prefijo}.xml"

                    if os.path.isfile(ruta_dat):
                        d_rep = lectura_archivo(ruta_dat)
                        self.eventos_reporte.extend(
                            d_rep[1:] if d_rep and d_rep[0][0] == "Nº" else (d_rep or [])
                        )
                    if os.path.isfile(ruta_res):
                        d_res = lectura_resumen(ruta_res)
                        if d_res:
                            self.resumen.extend(d_res)
                    if os.path.isfile(ruta_resp):
                        d_resp = lectura_resumen(ruta_resp)
                        if d_resp:
                            self.reporte_total.extend(d_resp)
                    if os.path.isfile(ruta_xml):
                        raiz_d = ET.parse(ruta_xml).getroot()
                        for child in raiz_d:
                            self.raiz.append(child)
            except Exception as err_u:
                print(f"Aviso leyendo unidad {ruta_cat}: {err_u}")

    def _cargar_dia_por_dia(self, fecha_inicio, fecha_fin):
        fecha = fecha_inicio
        while fecha <= fecha_fin:
            fecha_q = QDate(fecha.year, fecha.month, fecha.day)
            archivo = os.path.join(
                self.directorio_trabajo, fecha_q.toString("yyyyMMdd000000")
            )
            directorios = obtener_directorios(archivo)
            if os.path.exists(directorios["Directorio_base"]):
                (
                    eventos_reporte,
                    catalogo,
                    eventos,
                    _vector,
                    _canales_eventos_dia,
                    root_dia,
                    responsable_dia,
                    resumen_dia,
                ) = cargar_dia(directorios)
                try:
                    Guardar_dia(
                        eventos_reporte,
                        catalogo,
                        eventos,
                        root_dia,
                        responsable_dia,
                        resumen_dia,
                        directorios,
                    )
                    actualizar_periodos_emitidos_desde_fecha(
                        fecha, self.directorio_trabajo
                    )
                except Exception as err_d:
                    print(f"Aviso actualizando día {fecha}: {err_d}")

                self.eventos = self.eventos + eventos
                self.catalogo = self.catalogo + catalogo[1:]
                self.eventos_reporte = self.eventos_reporte + eventos_reporte[1:]
                self.resumen = self.resumen + lectura_resumen(
                    directorios["archivo_resumen"]
                )
                self.reporte_total = self.reporte_total + lectura_resumen(
                    directorios["archivo_responsables"]
                )
                for child in root_dia:
                    self.raiz.append(child)
            fecha = fecha + timedelta(days=1)

    def Respaldar_catalogo(self):
        self.catalogo_respaldo = copy.deepcopy(self.catalogo)
        self.eventos_reporte_respaldo = copy.deepcopy(self.eventos_reporte)
        self.resumen_respaldo = copy.deepcopy(self.resumen)
        self.arbol_respaldo = copy.deepcopy(self.arbol)
        self.reporte_total_respaldo = copy.deepcopy(self.reporte_total)

    def Cargar_catalogo(self):
        if hasattr(self, "catalogo_respaldo"):
            self.catalogo = copy.deepcopy(self.catalogo_respaldo)
            self.eventos_reporte = copy.deepcopy(self.eventos_reporte_respaldo)
            self.resumen = copy.deepcopy(self.resumen_respaldo)
            self.reporte_total = copy.deepcopy(self.reporte_total_respaldo)
            self.arbol = self.arbol_respaldo
            self.Btn_guardar.setEnabled(True)

    # =========================================================================
    # FILTRADO ESPACIAL (LUGAR GEOMÉTRICO) Y SISMOLÓGICO DEL ENJAMBRE
    # =========================================================================
    def _cumple_filtro_red(self, fila_cat) -> bool:
        if not fila_cat or len(fila_cat) <= IDX_FUENTE:
            return True
        fuente = str(fila_cat[IDX_FUENTE]).strip().upper()
        id_ev = str(fila_cat[IDX_INDICE]).strip()
        es_rsa = fuente == "RSA" or (len(id_ev) >= 2 and id_ev.endswith("00"))
        modo_red = self.cmbx_filtro_red.currentIndex()
        if modo_red == 0:
            return es_rsa
        elif modo_red == 2:
            return not es_rsa
        return True

    def filtros(self):
        """
        Filtra `self.catalogo` y `self.nuevo_arbol` (.xml) aplicando:
          1. Recorte de la región base (`cmbx_zona`).
          2. Inclusión dentro del lugar geométrico activo (Círculo, Rectángulo o Polígono).
          3. Red sísmica (`cmbx_filtro_red`), rango de profundidad y magnitud mínima.
          4. Reconstrucción de la estadística diaria del enjambre (`self.resumen`).
        """
        self.nuevo_arbol = ET.ElementTree(ET.Element("sismo"))
        if not self.catalogo:
            return

        coord_ = self.coordenadas[self.cmbx_zona.currentIndex()]
        lat1, lat2 = float(coord_[0]), float(coord_[1])
        long1, long2 = float(coord_[2]), float(coord_[3])

        definicion_lugar = self._obtener_definicion_lugar_actual()
        poly_enjambre = construir_poligono_lugar_geometrico(definicion_lugar)

        prof_min = float(self.spin_prof_min.value())
        prof_max = float(self.spin_prof_max.value())
        if prof_min > prof_max:
            prof_min, prof_max = prof_max, prof_min

        try:
            mag_min = float(self.cmbx_magnitud.currentText())
        except ValueError:
            mag_min = -10.0

        eventos_filtrados = [self.catalogo[0]]
        for fila_cat in self.catalogo[1:]:
            if not fila_cat or len(fila_cat) <= IDX_LUGAR:
                continue
            try:
                lat = float(fila_cat[IDX_LATITUD])
                lon = float(fila_cat[IDX_LONGITUD])
                prof = abs(float(fila_cat[IDX_PROFUNDIDAD]))
                mag = float(fila_cat[IDX_MAGNITUD])
            except (ValueError, TypeError, IndexError):
                continue

            if not self._cumple_filtro_red(fila_cat):
                continue
            if not (prof_min <= prof <= prof_max):
                continue
            if mag < mag_min:
                continue
            if not (lat1 <= lat <= lat2 and long1 <= lon <= long2):
                continue
            if poly_enjambre is not None and not poly_enjambre.contains(Point(lon, lat)):
                continue

            eventos_filtrados.append(fila_cat)

        # Identificar Sismo Principal cuando está activo el modo 'Sismo Principal y Réplicas'
        candidatos_espaciales = eventos_filtrados[1:]
        es_modo_replicas = (
            hasattr(self, "rb_modo_replicas") and self.rb_modo_replicas.isChecked()
        )
        self.sismo_principal_actual = None

        if hasattr(self, "cmbx_sismo_principal"):
            self._actualizando_combo_principal = True
            try:
                self.cmbx_sismo_principal.clear()
                if candidatos_espaciales:
                    fila_mayor_mag = max(
                        candidatos_espaciales,
                        key=lambda f: float(f[IDX_MAGNITUD]),
                    )
                    uni_m = (
                        str(fila_mayor_mag[IDX_UNIDAD_MAG]).strip()
                        if len(fila_mayor_mag) > IDX_UNIDAD_MAG
                        else "Md"
                    )
                    txt_auto = (
                        f"Auto (Mayor Mag: {float(fila_mayor_mag[IDX_MAGNITUD]):.1f} {uni_m} — "
                        f"{int(fila_mayor_mag[IDX_DIA]):02d}/{int(fila_mayor_mag[IDX_MES]):02d}/{fila_mayor_mag[IDX_ANIO]} "
                        f"{int(fila_mayor_mag[IDX_HORA]):02d}:{int(fila_mayor_mag[IDX_MINUTO]):02d})"
                    )
                    self.cmbx_sismo_principal.addItem(txt_auto, "AUTO")
                    idx_seleccionar = 0
                    for idx_c, f_cand in enumerate(candidatos_espaciales, start=1):
                        id_cand = str(f_cand[IDX_INDICE]).strip()
                        uni_c = (
                            str(f_cand[IDX_UNIDAD_MAG]).strip()
                            if len(f_cand) > IDX_UNIDAD_MAG
                            else "Md"
                        )
                        etiqueta_c = (
                            f"{float(f_cand[IDX_MAGNITUD]):.1f} {uni_c} | "
                            f"{int(f_cand[IDX_DIA]):02d}/{int(f_cand[IDX_MES]):02d} "
                            f"{int(f_cand[IDX_HORA]):02d}:{int(f_cand[IDX_MINUTO]):02d} | "
                            f"Prof {float(f_cand[IDX_PROFUNDIDAD]):.1f}km"
                        )
                        self.cmbx_sismo_principal.addItem(etiqueta_c, id_cand)
                        if (
                            self._id_sismo_principal_forzado
                            and id_cand == self._id_sismo_principal_forzado
                        ):
                            idx_seleccionar = idx_c
                    if idx_seleccionar == 0:
                        self._id_sismo_principal_forzado = None
                    self.cmbx_sismo_principal.setCurrentIndex(idx_seleccionar)
                else:
                    self.cmbx_sismo_principal.addItem("Sin sismos en el área", "AUTO")
            finally:
                self._actualizando_combo_principal = False

        if es_modo_replicas and candidatos_espaciales:
            fila_elegida = None
            if self._id_sismo_principal_forzado:
                for f_c in candidatos_espaciales:
                    if str(f_c[IDX_INDICE]).strip() == self._id_sismo_principal_forzado:
                        fila_elegida = f_c
                        break
            if fila_elegida is None:
                fila_elegida = max(
                    candidatos_espaciales,
                    key=lambda f: float(f[IDX_MAGNITUD]),
                )
            self.sismo_principal_actual = {
                "id": str(fila_elegida[IDX_INDICE]).strip(),
                "evento": str(fila_elegida[IDX_EVENTO]).strip(),
                "lat": float(fila_elegida[IDX_LATITUD]),
                "lon": float(fila_elegida[IDX_LONGITUD]),
                "prof": abs(float(fila_elegida[IDX_PROFUNDIDAD])),
                "mag": float(fila_elegida[IDX_MAGNITUD]),
                "unidad_mag": (
                    str(fila_elegida[IDX_UNIDAD_MAG]).strip()
                    if len(fila_elegida) > IDX_UNIDAD_MAG and str(fila_elegida[IDX_UNIDAD_MAG]).strip()
                    else "Md"
                ),
                "ubicacion": str(fila_elegida[IDX_LUGAR]).strip(),
            }
            if hasattr(self, "ck_solo_posteriores") and self.ck_solo_posteriores.isChecked():
                id_corte = self.sismo_principal_actual["id"]
                eventos_filtrados = [eventos_filtrados[0]] + [
                    f_ev
                    for f_ev in candidatos_espaciales
                    if str(f_ev[IDX_INDICE]).strip() >= id_corte
                ]

        self.catalogo = eventos_filtrados

        # Reconstruir vector/matriz diaria del enjambre para la portada PDF (caja_simbologia y estadistica_)
        if hasattr(self, "fecha_ini") and hasattr(self, "fecha_fin"):
            n_dias = max(1, (self.fecha_fin - self.fecha_ini).days + 1)
            conteo_por_dia = [0] * n_dias
            for ev in self.catalogo[1:]:
                if not ev or str(ev[IDX_INDICE]).strip() in ("Id", "00000000000000"):
                    continue
                try:
                    f_ev = datetime(
                        int(ev[IDX_INDICE][0:4]),
                        int(ev[IDX_INDICE][4:6]),
                        int(ev[IDX_INDICE][6:8]),
                    )
                    idx_d = (f_ev - self.fecha_ini).days
                    if 0 <= idx_d < n_dias:
                        conteo_por_dia[idx_d] += 1
                except Exception:
                    pass

            perfil_mapa = obtener_perfil_mapa(
                self.cmbx_zona.currentIndex(), es_periodo=True
            )
            if perfil_mapa["tipo_resumen_estadistico"] == "vector_filtrado":
                self.resumen = [0, 0] + conteo_por_dia
            else:
                self.resumen = [
                    [
                        "DIA",
                        "SISMO",
                        "FF",
                        "FC",
                        "TELESISMO",
                        "Evento Local",
                        "INDEFINIDO",
                        "Ruido",
                    ],
                    ["Total:", sum(conteo_por_dia), 0, 0, 0, 0, 0, 0],
                ]
                for c_dia in conteo_por_dia:
                    self.resumen.append([str(c_dia), "0", "0", "0", "0", "0", "0"])

        # Filtrar también el árbol XML con los mismos criterios
        modo_red = self.cmbx_filtro_red.currentIndex()
        for ev_xml in self.raiz.findall(".//Evento"):
            try:
                lon_x = float(ev_xml.find("longitud").text)
                lat_x = float(ev_xml.find("latitud").text)
                mag_x = float(ev_xml.find("magnitud").text)
                prof_txt = ev_xml.findtext("profundidad")
                prof_x = abs(float(prof_txt)) if prof_txt is not None else 0.0
                id_x = (ev_xml.findtext("id_evento") or "").strip()
                fuente_x = (ev_xml.findtext("fuente") or "").strip().upper()
                es_rsa_x = fuente_x == "RSA" or not fuente_x or id_x.endswith("00")
            except (AttributeError, ValueError, TypeError):
                continue

            if modo_red == 0 and not es_rsa_x:
                continue
            if modo_red == 2 and es_rsa_x:
                continue
            if not (prof_min <= prof_x <= prof_max) or mag_x < mag_min:
                continue
            if not (long1 <= lon_x <= long2 and lat1 <= lat_x <= lat2):
                continue
            if poly_enjambre is not None and not poly_enjambre.contains(Point(lon_x, lat_x)):
                continue
            if (
                self.sismo_principal_actual is not None
                and hasattr(self, "ck_solo_posteriores")
                and self.ck_solo_posteriores.isChecked()
                and id_x
                and id_x < self.sismo_principal_actual["id"]
            ):
                continue

            nuevo_ev = ET.SubElement(self.nuevo_arbol.getroot(), "Evento")
            for child in ev_xml:
                nuevo_ev.append(copy.deepcopy(child))

    # =========================================================================
    # VISTA PREVIA GIS, VENTANA EMERGENTE Y GENERACIÓN DEL INFORME PDF
    # =========================================================================
    def _obtener_estilo_circulos_mapa(self):
        if self.rb_circulos_concentricos.isChecked():
            return 2
        if self.rb_circulos_sin_relleno.isChecked():
            return False
        return True

    def _al_cambiar_parametros_filtro(self, *args, preservar_modo_dibujo=False):
        if not preservar_modo_dibujo and self._modo_dibujo_activo:
            self._cancelar_modo_dibujo()
        self._actualizar_visibilidad_controles_lugar()
        self.actualizar_vista_gis()

    def actualizar_vista_gis(self, *_args):
        if getattr(self, "widget_mapa_gis", None) is None:
            return
        try:
            if hasattr(self, "catalogo_respaldo") and len(getattr(self, "catalogo_respaldo", [])) > 1:
                self.Cargar_catalogo()
                self.filtros()
                catalogo_a_graficar = self.catalogo
            else:
                catalogo_a_graficar = getattr(self, "catalogo", [])

            idx_zona = self.cmbx_zona.currentIndex()
            coord_zona = (
                self.coordenadas[idx_zona]
                if 0 <= idx_zona < len(self.coordenadas)
                else None
            )
            zona_nombre = self.cmbx_zona.currentText().strip()
            estilo_circulos = self._obtener_estilo_circulos_mapa()
            mostrar_est = self.ck_gis_estaciones.isChecked()
            definicion_lugar = self._obtener_definicion_lugar_actual()

            sub_periodo = getattr(self, "periodo_reporte", "")
            pref_modo = (
                "SISMO Y RÉPLICAS"
                if self.sismo_principal_actual is not None
                else "ENJAMBRE"
            )
            titulo_gis = (
                f"{pref_modo} — {zona_nombre.upper()} ({sub_periodo})"
                if sub_periodo
                else f"{pref_modo} — {zona_nombre.upper()}"
            )

            stats = graficar_periodo_gis(
                self.widget_mapa_gis,
                catalogo_a_graficar,
                coordenadas_mapa=coord_zona,
                estilo_circulos=estilo_circulos,
                titulo_mapa=titulo_gis,
                parametros_est=self.parametros,
                mostrar_estaciones=mostrar_est,
                poligono_enjambre=definicion_lugar,
                sismo_principal=self.sismo_principal_actual,
            )

            if (
                getattr(self, "_ventana_emergente_gis", None) is not None
                and self._ventana_emergente_gis.isVisible()
                and getattr(self, "_widget_mapa_gis_emergente", None) is not None
            ):
                graficar_periodo_gis(
                    self._widget_mapa_gis_emergente,
                    catalogo_a_graficar,
                    coordenadas_mapa=coord_zona,
                    estilo_circulos=estilo_circulos,
                    titulo_mapa=titulo_gis,
                    parametros_est=self.parametros,
                    mostrar_estaciones=mostrar_est,
                    poligono_enjambre=definicion_lugar,
                    sismo_principal=self.sismo_principal_actual,
                )

            if self.sismo_principal_actual is not None:
                n_rep = max(0, stats["total"] - 1)
                self.lbl_resumen_gis.setText(
                    f"Principal: {self.sismo_principal_actual['mag']} {self.sismo_principal_actual['unidad_mag']} | Réplicas: {n_rep} (Sup: {stats['sup']} | Med: {stats['med']} | Prof: {stats['pro']})"
                )
            else:
                self.lbl_resumen_gis.setText(
                    f"Sismos en lugar geométrico: {stats['total']} (RSA: {stats['rsa']} | Sup: {stats['sup']} | Med: {stats['med']} | Prof: {stats['pro']})"
                )

            # Actualizar bitácora con métricas sismológicas del enjambre
            if hasattr(self, "catalogo_respaldo") and len(self.catalogo) > 1:
                mags = []
                profs = []
                for f in self.catalogo[1:]:
                    try:
                        mags.append(float(f[IDX_MAGNITUD]))
                        profs.append(abs(float(f[IDX_PROFUNDIDAD])))
                    except Exception:
                        pass
                mag_max = f"{max(mags):.2f} Md" if mags else "N/A"
                prof_prom = f"{(sum(profs) / len(profs)):.1f} km" if profs else "N/A"
                self._registrar_bitacora(
                    f"Período activo: {getattr(self, 'periodo_reporte', '')}\n"
                    f"Sismos dentro del lugar geométrico: {stats['total']} (de {max(0, len(self.catalogo_respaldo) - 1)} en el período)\n"
                    f"Magnitud máx.: {mag_max}  |  Profundidad media: {prof_prom}"
                )
        except Exception as e:
            print(f"Aviso actualizando vista GIS de enjambre: {e}")

    def abrir_ventana_emergente_gis(self):
        try:
            if getattr(self, "_ventana_emergente_gis", None) is None:
                ventana = QWidget(self, Qt.Window)
                ventana.setWindowTitle(
                    "Vista Ampliada GIS — Delimitación de Enjambre Sísmico (RSA)"
                )
                ventana.resize(1050, 800)
                layout_v = QVBoxLayout(ventana)
                layout_v.setContentsMargins(6, 6, 6, 6)
                layout_v.setSpacing(4)

                lienzo_emergente = widget_grafico_mpl(ventana)
                barra_nav = NavigationToolbar2QT(lienzo_emergente.canvas, ventana)
                layout_v.addWidget(barra_nav)
                layout_v.addWidget(lienzo_emergente, stretch=1)

                self._ventana_emergente_gis = ventana
                self._widget_mapa_gis_emergente = lienzo_emergente

            self._ventana_emergente_gis.show()
            self._ventana_emergente_gis.raise_()
            self._ventana_emergente_gis.activateWindow()
            self.actualizar_vista_gis()
        except Exception as e:
            QMessageBox.warning(
                self,
                "Vista Ampliada GIS",
                f"No se pudo abrir la ventana emergente GIS:\n{e}",
            )

    def exportar_imagen_gis(self):
        if getattr(self, "widget_mapa_gis", None) is None:
            return
        carpeta_sug = os.path.join(
            str(getattr(self, "directorio_reporte", self.directorio_trabajo)).rstrip("/\\"),
            "Enjambres",
            self.cmbx_zona.currentText().strip(),
        )
        try:
            Path(carpeta_sug).mkdir(parents=True, exist_ok=True)
        except OSError:
            carpeta_sug = self.directorio_trabajo

        ruta_sug = os.path.join(carpeta_sug, "enjambre_sismico_gis.png")
        ruta_png, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar Mapa GIS de Enjambre",
            ruta_sug,
            "Imagen PNG (*.png);;Documento PDF (*.pdf)",
        )
        if not ruta_png:
            return
        try:
            self.widget_mapa_gis.figure.savefig(
                ruta_png, dpi=300, bbox_inches="tight", facecolor="white"
            )
            QMessageBox.information(
                self, "Mapa exportado", f"Mapa GIS guardado en:\n{ruta_png}"
            )
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"No se pudo exportar la imagen GIS:\n{e}"
            )

    def Guardar_(self):
        """
        Genera el informe en PDF del enjambre sísmico empleando `reporte_resumen_modos()`
        de ReportLab junto con los archivos `_cat.csv`, `_res.csv` y `.xml` del enjambre.
        """
        if hasattr(self, "catalogo_respaldo") and len(getattr(self, "catalogo_respaldo", [])) > 1:
            self.Cargar_catalogo()
        self.filtros()

        if len(self.catalogo) <= 1:
            resp = QMessageBox.question(
                self,
                "Sin sismos en el lugar geométrico",
                "No se encontraron sismos dentro del lugar geométrico actual.\n¿Desea generar el informe PDF de todas formas?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if resp != QMessageBox.Yes:
                return

        from subprogramas.respaldo_base_datos import solicitar_destino_externo_si_liviana
        dir_externo_enj = solicitar_destino_externo_si_liviana(
            self,
            self.directorio_trabajo,
            "Base de Datos Liviana — Seleccione carpeta externa para guardar el informe de enjambre",
        )
        if dir_externo_enj == "":
            return

        zona_rep = self.cmbx_zona.currentText().strip()
        base_rep = str(dir_externo_enj if dir_externo_enj else getattr(self, "directorio_reporte", self.directorio_trabajo)).rstrip("/\\")
        directorio_destino = f"{base_rep}/Enjambres/{zona_rep}/"
        try:
            Path(directorio_destino).mkdir(parents=True, exist_ok=True)
        except OSError:
            pass

        titulo_custom = self.txt_nombre_enjambre.text().strip()
        if self.periodo_reporte.startswith("Período: "):
            nombre_base = self.periodo_reporte[9:].replace("/", "_").strip()
        else:
            nombre_base = self.periodo_reporte.replace("/", "_").strip()

        if titulo_custom:
            prefijo_limpio = "".join(
                c if c.isalnum() or c in (" ", "_", "-") else "_" for c in titulo_custom
            ).strip()
            nombre_archivo = f"{prefijo_limpio}_{nombre_base}"
            subtitulo_pdf = f"{titulo_custom} ({self.periodo_reporte})"
        elif self.sismo_principal_actual is not None:
            mag_p = self.sismo_principal_actual["mag"]
            uni_p = self.sismo_principal_actual["unidad_mag"]
            nombre_archivo = f"Sismo_y_Replicas_{zona_rep}_{nombre_base}"
            subtitulo_pdf = (
                f"Sismo Principal ({mag_p} {uni_p}) y sus Réplicas — {zona_rep} ({self.periodo_reporte})"
            )
        else:
            nombre_archivo = f"Enjambre_{zona_rep}_{nombre_base}"
            subtitulo_pdf = f"Enjambre Sísmico — {zona_rep} ({self.periodo_reporte})"

        ruta_pdf = os.path.join(directorio_destino, f"{nombre_archivo}_pdf1.pdf")
        ruta_cat = os.path.join(directorio_destino, f"{nombre_archivo}_cat.csv")
        ruta_res = os.path.join(directorio_destino, f"{nombre_archivo}_res.csv")
        ruta_xml = os.path.join(directorio_destino, f"{nombre_archivo}.xml")

        # Guardar catálogo filtrado del enjambre
        with open(ruta_cat, "w", newline="", encoding="utf-8") as f_cat:
            escritor = csv.writer(f_cat, delimiter=";")
            for fila in self.catalogo:
                if fila:
                    escritor.writerow(fila)

        # Guardar XML filtrado del enjambre
        self.nuevo_arbol.write(ruta_xml)

        # Resolver modo de reporte ReportLab
        bandera_relleno = self._obtener_estilo_circulos_mapa()
        bandera_firma = self.ck_box_firma.isChecked()
        con_detalle = self.ck_box_reporte.isChecked()
        if bandera_relleno == 2:
            modo_reporte = MODO_MAPA_ESPECIAL
        else:
            modo_reporte = (
                MODO_INSTITUCIONAL_DETALLADO
                if con_detalle
                else MODO_INSTITUCIONAL_RESUMEN
            )

        # Validar existencia del archivo .emf de la capa seleccionada
        indice_tipo_mapa = self.cmbx_mapa.currentIndex()
        ruta_emf = os.path.join(
            ruta_datos, "mapas", f"{zona_rep}_{indice_tipo_mapa}.emf"
        )
        if not os.path.isfile(ruta_emf):
            for idx_alt in (0, 1, 2):
                if os.path.isfile(
                    os.path.join(ruta_datos, "mapas", f"{zona_rep}_{idx_alt}.emf")
                ):
                    indice_tipo_mapa = idx_alt
                    break

        poligono_para_pdf = (
            self._obtener_definicion_lugar_actual()
            if self.ck_dibujar_contorno_pdf.isChecked()
            else None
        )

        reporte_resumen_modos(
            ruta_pdf,
            subtitulo_pdf,
            self.fecha_ini,
            self.fecha_fin,
            self.catalogo,
            self.resumen,
            self.cmbx_zona.currentIndex(),
            indice_tipo_mapa,
            modo_reporte,
            0,
            self.directorio_trabajo,
            self.nuevo_arbol,
            self.reporte_total,
            self.eventos,
            bandera_firma,
            bandera_relleno,
            poligono_enjambre=poligono_para_pdf,
            sismo_principal=self.sismo_principal_actual,
        )

        # Guardar resumen estadístico si es matriz
        if isinstance(self.resumen, list) and self.resumen and isinstance(self.resumen[0], list):
            with open(ruta_res, "w", newline="", encoding="utf-8") as f_res:
                escritor_r = csv.writer(f_res, delimiter=";")
                for idx_r, fila_r in enumerate(self.resumen):
                    fila_out = list(fila_r)
                    if idx_r > 1:
                        fila_out.insert(0, idx_r - 1)
                    escritor_r.writerow(fila_out)

        self._registrar_bitacora(
            f"✓ Informe de Enjambre generado exitosamente en:\n  {directorio_destino}\n"
            f"  • PDF: {os.path.basename(ruta_pdf)}\n"
            f"  • Sismos incluidos: {max(0, len(self.catalogo) - 1)} | Catálogo: {os.path.basename(ruta_cat)}"
        )
        QMessageBox.information(
            self,
            "Informe de Enjambre Generado",
            f"El informe PDF y el catálogo del enjambre se guardaron en:\n{ruta_pdf}",
        )

    def _registrar_bitacora(self, mensaje: str):
        if hasattr(self, "textEdit") and self.textEdit is not None:
            self.textEdit.setPlainText(mensaje)

    def Salir_(self):
        self.close()

    def limpiar_estado(self):
        try:
            if getattr(self, "_ventana_emergente_gis", None) is not None:
                try:
                    self._ventana_emergente_gis.close()
                    self._ventana_emergente_gis.deleteLater()
                except Exception:
                    pass
                self._ventana_emergente_gis = None
                self._widget_mapa_gis_emergente = None
            if getattr(self, "widget_mapa_gis", None) is not None:
                try:
                    if self._cid_click_gis is not None:
                        self.widget_mapa_gis.canvas.mpl_disconnect(self._cid_click_gis)
                        self._cid_click_gis = None
                    self.widget_mapa_gis.figure.clf()
                    self.widget_mapa_gis.canvas.deleteLater()
                    self.widget_mapa_gis.deleteLater()
                except Exception:
                    pass
                self.widget_mapa_gis = None
        except Exception as e:
            print(f"Aviso en limpieza de Reporte_enjambre: {e}")

    def closeEvent(self, event):
        self.limpiar_estado()
        self.cerrado.emit()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = Reporte_enjambre()
    ventana.show()
    sys.exit(app.exec_())
