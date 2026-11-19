"""
========================================================================================
Módulo: adquisicion_galgas_potenciometros.py
Propósito: Software de calibración y certificación de sensor de presión para banco
           hidráulico / prensa de hasta 100 Toneladas.
Circuito:  Puente de Wheatstone con excitación de 8.0 V y preamplificador INA114AP
           conectado a la tarjeta National Instruments NI-USB-6210.
Regla de Hardware por Defecto:
  - ai0 y ai1: Entradas DIFERENCIALES (TerminalConfiguration.DIFF).
    * ai0: Sensor de Presión Principal (INA114AP, AI 0 / AI 8).
    * ai1: Segunda entrada diferencial (galga o puente auxiliar, AI 1 / AI 9).
  - ai2 en adelante: Entradas SINGLE-ENDED (TerminalConfiguration.RSE).
Metodología de Calibración:
  1. Ajuste de Fondo de Escala: A 100 Toneladas se calibra la ganancia del INA114AP
     variando Rg hasta alcanzar la ventana óptima de 4.75 V a 4.95 V.
  2. Registro de Referencia: Se ingresa el valor medido de Rg colocada y se fija la escala.
  3. Ensayo en Osciloscopio (0 a 100 Toneladas): Registro continuo con promedios de 0.5 s,
     almacenando toda la señal en archivo CSV con trazabilidad completa.
  4. Modo Multímetro: Integración en bloques de 2.0 s para lectura ultraestable.
  5. Calibración contra Patrón: Regresión lineal por mínimos cuadrados y cálculo de R².
Entorno: C:\\entornos\\estructuras (Python 3.13 / PySide6 / pyqtgraph / nidaqmx / numpy)
========================================================================================
"""

import csv
import datetime
import math
import os
import random
import sys
import time
from collections import deque
from typing import Dict, List, Optional, Tuple

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

# Detección de NI-DAQmx
HAY_NIDAQMX = False
try:
    import nidaqmx
    from nidaqmx.constants import AcquisitionType, TerminalConfiguration
    from nidaqmx.system import System
    HAY_NIDAQMX = True
except (ImportError, Exception) as error_import:
    HAY_NIDAQMX = False
    print(f"Aviso: NI-DAQmx no disponible ({error_import}). Operación en modo simulación.")


class ModeloCanalNI:
    """Modela la configuración eléctrica de cada canal de la tarjeta."""

    def __init__(
        self,
        indice: int,
        nombre: str,
        etiqueta: str,
        modo_terminal: str,  # 'DIFF' o 'RSE'
        rango_voltaje: float = 10.0,
        habilitado: bool = True,
    ):
        self.indice = indice
        self.nombre = nombre
        self.etiqueta = etiqueta
        self.modo_terminal = modo_terminal
        self.rango_voltaje = rango_voltaje
        self.habilitado = habilitado


class VentanaCalibracionPrensa100Ton(QMainWindow):
    """
    Controlador principal de calibración para prensas de 100 Toneladas
    con sensor de presión, INA114AP y NI-USB-6210.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(
            "Calibración de Sensor de Presión (100 Toneladas) — Puente 8V + INA114AP & NI-USB-6210"
        )
        self.resize(1450, 950)

        # ---------------------------------------------------------------------
        # Parámetros del Circuito Electrónico y Sensor de Presión
        # ---------------------------------------------------------------------
        self.v_excitacion_puente: float = 8.0  # Alimentación nominal: 8.0 V
        self.rg_ohmios: float = 1000.0         # Resistencia externa Rg (Pines 1 y 8 del INA114AP)
        self.tara_offset_voltaje: float = 0.0  # Offset de tara para canal principal (V)

        # ---------------------------------------------------------------------
        # Parámetros de Fondo de Escala (100 Toneladas)
        # ---------------------------------------------------------------------
        self.carga_maxima_nominal: float = 100.0   # 100 Toneladas
        self.voltaje_objetivo_min: float = 4.75    # 4.75 V
        self.voltaje_objetivo_max: float = 4.95    # 4.95 V
        self.referencia_100_ton_fijada: bool = False
        self.v_referencia_100_ton: float = 4.85     # Tensión fijada a 100 Ton
        self.rg_instalada_referencia: float = 1000.0
        self.sensibilidad_nominal_ton_v: float = 100.0 / 4.85

        # ---------------------------------------------------------------------
        # Tiempos de Ventana y Frecuencia de Muestreo de Hardware
        # ---------------------------------------------------------------------
        self.tiempo_ventana_osciloscopio: float = 0.5  # Bloque de 0.5 s para osciloscopio
        self.tiempo_ventana_multimetro: float = 2.0    # Bloque de 2.0 s para multímetro
        self.frecuencia_muestreo_fs: int = 1000       # 1000 Hz en el ADC de la USB-6210

        # Tarjeta NI-USB-6210 y Canales
        self.nombre_dispositivo: str = "Dev1"
        self.canal_principal_nombre: str = "ai0"
        self.canales: List[ModeloCanalNI] = []

        # ---------------------------------------------------------------------
        # Estado de la Secuencia Activa y Grabación Dual (Promedios + Muestreo Real Fs)
        # ---------------------------------------------------------------------
        self.secuencia_activa = False
        self.modo_secuencia_actual: str = "Ninguno"  # 'Osciloscopio', 'Multimetro', 'Ensayo100Ton'
        self.id_secuencia_actual: int = 0
        self.tiempo_inicio_secuencia: Optional[float] = None
        self.guardar_muestreo_real_fs: bool = True   # Grabación dual activada por defecto

        # Archivo 1: Secuencia de Calibración por Promedios (0.5 s / 2.0 s)
        self.manejador_csv_promedios = None
        self.escritor_csv_promedios = None
        self.ruta_archivo_csv_promedios: Optional[str] = None
        self.contador_bloques_promedios: int = 0

        # Archivo 2: Secuencia Real en Bruto a Frecuencia de Tarjeta Fs (ej. 1000 Hz)
        self.manejador_csv_raw = None
        self.escritor_csv_raw = None
        self.ruta_archivo_csv_raw: Optional[str] = None
        self.contador_muestras_raw: int = 0

        # Variables de retrocompatibilidad
        self.contador_muestras_secuencia: int = 0
        self.manejador_csv_secuencia = None
        self.escritor_csv_secuencia = None
        self.ruta_archivo_csv_actual: Optional[str] = None

        # Carpeta base y gestión de sesiones de calibración
        self.carpeta_base_secuencias = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "secuencias_calibracion"
        )
        os.makedirs(self.carpeta_base_secuencias, exist_ok=True)
        self.id_sesion_actual: str = ""
        self.nombre_sesion_actual: str = ""
        self.carpeta_sesion_actual: str = ""
        self.tiempo_apertura_sesion: str = ""
        self.carpeta_secuencias: str = self.carpeta_base_secuencias

        # Buffers temporales para graficación en tiempo real (hasta 5000 puntos = ~40 min a 0.5s)
        self.max_puntos_grafica = 5000
        self.tiempos_grafica = deque(maxlen=self.max_puntos_grafica)
        self.voltajes_grafica = deque(maxlen=self.max_puntos_grafica)
        self.cargas_grafica = deque(maxlen=self.max_puntos_grafica)
        self.ultimos_promedios_canales: Dict[str, float] = {}

        # Estado de Escalabilidad del Osciloscopio (Amplitud Y y Tiempo X)
        self.auto_escala_y: bool = True
        self.y_min_manual: float = 0.0
        self.y_max_manual: float = 120.0  # 120 Ton o 10 V
        self.modo_tiempo_x: str = "Todo"   # 'Todo' o 'Ventana'
        self.segundos_ventana_visible: float = 60.0

        # Iniciar sesión inicial por defecto
        self.iniciar_nueva_sesion(etiqueta="Calibracion")

        # Temporizador periódico de bloques
        self.temporizador_adquisicion = QTimer(self)
        self.temporizador_adquisicion.timeout.connect(self.ejecutar_bloque_adquisicion)

        # Configuración pyqtgraph
        pg.setConfigOption("background", "#16161e")
        pg.setConfigOption("foreground", "#c0caf5")
        pg.setConfigOptions(antialias=True)

        # Inicializar canales por defecto: ai0/ai1 en DIFF, ai2+ en RSE
        self.inicializar_canales_por_defecto()

        # Construir interfaz gráfica
        self.inicializar_interfaz_usuario()
        self.buscar_tarjetas_nidaq()

    # =========================================================================
    # CONFIGURACIÓN POR DEFECTO DE CANALES (DIFF Y RSE)
    # =========================================================================

    def inicializar_canales_por_defecto(self) -> None:
        """
        Regla de Hardware Obligatoria:
        - ai0 y ai1: Entradas DIFERENCIALES (TerminalConfiguration.DIFF).
        - ai2 en adelante: Entradas SINGLE-ENDED (TerminalConfiguration.RSE).
        """
        self.canales.clear()
        self.canales.append(
            ModeloCanalNI(0, "ai0", "Sensor Presión Principal (INA114AP)", "DIFF", rango_voltaje=10.0, habilitado=True)
        )
        self.canales.append(
            ModeloCanalNI(1, "ai1", "Diferencial 2 (Galga/Puente Auxiliar)", "DIFF", rango_voltaje=10.0, habilitado=True)
        )
        for i in range(2, 8):
            self.canales.append(
                ModeloCanalNI(
                    i, f"ai{i}", f"Canal Single-Ended {i}", "RSE", rango_voltaje=10.0, habilitado=(i == 2)
                )
            )

    # =========================================================================
    # CONSTRUCCIÓN DE LA INTERFAZ GRÁFICA
    # =========================================================================

    def inicializar_interfaz_usuario(self) -> None:
        widget_central = QWidget(self)
        self.setCentralWidget(widget_central)
        layout_principal = QVBoxLayout(widget_central)
        layout_principal.setContentsMargins(8, 8, 8, 8)
        layout_principal.setSpacing(6)

        # 1. Barra Superior de Conexión de Hardware
        grupo_hardware = self.crear_panel_hardware()
        layout_principal.addWidget(grupo_hardware)

        # 1.1 Barra de Sesión de Calibración Activa
        panel_sesion = self.crear_panel_sesion()
        layout_principal.addWidget(panel_sesion)

        # 2. Pestañas de Trabajo
        self.pestanias = QTabWidget()
        self.pestania_ajuste_escala = self.crear_pestania_ajuste_fondo_escala()
        self.pestania_osciloscopio = self.crear_pestania_osciloscopio()
        self.pestania_multimetro = self.crear_pestania_multimetro()
        self.pestania_calibracion_patron = self.crear_pestania_calibracion_patron()
        self.pestania_historial = self.crear_pestania_historial()
        self.pestania_configuracion = self.crear_pestania_configuracion()

        self.pestanias.addTab(self.pestania_ajuste_escala, "🎯 1. Ajuste Fondo de Escala (100 Ton → 4.75-4.95 V)")
        self.pestanias.addTab(self.pestania_osciloscopio, "📺 2. Ensayo de Calibración en Osciloscopio (0 a 100 Ton)")
        self.pestanias.addTab(self.pestania_multimetro, "📟 3. Modo Multímetro (Promedio 2.0s)")
        self.pestanias.addTab(self.pestania_calibracion_patron, "📐 4. Calibración contra Manómetro Patrón")
        self.pestanias.addTab(self.pestania_historial, "📁 5. Historial de Secuencias Guardadas")
        self.pestanias.addTab(self.pestania_configuracion, "⚙️ 6. Configuración & Canales")

        layout_principal.addWidget(self.pestanias, stretch=1)

        # 3. Barra inferior de estado
        self.etiqueta_estado_global = QLabel(
            "Configuración activa: ai0/ai1 en DIFF, ai2+ en RSE. Excitación del puente = 8.0 V. Listo."
        )
        self.etiqueta_estado_global.setStyleSheet("color: #7aa2f7; font-size: 11px;")
        layout_principal.addWidget(self.etiqueta_estado_global)

    def crear_panel_hardware(self) -> QGroupBox:
        grupo = QGroupBox("Hardware: National Instruments NI-USB-6210 (ai0/ai1: DIFF | ai2+: RSE)")
        layout = QHBoxLayout(grupo)

        self.boton_buscar_tarjeta = QPushButton("🔍 Buscar Tarjeta")
        self.boton_buscar_tarjeta.setMinimumHeight(28)
        self.boton_buscar_tarjeta.setStyleSheet("font-weight: bold; padding: 4px 8px;")
        self.boton_buscar_tarjeta.clicked.connect(self.buscar_tarjetas_nidaq)
        layout.addWidget(self.boton_buscar_tarjeta)

        layout.addWidget(QLabel("Dispositivo:"))
        self.combo_dispositivos = QComboBox()
        self.combo_dispositivos.setMinimumWidth(130)
        self.combo_dispositivos.currentIndexChanged.connect(self.al_cambiar_dispositivo)
        layout.addWidget(self.combo_dispositivos)

        layout.addWidget(QLabel("Canal Monitoreado:"))
        self.combo_canal_monitoreado = QComboBox()
        self.combo_canal_monitoreado.setMinimumWidth(180)
        self.actualizar_combo_canales_monitoreo()
        self.combo_canal_monitoreado.currentIndexChanged.connect(self.al_cambiar_canal_monitoreado)
        layout.addWidget(self.combo_canal_monitoreado)

        self.boton_conectar = QPushButton("🔌 Enlazar")
        self.boton_conectar.setStyleSheet("background-color: #2c3e50; color: white; font-weight: bold;")
        self.boton_conectar.clicked.connect(self.conectar_tarjeta)
        layout.addWidget(self.boton_conectar)

        self.check_modo_simulacion = QCheckBox("Modo Simulación (Puente 8V)")
        self.check_modo_simulacion.toggled.connect(self.al_alternar_simulacion)
        layout.addWidget(self.check_modo_simulacion)

        layout.addStretch()

        self.indicador_hardware = QLabel("ESTADO: Desconectado")
        self.indicador_hardware.setStyleSheet(
            "font-weight: bold; color: #e74c3c; padding: 4px 10px; background-color: #fadbd8; border-radius: 4px;"
        )
        layout.addWidget(self.indicador_hardware)

        return grupo

    def actualizar_combo_canales_monitoreo(self) -> None:
        self.combo_canal_monitoreado.clear()
        for c in self.canales:
            texto = f"{c.nombre} [{c.modo_terminal}] — {c.etiqueta}"
            self.combo_canal_monitoreado.addItem(texto, c.nombre)
        self.combo_canal_monitoreado.setCurrentIndex(0)

    # =========================================================================
    # GESTIÓN DE SESIONES DE CALIBRACIÓN
    # =========================================================================

    def crear_panel_sesion(self) -> QGroupBox:
        grupo = QGroupBox("Sesión de Calibración Activa (Registros Organizados en Carpetas por Sesión)")
        layout = QHBoxLayout(grupo)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        layout.addWidget(QLabel("<b>📁 Carpeta de Sesión:</b>"))
        self.label_sesion_activa = QLabel(f"{self.id_sesion_actual}  [{self.nombre_sesion_actual}]")
        self.label_sesion_activa.setStyleSheet(
            "font-weight: bold; color: #00f2fe; padding: 4px 10px; background-color: #0b192c; "
            "border: 1px solid #1f6feb; border-radius: 4px; font-family: Consolas, monospace;"
        )
        layout.addWidget(self.label_sesion_activa, stretch=1)

        self.boton_nueva_sesion = QPushButton("➕ Iniciar Nueva Sesión...")
        self.boton_nueva_sesion.setStyleSheet(
            "background-color: #1f6feb; color: white; font-weight: bold; padding: 4px 10px;"
        )
        self.boton_nueva_sesion.clicked.connect(self.solicitar_nueva_sesion_ui)
        layout.addWidget(self.boton_nueva_sesion)

        self.boton_abrir_carpeta_sesion = QPushButton("📂 Abrir Carpeta de Sesión")
        self.boton_abrir_carpeta_sesion.setStyleSheet("padding: 4px 10px; font-weight: bold;")
        self.boton_abrir_carpeta_sesion.clicked.connect(self.abrir_carpeta_sesion_actual)
        layout.addWidget(self.boton_abrir_carpeta_sesion)

        self.boton_abrir_todas_sesiones = QPushButton("🗂️ Todas las Sesiones")
        self.boton_abrir_todas_sesiones.setStyleSheet("padding: 4px 8px;")
        self.boton_abrir_todas_sesiones.clicked.connect(self.abrir_carpeta_raiz_sesiones)
        layout.addWidget(self.boton_abrir_todas_sesiones)

        return grupo

    def iniciar_nueva_sesion(self, etiqueta: Optional[str] = None) -> str:
        """
        Crea un subdirectorio exclusivo para la sesión de trabajo y escribe el
        manifiesto metrológico de auditoría correspondiente.
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        limpia_etq = "".join(c for c in (etiqueta or "Calibracion") if c.isalnum() or c in ("_", "-")).strip()
        if not limpia_etq:
            limpia_etq = "Calibracion"

        self.id_sesion_actual = f"sesion_{timestamp}_{limpia_etq}"
        self.nombre_sesion_actual = etiqueta or "Calibración"
        self.tiempo_apertura_sesion = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.carpeta_sesion_actual = os.path.join(self.carpeta_base_secuencias, self.id_sesion_actual)
        os.makedirs(self.carpeta_sesion_actual, exist_ok=True)
        self.carpeta_secuencias = self.carpeta_sesion_actual

        # Escribir manifiesto de inicio de sesión
        self.escribir_manifiesto_sesion_inicial()

        if hasattr(self, "label_sesion_activa"):
            self.label_sesion_activa.setText(f"{self.id_sesion_actual}  [{self.nombre_sesion_actual}]")
        if hasattr(self, "line_carpeta_secuencias"):
            self.line_carpeta_secuencias.setText(self.carpeta_sesion_actual)

        self.registrar_log(f"Nueva sesión de trabajo iniciada: {self.id_sesion_actual}")
        return self.id_sesion_actual

    def solicitar_nueva_sesion_ui(self) -> None:
        if self.secuencia_activa:
            QMessageBox.warning(
                self, "Secuencia en Marcha", "Debe detener el ensayo activo antes de abrir una nueva sesión."
            )
            return

        nombre, ok = QInputDialog.getText(
            self,
            "Nueva Sesión de Ensayos / Calibración",
            "Ingrese un nombre o etiqueta para identificar la nueva sesión de calibración:\n"
            "(Ej: Jornada_Manana, Certificacion_100Ton, Lote_ValvulaA, Repeticion_2)",
            text=f"Calibracion_{datetime.datetime.now().strftime('%H%M')}",
        )
        if ok and nombre.strip():
            self.iniciar_nueva_sesion(etiqueta=nombre.strip())
            QMessageBox.information(
                self,
                "Nueva Sesión Activa",
                f"Se ha inicializado exitosamente la sesión:\n\n{self.id_sesion_actual}\n\n"
                f"Directorio de guardado:\n{self.carpeta_sesion_actual}\n\n"
                "Todos los ensayos continuos, lecturas de multímetro y calibraciones se guardarán en esta carpeta.",
            )

    def abrir_carpeta_sesion_actual(self) -> None:
        if os.path.exists(self.carpeta_sesion_actual):
            os.startfile(self.carpeta_sesion_actual)
        else:
            QMessageBox.warning(self, "Carpeta No Existe", f"No se encontró la carpeta:\n{self.carpeta_sesion_actual}")

    def abrir_carpeta_raiz_sesiones(self) -> None:
        if os.path.exists(self.carpeta_base_secuencias):
            os.startfile(self.carpeta_base_secuencias)

    def escribir_manifiesto_sesion_inicial(self) -> None:
        """Genera el encabezado técnico del manifiesto de sesión para trazabilidad metrológica."""
        ruta_manifiesto = os.path.join(self.carpeta_sesion_actual, "manifiesto_sesion.txt")
        g = self.calcular_ganancia_ina114(self.rg_instalada_referencia)
        lineas = [
            "================================================================================",
            "MANIFIESTO METROLÓGICO DE SESIÓN DE CALIBRACIÓN — PRENSA 100 TONELADAS",
            "================================================================================",
            f"ID de Sesión:              {self.id_sesion_actual}",
            f"Etiqueta / Descripción:    {self.nombre_sesion_actual}",
            f"Fecha y Hora de Apertura:  {self.tiempo_apertura_sesion}",
            f"Directorio de Almacenaje:  {self.carpeta_sesion_actual}",
            "--------------------------------------------------------------------------------",
            "CONFIGURACIÓN DE INSTRUMENTACIÓN Y ADQUISICIÓN:",
            "  • Hardware DAQ:          National Instruments NI-USB-6210 (16 bits)",
            "  • Canal Principal:       ai0 (DIFERENCIAL — Pines AI 0 / AI 8)",
            "  • Canal Secundario:      ai1 (DIFERENCIAL — Pines AI 1 / AI 9)",
            "  • Canales Auxiliares:    ai2 a ai7 (SINGLE-ENDED — Referenciados a AI GND)",
            "  • Preamplificador:       INA114AP [G = 1 + (50 kΩ / Rg)]",
            f"  • Tensión Excitación:    Vexc = {self.v_excitacion_puente:.3f} V (Puente de Wheatstone)",
            f"  • Resistencia Rg Ref.:   Rg = {self.rg_instalada_referencia:.1f} Ω (Ganancia G = {g:.2f})",
            f"  • Ref. Fondo de Escala:  100.0 Ton = {self.v_referencia_100_ton:.4f} V",
            f"  • Sensibilidad Nominal:  {self.sensibilidad_nominal_ton_v:.4f} Ton/V",
            f"  • Frecuencia Fs:         {self.frecuencia_muestreo_fs} Hz",
            f"  • Ventana Osciloscopio:  {self.tiempo_ventana_osciloscopio:.2f} s por bloque promediado",
            f"  • Ventana Multímetro:    {self.tiempo_ventana_multimetro:.2f} s por bloque integrado",
            "================================================================================",
            "REGISTRO CRONOLÓGICO DE ENSAYOS Y ARCHIVOS DE ESTA SESIÓN:",
            "--------------------------------------------------------------------------------",
        ]
        try:
            with open(ruta_manifiesto, "w", encoding="utf-8") as f:
                f.write("\n".join(lineas) + "\n")
        except Exception as e:
            self.registrar_log(f"Error escribiendo manifiesto de sesión: {e}")

    def registrar_secuencia_en_manifiesto(
        self,
        sec_id: int,
        modo: str,
        bloques_prom: int,
        muestras_raw: int,
        duracion: float,
        archivo_prom: str,
        archivo_raw: Optional[str],
        v_medio: float,
    ) -> None:
        """Anexa el registro dual de ensayos (promedios y muestreo real a Fs) al manifiesto de sesión."""
        ruta_manifiesto = os.path.join(self.carpeta_sesion_actual, "manifiesto_sesion.txt")
        c_ton = v_medio * self.sensibilidad_nominal_ton_v
        lineas = [
            f"• Ensayo #{sec_id:03d} | Tipo: {modo:<14} | Hora: {datetime.datetime.now().strftime('%H:%M:%S')} | "
            f"Duración: {duracion:6.1f} s | V_medio: {v_medio:+.4f} V ({c_ton:+.2f} Ton)",
            f"    ├── Secuencia Calibración (Promedios): {archivo_prom} ({bloques_prom} bloques)",
        ]
        if archivo_raw:
            lineas.append(
                f"    └── Secuencia Muestreo Real (Fs = {self.frecuencia_muestreo_fs} Hz): {archivo_raw} ({muestras_raw} muestras)"
            )
        else:
            lineas.append("    └── Secuencia Muestreo Real: No grabada (desactivada)")

        try:
            with open(ruta_manifiesto, "a", encoding="utf-8") as f:
                f.write("\n".join(lineas) + "\n")
        except Exception:
            pass

    # =========================================================================
    # PESTAÑA 1: AJUSTE DE FONDO DE ESCALA (100 Toneladas -> 4.75 a 4.95 V)
    # =========================================================================

    def crear_pestania_ajuste_fondo_escala(self) -> QWidget:
        widget = QWidget()
        layout_principal = QVBoxLayout(widget)
        layout_principal.setContentsMargins(10, 10, 10, 10)
        layout_principal.setSpacing(10)

        # Instrucción Metrológica para el Operador
        instrucciones = QLabel(
            "<b>PROCEDIMIENTO DE AJUSTE DE FONDO DE ESCALA:</b><br>"
            "1. Aplique la carga máxima nominal en la prensa (<b>100 Toneladas</b>).<br>"
            "2. Ajuste la ganancia del INA114AP variando la resistencia física <b>Rg</b> hasta que la tensión medida "
            "se ubique en la ventana óptima de <b>4.75 V a 4.95 V</b>.<br>"
            "3. Mida e ingrese el valor en Ohmios de la resistencia colocada (Rg) y presione <b>'Fijar Referencia 100 Toneladas'</b>."
        )
        instrucciones.setStyleSheet(
            "background-color: #1e272e; color: #d2dae2; padding: 10px; border-radius: 6px; font-size: 12px;"
        )
        layout_principal.addWidget(instrucciones)

        # Panel de Lectura y Semáforo de la Ventana Óptima [4.75 V - 4.95 V]
        grupo_semaforo = QGroupBox("Monitoreo en Tiempo Real de Fondo de Escala (Canal ai0 DIFF)")
        layout_sem = QVBoxLayout(grupo_semaforo)

        self.display_voltaje_fondo_escala = QLabel("+0.000000 V")
        self.display_voltaje_fondo_escala.setAlignment(Qt.AlignCenter)
        self.display_voltaje_fondo_escala.setStyleSheet(
            "font-size: 64px; font-weight: bold; color: #00f2fe; font-family: Consolas, monospace; "
            "background-color: #0b0c10; padding: 20px; border: 2px solid #1f2833; border-radius: 8px;"
        )
        layout_sem.addWidget(self.display_voltaje_fondo_escala)

        # Indicador de estado de la ventana objetivo
        self.label_estado_ventana_objetivo = QLabel("ZONA: Tensión fuera del rango objetivo (Ajuste Rg)")
        self.label_estado_ventana_objetivo.setAlignment(Qt.AlignCenter)
        self.label_estado_ventana_objetivo.setStyleSheet(
            "font-size: 15px; font-weight: bold; color: #f1c40f; padding: 8px; background-color: #2c3e50; border-radius: 6px;"
        )
        layout_sem.addWidget(self.label_estado_ventana_objetivo)

        # Barra de progreso visual que mapea de 0.0 V a 5.0 V
        self.barra_nivel_fondo_escala = QProgressBar()
        self.barra_nivel_fondo_escala.setRange(0, 5000)  # en mV (0 a 5000 mV)
        self.barra_nivel_fondo_escala.setValue(0)
        self.barra_nivel_fondo_escala.setTextVisible(True)
        self.barra_nivel_fondo_escala.setFormat("%v mV / 5000 mV (Zona óptima: 4750 mV a 4950 mV)")
        layout_sem.addWidget(self.barra_nivel_fondo_escala)

        layout_principal.addWidget(grupo_semaforo)

        # Formulario de Referenciación y Fijación
        grupo_fijar = QGroupBox("Registro de Parámetros de Fondo de Escala y Resistencia Rg Colocada")
        grid_fijar = QGridLayout(grupo_fijar)

        grid_fijar.addWidget(QLabel("Carga Máxima Nominal:"), 0, 0)
        self.spin_carga_max_nominal = QDoubleSpinBox()
        self.spin_carga_max_nominal.setRange(1.0, 10000.0)
        self.spin_carga_max_nominal.setValue(100.0)
        self.spin_carga_max_nominal.setDecimals(1)
        self.spin_carga_max_nominal.setSuffix(" Toneladas")
        grid_fijar.addWidget(self.spin_carga_max_nominal, 0, 1)

        grid_fijar.addWidget(QLabel("Resistencia Rg Colocada (Medida):"), 0, 2)
        self.spin_rg_colocada = QDoubleSpinBox()
        self.spin_rg_colocada.setRange(1.0, 100000.0)
        self.spin_rg_colocada.setValue(1000.0)
        self.spin_rg_colocada.setDecimals(1)
        self.spin_rg_colocada.setSuffix(" Ω (Pines 1 y 8)")
        grid_fijar.addWidget(self.spin_rg_colocada, 0, 3)

        self.boton_fijar_referencia_100ton = QPushButton("📌 Fijar Referencia de Fondo de Escala (100 Ton)")
        self.boton_fijar_referencia_100ton.setMinimumHeight(38)
        self.boton_fijar_referencia_100ton.setStyleSheet(
            "background-color: #2ed573; color: white; font-weight: bold; font-size: 13px;"
        )
        self.boton_fijar_referencia_100ton.clicked.connect(self.fijar_referencia_fondo_escala)
        grid_fijar.addWidget(self.boton_fijar_referencia_100ton, 1, 0, 1, 4)

        self.label_info_referencia_fijada = QLabel("Estado de Referencia: No fijada aún (pendiente de calibrar)")
        self.label_info_referencia_fijada.setStyleSheet("font-size: 13px; font-weight: bold; color: #a4b0be;")
        grid_fijar.addWidget(self.label_info_referencia_fijada, 2, 0, 1, 4)

        layout_principal.addWidget(grupo_fijar)
        layout_principal.addStretch()

        return widget

    def fijar_referencia_fondo_escala(self) -> None:
        """Registra el punto de 100 Toneladas y la resistencia física colocada."""
        v_actual = getattr(self, "ultimo_voltaje_ai0", 0.0)
        carga_max = self.spin_carga_max_nominal.value()
        rg_medida = self.spin_rg_colocada.value()

        if v_actual <= 0.5:
            r = QMessageBox.question(
                self,
                "Voltaje Bajo",
                f"El voltaje actual ({v_actual:+.4f} V) es muy bajo para 100 Toneladas.\n¿Desea fijarlo de todas formas?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if r == QMessageBox.No:
                return

        self.v_referencia_100_ton = v_actual
        self.carga_maxima_nominal = carga_max
        self.rg_instalada_referencia = rg_medida
        self.rg_ohmios = rg_medida
        self.referencia_100_ton_fijada = True

        g = self.calcular_ganancia_ina114(rg_medida)
        self.sensibilidad_nominal_ton_v = carga_max / v_actual if v_actual > 0 else 1.0

        self.label_info_referencia_fijada.setText(
            f"✓ REFERENCIA FIJADA: {carga_max:.1f} Ton = {v_actual:.4f} V  |  Rg colocada = {rg_medida:.1f} Ω (G = {g:.2f})  |  Sensibilidad = {self.sensibilidad_nominal_ton_v:.3f} Ton/V"
        )
        self.label_info_referencia_fijada.setStyleSheet("font-size: 13px; font-weight: bold; color: #00f2fe;")

        self.registrar_log(
            f"Fondo de Escala Referenciado: {carga_max} Ton -> {v_actual:.4f} V con Rg = {rg_medida} Ω (G = {g:.2f})"
        )
        QMessageBox.information(
            self,
            "Fondo de Escala Fijado",
            f"Se ha referenciado exitosamente:\n\n• Carga Nominal: {carga_max:.1f} Ton\n• Voltaje Medido: {v_actual:.4f} V\n• Rg Colocada: {rg_medida:.1f} Ω\n• Ganancia INA114AP: G = {g:.2f}\n\nPuede descargar la prensa y pasar a la Pestaña 2 para el ensayo en osciloscopio.",
        )

    # =========================================================================
    # PESTAÑA 2: ENSAYO DE CALIBRACIÓN EN OSCILOSCOPIO (0 a 100 Ton)
    # =========================================================================

    def crear_pestania_osciloscopio(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        barra_ctrl = QGroupBox("Control del Ensayo de Calibración Completo (0 a 100 Toneladas) — Bloques de 0.5 s")
        layout_ctrl = QHBoxLayout(barra_ctrl)

        self.boton_iniciar_ensayo_100ton = QPushButton("▶ Iniciar Ensayo (0 a 100 Ton)")
        self.boton_iniciar_ensayo_100ton.setMinimumHeight(36)
        self.boton_iniciar_ensayo_100ton.setStyleSheet(
            "background-color: #2ed573; color: white; font-weight: bold; font-size: 13px; padding: 0 16px;"
        )
        self.boton_iniciar_ensayo_100ton.clicked.connect(lambda: self.iniciar_secuencia("Ensayo100Ton"))
        layout_ctrl.addWidget(self.boton_iniciar_ensayo_100ton)

        self.boton_parar_ensayo_100ton = QPushButton("⏹ Finalizar Ensayo")
        self.boton_parar_ensayo_100ton.setMinimumHeight(36)
        self.boton_parar_ensayo_100ton.setStyleSheet(
            "background-color: #ff4757; color: white; font-weight: bold; font-size: 13px; padding: 0 16px;"
        )
        self.boton_parar_ensayo_100ton.setEnabled(False)
        self.boton_parar_ensayo_100ton.clicked.connect(self.detener_secuencia)
        layout_ctrl.addWidget(self.boton_parar_ensayo_100ton)

        self.boton_tara_osc = QPushButton("⚖️ Poner a Cero en Carga Mínima (Tara)")
        self.boton_tara_osc.setMinimumHeight(36)
        self.boton_tara_osc.setStyleSheet("background-color: #34495e; color: white; font-weight: bold;")
        self.boton_tara_osc.clicked.connect(self.establecer_tara_cero)
        layout_ctrl.addWidget(self.boton_tara_osc)

        layout_ctrl.addStretch()

        # Selector de Unidad para el Gráfico (Voltios vs Toneladas)
        layout_ctrl.addWidget(QLabel("Visualizar en:"))
        self.radio_ver_toneladas = QRadioButton("Toneladas (Ton)")
        self.radio_ver_toneladas.setChecked(True)
        self.radio_ver_toneladas.toggled.connect(self.al_cambiar_unidad_grafica_osc)
        layout_ctrl.addWidget(self.radio_ver_toneladas)

        self.radio_ver_voltios = QRadioButton("Voltios (V)")
        self.radio_ver_voltios.toggled.connect(self.al_cambiar_unidad_grafica_osc)
        layout_ctrl.addWidget(self.radio_ver_voltios)

        # Checkbox de Grabación Dual (Promedios + Real a Fs)
        self.check_guardar_raw_osc = QCheckBox("Dual: Muestreo Real Fs (1000 Hz)")
        self.check_guardar_raw_osc.setChecked(True)
        self.check_guardar_raw_osc.setStyleSheet("font-weight: bold; color: #00f2fe; padding-left: 6px;")
        self.check_guardar_raw_osc.setToolTip(
            "Grabación simultánea de dos secuencias:\n"
            "• Secuencia 1: Calibración por promedios de bloque (0.5 s)\n"
            "• Secuencia 2: Muestreo real continuo a frecuencia de tarjeta (1000 Hz)"
        )
        self.check_guardar_raw_osc.toggled.connect(self.al_alternar_guardar_raw)
        layout_ctrl.addWidget(self.check_guardar_raw_osc)

        self.display_valor_osc_ensayo = QLabel("Carga Actual: 0.00 Ton (+0.000 V)")
        self.display_valor_osc_ensayo.setStyleSheet(
            "font-size: 15px; font-weight: bold; color: #2ed573; padding: 4px 12px; background-color: #1e272e; border-radius: 4px;"
        )
        layout_ctrl.addWidget(self.display_valor_osc_ensayo)

        layout.addWidget(barra_ctrl)

        # Barra de Escalabilidad: Amplitud (Eje Y) y Tiempo (Eje X)
        barra_escalas = self.crear_barra_escalas_osciloscopio()
        layout.addWidget(barra_escalas)

        # Gráfico Osciloscopio pyqtgraph
        self.grafico_osciloscopio_ensayo = pg.PlotWidget()
        self.grafico_osciloscopio_ensayo.setTitle(
            "<span style='color: #2ed573; font-size: 14px; font-weight: bold;'>Curva de Ensayo Continuo: 0 a 100 Toneladas (Promedios cada 0.5 s)</span>"
        )
        self.grafico_osciloscopio_ensayo.setLabel("left", "Carga en Prensa", units="Ton")
        self.grafico_osciloscopio_ensayo.setLabel("bottom", "Tiempo de Ensayo", units="s")
        self.grafico_osciloscopio_ensayo.showGrid(x=True, y=True, alpha=0.3)
        self.grafico_osciloscopio_ensayo.addLegend(offset=(10, 10))

        self.curva_osciloscopio_ensayo = self.grafico_osciloscopio_ensayo.plot(
            pen=pg.mkPen(color="#2ed573", width=2),
            symbol="o",
            symbolSize=4,
            symbolBrush="#2ed573",
            name="Curva Promediada (0.5s)",
        )
        layout.addWidget(self.grafico_osciloscopio_ensayo, stretch=1)

        return widget

    def crear_barra_escalas_osciloscopio(self) -> QGroupBox:
        barra_escalas = QGroupBox("Escalabilidad del Osciloscopio — Amplitud (Eje Y) y Tiempo (Eje X)")
        layout_escalas = QHBoxLayout(barra_escalas)
        layout_escalas.setContentsMargins(8, 4, 8, 4)
        layout_escalas.setSpacing(8)

        # --- Subgrupo Eje Y (Amplitud) ---
        layout_escalas.addWidget(QLabel("<b>Amplitud (Y):</b>"))
        self.check_auto_escala_y = QCheckBox("Auto Y")
        self.check_auto_escala_y.setChecked(True)
        self.check_auto_escala_y.toggled.connect(self.al_alternar_auto_escala_y)
        layout_escalas.addWidget(self.check_auto_escala_y)

        self.combo_preset_y = QComboBox()
        self.combo_preset_y.setMinimumWidth(130)
        layout_escalas.addWidget(self.combo_preset_y)

        layout_escalas.addWidget(QLabel("Mín:"))
        self.spin_y_min = QDoubleSpinBox()
        self.spin_y_min.setRange(-100.0, 1000.0)
        self.spin_y_min.setValue(0.0)
        self.spin_y_min.setDecimals(1)
        self.spin_y_min.setEnabled(False)
        self.spin_y_min.valueChanged.connect(self.al_cambiar_spin_y_manual)
        layout_escalas.addWidget(self.spin_y_min)

        layout_escalas.addWidget(QLabel("Máx:"))
        self.spin_y_max = QDoubleSpinBox()
        self.spin_y_max.setRange(0.05, 2000.0)
        self.spin_y_max.setValue(120.0)
        self.spin_y_max.setDecimals(1)
        self.spin_y_max.setEnabled(False)
        self.spin_y_max.valueChanged.connect(self.al_cambiar_spin_y_manual)
        layout_escalas.addWidget(self.spin_y_max)

        self.boton_auto_y = QPushButton("🔄 Auto Y")
        self.boton_auto_y.setToolTip("Ajustar escala vertical automáticamente a los datos")
        self.boton_auto_y.setStyleSheet("font-size: 11px; padding: 2px 8px;")
        self.boton_auto_y.clicked.connect(self.forzar_auto_y)
        layout_escalas.addWidget(self.boton_auto_y)

        # Separador vertical
        separador = QFrame()
        separador.setFrameShape(QFrame.VLine)
        separador.setFrameShadow(QFrame.Sunken)
        layout_escalas.addWidget(separador)

        # --- Subgrupo Eje X (Tiempo) ---
        layout_escalas.addWidget(QLabel("<b>Tiempo (X):</b>"))
        self.combo_preset_x = QComboBox()
        self.combo_preset_x.setMinimumWidth(160)
        self.combo_preset_x.addItem("Ver Todo el Ensayo (0 a t)", "todo")
        self.combo_preset_x.addItem("Últimos 15 s", 15.0)
        self.combo_preset_x.addItem("Últimos 30 s", 30.0)
        self.combo_preset_x.addItem("Últimos 60 s (1 min)", 60.0)
        self.combo_preset_x.addItem("Últimos 120 s (2 min)", 120.0)
        self.combo_preset_x.addItem("Últimos 300 s (5 min)", 300.0)
        self.combo_preset_x.addItem("Personalizado", "custom")
        self.combo_preset_x.currentIndexChanged.connect(self.al_cambiar_preset_x)
        layout_escalas.addWidget(self.combo_preset_x)

        self.spin_ventana_x = QDoubleSpinBox()
        self.spin_ventana_x.setRange(2.0, 7200.0)
        self.spin_ventana_x.setValue(60.0)
        self.spin_ventana_x.setDecimals(1)
        self.spin_ventana_x.setSuffix(" s")
        self.spin_ventana_x.setEnabled(False)
        self.spin_ventana_x.valueChanged.connect(self.al_cambiar_spin_x_manual)
        layout_escalas.addWidget(self.spin_ventana_x)

        self.boton_ver_todo_x = QPushButton("🔍 Ver Todo (X)")
        self.boton_ver_todo_x.setToolTip("Restablecer vista para ver todo el ensayo desde t = 0")
        self.boton_ver_todo_x.setStyleSheet("font-size: 11px; padding: 2px 8px;")
        self.boton_ver_todo_x.clicked.connect(self.forzar_ver_todo_x)
        layout_escalas.addWidget(self.boton_ver_todo_x)

        # Poblar lista desplegable de Y según la unidad activa
        self.poblar_presets_y()
        self.combo_preset_y.currentIndexChanged.connect(self.al_cambiar_preset_y)

        return barra_escalas

    def poblar_presets_y(self) -> None:
        self.combo_preset_y.blockSignals(True)
        self.combo_preset_y.clear()
        if self.radio_ver_toneladas.isChecked():
            self.combo_preset_y.addItem("Auto (Dinámico)", "auto")
            self.combo_preset_y.addItem("0 a 20 Ton", (0.0, 20.0))
            self.combo_preset_y.addItem("0 a 50 Ton", (0.0, 50.0))
            self.combo_preset_y.addItem("0 a 100 Ton", (0.0, 100.0))
            self.combo_preset_y.addItem("0 a 120 Ton", (0.0, 120.0))
            self.combo_preset_y.addItem("Manual", "manual")
            self.spin_y_min.setSuffix(" Ton")
            self.spin_y_max.setSuffix(" Ton")
            self.spin_y_min.setRange(-50.0, 500.0)
            self.spin_y_max.setRange(0.1, 1000.0)
            if not self.auto_escala_y:
                self.spin_y_min.setValue(self.y_min_manual)
                self.spin_y_max.setValue(self.y_max_manual)
        else:
            self.combo_preset_y.addItem("Auto (Dinámico)", "auto")
            self.combo_preset_y.addItem("0 a 1.0 V", (0.0, 1.0))
            self.combo_preset_y.addItem("0 a 2.5 V", (0.0, 2.5))
            self.combo_preset_y.addItem("0 a 5.0 V", (0.0, 5.0))
            self.combo_preset_y.addItem("0 a 10.0 V", (0.0, 10.0))
            self.combo_preset_y.addItem("Manual", "manual")
            self.spin_y_min.setSuffix(" V")
            self.spin_y_max.setSuffix(" V")
            self.spin_y_min.setRange(-1.0, 15.0)
            self.spin_y_max.setRange(0.01, 20.0)
            if not self.auto_escala_y:
                self.spin_y_min.setValue(self.y_min_manual)
                self.spin_y_max.setValue(self.y_max_manual)

        self.combo_preset_y.setCurrentIndex(0 if self.auto_escala_y else self.combo_preset_y.count() - 1)
        self.combo_preset_y.blockSignals(False)

    def al_alternar_auto_escala_y(self, activo: bool) -> None:
        self.auto_escala_y = activo
        self.spin_y_min.setEnabled(not activo)
        self.spin_y_max.setEnabled(not activo)
        if activo:
            self.combo_preset_y.blockSignals(True)
            self.combo_preset_y.setCurrentIndex(0)
            self.combo_preset_y.blockSignals(False)
            self.grafico_osciloscopio_ensayo.enableAutoRange(axis="y")
        else:
            self.aplicar_escala_y_actual()

    def al_cambiar_preset_y(self) -> None:
        dato = self.combo_preset_y.currentData()
        if dato == "auto":
            self.check_auto_escala_y.setChecked(True)
        elif dato == "manual":
            self.check_auto_escala_y.setChecked(False)
            self.aplicar_escala_y_actual()
        elif isinstance(dato, (tuple, list)):
            self.check_auto_escala_y.setChecked(False)
            self.y_min_manual = float(dato[0])
            self.y_max_manual = float(dato[1])
            self.spin_y_min.setValue(self.y_min_manual)
            self.spin_y_max.setValue(self.y_max_manual)
            self.aplicar_escala_y_actual()

    def al_cambiar_spin_y_manual(self) -> None:
        if not self.auto_escala_y:
            self.y_min_manual = self.spin_y_min.value()
            self.y_max_manual = max(self.y_min_manual + 0.1, self.spin_y_max.value())
            self.aplicar_escala_y_actual()

    def forzar_auto_y(self) -> None:
        self.check_auto_escala_y.setChecked(True)
        self.grafico_osciloscopio_ensayo.enableAutoRange(axis="y")

    def aplicar_escala_y_actual(self) -> None:
        if not self.auto_escala_y:
            self.grafico_osciloscopio_ensayo.disableAutoRange(axis="y")
            self.grafico_osciloscopio_ensayo.setYRange(self.y_min_manual, self.y_max_manual, padding=0.02)
        else:
            self.grafico_osciloscopio_ensayo.enableAutoRange(axis="y")

    def al_cambiar_preset_x(self) -> None:
        dato = self.combo_preset_x.currentData()
        if dato == "todo":
            self.modo_tiempo_x = "Todo"
            self.spin_ventana_x.setEnabled(False)
        elif dato == "custom":
            self.modo_tiempo_x = "Ventana"
            self.spin_ventana_x.setEnabled(True)
            self.segundos_ventana_visible = self.spin_ventana_x.value()
        else:
            self.modo_tiempo_x = "Ventana"
            self.spin_ventana_x.setEnabled(False)
            self.segundos_ventana_visible = float(dato)
            self.spin_ventana_x.setValue(self.segundos_ventana_visible)
        self.aplicar_escalas_grafico_osc()

    def al_cambiar_spin_x_manual(self) -> None:
        if self.modo_tiempo_x == "Ventana" and self.combo_preset_x.currentData() == "custom":
            self.segundos_ventana_visible = self.spin_ventana_x.value()
            self.aplicar_escalas_grafico_osc()

    def forzar_ver_todo_x(self) -> None:
        self.combo_preset_x.setCurrentIndex(0)

    def aplicar_escalas_grafico_osc(self) -> None:
        if not self.tiempos_grafica:
            return

        t_actual = self.tiempos_grafica[-1]

        # Eje X (Tiempo)
        if self.modo_tiempo_x == "Todo":
            t_max = max(t_actual * 1.02, 5.0)
            self.grafico_osciloscopio_ensayo.setXRange(0.0, t_max, padding=0.01)
        else:
            v_seg = self.segundos_ventana_visible
            t_min = max(0.0, t_actual - v_seg)
            t_max = max(t_min + v_seg, t_actual + 0.5)
            self.grafico_osciloscopio_ensayo.setXRange(t_min, t_max, padding=0.01)

        # Eje Y (Amplitud)
        self.aplicar_escala_y_actual()

    def al_cambiar_unidad_grafica_osc(self) -> None:
        if self.radio_ver_toneladas.isChecked():
            self.grafico_osciloscopio_ensayo.setLabel("left", "Carga en Prensa", units="Ton")
        else:
            self.grafico_osciloscopio_ensayo.setLabel("left", "Tensión de Salida INA114", units="V")
        self.poblar_presets_y()
        self.forzar_auto_y()
        self.refrescar_curva_osciloscopio()

    def refrescar_curva_osciloscopio(self) -> None:
        if not self.tiempos_grafica:
            return
        if self.radio_ver_toneladas.isChecked():
            self.curva_osciloscopio_ensayo.setData(list(self.tiempos_grafica), list(self.cargas_grafica))
        else:
            self.curva_osciloscopio_ensayo.setData(list(self.tiempos_grafica), list(self.voltajes_grafica))
        self.aplicar_escalas_grafico_osc()

    def al_alternar_guardar_raw(self, estado: bool) -> None:
        self.guardar_muestreo_real_fs = estado
        if hasattr(self, "check_guardar_raw_osc") and self.check_guardar_raw_osc.isChecked() != estado:
            self.check_guardar_raw_osc.blockSignals(True)
            self.check_guardar_raw_osc.setChecked(estado)
            self.check_guardar_raw_osc.blockSignals(False)
        if hasattr(self, "check_guardar_raw_multi") and self.check_guardar_raw_multi.isChecked() != estado:
            self.check_guardar_raw_multi.blockSignals(True)
            self.check_guardar_raw_multi.setChecked(estado)
            self.check_guardar_raw_multi.blockSignals(False)
        if hasattr(self, "check_guardar_raw_config") and self.check_guardar_raw_config.isChecked() != estado:
            self.check_guardar_raw_config.blockSignals(True)
            self.check_guardar_raw_config.setChecked(estado)
            self.check_guardar_raw_config.blockSignals(False)
        modo_txt = "ACTIVADA" if estado else "DESACTIVADA"
        self.registrar_log(f"Grabación simultánea de Señal Real a Fs ({self.frecuencia_muestreo_fs} Hz): {modo_txt}")

    # =========================================================================
    # PESTAÑA 3: MODO MULTÍMETRO (2.0 s por defecto)
    # =========================================================================

    def crear_pestania_multimetro(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(8)

        barra_ctrl = QGroupBox("Control de Secuencia — Modo Multímetro (Promedio Integrado de 2.0 s)")
        layout_ctrl = QHBoxLayout(barra_ctrl)

        self.boton_iniciar_multimetro = QPushButton("▶ Iniciar Secuencia (Multímetro)")
        self.boton_iniciar_multimetro.setMinimumHeight(34)
        self.boton_iniciar_multimetro.setStyleSheet(
            "background-color: #2ed573; color: white; font-weight: bold; font-size: 12px; padding: 0 14px;"
        )
        self.boton_iniciar_multimetro.clicked.connect(lambda: self.iniciar_secuencia("Multimetro"))
        layout_ctrl.addWidget(self.boton_iniciar_multimetro)

        self.boton_parar_multimetro = QPushButton("⏹ Parar Secuencia")
        self.boton_parar_multimetro.setMinimumHeight(34)
        self.boton_parar_multimetro.setStyleSheet(
            "background-color: #ff4757; color: white; font-weight: bold; font-size: 12px; padding: 0 14px;"
        )
        self.boton_parar_multimetro.setEnabled(False)
        self.boton_parar_multimetro.clicked.connect(self.detener_secuencia)
        layout_ctrl.addWidget(self.boton_parar_multimetro)

        self.boton_tara_multi = QPushButton("⚖️ Poner a Cero (Tara)")
        self.boton_tara_multi.setMinimumHeight(34)
        self.boton_tara_multi.setStyleSheet("background-color: #34495e; color: white; font-weight: bold;")
        self.boton_tara_multi.clicked.connect(self.establecer_tara_cero)
        layout_ctrl.addWidget(self.boton_tara_multi)

        self.check_guardar_raw_multi = QCheckBox("Dual: Muestreo Real Fs (1000 Hz)")
        self.check_guardar_raw_multi.setChecked(True)
        self.check_guardar_raw_multi.setStyleSheet("font-weight: bold; color: #00f2fe; padding-left: 6px;")
        self.check_guardar_raw_multi.toggled.connect(self.al_alternar_guardar_raw)
        layout_ctrl.addWidget(self.check_guardar_raw_multi)

        layout_ctrl.addStretch()
        layout.addWidget(barra_ctrl)

        # Display Numérico Digital de Gran Formato
        panel_disp = QGroupBox("Display Numérico Digital (Promedio de Integración en Bloque)")
        layout_disp = QVBoxLayout(panel_disp)

        self.lcd_multimetro = QLabel("+0.000000 V")
        self.lcd_multimetro.setAlignment(Qt.AlignCenter)
        self.lcd_multimetro.setStyleSheet(
            "font-size: 58px; font-weight: bold; color: #00f2fe; font-family: Consolas, monospace; "
            "background-color: #0b0c10; padding: 25px; border: 2px solid #1f2833; border-radius: 8px;"
        )
        layout_disp.addWidget(self.lcd_multimetro)

        self.lcd_toneladas_multi = QLabel("0.00 Toneladas")
        self.lcd_toneladas_multi.setAlignment(Qt.AlignCenter)
        self.lcd_toneladas_multi.setStyleSheet(
            "font-size: 32px; font-weight: bold; color: #f1c40f; padding: 8px; background-color: #1e272e; border-radius: 6px;"
        )
        layout_disp.addWidget(self.lcd_toneladas_multi)

        layout_indicadores = QHBoxLayout()
        self.label_puente_mv_multi = QLabel("Tensión Puente (Vin): 0.0000 mV")
        self.label_puente_mv_multi.setStyleSheet("font-size: 13px; font-weight: bold; color: #e056fd; padding: 4px;")

        self.label_ruido_multi = QLabel("Ruido Vpp en Bloque: 0.000 mV")
        self.label_ruido_multi.setStyleSheet("font-size: 13px; font-weight: bold; color: #ff9f43; padding: 4px;")

        self.label_sigma_multi = QLabel("Desv. Estándar (σ): 0.000 mV")
        self.label_sigma_multi.setStyleSheet("font-size: 13px; font-weight: bold; color: #c8d6e5; padding: 4px;")

        layout_indicadores.addWidget(self.label_puente_mv_multi)
        layout_indicadores.addWidget(self.label_ruido_multi)
        layout_indicadores.addWidget(self.label_sigma_multi)

        layout_disp.addLayout(layout_indicadores)
        layout.addWidget(panel_disp, stretch=1)

        return widget

    # =========================================================================
    # PESTAÑA 4: CALIBRACIÓN CONTRA MANÓMETRO PATRÓN
    # =========================================================================

    def crear_pestania_calibracion_patron(self) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(6, 6, 6, 6)

        divisor = QSplitter(Qt.Horizontal)

        panel_izq = QWidget()
        layout_izq = QVBoxLayout(panel_izq)
        layout_izq.setContentsMargins(0, 0, 0, 0)
        layout_izq.setSpacing(6)

        grupo_reg = QGroupBox("Registro de Puntos de Calibración contra Medida Patrón")
        layout_reg = QVBoxLayout(grupo_reg)

        fila_patron = QHBoxLayout()
        fila_patron.addWidget(QLabel("Carga Patrón en Prensa:"))

        self.spin_presion_patron = QDoubleSpinBox()
        self.spin_presion_patron.setRange(-500.0, 50000.0)
        self.spin_presion_patron.setValue(0.0)
        self.spin_presion_patron.setDecimals(2)
        fila_patron.addWidget(self.spin_presion_patron)

        self.combo_unidad_patron = QComboBox()
        self.combo_unidad_patron.addItems(["Ton", "bar", "psi", "kN", "kg/cm²"])
        self.combo_unidad_patron.currentIndexChanged.connect(self.al_cambiar_unidad_patron)
        fila_patron.addWidget(self.combo_unidad_patron)

        self.boton_capturar_punto_patron = QPushButton("📥 Capturar Punto con Valor Actual")
        self.boton_capturar_punto_patron.setStyleSheet("background-color: #1e90ff; color: white; font-weight: bold;")
        self.boton_capturar_punto_patron.clicked.connect(self.capturar_punto_calibracion)
        fila_patron.addWidget(self.boton_capturar_punto_patron)

        layout_reg.addLayout(fila_patron)

        self.tabla_calibracion_patron = QTableWidget()
        self.tabla_calibracion_patron.setColumnCount(7)
        self.tabla_calibracion_patron.setHorizontalHeaderLabels([
            "Pto #", "Carga Patrón", "Unidad", "V Promedio (V)", "Vin Puente (mV)", "Rg (Ω)", "Ganancia G"
        ])
        self.tabla_calibracion_patron.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla_calibracion_patron.setAlternatingRowColors(True)
        layout_reg.addWidget(self.tabla_calibracion_patron)

        acciones_reg = QHBoxLayout()
        self.boton_calcular_regresion = QPushButton("📐 Calcular Regresión Lineal (y = m·x + b)")
        self.boton_calcular_regresion.setStyleSheet("background-color: #8e44ad; color: white; font-weight: bold;")
        self.boton_calcular_regresion.clicked.connect(self.calcular_regresion_lineal)
        acciones_reg.addWidget(self.boton_calcular_regresion)

        self.boton_guardar_calibracion_sesion = QPushButton("💾 Guardar Calibración en Sesión")
        self.boton_guardar_calibracion_sesion.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold;")
        self.boton_guardar_calibracion_sesion.clicked.connect(self.guardar_calibracion_patron_sesion)
        acciones_reg.addWidget(self.boton_guardar_calibracion_sesion)

        self.boton_limpiar_tabla_patron = QPushButton("🗑 Limpiar Tabla")
        self.boton_limpiar_tabla_patron.clicked.connect(self.limpiar_tabla_patron)
        acciones_reg.addWidget(self.boton_limpiar_tabla_patron)

        layout_reg.addLayout(acciones_reg)

        self.label_resultado_ecuacion = QLabel("Ecuación: Carga = (---) · V_medido + (---)  |  R² = ---")
        self.label_resultado_ecuacion.setStyleSheet(
            "font-size: 13px; font-weight: bold; color: #f1c40f; padding: 6px; background-color: #1e272e; border-radius: 4px;"
        )
        layout_reg.addWidget(self.label_resultado_ecuacion)

        layout_izq.addWidget(grupo_reg)

        panel_der = QWidget()
        layout_der = QVBoxLayout(panel_der)
        layout_der.setContentsMargins(0, 0, 0, 0)

        self.grafico_calibracion_xy = pg.PlotWidget()
        self.grafico_calibracion_xy.setTitle(
            "<span style='color: #f1c40f; font-size: 13px; font-weight: bold;'>Curva de Calibración: Carga Patrón vs. Voltaje Promedio</span>"
        )
        self.grafico_calibracion_xy.setLabel("bottom", "Voltaje Promedio Medido", units="V")
        self.grafico_calibracion_xy.setLabel("left", "Carga Patrón", units="Ton")
        self.grafico_calibracion_xy.showGrid(x=True, y=True, alpha=0.3)
        self.grafico_calibracion_xy.addLegend(offset=(10, 10))

        self.curva_puntos_patron = pg.ScatterPlotItem(
            size=10, pen=pg.mkPen(None), brush=pg.mkBrush(255, 215, 0, 230), symbol="o", name="Puntos Medidos"
        )
        self.grafico_calibracion_xy.addItem(self.curva_puntos_patron)

        self.curva_linea_ajuste = self.grafico_calibracion_xy.plot(
            [], [], pen=pg.mkPen(color="#00ffff", width=2, style=Qt.DashLine), name="Recta de Calibración"
        )
        layout_der.addWidget(self.grafico_calibracion_xy)

        divisor.addWidget(panel_izq)
        divisor.addWidget(panel_der)
        divisor.setStretchFactor(0, 5)
        divisor.setStretchFactor(1, 5)

        layout.addWidget(divisor)
        return widget

    # =========================================================================
    # PESTAÑA 5: HISTORIAL DE SECUENCIAS GUARDADAS
    # =========================================================================

    def crear_pestania_historial(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        barra_hist = QHBoxLayout()
        self.boton_abrir_carpeta_secuencias = QPushButton("📂 Abrir Carpeta de Sesión Actual")
        self.boton_abrir_carpeta_secuencias.setStyleSheet("font-weight: bold; padding: 6px 12px;")
        self.boton_abrir_carpeta_secuencias.clicked.connect(self.abrir_carpeta_sesion_actual)
        barra_hist.addWidget(self.boton_abrir_carpeta_secuencias)

        self.boton_abrir_raiz_hist = QPushButton("🗂️ Ver Raíz de Todas las Sesiones")
        self.boton_abrir_raiz_hist.setStyleSheet("padding: 6px 10px;")
        self.boton_abrir_raiz_hist.clicked.connect(self.abrir_carpeta_raiz_sesiones)
        barra_hist.addWidget(self.boton_abrir_raiz_hist)

        self.boton_nueva_sesion_hist = QPushButton("➕ Iniciar Nueva Sesión...")
        self.boton_nueva_sesion_hist.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 6px 12px;")
        self.boton_nueva_sesion_hist.clicked.connect(self.solicitar_nueva_sesion_ui)
        barra_hist.addWidget(self.boton_nueva_sesion_hist)

        barra_hist.addStretch()
        layout.addLayout(barra_hist)

        self.tabla_historial_secuencias = QTableWidget()
        self.tabla_historial_secuencias.setColumnCount(10)
        self.tabla_historial_secuencias.setHorizontalHeaderLabels([
            "ID", "Sesión", "Fecha / Hora", "Tipo", "Bloques (Prom)", "Muestras (Fs)", "Duración (s)", "Voltaje Medio (V)", "CSV Calibración (Prom)", "CSV Señal Bruta (Fs)"
        ])
        self.tabla_historial_secuencias.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla_historial_secuencias.setAlternatingRowColors(True)
        layout.addWidget(self.tabla_historial_secuencias)

        grupo_log = QGroupBox("Registro de Eventos y Auditoría de Calibración")
        layout_log = QVBoxLayout(grupo_log)
        self.caja_log = QTextEdit()
        self.caja_log.setReadOnly(True)
        self.caja_log.setStyleSheet(
            "background-color: #101014; color: #a9b1d6; font-family: Consolas, monospace; font-size: 11px;"
        )
        layout_log.addWidget(self.caja_log)
        layout.addWidget(grupo_log)

        return widget

    # =========================================================================
    # PESTAÑA 6: CONFIGURACIÓN & CANALES (DIFF / RSE)
    # =========================================================================

    def crear_pestania_configuracion(self) -> QWidget:
        widget = QWidget()
        layout_central = QVBoxLayout(widget)
        layout_central.setContentsMargins(8, 8, 8, 8)
        layout_central.setSpacing(8)

        grupo_canales = QGroupBox("1. Asignación de Canales NI-USB-6210 (ai0, ai1 en DIFF | ai2+ en RSE)")
        layout_can = QVBoxLayout(grupo_canales)

        self.tabla_canales = QTableWidget()
        self.tabla_canales.setColumnCount(5)
        self.tabla_canales.setHorizontalHeaderLabels([
            "Hab.", "Canal Físico", "Etiqueta / Sensor", "Modo Terminal", "Rango de Voltaje"
        ])
        self.tabla_canales.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla_canales.setAlternatingRowColors(True)
        layout_can.addWidget(self.tabla_canales)
        self.poblar_tabla_canales_ui()

        nota_canales = QLabel(
            "✓ REGLA DE HARDWARE: Los canales ai0 y ai1 operan en modo DIFERENCIAL (DIFF). "
            "Los canales ai2 en adelante operan en modo SINGLE-ENDED (RSE)."
        )
        nota_canales.setStyleSheet("color: #00f2fe; font-size: 11px; font-weight: bold;")
        layout_can.addWidget(nota_canales)
        layout_central.addWidget(grupo_canales, stretch=1)

        grupo_tiempos = QGroupBox("2. Tiempos de Integración de Ventana y Frecuencia de Muestreo")
        form_tiempos = QFormLayout(grupo_tiempos)

        self.spin_tiempo_osciloscopio = QDoubleSpinBox()
        self.spin_tiempo_osciloscopio.setRange(0.05, 5.0)
        self.spin_tiempo_osciloscopio.setValue(self.tiempo_ventana_osciloscopio)
        self.spin_tiempo_osciloscopio.setDecimals(2)
        self.spin_tiempo_osciloscopio.setSuffix(" s (Refresco de Gráfica)")
        self.spin_tiempo_osciloscopio.valueChanged.connect(self.al_cambiar_tiempos_config)
        form_tiempos.addRow("Ventana Modo Osciloscopio:", self.spin_tiempo_osciloscopio)

        self.spin_tiempo_multimetro = QDoubleSpinBox()
        self.spin_tiempo_multimetro.setRange(0.1, 10.0)
        self.spin_tiempo_multimetro.setValue(self.tiempo_ventana_multimetro)
        self.spin_tiempo_multimetro.setDecimals(2)
        self.spin_tiempo_multimetro.setSuffix(" s (Display Numérico)")
        self.spin_tiempo_multimetro.valueChanged.connect(self.al_cambiar_tiempos_config)
        form_tiempos.addRow("Ventana Modo Multímetro:", self.spin_tiempo_multimetro)

        self.combo_fs = QComboBox()
        self.combo_fs.addItem("500 Hz", 500)
        self.combo_fs.addItem("1000 Hz (Estándar recomendado)", 1000)
        self.combo_fs.addItem("2000 Hz", 2000)
        self.combo_fs.addItem("5000 Hz", 5000)
        self.combo_fs.setCurrentIndex(1)
        self.combo_fs.currentIndexChanged.connect(self.al_cambiar_tiempos_config)
        form_tiempos.addRow("Frecuencia de Muestreo ADC (Fs):", self.combo_fs)

        self.check_guardar_raw_config = QCheckBox(
            "Grabación Dual: Archivo de Calibración (Promedios) + Archivo de Señal Real (Fs)"
        )
        self.check_guardar_raw_config.setChecked(True)
        self.check_guardar_raw_config.setStyleSheet("font-weight: bold; color: #00f2fe;")
        self.check_guardar_raw_config.toggled.connect(self.al_alternar_guardar_raw)
        form_tiempos.addRow("Modo de Almacenamiento:", self.check_guardar_raw_config)

        layout_central.addWidget(grupo_tiempos)

        grupo_ina = QGroupBox("3. Circuito Pre-amplificador INA114AP y Puente de Wheatstone (8 V)")
        form_ina = QFormLayout(grupo_ina)

        self.spin_vexc = QDoubleSpinBox()
        self.spin_vexc.setRange(1.0, 15.0)
        self.spin_vexc.setValue(self.v_excitacion_puente)
        self.spin_vexc.setDecimals(2)
        self.spin_vexc.setSuffix(" V")
        self.spin_vexc.valueChanged.connect(self.al_cambiar_parametros_ina)
        form_ina.addRow("Tensión de Excitación del Puente (Vexc):", self.spin_vexc)

        self.spin_rg = QDoubleSpinBox()
        self.spin_rg.setRange(1.0, 100000.0)
        self.spin_rg.setValue(self.rg_ohmios)
        self.spin_rg.setDecimals(1)
        self.spin_rg.setSuffix(" Ω (Pines 1 y 8)")
        self.spin_rg.valueChanged.connect(self.al_cambiar_parametros_ina)
        form_ina.addRow("Resistencia de Ganancia (Rg):", self.spin_rg)

        self.label_ganancia_teorica = QLabel("Ganancia Calculada: G = 51.00  [G = 1 + (50 kΩ / Rg)]")
        self.label_ganancia_teorica.setStyleSheet("font-size: 13px; font-weight: bold; color: #00f2fe;")
        form_ina.addRow("Ganancia Teórica:", self.label_ganancia_teorica)

        layout_central.addWidget(grupo_ina)

        grupo_dir = QGroupBox("4. Carpeta de Secuencias")
        layout_dir = QHBoxLayout(grupo_dir)
        self.line_carpeta_secuencias = QLineEdit(self.carpeta_secuencias)
        self.line_carpeta_secuencias.setReadOnly(True)
        layout_dir.addWidget(self.line_carpeta_secuencias)

        self.boton_cambiar_carpeta = QPushButton("Cambiar Carpeta...")
        self.boton_cambiar_carpeta.clicked.connect(self.al_cambiar_carpeta_almacenamiento)
        layout_dir.addWidget(self.boton_cambiar_carpeta)

        layout_central.addWidget(grupo_dir)
        return widget

    def poblar_tabla_canales_ui(self) -> None:
        self.tabla_canales.setRowCount(len(self.canales))
        for fila, c in enumerate(self.canales):
            chk = QCheckBox()
            chk.setChecked(c.habilitado)
            chk.toggled.connect(lambda estado, obj=c: self.al_alternar_canal_habilitado(obj, estado))
            self.tabla_canales.setCellWidget(fila, 0, chk)

            it_nombre = QTableWidgetItem(c.nombre)
            it_nombre.setFlags(it_nombre.flags() & ~Qt.ItemIsEditable)
            self.tabla_canales.setItem(fila, 1, it_nombre)

            it_etq = QTableWidgetItem(c.etiqueta)
            self.tabla_canales.setItem(fila, 2, it_etq)

            it_modo = QTableWidgetItem(c.modo_terminal)
            it_modo.setFlags(it_modo.flags() & ~Qt.ItemIsEditable)
            if c.modo_terminal == "DIFF":
                it_modo.setForeground(QColor("#00ffff"))
                it_modo.setFont(QFont("Segoe UI", 9, QFont.Bold))
            else:
                it_modo.setForeground(QColor("#39ff14"))
            self.tabla_canales.setItem(fila, 3, it_modo)

            combo_r = QComboBox()
            combo_r.addItem("± 10.0 V", 10.0)
            combo_r.addItem("± 5.0 V", 5.0)
            combo_r.addItem("± 1.0 V", 1.0)
            combo_r.addItem("± 0.2 V", 0.2)
            combo_r.currentIndexChanged.connect(
                lambda idx, obj=c, cb=combo_r: self.al_cambiar_rango_canal(obj, float(cb.currentData()))
            )
            self.tabla_canales.setCellWidget(fila, 4, combo_r)

    def al_alternar_canal_habilitado(self, canal: ModeloCanalNI, estado: bool) -> None:
        canal.habilitado = estado

    def al_cambiar_rango_canal(self, canal: ModeloCanalNI, rango: float) -> None:
        canal.rango_voltaje = rango

    def al_cambiar_canal_monitoreado(self) -> None:
        ch_nom = self.combo_canal_monitoreado.currentData()
        if ch_nom:
            self.canal_principal_nombre = ch_nom
            canal_obj = next((c for c in self.canales if c.nombre == ch_nom), None)
            modo_txt = canal_obj.modo_terminal if canal_obj else "DIFF"
            self.registrar_log(f"Canal principal seleccionado: {ch_nom} ({modo_txt})")

    # =========================================================================
    # LÓGICA DE CONTROL DE SECUENCIAS (INICIO Y PARADA)
    # =========================================================================

    def iniciar_secuencia(self, modo: str) -> None:
        if self.secuencia_activa:
            QMessageBox.warning(self, "Secuencia Activa", "Detenga la secuencia actual antes de iniciar otra.")
            return

        self.secuencia_activa = True
        self.modo_secuencia_actual = modo
        self.id_secuencia_actual += 1
        self.tiempo_inicio_secuencia = time.time()
        self.contador_bloques_promedios = 0
        self.contador_muestras_raw = 0
        self.contador_muestras_secuencia = 0

        # Limpiar buffers de gráfica de ensayo
        self.tiempos_grafica.clear()
        self.voltajes_grafica.clear()
        self.cargas_grafica.clear()

        # Determinar ventana de tiempo del bloque
        ventana_t = (
            self.tiempo_ventana_osciloscopio
            if modo in ("Osciloscopio", "Ensayo100Ton")
            else self.tiempo_ventana_multimetro
        )

        timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        if modo == "Ensayo100Ton":
            base_nombre = f"ensayo_0_a_100_ton_{self.id_secuencia_actual:03d}_{timestamp_str}"
        else:
            base_nombre = f"secuencia_{self.id_secuencia_actual:03d}_{modo.lower()}_{timestamp_str}"

        # 1. Nombre y ruta de Secuencia de Calibración (Promedios)
        nombre_archivo_prom = f"{base_nombre}_calibracion_promedios_{ventana_t:.1f}s.csv"
        self.ruta_archivo_csv_promedios = os.path.join(self.carpeta_sesion_actual, nombre_archivo_prom)
        self.ruta_archivo_csv_actual = self.ruta_archivo_csv_promedios

        # 2. Nombre y ruta de Secuencia Real a Fs Hardware
        if self.guardar_muestreo_real_fs:
            nombre_archivo_raw = f"{base_nombre}_muestreo_real_fs{self.frecuencia_muestreo_fs}Hz.csv"
            self.ruta_archivo_csv_raw = os.path.join(self.carpeta_sesion_actual, nombre_archivo_raw)
        else:
            nombre_archivo_raw = None
            self.ruta_archivo_csv_raw = None

        canales_activos = [c for c in self.canales if c.habilitado]

        try:
            # Archivo 1: Calibración por Promedios
            self.manejador_csv_promedios = open(self.ruta_archivo_csv_promedios, "w", newline="", encoding="utf-8")
            self.escritor_csv_promedios = csv.writer(self.manejador_csv_promedios)
            self.manejador_csv_secuencia = self.manejador_csv_promedios
            self.escritor_csv_secuencia = self.escritor_csv_promedios

            self.escritor_csv_promedios.writerow(["# ENSAYO DE CALIBRACION — PROMEDIOS DE BLOQUE INTEGRADO"])
            self.escritor_csv_promedios.writerow(["# ID_Sesion", self.id_sesion_actual])
            self.escritor_csv_promedios.writerow(["# Nombre_Sesion", self.nombre_sesion_actual])
            self.escritor_csv_promedios.writerow(["# ID_Secuencia", self.id_secuencia_actual])
            self.escritor_csv_promedios.writerow(["# Tipo_Ensayo", modo])
            self.escritor_csv_promedios.writerow(["# Fecha_Hora_Inicio", datetime.datetime.now().isoformat()])
            self.escritor_csv_promedios.writerow(["# Tarjeta_DAQ", "NI-USB-6210"])
            self.escritor_csv_promedios.writerow(["# V_excitacion_puente_V", self.v_excitacion_puente])
            self.escritor_csv_promedios.writerow(["# Rg_instalada_Ohmios", self.rg_instalada_referencia])
            self.escritor_csv_promedios.writerow(["# Ganancia_INA114", self.calcular_ganancia_ina114(self.rg_instalada_referencia)])
            self.escritor_csv_promedios.writerow(["# V_referencia_100_Ton_V", self.v_referencia_100_ton])
            self.escritor_csv_promedios.writerow(["# Sensibilidad_Nominal_Ton_V", self.sensibilidad_nominal_ton_v])
            self.escritor_csv_promedios.writerow(["# Fs_Hardware_Hz", self.frecuencia_muestreo_fs])
            self.escritor_csv_promedios.writerow(["# Ventana_Integracion_Bloque_s", ventana_t])
            self.escritor_csv_promedios.writerow([
                "# Canales_Configurados",
                "; ".join([f"{c.nombre}({c.modo_terminal})" for c in canales_activos]),
            ])
            self.escritor_csv_promedios.writerow([])

            cabeceras_prom = [
                "Tiempo_s",
                "Voltaje_ai0_DIFF_V",
                "Carga_Calculada_Ton",
                "Tension_Puente_ai0_mV",
                "Sensibilidad_ai0_mV_V",
            ]
            for c in canales_activos:
                if c.nombre != "ai0":
                    cabeceras_prom.append(f"{c.nombre}_{c.modo_terminal}_V")
            cabeceras_prom.extend(["Ruido_Vpp_mV", "Desv_Estandar_mV"])
            self.escritor_csv_promedios.writerow(cabeceras_prom)

            # Archivo 2: Muestreo Real en Bruto a Fs de la Tarjeta
            if self.guardar_muestreo_real_fs and self.ruta_archivo_csv_raw:
                self.manejador_csv_raw = open(self.ruta_archivo_csv_raw, "w", newline="", encoding="utf-8")
                self.escritor_csv_raw = csv.writer(self.manejador_csv_raw)

                self.escritor_csv_raw.writerow(["# SECUENCIA DE MUESTREO REAL EN BRUTO (ALTA VELOCIDAD HARDWARE DAQ)"])
                self.escritor_csv_raw.writerow(["# ID_Sesion", self.id_sesion_actual])
                self.escritor_csv_raw.writerow(["# Nombre_Sesion", self.nombre_sesion_actual])
                self.escritor_csv_raw.writerow(["# ID_Secuencia", self.id_secuencia_actual])
                self.escritor_csv_raw.writerow(["# Tipo_Ensayo", modo])
                self.escritor_csv_raw.writerow(["# Fecha_Hora_Inicio", datetime.datetime.now().isoformat()])
                self.escritor_csv_raw.writerow(["# Tarjeta_DAQ", "NI-USB-6210"])
                self.escritor_csv_raw.writerow(["# Frecuencia_Muestreo_Fs_Hz", self.frecuencia_muestreo_fs])
                self.escritor_csv_raw.writerow(["# Periodo_Muestreo_dt_s", 1.0 / self.frecuencia_muestreo_fs])
                self.escritor_csv_raw.writerow(["# V_excitacion_puente_V", self.v_excitacion_puente])
                self.escritor_csv_raw.writerow(["# Rg_instalada_Ohmios", self.rg_instalada_referencia])
                self.escritor_csv_raw.writerow(["# Ganancia_INA114", self.calcular_ganancia_ina114(self.rg_instalada_referencia)])
                self.escritor_csv_raw.writerow(["# V_referencia_100_Ton_V", self.v_referencia_100_ton])
                self.escritor_csv_raw.writerow(["# Sensibilidad_Nominal_Ton_V", self.sensibilidad_nominal_ton_v])
                self.escritor_csv_raw.writerow([
                    "# Canales_Configurados",
                    "; ".join([f"{c.nombre}({c.modo_terminal})" for c in canales_activos]),
                ])
                self.escritor_csv_raw.writerow([])

                cabeceras_raw = [
                    "Indice_Muestra",
                    "Tiempo_Hardware_s",
                    "Voltaje_ai0_DIFF_V",
                    "Carga_Instantanea_Ton",
                ]
                for c in canales_activos:
                    if c.nombre != "ai0":
                        cabeceras_raw.append(f"{c.nombre}_{c.modo_terminal}_V")
                self.escritor_csv_raw.writerow(cabeceras_raw)

        except Exception as e:
            QMessageBox.critical(self, "Error al Crear Archivo", f"No se pudo crear los archivos de ensayo:\n{e}")
            self.secuencia_activa = False
            return

        intervalo_ms = int(ventana_t * 1000)
        self.temporizador_adquisicion.start(intervalo_ms)
        self.actualizar_estado_botones(activo=True)

        msg_log = (
            f"Secuencia #{self.id_secuencia_actual:03d} iniciada [{modo}].\n"
            f"  • Archivo Calibración (Promedios {ventana_t:.1f}s): {nombre_archivo_prom}"
        )
        if nombre_archivo_raw:
            msg_log += f"\n  • Archivo Muestreo Real (Fs={self.frecuencia_muestreo_fs}Hz): {nombre_archivo_raw}"
        self.registrar_log(msg_log)
        self.etiqueta_estado_global.setText(
            f"Grabando Ensayo #{self.id_secuencia_actual:03d} ({modo}) — Dual (Promedios + Real Fs)..."
        )

    def detener_secuencia(self) -> None:
        if not self.secuencia_activa:
            return

        self.temporizador_adquisicion.stop()

        if self.manejador_csv_promedios:
            try:
                self.manejador_csv_promedios.close()
            except Exception:
                pass
            self.manejador_csv_promedios = None
            self.escritor_csv_promedios = None
            self.manejador_csv_secuencia = None
            self.escritor_csv_secuencia = None

        if self.manejador_csv_raw:
            try:
                self.manejador_csv_raw.close()
            except Exception:
                pass
            self.manejador_csv_raw = None
            self.escritor_csv_raw = None

        duracion_total = round(time.time() - (self.tiempo_inicio_secuencia or time.time()), 2)
        modo = self.modo_secuencia_actual

        archivo_prom_nom = os.path.basename(self.ruta_archivo_csv_promedios or "")
        archivo_raw_nom = (
            os.path.basename(self.ruta_archivo_csv_raw or "")
            if self.ruta_archivo_csv_raw
            else None
        )

        self.agregar_secuencia_al_historial(
            sec_id=self.id_secuencia_actual,
            modo=modo,
            bloques_prom=self.contador_bloques_promedios,
            muestras_raw=self.contador_muestras_raw,
            duracion=duracion_total,
            archivo_prom=archivo_prom_nom,
            archivo_raw=archivo_raw_nom,
        )

        self.secuencia_activa = False
        self.actualizar_estado_botones(activo=False)

        resumen_cierre = (
            f"Ensayo #{self.id_secuencia_actual:03d} [{modo}] finalizado con éxito ({duracion_total} s):\n"
            f"  • Secuencia Calibración: {self.contador_bloques_promedios} bloques promediados guardados.\n"
            f"  • Secuencia Muestreo Real: {self.contador_muestras_raw} muestras a {self.frecuencia_muestreo_fs} Hz guardadas."
        )
        self.registrar_log(resumen_cierre)
        self.etiqueta_estado_global.setText(
            f"Ensayo #{self.id_secuencia_actual:03d} guardado: Dual (Calibración + Señal Real Fs) completado."
        )

    def actualizar_estado_botones(self, activo: bool) -> None:
        self.boton_iniciar_ensayo_100ton.setEnabled(not activo)
        self.boton_parar_ensayo_100ton.setEnabled(activo)
        self.boton_iniciar_multimetro.setEnabled(not activo)
        self.boton_parar_multimetro.setEnabled(activo)

        self.combo_dispositivos.setEnabled(not activo)
        self.combo_fs.setEnabled(not activo)
        self.spin_tiempo_osciloscopio.setEnabled(not activo)
        self.spin_tiempo_multimetro.setEnabled(not activo)

    # =========================================================================
    # EJECUCIÓN DEL MUESTREO POR BLOQUES DE HARDWARE
    # =========================================================================

    def ejecutar_bloque_adquisicion(self) -> None:
        modo = self.modo_secuencia_actual if self.secuencia_activa else "MonitoreoLibre"
        ventana_seg = self.tiempo_ventana_osciloscopio if modo in ("Osciloscopio", "Ensayo100Ton", "MonitoreoLibre") else self.tiempo_ventana_multimetro
        fs = self.frecuencia_muestreo_fs
        n_muestras = int(ventana_seg * fs)

        t_relativo = round(time.time() - (self.tiempo_inicio_secuencia or time.time()), 3) if self.secuencia_activa else 0.0
        canales_activos = [c for c in self.canales if c.habilitado]

        if not canales_activos:
            return

        # 1. Adquisición del bloque de hardware
        bloques_datos: Dict[str, np.ndarray] = {}

        if self.check_modo_simulacion.isChecked() or not HAY_NIDAQMX:
            # Simulación: Rizado de bomba + rampa hacia 100 Ton si se ensaya
            g = self.calcular_ganancia_ina114(self.rg_ohmios)
            t_vec = np.linspace(0, ventana_seg, n_muestras)

            for c in canales_activos:
                if c.nombre == "ai0":
                    if self.secuencia_activa and modo == "Ensayo100Ton":
                        # Rampa simulada de carga de 0 a 100 Ton en 40 segundos
                        fraccion = min(t_relativo / 40.0, 1.0)
                        v_ideal = fraccion * 4.85
                    else:
                        v_ideal = (self.spin_presion_patron.value() / 100.0) * 4.85

                    rizado = 0.025 * np.sin(2 * np.pi * 35.0 * t_vec)
                    ruido = np.random.uniform(-0.010, 0.010, n_muestras)
                    bloques_datos[c.nombre] = v_ideal + rizado + ruido
                elif c.nombre == "ai1":
                    bloques_datos[c.nombre] = 0.040 * np.sin(2 * np.pi * 1.5 * t_vec) + np.random.uniform(-0.003, 0.003, n_muestras)
                else:
                    bloques_datos[c.nombre] = min(t_relativo * 0.05, 5.0) + np.random.uniform(-0.002, 0.002, n_muestras)
        else:
            bloques_datos = self.adquirir_bloques_hardware_multicanal(canales_activos, n_muestras, ventana_seg)

        if not bloques_datos:
            return

        # 2. Promedio aritmético y estadísticas del bloque
        bloque_ai0 = bloques_datos.get("ai0", np.array([0.0]))
        v_ai0_bruto = float(np.mean(bloque_ai0))
        v_ai0_neto = v_ai0_bruto - self.tara_offset_voltaje
        self.ultimos_promedios_canales["ai0"] = v_ai0_neto

        g_actual = self.calcular_ganancia_ina114(self.rg_ohmios)
        v_puente_mv = (v_ai0_neto / g_actual) * 1000.0 if g_actual > 0 else 0.0
        sens_mv_v = (v_puente_mv / self.v_excitacion_puente) if self.v_excitacion_puente > 0 else 0.0

        # Carga estimada en Toneladas según referencia
        carga_ton_estimada = v_ai0_neto * self.sensibilidad_nominal_ton_v

        ruido_vpp_mv = (float(np.max(bloque_ai0)) - float(np.min(bloque_ai0))) * 1000.0
        sigma_mv = float(np.std(bloque_ai0)) * 1000.0

        self.ultimo_voltaje_ai0 = v_ai0_neto
        self.ultima_tension_puente_ai0 = v_puente_mv
        self.ultima_carga_ton_ai0 = carga_ton_estimada

        # 3. Actualizar Visualización de la Pestaña 1 (Fondo de Escala y Semáforo)
        self.actualizar_visualizacion_fondo_escala(v_ai0_neto)

        # 4. Actualizar Visualización según Pestaña Activa
        if self.secuencia_activa and modo == "Ensayo100Ton":
            self.tiempos_grafica.append(t_relativo)
            self.voltajes_grafica.append(v_ai0_neto)
            self.cargas_grafica.append(carga_ton_estimada)

            if self.radio_ver_toneladas.isChecked():
                self.curva_osciloscopio_ensayo.setData(list(self.tiempos_grafica), list(self.cargas_grafica))
            else:
                self.curva_osciloscopio_ensayo.setData(list(self.tiempos_grafica), list(self.voltajes_grafica))

            # Aplicar escalabilidad en tiempo (X) y amplitud (Y)
            self.aplicar_escalas_grafico_osc()

            self.display_valor_osc_ensayo.setText(
                f"Carga: {carga_ton_estimada:+.2f} Ton  ({v_ai0_neto:+.4f} V)"
            )

        elif self.secuencia_activa and modo == "Multimetro":
            self.lcd_multimetro.setText(f"{v_ai0_neto:+.6f} V")
            self.lcd_toneladas_multi.setText(f"{carga_ton_estimada:+.2f} Toneladas")
            self.label_puente_mv_multi.setText(f"Tensión Puente: {v_puente_mv:.4f} mV")
            self.label_ruido_multi.setText(f"Ruido Vpp en Bloque: {ruido_vpp_mv:.3f} mV")
            self.label_sigma_multi.setText(f"Desv. Estándar (σ): {sigma_mv:.3f} mV")

        # 5. Escribir fila en CSV de Calibración por Promedios (Secuencia 1)
        if self.secuencia_activa and self.escritor_csv_promedios:
            self.contador_bloques_promedios += 1
            self.contador_muestras_secuencia = self.contador_bloques_promedios
            fila_csv_prom = [
                t_relativo,
                round(v_ai0_neto, 6),
                round(carga_ton_estimada, 3),
                round(v_puente_mv, 5),
                round(sens_mv_v, 5),
            ]
            for c in canales_activos:
                if c.nombre != "ai0":
                    bl = bloques_datos.get(c.nombre, np.array([0.0]))
                    fila_csv_prom.append(round(float(np.mean(bl)), 6))
            fila_csv_prom.extend([round(ruido_vpp_mv, 3), round(sigma_mv, 3)])

            try:
                self.escritor_csv_promedios.writerow(fila_csv_prom)
                self.manejador_csv_promedios.flush()
            except Exception as e:
                self.registrar_log(f"Error escribiendo en CSV de promedios: {e}")

        # 6. Escribir todas las muestras en CSV de Muestreo Real en Bruto a Fs (Secuencia 2)
        if self.secuencia_activa and self.escritor_csv_raw:
            dt = 1.0 / fs
            t_inicio_bloque = max(0.0, t_relativo - ventana_seg)
            idx_base = self.contador_muestras_raw
            v_raw_ai0 = bloque_ai0 - self.tara_offset_voltaje
            cargas_raw = v_raw_ai0 * self.sensibilidad_nominal_ton_v

            filas_raw = []
            for i in range(n_muestras):
                t_i = t_inicio_bloque + (i * dt)
                fila_i = [
                    idx_base + i,
                    round(t_i, 5),
                    round(float(v_raw_ai0[i]), 6),
                    round(float(cargas_raw[i]), 3),
                ]
                for c in canales_activos:
                    if c.nombre != "ai0":
                        bl_ch = bloques_datos.get(c.nombre)
                        val_ch = float(bl_ch[i]) if bl_ch is not None and i < len(bl_ch) else 0.0
                        fila_i.append(round(val_ch, 6))
                filas_raw.append(fila_i)

            try:
                self.escritor_csv_raw.writerows(filas_raw)
                self.manejador_csv_raw.flush()
                self.contador_muestras_raw += n_muestras
            except Exception as e:
                self.registrar_log(f"Error escribiendo en CSV de señal real: {e}")

    def actualizar_visualizacion_fondo_escala(self, voltaje: float) -> None:
        """Actualiza el display grande, la barra y el semáforo para la ventana [4.75V, 4.95V]."""
        self.display_voltaje_fondo_escala.setText(f"{voltaje:+.5f} V")

        mv_val = int(max(0.0, min(voltaje * 1000.0, 5000.0)))
        self.barra_nivel_fondo_escala.setValue(mv_val)

        if voltaje < self.voltaje_objetivo_min:
            # Voltaje bajo
            diferencia = self.voltaje_objetivo_min - voltaje
            self.label_estado_ventana_objetivo.setText(
                f"🟡 TENSIÓN BAJA: {voltaje:.3f} V (< 4.75 V) → DISMINUIR Rg para subir ganancia (Faltan {diferencia:.3f} V)"
            )
            self.label_estado_ventana_objetivo.setStyleSheet(
                "font-size: 14px; font-weight: bold; color: #f1c40f; padding: 8px; background-color: #2c3e50; border-radius: 6px;"
            )
            self.display_voltaje_fondo_escala.setStyleSheet(
                "font-size: 64px; font-weight: bold; color: #f1c40f; font-family: Consolas, monospace; "
                "background-color: #0b0c10; padding: 20px; border: 2px solid #f1c40f; border-radius: 8px;"
            )
        elif self.voltaje_objetivo_min <= voltaje <= self.voltaje_objetivo_max:
            # Rango óptimo
            self.label_estado_ventana_objetivo.setText(
                f"🟢 ¡RANGO ÓPTIMO ALCANZADO!: {voltaje:.4f} V (Dentro de 4.75 V a 4.95 V) → FIJAR REFERENCIA DE 100 TON"
            )
            self.label_estado_ventana_objetivo.setStyleSheet(
                "font-size: 15px; font-weight: bold; color: #2ed573; padding: 8px; background-color: #1b4332; border: 2px solid #2ed573; border-radius: 6px;"
            )
            self.display_voltaje_fondo_escala.setStyleSheet(
                "font-size: 64px; font-weight: bold; color: #2ed573; font-family: Consolas, monospace; "
                "background-color: #081c15; padding: 20px; border: 3px solid #2ed573; border-radius: 8px;"
            )
        else:
            # Voltaje alto / peligro de saturación
            exceso = voltaje - self.voltaje_objetivo_max
            self.label_estado_ventana_objetivo.setText(
                f"🔴 TENSIÓN ALTA / SATURACIÓN: {voltaje:.3f} V (> 4.95 V) → AUMENTAR Rg para bajar ganancia (Exceso {exceso:.3f} V)"
            )
            self.label_estado_ventana_objetivo.setStyleSheet(
                "font-size: 14px; font-weight: bold; color: #ff4757; padding: 8px; background-color: #400000; border: 2px solid #ff4757; border-radius: 6px;"
            )
            self.display_voltaje_fondo_escala.setStyleSheet(
                "font-size: 64px; font-weight: bold; color: #ff4757; font-family: Consolas, monospace; "
                "background-color: #1a0000; padding: 20px; border: 2px solid #ff4757; border-radius: 8px;"
            )

    def adquirir_bloques_hardware_multicanal(
        self, canales_activos: List[ModeloCanalNI], n_muestras: int, timeout_s: float
    ) -> Dict[str, np.ndarray]:
        resultados: Dict[str, np.ndarray] = {}
        try:
            with nidaqmx.Task() as tarea:
                for c in canales_activos:
                    term = (
                        TerminalConfiguration.DIFF
                        if c.modo_terminal == "DIFF"
                        else TerminalConfiguration.RSE
                    )
                    tarea.ai_channels.add_ai_voltage_chan(
                        f"{self.nombre_dispositivo}/{c.nombre}",
                        terminal_config=term,
                        min_val=-c.rango_voltaje,
                        max_val=c.rango_voltaje,
                    )

                tarea.timing.cfg_samp_clk_timing(
                    rate=self.frecuencia_muestreo_fs,
                    sample_mode=AcquisitionType.FINITE,
                    samps_per_chan=n_muestras,
                )
                datos = tarea.read(
                    number_of_samples_per_channel=n_muestras,
                    timeout=timeout_s + 2.0,
                )

                if len(canales_activos) == 1:
                    datos = [datos]

                for idx, c in enumerate(canales_activos):
                    resultados[c.nombre] = np.array(datos[idx], dtype=float)

        except Exception as e:
            self.registrar_log(f"Error en bloque NI-USB-6210: {e}")
        return resultados

    def establecer_tara_cero(self) -> None:
        if hasattr(self, "ultimo_voltaje_ai0"):
            self.tara_offset_voltaje += self.ultimo_voltaje_ai0
            self.registrar_log(f"Tara aplicada en carga mínima: Offset = {self.tara_offset_voltaje:+.6f} V")
        else:
            self.tara_offset_voltaje = 0.0

    # =========================================================================
    # CALIBRACIÓN CON MEDIDA PATRÓN
    # =========================================================================

    def capturar_punto_calibracion(self) -> None:
        if not hasattr(self, "ultimo_voltaje_ai0"):
            QMessageBox.warning(self, "Sin Medición", "Inicie primero una secuencia para adquirir datos.")
            return

        presion_patron = self.spin_presion_patron.value()
        unidad = self.combo_unidad_patron.currentText()
        rg = self.rg_instalada_referencia
        ganancia = self.calcular_ganancia_ina114(rg)

        v_prom = self.ultimo_voltaje_ai0
        v_puente_mv = self.ultima_tension_puente_ai0

        fila = self.tabla_calibracion_patron.rowCount()
        self.tabla_calibracion_patron.insertRow(fila)

        self.tabla_calibracion_patron.setItem(fila, 0, QTableWidgetItem(str(fila + 1)))
        self.tabla_calibracion_patron.setItem(fila, 1, QTableWidgetItem(f"{presion_patron:.3f}"))
        self.tabla_calibracion_patron.setItem(fila, 2, QTableWidgetItem(unidad))
        self.tabla_calibracion_patron.setItem(fila, 3, QTableWidgetItem(f"{v_prom:.5f}"))
        self.tabla_calibracion_patron.setItem(fila, 4, QTableWidgetItem(f"{v_puente_mv:.4f}"))
        self.tabla_calibracion_patron.setItem(fila, 5, QTableWidgetItem(f"{rg:.1f}"))
        self.tabla_calibracion_patron.setItem(fila, 6, QTableWidgetItem(f"{ganancia:.2f}"))

        self.registrar_log(
            f"Punto calibración: {presion_patron} {unidad} -> V_ai0 = {v_prom:.5f} V"
        )
        self.actualizar_grafico_xy_patron()

    def limpiar_tabla_patron(self) -> None:
        self.tabla_calibracion_patron.setRowCount(0)
        self.curva_puntos_patron.setData([])
        self.curva_linea_ajuste.setData([], [])
        self.label_resultado_ecuacion.setText("Ecuación: Carga = (---) · V_medido + (---)  |  R² = ---")

    def al_cambiar_unidad_patron(self) -> None:
        u = self.combo_unidad_patron.currentText()
        self.grafico_calibracion_xy.setLabel("left", f"Carga Patrón", units=u)

    def actualizar_grafico_xy_patron(self) -> None:
        n_filas = self.tabla_calibracion_patron.rowCount()
        if n_filas == 0:
            return

        voltajes, presiones = [], []
        for f in range(n_filas):
            try:
                p = float(self.tabla_calibracion_patron.item(f, 1).text())
                v = float(self.tabla_calibracion_patron.item(f, 3).text())
                presiones.append(p)
                voltajes.append(v)
            except Exception:
                pass

        if voltajes and presiones:
            self.curva_puntos_patron.setData(x=voltajes, y=presiones)

    def calcular_regresion_lineal(self) -> None:
        n_filas = self.tabla_calibracion_patron.rowCount()
        if n_filas < 2:
            QMessageBox.warning(self, "Puntos Insuficientes", "Debe registrar al menos 2 puntos para la regresión.")
            return

        voltajes, presiones = [], []
        for f in range(n_filas):
            try:
                p = float(self.tabla_calibracion_patron.item(f, 1).text())
                v = float(self.tabla_calibracion_patron.item(f, 3).text())
                presiones.append(p)
                voltajes.append(v)
            except Exception:
                pass

        arr_v = np.array(voltajes, dtype=float)
        arr_p = np.array(presiones, dtype=float)

        m, b = np.polyfit(arr_v, arr_p, 1)

        p_pred = m * arr_v + b
        ss_res = np.sum((arr_p - p_pred) ** 2)
        ss_tot = np.sum((arr_p - np.mean(arr_p)) ** 2)
        r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 1.0

        unidad = self.combo_unidad_patron.currentText()
        signo = "+" if b >= 0 else "-"
        self.label_resultado_ecuacion.setText(
            f"Carga [{unidad}] = {m:.4f} · V {signo} {abs(b):.4f}  |  Sensibilidad: {m:.4f} {unidad}/V  |  R² = {r2:.5f}"
        )

        v_min, v_max = float(np.min(arr_v)), float(np.max(arr_v))
        if v_min == v_max:
            v_min -= 0.5
            v_max += 0.5
        v_eje = np.linspace(v_min, v_max, 50)
        p_eje = m * v_eje + b

        self.curva_linea_ajuste.setData(v_eje, p_eje)
        self.curva_puntos_patron.setData(x=arr_v, y=arr_p)
        self.registrar_log(f"Regresión: m={m:.4f} {unidad}/V, b={b:.4f}, R²={r2:.5f}")

    def guardar_calibracion_patron_sesion(self) -> None:
        """Guarda los puntos de calibración y la recta de ajuste dentro de la carpeta de la sesión activa."""
        n_filas = self.tabla_calibracion_patron.rowCount()
        if n_filas == 0:
            QMessageBox.warning(self, "Sin Puntos", "No hay puntos de calibración en la tabla para guardar.")
            return

        timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_archivo = f"calibracion_patron_{timestamp_str}.csv"
        ruta_archivo = os.path.join(self.carpeta_sesion_actual, nombre_archivo)

        try:
            with open(ruta_archivo, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["# CALIBRACION DE SENSOR CONTRA MANOMETRO PATRON"])
                writer.writerow(["# ID_Sesion", self.id_sesion_actual])
                writer.writerow(["# Nombre_Sesion", self.nombre_sesion_actual])
                writer.writerow(["# Fecha_Hora", datetime.datetime.now().isoformat()])
                writer.writerow(["# Ecuacion_Ajuste", self.label_resultado_ecuacion.text()])
                writer.writerow([])
                writer.writerow([
                    "Pto_Num",
                    "Carga_Patron",
                    "Unidad",
                    "V_Promedio_V",
                    "Vin_Puente_mV",
                    "Rg_Ohmios",
                    "Ganancia_G",
                ])
                for f_idx in range(n_filas):
                    fila_datos = [
                        self.tabla_calibracion_patron.item(f_idx, c).text()
                        if self.tabla_calibracion_patron.item(f_idx, c)
                        else ""
                        for c in range(self.tabla_calibracion_patron.columnCount())
                    ]
                    writer.writerow(fila_datos)

            self.registrar_log(f"Calibración contra patrón guardada: {nombre_archivo}")
            QMessageBox.information(
                self,
                "Calibración Guardada en Sesión",
                f"Se guardaron exitosamente {n_filas} puntos de calibración en:\n\n{ruta_archivo}",
            )
        except Exception as e:
            QMessageBox.critical(self, "Error al Guardar", f"No se pudo guardar el archivo de calibración:\n{e}")

    # =========================================================================
    # HISTORIAL DE SECUENCIAS
    # =========================================================================

    def agregar_secuencia_al_historial(
        self,
        sec_id: int,
        modo: str,
        bloques_prom: int,
        muestras_raw: int,
        duracion: float,
        archivo_prom: str,
        archivo_raw: Optional[str],
    ) -> None:
        fila = self.tabla_historial_secuencias.rowCount()
        self.tabla_historial_secuencias.insertRow(fila)

        fecha_hora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        v_med = self.ultimo_voltaje_ai0 if hasattr(self, "ultimo_voltaje_ai0") else 0.0
        v_medio_str = f"{v_med:+.5f} V"

        self.tabla_historial_secuencias.setItem(fila, 0, QTableWidgetItem(f"#{sec_id:03d}"))
        self.tabla_historial_secuencias.setItem(fila, 1, QTableWidgetItem(self.id_sesion_actual))
        self.tabla_historial_secuencias.setItem(fila, 2, QTableWidgetItem(fecha_hora))
        self.tabla_historial_secuencias.setItem(fila, 3, QTableWidgetItem(modo))
        self.tabla_historial_secuencias.setItem(fila, 4, QTableWidgetItem(str(bloques_prom)))
        self.tabla_historial_secuencias.setItem(
            fila, 5, QTableWidgetItem(f"{muestras_raw:,}" if archivo_raw else "---")
        )
        self.tabla_historial_secuencias.setItem(fila, 6, QTableWidgetItem(f"{duracion:.1f} s"))
        self.tabla_historial_secuencias.setItem(fila, 7, QTableWidgetItem(v_medio_str))
        self.tabla_historial_secuencias.setItem(fila, 8, QTableWidgetItem(archivo_prom))
        self.tabla_historial_secuencias.setItem(fila, 9, QTableWidgetItem(archivo_raw or "Desactivado"))

        # Anexar al manifiesto de la sesión activa
        self.registrar_secuencia_en_manifiesto(
            sec_id=sec_id,
            modo=modo,
            bloques_prom=bloques_prom,
            muestras_raw=muestras_raw,
            duracion=duracion,
            archivo_prom=archivo_prom,
            archivo_raw=archivo_raw,
            v_medio=v_med,
        )

    def abrir_carpeta_secuencias(self) -> None:
        self.abrir_carpeta_sesion_actual()

    # =========================================================================
    # CONFIGURACIÓN TÉCNICA Y HARDWARE
    # =========================================================================

    def calcular_ganancia_ina114(self, rg: float) -> float:
        if rg <= 0:
            return 1.0
        return 1.0 + (50000.0 / rg)

    def al_cambiar_tiempos_config(self) -> None:
        self.tiempo_ventana_osciloscopio = self.spin_tiempo_osciloscopio.value()
        self.tiempo_ventana_multimetro = self.spin_tiempo_multimetro.value()
        self.frecuencia_muestreo_fs = int(self.combo_fs.currentData())
        self.registrar_log(
            f"Configuración: Tosc={self.tiempo_ventana_osciloscopio}s, Tnum={self.tiempo_ventana_multimetro}s, Fs={self.frecuencia_muestreo_fs}Hz"
        )

    def al_cambiar_parametros_ina(self) -> None:
        self.v_excitacion_puente = self.spin_vexc.value()
        self.rg_ohmios = self.spin_rg.value()
        g = self.calcular_ganancia_ina114(self.rg_ohmios)
        self.label_ganancia_teorica.setText(f"Ganancia Calculada: G = {g:.2f}  [G = 1 + (50 kΩ / Rg)]")

    def al_cambiar_carpeta_almacenamiento(self) -> None:
        nueva = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta Base de Secuencias", self.carpeta_base_secuencias)
        if nueva:
            self.carpeta_base_secuencias = nueva
            self.carpeta_sesion_actual = os.path.join(self.carpeta_base_secuencias, self.id_sesion_actual)
            os.makedirs(self.carpeta_sesion_actual, exist_ok=True)
            self.carpeta_secuencias = self.carpeta_sesion_actual
            self.line_carpeta_secuencias.setText(self.carpeta_sesion_actual)

    def buscar_tarjetas_nidaq(self) -> None:
        self.combo_dispositivos.clear()
        dispositivos = []
        if HAY_NIDAQMX:
            try:
                for d in System.local().devices:
                    dispositivos.append(d.name)
            except Exception as e:
                self.registrar_log(f"Error consultando NI-DAQ: {e}")

        if dispositivos:
            for d in dispositivos:
                self.combo_dispositivos.addItem(d)
            self.check_modo_simulacion.setChecked(False)
            self.indicador_hardware.setText("NI-USB-6210 Detectada")
            self.indicador_hardware.setStyleSheet(
                "font-weight: bold; color: #2980b9; padding: 4px 10px; background-color: #d4e6f1; border-radius: 4px;"
            )
        else:
            self.combo_dispositivos.addItem("SIMULADOR_USB6210")
            self.check_modo_simulacion.setChecked(True)
            self.indicador_hardware.setText("Modo Simulación (Puente 8V)")
            self.indicador_hardware.setStyleSheet(
                "font-weight: bold; color: #d35400; padding: 4px 10px; background-color: #fdebd0; border-radius: 4px;"
            )

        self.al_cambiar_dispositivo()

    def al_cambiar_dispositivo(self) -> None:
        self.nombre_dispositivo = self.combo_dispositivos.currentText().strip()

    def al_alternar_simulacion(self, activado: bool) -> None:
        if activado:
            self.indicador_hardware.setText("Modo Simulación (Puente 8V)")
            self.indicador_hardware.setStyleSheet(
                "font-weight: bold; color: #d35400; padding: 4px 10px; background-color: #fdebd0; border-radius: 4px;"
            )
        else:
            self.indicador_hardware.setText("Hardware NI Conectado")
            self.indicador_hardware.setStyleSheet(
                "font-weight: bold; color: #27ae60; padding: 4px 10px; background-color: #d5f5e3; border-radius: 4px;"
            )

    def conectar_tarjeta(self) -> None:
        if self.check_modo_simulacion.isChecked() or not HAY_NIDAQMX:
            QMessageBox.information(self, "Modo Simulación", "Operando en simulación de puente de Wheatstone (8V).")
            return
        try:
            if self.nombre_dispositivo not in [d.name for d in System.local().devices]:
                raise ValueError("Dispositivo no encontrado.")
            QMessageBox.information(self, "Conexión Exitosa", f"Tarjeta NI-USB-6210 ({self.nombre_dispositivo}) lista.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo conectar {self.nombre_dispositivo}:\n{e}")

    def registrar_log(self, mensaje: str) -> None:
        h = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        if hasattr(self, "caja_log"):
            self.caja_log.append(f"[{h}] {mensaje}")
        else:
            print(f"[{h}] {mensaje}")

    def closeEvent(self, evento) -> None:
        self.detener_secuencia()
        evento.accept()


# =============================================================================
# PUNTO DE ENTRADA
# =============================================================================

def principal() -> None:
    app = QApplication(sys.argv)
    ventana = VentanaCalibracionPrensa100Ton()
    ventana.show()
    # Iniciar un temporizador continuo para que el display de fondo de escala viva en tiempo real
    timer_monitoreo = QTimer(ventana)
    timer_monitoreo.timeout.connect(ventana.ejecutar_bloque_adquisicion)
    timer_monitoreo.start(int(ventana.tiempo_ventana_osciloscopio * 1000))
    sys.exit(app.exec())


if __name__ == "__main__":
    principal()
