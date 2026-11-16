import os
import sys
import csv
import json
import zipfile
import shutil
from pathlib import Path
from datetime import datetime

from PyQt5.QtCore import Qt, QDate, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QBrush
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QGroupBox, QLabel, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
    QCheckBox, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QMessageBox, QFileDialog, QSplitter, QTabWidget,
    QTextBrowser, QPlainTextEdit, QListWidget, QListWidgetItem, QDateEdit,
    QInputDialog, QScrollArea, QProgressBar
)

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT
from matplotlib.widgets import RectangleSelector
from matplotlib.patches import Rectangle


def extraer_hasta_directorio(ruta_completa, nombre_directorio):
    partes = Path(ruta_completa).parts
    if nombre_directorio in partes:
        indice = partes.index(nombre_directorio)
        ruta_recortada = Path(*partes[:indice + 1])
        return str(ruta_recortada) + '/'
    return ''


ruta_actual = os.path.dirname(os.path.abspath(__file__))
ruta_proyecto = extraer_hasta_directorio(ruta_actual, 'rsa_sismologia')
if not ruta_proyecto:
    ruta_proyecto = os.path.abspath(os.path.join(ruta_actual, '..', '..'))

ruta_librerias = os.path.abspath(os.path.join(ruta_proyecto, 'src', 'librerias'))
ruta_datos = os.path.abspath(os.path.join(ruta_proyecto, 'datos'))

if ruta_librerias not in sys.path:
    sys.path.insert(0, ruta_librerias)
if ruta_datos not in sys.path:
    sys.path.insert(0, ruta_datos)

from rsa_io import lectura_archivo, escritura_archivo
from metodos_gestion import obtener_directorios
from metodos_gis_rsa import _obtener_capas_base_gis
from rsa_utilidades import (
    cargar_config_local_pc,
    guardar_config_local_pc,
    verificar_permiso_configuracion_pc,
    verificar_permiso_respaldo_pc,
    escritura_segura_configuracion,
)


ESTILO_PANEL_CONFIG = """
QGroupBox {
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 11px;
    font-weight: bold;
    color: #1a237e;
    border: 1px solid #b0bec5;
    border-radius: 6px;
    margin-top: 10px;
    padding-top: 10px;
    background-color: #fafafa;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 6px;
    background-color: #fafafa;
}
QPushButton {
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 10pt;
    padding: 5px 12px;
    border-radius: 4px;
    border: 1px solid #90a4ae;
    background-color: #eceff1;
    color: #263238;
}
QPushButton:hover {
    background-color: #cfd8dc;
}
QPushButton#btn_primario {
    background-color: #1e3a8a;
    color: #ffffff;
    font-weight: bold;
    border: 1px solid #1e3a8a;
}
QPushButton#btn_primario:hover {
    background-color: #1d4ed8;
}
QPushButton#btn_salir {
    background-color: #fee2e2;
    color: #991b1b;
    font-weight: bold;
    border: 1px solid #f87171;
}
QPushButton#btn_salir:hover {
    background-color: #fecaca;
}
QTableWidget {
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 9pt;
    gridline-color: #cfd8dc;
    selection-background-color: #dbeafe;
    selection-color: #1e3a8a;
}
QHeaderView::section {
    background-color: #e2e8f0;
    color: #1e293b;
    font-weight: bold;
    padding: 4px;
    border: 1px solid #cbd5e1;
}
"""


def _leer_catalogo_estaciones_completo():
    """
    Lee `datos/estaciones.csv` devolviendo `(cabecera, filas_datos)`.
    Garantiza que cada fila tenga exactamente 25 columnas.
    """
    ruta_est = os.path.join(ruta_datos, 'estaciones.csv')
    filas = lectura_archivo(ruta_est) or []
    if not filas:
        cabecera = [
            "ESTACION(21)", "NOMBRE(0)", "CODIGO(1)", "SENSOR(2)", "CANALES(3)",
            "HAB_CANAL(4)", "COMPONENTE(5)", "HAB_GRAFICO(6)", "BITS(7)",
            "CALIBRACION(8)", "GANANCIA(9)", "DIEZ_PLT(10)", "FACTOR_MUL(11)",
            "CALIDAD(16)", "UBICACION(17)", "CANAL(18)", "RED(19)", "MUESTREO(20)",
            "LONGITUD(12)", "LATITUD(13)", "ALTITUD(14)", "RUIDO(15)",
            "FILTRO(22)", "POLARIDAD(23)", "ORIEN(N)"
        ]
        return cabecera, []
    cabecera = list(filas[0])
    datos = []
    for f in filas[1:]:
        fila_norm = list(f) + [""] * max(0, 25 - len(f))
        datos.append(fila_norm[:25])
    return cabecera, datos


def _crear_etiqueta_estado_seguridad(parent=None) -> QLabel:
    """
    Crea un indicador visual que muestra el equipo actual, el usuario habitual del PC
    y si cuenta con autorización del Administrador (RSA) para modificar configuraciones.
    """
    autorizado, usuario, nombre_pc, _ = verificar_permiso_configuracion_pc()
    lbl = QLabel(parent)
    lbl.setWordWrap(True)
    if autorizado:
        rol_txt = "Administrador (RSA)" if usuario == "RSA" else "Autorizado por Administrador"
        lbl.setText(
            f"🔒 <b>Seguridad PC ({nombre_pc}):</b> Usuario activo <b>{usuario}</b> "
            f"[<i>{rol_txt}</i>] — Respaldo automático activo."
        )
        lbl.setStyleSheet(
            "background-color: #ecfdf5; border: 1px solid #6ee7b7; border-radius: 4px; "
            "padding: 5px 8px; color: #065f46; font-size: 8.5pt;"
        )
    else:
        lbl.setText(
            f"🔒 <b>Seguridad PC ({nombre_pc}):</b> Usuario activo <b>{usuario}</b> "
            f"[<i>Solo lectura — Al guardar se solicitará clave de Administrador RSA</i>]."
        )
        lbl.setStyleSheet(
            "background-color: #fef3c7; border: 1px solid #fcd34d; border-radius: 4px; "
            "padding: 5px 8px; color: #92400e; font-size: 8.5pt;"
        )
    return lbl


def _solicitar_autorizacion_administrador(parent_widget, motivo_bloqueo: str) -> bool:
    """
    Verifica si el usuario/PC actual tiene permiso para guardar configuraciones.
    Si el usuario activo no está en la lista de autorizados de `config_local_pc.json`,
    permite que el Administrador (`RSA`) autorice la operación ingresando su clave.
    """
    autorizado, usuario, nombre_pc, msg = verificar_permiso_configuracion_pc()
    if autorizado:
        return True

    cfg = cargar_config_local_pc()
    clave_esperada = str(cfg.get("clave_administrador") or "RSA").strip()

    clave_ingresada, ok = QInputDialog.getText(
        parent_widget,
        "Autorización de Administrador Requerida",
        f"{msg}\n\n"
        f"{motivo_bloqueo}\n"
        f"Ingrese la clave de Administrador (por defecto 'RSA') para autorizar el guardado en el equipo «{nombre_pc}»:",
        QLineEdit.Password,
    )
    if ok and clave_ingresada.strip() == clave_esperada:
        return True

    if ok:
        QMessageBox.critical(
            parent_widget,
            "Acceso Denegado",
            "Clave de Administrador incorrecta. No se modificó ningún archivo de configuración.",
        )
    return False


def _guardar_config_con_seguridad(
    parent_widget,
    ruta_csv: str,
    filas_completas: list,
    descripcion_archivo: str,
    validador_extra=None,
) -> bool:
    """
    Ejecuta todas las garantías de seguridad antes de escribir un archivo maestro en `datos/`:
      1. Verifica permisos por computadora y usuario (`config_local_pc.json` / Administrador `RSA`).
      2. Ejecuta validaciones de integridad estructural (`validador_extra`).
      3. Pide confirmación explícita al administrador/usuario autorizado.
      4. Crea copia de respaldo con fecha/hora en `datos/respaldos_config/` y escribe de forma atómica.
    """
    if not _solicitar_autorizacion_administrador(
        parent_widget, f"Intento de escritura sobre {descripcion_archivo}."
    ):
        return False

    if validador_extra is not None:
        ok_val, msg_err = validador_extra(filas_completas)
        if not ok_val:
            QMessageBox.critical(
                parent_widget,
                "Validación de Integridad Fallida",
                f"No se puede guardar {descripcion_archivo} por la siguiente inconsistencia:\n\n{msg_err}",
            )
            return False

    _, usuario_act, nombre_pc, _ = verificar_permiso_configuracion_pc()
    resp = QMessageBox.question(
        parent_widget,
        "Confirmación de Seguridad — Guardar Configuración",
        f"¿Confirma que desea actualizar el archivo maestro de configuración?\n\n"
        f"• Archivo: {descripcion_archivo}\n"
        f"• Ruta: {ruta_csv}\n"
        f"• Equipo / Usuario: {nombre_pc} / {usuario_act}\n\n"
        f"Se creará automáticamente una copia de respaldo previa en 'datos/respaldos_config/'.",
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No,
    )
    if resp != QMessageBox.Yes:
        return False

    try:
        ruta_bak = escritura_segura_configuracion(ruta_csv, filas_completas)
        detalle_bak = f"\n\nRespaldo previo creado en:\n{ruta_bak}" if ruta_bak else ""
        QMessageBox.information(
            parent_widget,
            "Configuración Guardada con Seguridad",
            f"Se actualizó correctamente {descripcion_archivo} en:\n{ruta_csv}{detalle_bak}",
        )
        return True
    except Exception as e:
        QMessageBox.critical(
            parent_widget,
            "Error al Guardar Configuración",
            f"No se pudo guardar {descripcion_archivo}:\n{e}",
        )
        return False


# =========================================================================================
# 1. CONFIGURACIÓN DE ESTACIONES SÍSMICAS (datos/estaciones.csv — 101 registros constantes)
# =========================================================================================
class Configurar_estaciones(QWidget):
    cerrado = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("CONFIGURACIÓN DE ESTACIONES SÍSMICAS - RSA")
        self.setStyleSheet(ESTILO_PANEL_CONFIG)
        self.ruta_csv = os.path.join(ruta_datos, "estaciones.csv")
        self.cabecera, self.filas_estaciones = _leer_catalogo_estaciones_completo()
        self.indice_seleccionado = 0

        layout_raiz = QHBoxLayout(self)
        layout_raiz.setContentsMargins(8, 8, 8, 8)
        splitter = QSplitter(Qt.Horizontal, self)
        layout_raiz.addWidget(splitter)

        # Panel izquierdo: Formulario de edición de la estación seleccionada (fijo 0..100)
        panel_izq = QWidget(self)
        panel_izq.setMinimumWidth(360)
        panel_izq.setMaximumWidth(430)
        v_izq = QVBoxLayout(panel_izq)
        v_izq.setContentsMargins(4, 4, 4, 4)

        grp_edicion = QGroupBox("PARÁMETROS DE LA ESTACIÓN (ÍNDICE CONSTANTE 0–100)", panel_izq)
        form = QGridLayout(grp_edicion)
        form.setHorizontalSpacing(8)
        form.setVerticalSpacing(5)

        self.lbl_indice_est = QLabel("0", grp_edicion)
        self.lbl_indice_est.setStyleSheet("font-weight: bold; color: #1e3a8a; font-size: 11pt;")
        self.edt_nombre = QLineEdit(grp_edicion)
        self.edt_codigo = QLineEdit(grp_edicion)
        self.edt_codigo.setMaxLength(6)
        self.cmb_sensor = QComboBox(grp_edicion)
        self.cmb_sensor.addItems(["SISMICO", "ACELEROGRAFICO"])
        self.spn_canales = QSpinBox(grp_edicion)
        self.spn_canales.setRange(1, 12)
        self.chk_hab_canal = QCheckBox("Habilitada (HAB_CANAL = 1)", grp_edicion)
        self.spn_componente = QSpinBox(grp_edicion)
        self.spn_componente.setRange(1, 6)
        self.chk_hab_grafico = QCheckBox("Graficar extracción (HAB_GRAFICO = 1)", grp_edicion)
        self.spn_bits = QSpinBox(grp_edicion)
        self.spn_bits.setRange(8, 32)
        self.edt_calibracion = QLineEdit(grp_edicion)
        self.edt_ganancia = QLineEdit(grp_edicion)
        self.spn_diez_plt = QSpinBox(grp_edicion)
        self.spn_diez_plt.setRange(1, 50)
        self.edt_factor_mul = QLineEdit(grp_edicion)
        self.edt_calidad = QLineEdit(grp_edicion)
        self.edt_ubicacion = QLineEdit(grp_edicion)
        self.cmb_canal_tipo = QComboBox(grp_edicion)
        self.cmb_canal_tipo.setEditable(True)
        self.cmb_canal_tipo.addItems(["ENZ", "XYZ", "TRV"])
        self.edt_red = QLineEdit(grp_edicion)
        self.spn_muestreo = QSpinBox(grp_edicion)
        self.spn_muestreo.setRange(1, 1000)
        self.edt_longitud = QLineEdit(grp_edicion)
        self.edt_latitud = QLineEdit(grp_edicion)
        self.edt_altitud = QLineEdit(grp_edicion)
        self.edt_ruido = QLineEdit(grp_edicion)
        self.edt_filtro = QLineEdit(grp_edicion)
        self.cmb_polaridad = QComboBox(grp_edicion)
        self.cmb_polaridad.addItems(["P", "N"])
        self.edt_orien = QLineEdit(grp_edicion)

        campos = [
            ("N° Estación (Fijo):", self.lbl_indice_est),
            ("Nombre (NOMBRE):", self.edt_nombre),
            ("Código 4 letras (CODIGO):", self.edt_codigo),
            ("Tipo Sensor (SENSOR):", self.cmb_sensor),
            ("N° Canales (CANALES):", self.spn_canales),
            ("Estado Canal:", self.chk_hab_canal),
            ("Componente ProcesoV2:", self.spn_componente),
            ("Estado Gráfico:", self.chk_hab_grafico),
            ("Bits ADC (BITS):", self.spn_bits),
            ("Calibración:", self.edt_calibracion),
            ("Ganancia:", self.edt_ganancia),
            ("Diezmado PLT (DIEZ_PLT):", self.spn_diez_plt),
            ("Factor Multiplicador:", self.edt_factor_mul),
            ("Calidad / Ubicación:", None),
            ("Ejes Canal / Red:", None),
            ("Muestreo (Hz):", self.spn_muestreo),
            ("Longitud / Latitud (°):", None),
            ("Altitud (m) / Ruido:", None),
            ("Filtro / Polaridad / Orien:", None),
        ]

        fila_idx = 0
        for etiqueta, w_ctrl in campos:
            form.addWidget(QLabel(etiqueta, grp_edicion), fila_idx, 0)
            if w_ctrl is not None:
                form.addWidget(w_ctrl, fila_idx, 1)
            elif "Calidad" in etiqueta:
                h_cal = QHBoxLayout()
                h_cal.addWidget(self.edt_calidad)
                h_cal.addWidget(self.edt_ubicacion)
                form.addLayout(h_cal, fila_idx, 1)
            elif "Ejes Canal" in etiqueta:
                h_cr = QHBoxLayout()
                h_cr.addWidget(self.cmb_canal_tipo)
                h_cr.addWidget(self.edt_red)
                form.addLayout(h_cr, fila_idx, 1)
            elif "Longitud" in etiqueta:
                h_coord = QHBoxLayout()
                self.edt_longitud.setPlaceholderText("Long (ej. -79.01)")
                self.edt_latitud.setPlaceholderText("Lat (ej. -2.90)")
                h_coord.addWidget(self.edt_longitud)
                h_coord.addWidget(self.edt_latitud)
                form.addLayout(h_coord, fila_idx, 1)
            elif "Altitud" in etiqueta:
                h_ar = QHBoxLayout()
                self.edt_altitud.setPlaceholderText("Altitud (m)")
                self.edt_ruido.setPlaceholderText("Ruido")
                h_ar.addWidget(self.edt_altitud)
                h_ar.addWidget(self.edt_ruido)
                form.addLayout(h_ar, fila_idx, 1)
            elif "Filtro" in etiqueta:
                h_fpo = QHBoxLayout()
                self.edt_filtro.setPlaceholderText("Filtro")
                self.edt_orien.setPlaceholderText("Orien")
                h_fpo.addWidget(self.edt_filtro)
                h_fpo.addWidget(self.cmb_polaridad)
                h_fpo.addWidget(self.edt_orien)
                form.addLayout(h_fpo, fila_idx, 1)
            fila_idx += 1

        v_izq.addWidget(grp_edicion)
        v_izq.addWidget(_crear_etiqueta_estado_seguridad(panel_izq))

        h_btns = QHBoxLayout()
        self.btn_aplicar_fila = QPushButton("Aplicar a Estación", panel_izq)
        self.btn_aplicar_fila.clicked.connect(self.aplicar_cambios_estacion)
        self.btn_guardar_csv = QPushButton("Guardar estaciones.csv", panel_izq)
        self.btn_guardar_csv.setObjectName("btn_primario")
        self.btn_guardar_csv.clicked.connect(self.guardar_archivo_estaciones)
        self.btn_salir = QPushButton("Salir", panel_izq)
        self.btn_salir.setObjectName("btn_salir")
        self.btn_salir.clicked.connect(self.close)
        h_btns.addWidget(self.btn_aplicar_fila)
        h_btns.addWidget(self.btn_guardar_csv)
        h_btns.addWidget(self.btn_salir)
        v_izq.addLayout(h_btns)

        # Panel derecho: Filtro de búsqueda + Tabla de 101 estaciones
        panel_der = QWidget(self)
        v_der = QVBoxLayout(panel_der)
        v_der.setContentsMargins(4, 4, 4, 4)

        h_filtro = QHBoxLayout()
        h_filtro.addWidget(QLabel("Buscar estación / código:", panel_der))
        self.edt_buscar = QLineEdit(panel_der)
        self.edt_buscar.setPlaceholderText("Escriba nombre, código o número...")
        self.edt_buscar.textChanged.connect(self._filtrar_tabla)
        self.chk_solo_habilitadas = QCheckBox("Mostrar solo habilitadas (HAB_CANAL=1)", panel_der)
        self.chk_solo_habilitadas.toggled.connect(self._filtrar_tabla)
        h_filtro.addWidget(self.edt_buscar, 1)
        h_filtro.addWidget(self.chk_solo_habilitadas)
        v_der.addLayout(h_filtro)

        self.tabla = QTableWidget(panel_der)
        self.tabla.setColumnCount(len(self.cabecera))
        self.tabla.setHorizontalHeaderLabels(self.cabecera)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.itemSelectionChanged.connect(self._al_seleccionar_fila_tabla)
        v_der.addWidget(self.tabla, 1)

        splitter.addWidget(panel_izq)
        splitter.addWidget(panel_der)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        self._poblar_tabla()
        if self.tabla.rowCount() > 0:
            self.tabla.selectRow(0)

    def _poblar_tabla(self):
        self.tabla.setRowCount(len(self.filas_estaciones))
        for r_idx, fila in enumerate(self.filas_estaciones):
            es_hab = (len(fila) > 5 and str(fila[5]).strip() == '1')
            color_fondo = QColor("#ecfdf5") if es_hab else QColor("#ffffff")
            for c_idx, val in enumerate(fila):
                item = QTableWidgetItem(str(val))
                item.setBackground(QBrush(color_fondo))
                if es_hab and c_idx in (0, 1, 2):
                    f = item.font()
                    f.setBold(True)
                    item.setFont(f)
                self.tabla.setItem(r_idx, c_idx, item)
        self.tabla.resizeColumnsToContents()

    def _filtrar_tabla(self):
        texto = self.edt_buscar.text().strip().lower()
        solo_hab = self.chk_solo_habilitadas.isChecked()
        for r_idx, fila in enumerate(self.filas_estaciones):
            es_hab = (len(fila) > 5 and str(fila[5]).strip() == '1')
            coincide_txt = (
                not texto
                or texto in str(fila[0]).lower()
                or texto in str(fila[1]).lower()
                or texto in str(fila[2]).lower()
                or texto in str(fila[3]).lower()
            )
            visible = coincide_txt and (not solo_hab or es_hab)
            self.tabla.setRowHidden(r_idx, not visible)

    def _al_seleccionar_fila_tabla(self):
        filas_sel = self.tabla.selectionModel().selectedRows()
        if not filas_sel:
            return
        idx = filas_sel[0].row()
        if not (0 <= idx < len(self.filas_estaciones)):
            return
        self.indice_seleccionado = idx
        f = self.filas_estaciones[idx]
        self.lbl_indice_est.setText(str(f[0]))
        self.edt_nombre.setText(str(f[1]))
        self.edt_codigo.setText(str(f[2]))
        self.cmb_sensor.setCurrentText(str(f[3]).strip() or "SISMICO")
        try:
            self.spn_canales.setValue(int(float(f[4])))
        except Exception:
            self.spn_canales.setValue(1)
        self.chk_hab_canal.setChecked(str(f[5]).strip() == '1')
        try:
            self.spn_componente.setValue(int(float(f[6])))
        except Exception:
            self.spn_componente.setValue(1)
        self.chk_hab_grafico.setChecked(str(f[7]).strip() == '1')
        try:
            self.spn_bits.setValue(int(float(f[8])))
        except Exception:
            self.spn_bits.setValue(16)
        self.edt_calibracion.setText(str(f[9]))
        self.edt_ganancia.setText(str(f[10]))
        try:
            self.spn_diez_plt.setValue(int(float(f[11])))
        except Exception:
            self.spn_diez_plt.setValue(1)
        self.edt_factor_mul.setText(str(f[12]))
        self.edt_calidad.setText(str(f[13]))
        self.edt_ubicacion.setText(str(f[14]))
        self.cmb_canal_tipo.setCurrentText(str(f[15]))
        self.edt_red.setText(str(f[16]))
        try:
            self.spn_muestreo.setValue(int(float(f[17])))
        except Exception:
            self.spn_muestreo.setValue(100)
        self.edt_longitud.setText(str(f[18]))
        self.edt_latitud.setText(str(f[19]))
        self.edt_altitud.setText(str(f[20]))
        self.edt_ruido.setText(str(f[21]))
        self.edt_filtro.setText(str(f[22]))
        self.cmb_polaridad.setCurrentText(str(f[23]).strip() or "P")
        self.edt_orien.setText(str(f[24]))

    def aplicar_cambios_estacion(self):
        idx = self.indice_seleccionado
        if not (0 <= idx < len(self.filas_estaciones)):
            return
        codigo_limpio = self.edt_codigo.text().strip().upper()
        if not codigo_limpio:
            QMessageBox.warning(self, "Validación", "El código de la estación no puede estar vacío.")
            return
        nueva_fila = [
            str(self.filas_estaciones[idx][0]),
            self.edt_nombre.text().strip(),
            codigo_limpio,
            self.cmb_sensor.currentText().strip(),
            str(self.spn_canales.value()),
            "1" if self.chk_hab_canal.isChecked() else "0",
            str(self.spn_componente.value()),
            "1" if self.chk_hab_grafico.isChecked() else "0",
            str(self.spn_bits.value()),
            self.edt_calibracion.text().strip(),
            self.edt_ganancia.text().strip(),
            str(self.spn_diez_plt.value()),
            self.edt_factor_mul.text().strip(),
            self.edt_calidad.text().strip() or "D",
            self.edt_ubicacion.text().strip() or "0",
            self.cmb_canal_tipo.currentText().strip() or "ENZ",
            self.edt_red.text().strip() or "UC",
            str(self.spn_muestreo.value()),
            self.edt_longitud.text().strip() or "0",
            self.edt_latitud.text().strip() or "0",
            self.edt_altitud.text().strip() or "0",
            self.edt_ruido.text().strip() or "0",
            self.edt_filtro.text() if self.edt_filtro.text() else " ",
            self.cmb_polaridad.currentText().strip() or "P",
            self.edt_orien.text().strip(),
        ]
        self.filas_estaciones[idx] = nueva_fila
        self._poblar_tabla()
        self._filtrar_tabla()
        self.tabla.selectRow(idx)

    def guardar_archivo_estaciones(self):
        self.aplicar_cambios_estacion()

        def _validar_estaciones(filas_totales):
            datos = filas_totales[1:]
            if len(datos) != 101:
                return False, f"estaciones.csv debe mantener exactamente 101 estaciones (0..100); actual: {len(datos)}."
            for i, f in enumerate(datos):
                if len(f) < 25:
                    return False, f"La estación en la fila {i} tiene menos de 25 columnas."
                if not str(f[1]).strip() or not str(f[2]).strip():
                    return False, f"La estación N° {f[0]} tiene NOMBRE o CODIGO vacío."
            return True, ""

        _guardar_config_con_seguridad(
            self,
            self.ruta_csv,
            [self.cabecera] + self.filas_estaciones,
            "estaciones.csv (101 estaciones de la red)",
            validador_extra=_validar_estaciones,
        )

    def limpiar_estado(self):
        pass

    def closeEvent(self, event):
        self.limpiar_estado()
        self.cerrado.emit()
        super().closeEvent(event)


# ==============================================================================
# 7. RESPALDO Y RESTAURACIÓN DEL PROGRAMA (ZIP - SOLO PC ADMINISTRADOR)
# ==============================================================================

CARPETAS_RESPALDO_PROGRAMA = ("datos", "modulos externos", "src")
CARPETAS_EXCLUIDAS_RESPALDO = {"__pycache__", "vw backup"}
EXTENSIONES_EXCLUIDAS_RESPALDO = {".vwx", ".vwxw", ".vwt", ".mcd", ".pyc", ".pyo"}


def recolectar_archivos_respaldo(raiz_origen: str):
    """
    Recorre `datos/`, `modulos externos/` y `src/` dentro de `raiz_origen`
    excluyendo carpetas de caché (`__pycache__`), respaldos Vectorworks (`VW Backup`)
    y extensiones excluidas (`.vwx`, `.vwxw`, `.vwt`, `.mcd`, `.pyc`, `.pyo`).

    Retorna:
        tuple[list[tuple[str, str]], int]: `(lista_(ruta_abs, ruta_rel_zip), conteo_excluidos)`
    """
    raiz_path = Path(raiz_origen).resolve()
    archivos_incluir = []
    conteo_excluidos = 0

    for carpeta_base in CARPETAS_RESPALDO_PROGRAMA:
        dir_objetivo = raiz_path / carpeta_base
        if not dir_objetivo.is_dir():
            continue
        for actual, subdirs, nombres in os.walk(dir_objetivo):
            subdirs_filtrados = []
            for d in subdirs:
                if d.strip().lower() in CARPETAS_EXCLUIDAS_RESPALDO:
                    conteo_excluidos += 1
                else:
                    subdirs_filtrados.append(d)
            subdirs[:] = sorted(subdirs_filtrados, key=str.lower)

            for nom in sorted(nombres, key=str.lower):
                ext = os.path.splitext(nom)[1].lower()
                if ext in EXTENSIONES_EXCLUIDAS_RESPALDO:
                    conteo_excluidos += 1
                    continue
                ruta_abs = os.path.join(actual, nom)
                ruta_rel = os.path.relpath(ruta_abs, raiz_path).replace("\\", "/")
                archivos_incluir.append((ruta_abs, ruta_rel))

    return archivos_incluir, conteo_excluidos


class HiloRespaldoZip(QThread):
    """Hilo de trabajo para comprimir el programa en formato ZIP sin bloquear la UI."""

    progreso = pyqtSignal(int, str)
    terminado = pyqtSignal(bool, str, dict)

    def __init__(self, raiz_origen: str, ruta_zip_destino: str, parent=None):
        super().__init__(parent)
        self.raiz_origen = raiz_origen
        self.ruta_zip_destino = ruta_zip_destino

    def run(self):
        ruta_tmp = self.ruta_zip_destino + ".tmp"
        try:
            archivos, excluidos = recolectar_archivos_respaldo(self.raiz_origen)
            total = len(archivos)
            if total == 0:
                self.terminado.emit(
                    False,
                    "No se encontraron archivos válidos en datos/, modulos externos/ o src/.",
                    {"incluidos": 0, "excluidos": excluidos},
                )
                return

            os.makedirs(os.path.dirname(os.path.abspath(self.ruta_zip_destino)), exist_ok=True)
            with zipfile.ZipFile(ruta_tmp, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
                for idx, (ruta_abs, ruta_rel) in enumerate(archivos, start=1):
                    zf.write(ruta_abs, arcname=ruta_rel)
                    pct = int((idx * 100) / total)
                    self.progreso.emit(pct, ruta_rel)

            os.replace(ruta_tmp, self.ruta_zip_destino)
            tam_mb = os.path.getsize(self.ruta_zip_destino) / (1024.0 * 1024.0)
            self.terminado.emit(
                True,
                f"Respaldo generado correctamente ({tam_mb:.2f} MB).",
                {"incluidos": total, "excluidos": excluidos, "tam_mb": tam_mb},
            )
        except Exception as e:
            try:
                if os.path.exists(ruta_tmp):
                    os.remove(ruta_tmp)
            except Exception:
                pass
            self.terminado.emit(False, f"Error generando el respaldo ZIP: {e}", {})


class HiloRestaurarZip(QThread):
    """
    Hilo de trabajo para descomprimir un respaldo ZIP respetando la estructura
    de directorios y copiando únicamente archivos nuevos o más recientes.
    """

    progreso = pyqtSignal(int, str)
    terminado = pyqtSignal(bool, str, dict)

    def __init__(self, ruta_zip_origen: str, carpeta_destino: str, parent=None):
        super().__init__(parent)
        self.ruta_zip_origen = ruta_zip_origen
        self.carpeta_destino = carpeta_destino

    def run(self):
        try:
            raiz_dest = os.path.abspath(self.carpeta_destino)
            os.makedirs(raiz_dest, exist_ok=True)

            with zipfile.ZipFile(self.ruta_zip_origen, "r") as zf:
                entradas = [info for info in zf.infolist() if not info.is_dir()]
                total = len(entradas)
                if total == 0:
                    self.terminado.emit(
                        False,
                        "El archivo ZIP seleccionado no contiene archivos.",
                        {},
                    )
                    return

                nuevos = 0
                actualizados = 0
                omitidos = 0

                for idx, info in enumerate(entradas, start=1):
                    nombre_rel = info.filename.replace("\\", "/").lstrip("/")
                    dest_abs = os.path.abspath(os.path.join(raiz_dest, *nombre_rel.split("/")))

                    # Protección contra rutas maliciosas fuera de carpeta_destino (Zip Slip)
                    if os.path.commonpath([raiz_dest, dest_abs]) != raiz_dest:
                        omitidos += 1
                        continue

                    mtime_zip = datetime(*info.date_time).timestamp()
                    existe_previo = os.path.isfile(dest_abs)

                    if existe_previo:
                        mtime_local = os.path.getmtime(dest_abs)
                        # Tolerancia de 2 s por resolución DOS de fechas en archivos ZIP
                        if mtime_zip <= mtime_local + 2.0:
                            omitidos += 1
                            pct = int((idx * 100) / total)
                            self.progreso.emit(pct, f"Omitido (actual/antiguo): {nombre_rel}")
                            continue

                    os.makedirs(os.path.dirname(dest_abs), exist_ok=True)
                    with zf.open(info, "r") as f_src, open(dest_abs, "wb") as f_dst:
                        shutil.copyfileobj(f_src, f_dst)
                    os.utime(dest_abs, (mtime_zip, mtime_zip))

                    if existe_previo:
                        actualizados += 1
                        estado_txt = f"Actualizado: {nombre_rel}"
                    else:
                        nuevos += 1
                        estado_txt = f"Nuevo: {nombre_rel}"

                    pct = int((idx * 100) / total)
                    self.progreso.emit(pct, estado_txt)

            self.terminado.emit(
                True,
                "Restauración / actualización completada.",
                {
                    "total": total,
                    "nuevos": nuevos,
                    "actualizados": actualizados,
                    "omitidos": omitidos,
                },
            )
        except Exception as e:
            self.terminado.emit(False, f"Error restaurando desde ZIP: {e}", {})


class Respaldar_programa(QWidget):
    cerrado = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("RESPALDO Y ACTUALIZACIÓN DEL PROGRAMA (ZIP) - RSA")
        self.setStyleSheet(ESTILO_PANEL_CONFIG)
        self.raiz_proyecto = os.path.abspath(ruta_proyecto)
        self._hilo_activo = None

        layout_raiz = QVBoxLayout(self)
        layout_raiz.setContentsMargins(12, 10, 12, 10)
        layout_raiz.setSpacing(10)

        autorizado_pc, nombre_pc, msg_pc = verificar_permiso_respaldo_pc()
        lbl_seg = QLabel(
            f"Equipo actual: <b>{nombre_pc}</b> — {msg_pc}",
            self,
        )
        lbl_seg.setWordWrap(True)
        if autorizado_pc:
            lbl_seg.setStyleSheet(
                "background:#e8f5e9; color:#1b5e20; border:1px solid #81c784; "
                "border-radius:4px; padding:6px 10px;"
            )
        else:
            lbl_seg.setStyleSheet(
                "background:#ffebee; color:#b71c1c; border:1px solid #e57373; "
                "border-radius:4px; padding:6px 10px;"
            )
        layout_raiz.addWidget(lbl_seg)

        # 1. Sección de creación de respaldo ZIP
        grp_backup = QGroupBox("1. GENERAR RESPALDO DEL PROGRAMA (.ZIP)", self)
        v_bkp = QVBoxLayout(grp_backup)
        lbl_info_bkp = QLabel(
            f"<b>Origen:</b> <code>{self.raiz_proyecto}</code><br>"
            "<b>Carpetas incluidas:</b> <code>datos/</code>, <code>modulos externos/</code> y <code>src/</code> "
            "(respetando íntegramente su estructura de directorios).<br>"
            "<b>Exclusiones automáticas:</b> GitHub/Agente, <code>datos/mapas/VW Backup/</code>, "
            "archivos de Vectorworks (<code>*.vwx</code>, <code>*.vwxw</code>, <code>*.vwt</code>, <code>*.mcd</code>) "
            "y caché Python (<code>__pycache__/</code>, <code>*.pyc</code>).",
            grp_backup,
        )
        lbl_info_bkp.setWordWrap(True)
        lbl_info_bkp.setStyleSheet("font-weight: normal; color: #263238;")
        v_bkp.addWidget(lbl_info_bkp)

        h_bkp_btn = QHBoxLayout()
        self.btn_crear_zip = QPushButton("Generar Respaldo ZIP (Guardar como...)", grp_backup)
        self.btn_crear_zip.setObjectName("btn_primario")
        self.btn_crear_zip.setEnabled(autorizado_pc)
        self.btn_crear_zip.clicked.connect(self.ejecutar_respaldo_zip)
        h_bkp_btn.addWidget(self.btn_crear_zip)
        h_bkp_btn.addStretch()
        v_bkp.addLayout(h_bkp_btn)
        layout_raiz.addWidget(grp_backup)

        # 2. Progreso y bitácora
        grp_prog = QGroupBox("2. PROGRESO Y BITÁCORA DE OPERACIÓN", self)
        v_prog = QVBoxLayout(grp_prog)
        self.lbl_estado_op = QLabel("En espera.", grp_prog)
        self.lbl_estado_op.setStyleSheet("font-weight: normal; color: #37474f;")
        self.barra_progreso = QProgressBar(grp_prog)
        self.barra_progreso.setRange(0, 100)
        self.barra_progreso.setValue(0)
        self.txt_bitacora = QPlainTextEdit(grp_prog)
        self.txt_bitacora.setReadOnly(True)
        self.txt_bitacora.setMinimumHeight(180)
        v_prog.addWidget(self.lbl_estado_op)
        v_prog.addWidget(self.barra_progreso)
        v_prog.addWidget(self.txt_bitacora, 1)
        layout_raiz.addWidget(grp_prog, 1)

        h_pie = QHBoxLayout()
        h_pie.addStretch()
        self.btn_salir = QPushButton("Salir", self)
        self.btn_salir.setObjectName("btn_salir")
        self.btn_salir.clicked.connect(self.close)
        h_pie.addWidget(self.btn_salir)
        layout_raiz.addLayout(h_pie)

    def _establecer_controles_activos(self, habilitado: bool):
        autorizado_pc, _, _ = verificar_permiso_respaldo_pc()
        self.btn_crear_zip.setEnabled(habilitado and autorizado_pc)
        self.btn_salir.setEnabled(habilitado)

    def ejecutar_respaldo_zip(self):
        autorizado_pc, _, msg_pc = verificar_permiso_respaldo_pc()
        if not autorizado_pc:
            QMessageBox.warning(self, "Acceso Restringido", msg_pc)
            return

        nombre_sug = f"respaldo_rsa_sismologia_{datetime.now().strftime('%Y%m%d_%H%M')}.zip"
        ruta_zip, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar respaldo del programa como...",
            os.path.join(self.raiz_proyecto, nombre_sug),
            "Archivos ZIP (*.zip)",
        )
        if not ruta_zip:
            return
        if not ruta_zip.lower().endswith(".zip"):
            ruta_zip += ".zip"

        self.txt_bitacora.clear()
        self.barra_progreso.setValue(0)
        self.lbl_estado_op.setText("Comprimiendo archivos...")
        self._establecer_controles_activos(False)

        self._hilo_activo = HiloRespaldoZip(self.raiz_proyecto, ruta_zip, self)
        self._hilo_activo.progreso.connect(self._al_avanzar_operacion)
        self._hilo_activo.terminado.connect(self._al_terminar_respaldo)
        self._hilo_activo.start()

    def _al_avanzar_operacion(self, porcentaje: int, detalle: str):
        self.barra_progreso.setValue(porcentaje)
        self.lbl_estado_op.setText(detalle)

    def _al_terminar_respaldo(self, ok: bool, mensaje: str, stats: dict):
        self._establecer_controles_activos(True)
        if ok:
            self.barra_progreso.setValue(100)
            self.lbl_estado_op.setText(mensaje)
            self.txt_bitacora.appendPlainText(
                f"✓ {mensaje}\n"
                f"• Archivos comprimidos: {stats.get('incluidos', 0)}\n"
                f"• Elementos excluidos (VW Backup / Vectorworks / __pycache__): {stats.get('excluidos', 0)}"
            )
            QMessageBox.information(self, "Respaldo Completado", mensaje)
        else:
            self.lbl_estado_op.setText(mensaje)
            self.txt_bitacora.appendPlainText(f"✗ {mensaje}")
            QMessageBox.critical(self, "Error en Respaldo", mensaje)

    def limpiar_estado(self):
        if self._hilo_activo is not None and self._hilo_activo.isRunning():
            self._hilo_activo.wait(2000)
        self._hilo_activo = None

    def closeEvent(self, event):
        self.limpiar_estado()
        self.cerrado.emit()
        super().closeEvent(event)


class Restaurar_programa(QWidget):
    """
    Módulo abierto a cualquier equipo para descomprimir/actualizar el programa
    desde un archivo ZIP respetando la estructura de directorios y copiando
    únicamente archivos nuevos o más recientes.
    """
    cerrado = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ACTUALIZAR / RECUPERAR PROGRAMA DESDE ZIP - RSA")
        self.setStyleSheet(ESTILO_PANEL_CONFIG)
        self.raiz_proyecto = os.path.abspath(ruta_proyecto)
        self._hilo_activo = None

        layout_raiz = QVBoxLayout(self)
        layout_raiz.setContentsMargins(12, 10, 12, 10)
        layout_raiz.setSpacing(10)

        grp_rest = QGroupBox("1. SELECCIÓN DE RESPALDO (.ZIP) Y CARPETA DESTINO", self)
        grid_r = QGridLayout(grp_rest)

        self.edt_zip_origen = QLineEdit(grp_rest)
        self.edt_zip_origen.setPlaceholderText("Seleccione el archivo .zip de respaldo...")
        self.btn_buscar_zip = QPushButton("Examinar ZIP...", grp_rest)
        self.btn_buscar_zip.clicked.connect(self.seleccionar_zip_origen)

        self.edt_dir_destino = QLineEdit(self.raiz_proyecto, grp_rest)
        self.btn_buscar_dest = QPushButton("Carpeta destino...", grp_rest)
        self.btn_buscar_dest.clicked.connect(self.seleccionar_carpeta_destino)

        lbl_nota_inc = QLabel(
            "<b>Actualización ágil:</b> solo se copian archivos nuevos o con fecha de modificación "
            "más reciente que la versión existente en destino; las versiones iguales o más antiguas se omiten, "
            "respetando íntegramente la estructura de directorios.",
            grp_rest,
        )
        lbl_nota_inc.setWordWrap(True)
        lbl_nota_inc.setStyleSheet("font-weight: normal; color: #1e3a8a;")

        self.btn_restaurar_zip = QPushButton("Restaurar / Actualizar desde ZIP", grp_rest)
        self.btn_restaurar_zip.setObjectName("btn_primario")
        self.btn_restaurar_zip.clicked.connect(self.ejecutar_restauracion_zip)

        grid_r.addWidget(QLabel("Archivo ZIP:"), 0, 0)
        grid_r.addWidget(self.edt_zip_origen, 0, 1)
        grid_r.addWidget(self.btn_buscar_zip, 0, 2)
        grid_r.addWidget(QLabel("Carpeta destino:"), 1, 0)
        grid_r.addWidget(self.edt_dir_destino, 1, 1)
        grid_r.addWidget(self.btn_buscar_dest, 1, 2)
        grid_r.addWidget(lbl_nota_inc, 2, 0, 1, 3)
        grid_r.addWidget(self.btn_restaurar_zip, 3, 0, 1, 3)
        layout_raiz.addWidget(grp_rest)

        grp_prog = QGroupBox("2. PROGRESO Y BITÁCORA DE ACTUALIZACIÓN", self)
        v_prog = QVBoxLayout(grp_prog)
        self.lbl_estado_op = QLabel("En espera.", grp_prog)
        self.lbl_estado_op.setStyleSheet("font-weight: normal; color: #37474f;")
        self.barra_progreso = QProgressBar(grp_prog)
        self.barra_progreso.setRange(0, 100)
        self.barra_progreso.setValue(0)
        self.txt_bitacora = QPlainTextEdit(grp_prog)
        self.txt_bitacora.setReadOnly(True)
        self.txt_bitacora.setMinimumHeight(180)
        v_prog.addWidget(self.lbl_estado_op)
        v_prog.addWidget(self.barra_progreso)
        v_prog.addWidget(self.txt_bitacora, 1)
        layout_raiz.addWidget(grp_prog, 1)

        h_pie = QHBoxLayout()
        h_pie.addStretch()
        self.btn_salir = QPushButton("Salir", self)
        self.btn_salir.setObjectName("btn_salir")
        self.btn_salir.clicked.connect(self.close)
        h_pie.addWidget(self.btn_salir)
        layout_raiz.addLayout(h_pie)

    def _establecer_controles_activos(self, habilitado: bool):
        self.btn_buscar_zip.setEnabled(habilitado)
        self.btn_buscar_dest.setEnabled(habilitado)
        self.btn_restaurar_zip.setEnabled(habilitado)
        self.btn_salir.setEnabled(habilitado)

    def seleccionar_zip_origen(self):
        ruta, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar respaldo ZIP",
            self.raiz_proyecto,
            "Archivos ZIP (*.zip)",
        )
        if ruta:
            self.edt_zip_origen.setText(ruta)

    def seleccionar_carpeta_destino(self):
        carpeta = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar carpeta destino para restaurar",
            self.edt_dir_destino.text().strip() or self.raiz_proyecto,
        )
        if carpeta:
            self.edt_dir_destino.setText(carpeta)

    def ejecutar_restauracion_zip(self):
        ruta_zip = self.edt_zip_origen.text().strip()
        carpeta_dest = self.edt_dir_destino.text().strip()
        if not ruta_zip or not os.path.isfile(ruta_zip):
            QMessageBox.warning(self, "Validación", "Seleccione un archivo .zip válido.")
            return
        if not carpeta_dest:
            QMessageBox.warning(self, "Validación", "Indique la carpeta destino.")
            return

        resp = QMessageBox.question(
            self,
            "Confirmar actualización incremental",
            f"Se extraerán únicamente los archivos nuevos o más recientes desde:\n{ruta_zip}\n\n"
            f"Hacia:\n{carpeta_dest}\n\n¿Desea continuar?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if resp != QMessageBox.Yes:
            return

        self.txt_bitacora.clear()
        self.barra_progreso.setValue(0)
        self.lbl_estado_op.setText("Verificando fechas y extrayendo archivos más nuevos...")
        self._establecer_controles_activos(False)

        self._hilo_activo = HiloRestaurarZip(ruta_zip, carpeta_dest, self)
        self._hilo_activo.progreso.connect(self._al_avanzar_operacion)
        self._hilo_activo.terminado.connect(self._al_terminar_restauracion)
        self._hilo_activo.start()

    def _al_avanzar_operacion(self, porcentaje: int, detalle: str):
        self.barra_progreso.setValue(porcentaje)
        self.lbl_estado_op.setText(detalle)

    def _al_terminar_restauracion(self, ok: bool, mensaje: str, stats: dict):
        self._establecer_controles_activos(True)
        if ok:
            self.barra_progreso.setValue(100)
            self.lbl_estado_op.setText(mensaje)
            resumen = (
                f"✓ {mensaje}\n"
                f"• Total en ZIP: {stats.get('total', 0)}\n"
                f"• Archivos nuevos copiados: {stats.get('nuevos', 0)}\n"
                f"• Archivos actualizados (más recientes): {stats.get('actualizados', 0)}\n"
                f"• Archivos omitidos (iguales o más antiguos): {stats.get('omitidos', 0)}"
            )
            self.txt_bitacora.appendPlainText(resumen)
            QMessageBox.information(self, "Actualización Completada", resumen)
        else:
            self.lbl_estado_op.setText(mensaje)
            self.txt_bitacora.appendPlainText(f"✗ {mensaje}")
            QMessageBox.critical(self, "Error en Actualización", mensaje)

    def limpiar_estado(self):
        if self._hilo_activo is not None and self._hilo_activo.isRunning():
            self._hilo_activo.wait(2000)
        self._hilo_activo = None

    def closeEvent(self, event):
        self.limpiar_estado()
        self.cerrado.emit()
        super().closeEvent(event)


# =========================================================================================
# 2. CONFIGURACIÓN DE ESTACIONES ANALÓGICAS (datos/analogicas.csv — 16 canales constantes)
# =========================================================================================
class Configurar_analogicas(QWidget):
    cerrado = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("CONFIGURACIÓN DE ESTACIONES ANALÓGICAS - RSA")
        self.setStyleSheet(ESTILO_PANEL_CONFIG)
        self.ruta_csv = os.path.join(ruta_datos, "analogicas.csv")
        _, self.catalogo_estaciones = _leer_catalogo_estaciones_completo()
        self.mapa_por_num = {str(f[0]).strip(): (str(f[1]).strip(), str(f[2]).strip()) for f in self.catalogo_estaciones}

        filas_raw = lectura_archivo(self.ruta_csv) or []
        self.cabecera = filas_raw[0] if filas_raw else ["ESTACION", "NOMBRE", "CODIGO"]
        self.filas_analogicas = [list(r[:3]) for r in filas_raw[1:17]]
        while len(self.filas_analogicas) < 16:
            idx_faltante = str(len(self.filas_analogicas))
            nom_def, cod_def = self.mapa_por_num.get(idx_faltante, ("", ""))
            self.filas_analogicas.append([idx_faltante, nom_def, cod_def])

        layout_raiz = QHBoxLayout(self)
        layout_raiz.setContentsMargins(8, 8, 8, 8)

        # Panel izquierdo: Instrucciones y botones de acción
        panel_izq = QWidget(self)
        panel_izq.setFixedWidth(330)
        v_izq = QVBoxLayout(panel_izq)

        grp_info = QGroupBox("CANALES ANALÓGICOS (16 CANALES CONSTANTES)", panel_izq)
        v_info = QVBoxLayout(grp_info)
        lbl_desc = QLabel(
            "<p>El archivo <b>analogicas.csv</b> define las <b>16 estaciones</b> fijas "
            "del sistema de adquisición analógico.</p>"
            "<p>Para evitar inconsistencias, cada uno de los 16 canales se escoge "
            "directamente desde el catálogo oficial <b>estaciones.csv</b>; al seleccionar "
            "una estación en el desplegable de cada fila, se asignan automáticamente su "
            "número (<code>ESTACION</code>), <code>NOMBRE</code> y <code>CODIGO</code>.</p>",
            grp_info,
        )
        lbl_desc.setWordWrap(True)
        v_info.addWidget(lbl_desc)
        v_izq.addWidget(grp_info)
        v_izq.addWidget(_crear_etiqueta_estado_seguridad(panel_izq))
        v_izq.addStretch()

        self.btn_guardar = QPushButton("Guardar analogicas.csv", panel_izq)
        self.btn_guardar.setObjectName("btn_primario")
        self.btn_guardar.clicked.connect(self.guardar_analogicas)
        self.btn_salir = QPushButton("Salir", panel_izq)
        self.btn_salir.setObjectName("btn_salir")
        self.btn_salir.clicked.connect(self.close)
        v_izq.addWidget(self.btn_guardar)
        v_izq.addWidget(self.btn_salir)

        # Panel derecho: Tabla de 16 filas con QComboBox vinculado a estaciones.csv
        panel_der = QWidget(self)
        v_der = QVBoxLayout(panel_der)
        self.tabla = QTableWidget(16, 4, panel_der)
        self.tabla.setHorizontalHeaderLabels([
            "Canal Analógico",
            "Seleccionar Estación (desde estaciones.csv)",
            "NOMBRE (Automático)",
            "CODIGO (Automático)",
        ])
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.combos_canales = []

        opciones_combo = [
            (str(f[0]).strip(), f"{f[0]} — {f[2]} — {f[1]}")
            for f in self.catalogo_estaciones
        ]

        for fila_idx in range(16):
            num_actual = str(self.filas_analogicas[fila_idx][0]).strip()
            nom_actual, cod_actual = self.mapa_por_num.get(
                num_actual,
                (self.filas_analogicas[fila_idx][1], self.filas_analogicas[fila_idx][2]),
            )

            item_canal = QTableWidgetItem(f"Canal {fila_idx + 1}")
            item_canal.setFlags(Qt.ItemIsEnabled)
            self.tabla.setItem(fila_idx, 0, item_canal)

            cmb = QComboBox(self.tabla)
            for num_est, etiqueta in opciones_combo:
                cmb.addItem(etiqueta, num_est)
            idx_combo = cmb.findData(num_actual)
            if idx_combo >= 0:
                cmb.setCurrentIndex(idx_combo)
            cmb.currentIndexChanged.connect(lambda _idx, r=fila_idx: self._al_cambiar_estacion_canal(r))
            self.tabla.setCellWidget(fila_idx, 1, cmb)
            self.combos_canales.append(cmb)

            item_nom = QTableWidgetItem(nom_actual)
            item_nom.setFlags(Qt.ItemIsEnabled)
            self.tabla.setItem(fila_idx, 2, item_nom)

            item_cod = QTableWidgetItem(cod_actual)
            item_cod.setFlags(Qt.ItemIsEnabled)
            self.tabla.setItem(fila_idx, 3, item_cod)

        v_der.addWidget(self.tabla)
        layout_raiz.addWidget(panel_izq, 0)
        layout_raiz.addWidget(panel_der, 1)

    def _al_cambiar_estacion_canal(self, fila_idx: int):
        cmb = self.combos_canales[fila_idx]
        num_est = str(cmb.currentData()).strip()
        nom, cod = self.mapa_por_num.get(num_est, ("", ""))
        self.filas_analogicas[fila_idx] = [num_est, nom, cod]
        self.tabla.item(fila_idx, 2).setText(nom)
        self.tabla.item(fila_idx, 3).setText(cod)

    def guardar_analogicas(self):
        for r in range(16):
            self._al_cambiar_estacion_canal(r)

        def _validar_analogicas(filas_totales):
            datos = filas_totales[1:]
            if len(datos) != 16:
                return False, f"analogicas.csv debe mantener exactamente 16 canales; actual: {len(datos)}."
            for idx_c, fila_c in enumerate(datos):
                if str(fila_c[0]).strip() not in self.mapa_por_num:
                    return False, f"El canal {idx_c + 1} no corresponde a una estación válida de estaciones.csv."
            return True, ""

        _guardar_config_con_seguridad(
            self,
            self.ruta_csv,
            [self.cabecera] + self.filas_analogicas,
            "analogicas.csv (16 canales analógicos)",
            validador_extra=_validar_analogicas,
        )

    def limpiar_estado(self):
        pass

    def closeEvent(self, event):
        self.limpiar_estado()
        self.cerrado.emit()
        super().closeEvent(event)


# ==============================================================================
# 7. RESPALDO Y RESTAURACIÓN DEL PROGRAMA (ZIP - SOLO PC ADMINISTRADOR)
# ==============================================================================

CARPETAS_RESPALDO_PROGRAMA = ("datos", "modulos externos", "src")
CARPETAS_EXCLUIDAS_RESPALDO = {"__pycache__", "vw backup"}
EXTENSIONES_EXCLUIDAS_RESPALDO = {".vwx", ".vwxw", ".vwt", ".mcd", ".pyc", ".pyo"}


def recolectar_archivos_respaldo(raiz_origen: str):
    """
    Recorre `datos/`, `modulos externos/` y `src/` dentro de `raiz_origen`
    excluyendo carpetas de caché (`__pycache__`), respaldos Vectorworks (`VW Backup`)
    y extensiones excluidas (`.vwx`, `.vwxw`, `.vwt`, `.mcd`, `.pyc`, `.pyo`).

    Retorna:
        tuple[list[tuple[str, str]], int]: `(lista_(ruta_abs, ruta_rel_zip), conteo_excluidos)`
    """
    raiz_path = Path(raiz_origen).resolve()
    archivos_incluir = []
    conteo_excluidos = 0

    for carpeta_base in CARPETAS_RESPALDO_PROGRAMA:
        dir_objetivo = raiz_path / carpeta_base
        if not dir_objetivo.is_dir():
            continue
        for actual, subdirs, nombres in os.walk(dir_objetivo):
            subdirs_filtrados = []
            for d in subdirs:
                if d.strip().lower() in CARPETAS_EXCLUIDAS_RESPALDO:
                    conteo_excluidos += 1
                else:
                    subdirs_filtrados.append(d)
            subdirs[:] = sorted(subdirs_filtrados, key=str.lower)

            for nom in sorted(nombres, key=str.lower):
                ext = os.path.splitext(nom)[1].lower()
                if ext in EXTENSIONES_EXCLUIDAS_RESPALDO:
                    conteo_excluidos += 1
                    continue
                ruta_abs = os.path.join(actual, nom)
                ruta_rel = os.path.relpath(ruta_abs, raiz_path).replace("\\", "/")
                archivos_incluir.append((ruta_abs, ruta_rel))

    return archivos_incluir, conteo_excluidos


class HiloRespaldoZip(QThread):
    """Hilo de trabajo para comprimir el programa en formato ZIP sin bloquear la UI."""

    progreso = pyqtSignal(int, str)
    terminado = pyqtSignal(bool, str, dict)

    def __init__(self, raiz_origen: str, ruta_zip_destino: str, parent=None):
        super().__init__(parent)
        self.raiz_origen = raiz_origen
        self.ruta_zip_destino = ruta_zip_destino

    def run(self):
        ruta_tmp = self.ruta_zip_destino + ".tmp"
        try:
            archivos, excluidos = recolectar_archivos_respaldo(self.raiz_origen)
            total = len(archivos)
            if total == 0:
                self.terminado.emit(
                    False,
                    "No se encontraron archivos válidos en datos/, modulos externos/ o src/.",
                    {"incluidos": 0, "excluidos": excluidos},
                )
                return

            os.makedirs(os.path.dirname(os.path.abspath(self.ruta_zip_destino)), exist_ok=True)
            with zipfile.ZipFile(ruta_tmp, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
                for idx, (ruta_abs, ruta_rel) in enumerate(archivos, start=1):
                    zf.write(ruta_abs, arcname=ruta_rel)
                    pct = int((idx * 100) / total)
                    self.progreso.emit(pct, ruta_rel)

            os.replace(ruta_tmp, self.ruta_zip_destino)
            tam_mb = os.path.getsize(self.ruta_zip_destino) / (1024.0 * 1024.0)
            self.terminado.emit(
                True,
                f"Respaldo generado correctamente ({tam_mb:.2f} MB).",
                {"incluidos": total, "excluidos": excluidos, "tam_mb": tam_mb},
            )
        except Exception as e:
            try:
                if os.path.exists(ruta_tmp):
                    os.remove(ruta_tmp)
            except Exception:
                pass
            self.terminado.emit(False, f"Error generando el respaldo ZIP: {e}", {})


class HiloRestaurarZip(QThread):
    """
    Hilo de trabajo para descomprimir un respaldo ZIP respetando la estructura
    de directorios y copiando únicamente archivos nuevos o más recientes.
    """

    progreso = pyqtSignal(int, str)
    terminado = pyqtSignal(bool, str, dict)

    def __init__(self, ruta_zip_origen: str, carpeta_destino: str, parent=None):
        super().__init__(parent)
        self.ruta_zip_origen = ruta_zip_origen
        self.carpeta_destino = carpeta_destino

    def run(self):
        try:
            raiz_dest = os.path.abspath(self.carpeta_destino)
            os.makedirs(raiz_dest, exist_ok=True)

            with zipfile.ZipFile(self.ruta_zip_origen, "r") as zf:
                entradas = [info for info in zf.infolist() if not info.is_dir()]
                total = len(entradas)
                if total == 0:
                    self.terminado.emit(
                        False,
                        "El archivo ZIP seleccionado no contiene archivos.",
                        {},
                    )
                    return

                nuevos = 0
                actualizados = 0
                omitidos = 0

                for idx, info in enumerate(entradas, start=1):
                    nombre_rel = info.filename.replace("\\", "/").lstrip("/")
                    dest_abs = os.path.abspath(os.path.join(raiz_dest, *nombre_rel.split("/")))

                    # Protección contra rutas maliciosas fuera de carpeta_destino (Zip Slip)
                    if os.path.commonpath([raiz_dest, dest_abs]) != raiz_dest:
                        omitidos += 1
                        continue

                    mtime_zip = datetime(*info.date_time).timestamp()
                    existe_previo = os.path.isfile(dest_abs)

                    if existe_previo:
                        mtime_local = os.path.getmtime(dest_abs)
                        # Tolerancia de 2 s por resolución DOS de fechas en archivos ZIP
                        if mtime_zip <= mtime_local + 2.0:
                            omitidos += 1
                            pct = int((idx * 100) / total)
                            self.progreso.emit(pct, f"Omitido (actual/antiguo): {nombre_rel}")
                            continue

                    os.makedirs(os.path.dirname(dest_abs), exist_ok=True)
                    with zf.open(info, "r") as f_src, open(dest_abs, "wb") as f_dst:
                        shutil.copyfileobj(f_src, f_dst)
                    os.utime(dest_abs, (mtime_zip, mtime_zip))

                    if existe_previo:
                        actualizados += 1
                        estado_txt = f"Actualizado: {nombre_rel}"
                    else:
                        nuevos += 1
                        estado_txt = f"Nuevo: {nombre_rel}"

                    pct = int((idx * 100) / total)
                    self.progreso.emit(pct, estado_txt)

            self.terminado.emit(
                True,
                "Restauración / actualización completada.",
                {
                    "total": total,
                    "nuevos": nuevos,
                    "actualizados": actualizados,
                    "omitidos": omitidos,
                },
            )
        except Exception as e:
            self.terminado.emit(False, f"Error restaurando desde ZIP: {e}", {})


class Respaldar_programa(QWidget):
    cerrado = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("RESPALDO Y ACTUALIZACIÓN DEL PROGRAMA (ZIP) - RSA")
        self.setStyleSheet(ESTILO_PANEL_CONFIG)
        self.raiz_proyecto = os.path.abspath(ruta_proyecto)
        self._hilo_activo = None

        layout_raiz = QVBoxLayout(self)
        layout_raiz.setContentsMargins(12, 10, 12, 10)
        layout_raiz.setSpacing(10)

        autorizado_pc, nombre_pc, msg_pc = verificar_permiso_respaldo_pc()
        lbl_seg = QLabel(
            f"Equipo actual: <b>{nombre_pc}</b> — {msg_pc}",
            self,
        )
        lbl_seg.setWordWrap(True)
        if autorizado_pc:
            lbl_seg.setStyleSheet(
                "background:#e8f5e9; color:#1b5e20; border:1px solid #81c784; "
                "border-radius:4px; padding:6px 10px;"
            )
        else:
            lbl_seg.setStyleSheet(
                "background:#ffebee; color:#b71c1c; border:1px solid #e57373; "
                "border-radius:4px; padding:6px 10px;"
            )
        layout_raiz.addWidget(lbl_seg)

        # 1. Sección de creación de respaldo ZIP
        grp_backup = QGroupBox("1. GENERAR RESPALDO DEL PROGRAMA (.ZIP)", self)
        v_bkp = QVBoxLayout(grp_backup)
        lbl_info_bkp = QLabel(
            f"<b>Origen:</b> <code>{self.raiz_proyecto}</code><br>"
            "<b>Carpetas incluidas:</b> <code>datos/</code>, <code>modulos externos/</code> y <code>src/</code> "
            "(respetando íntegramente su estructura de directorios).<br>"
            "<b>Exclusiones automáticas:</b> GitHub/Agente, <code>datos/mapas/VW Backup/</code>, "
            "archivos de Vectorworks (<code>*.vwx</code>, <code>*.vwxw</code>, <code>*.vwt</code>, <code>*.mcd</code>) "
            "y caché Python (<code>__pycache__/</code>, <code>*.pyc</code>).",
            grp_backup,
        )
        lbl_info_bkp.setWordWrap(True)
        lbl_info_bkp.setStyleSheet("font-weight: normal; color: #263238;")
        v_bkp.addWidget(lbl_info_bkp)

        h_bkp_btn = QHBoxLayout()
        self.btn_crear_zip = QPushButton("Generar Respaldo ZIP (Guardar como...)", grp_backup)
        self.btn_crear_zip.setObjectName("btn_primario")
        self.btn_crear_zip.setEnabled(autorizado_pc)
        self.btn_crear_zip.clicked.connect(self.ejecutar_respaldo_zip)
        h_bkp_btn.addWidget(self.btn_crear_zip)
        h_bkp_btn.addStretch()
        v_bkp.addLayout(h_bkp_btn)
        layout_raiz.addWidget(grp_backup)

        # 2. Progreso y bitácora
        grp_prog = QGroupBox("2. PROGRESO Y BITÁCORA DE OPERACIÓN", self)
        v_prog = QVBoxLayout(grp_prog)
        self.lbl_estado_op = QLabel("En espera.", grp_prog)
        self.lbl_estado_op.setStyleSheet("font-weight: normal; color: #37474f;")
        self.barra_progreso = QProgressBar(grp_prog)
        self.barra_progreso.setRange(0, 100)
        self.barra_progreso.setValue(0)
        self.txt_bitacora = QPlainTextEdit(grp_prog)
        self.txt_bitacora.setReadOnly(True)
        self.txt_bitacora.setMinimumHeight(180)
        v_prog.addWidget(self.lbl_estado_op)
        v_prog.addWidget(self.barra_progreso)
        v_prog.addWidget(self.txt_bitacora, 1)
        layout_raiz.addWidget(grp_prog, 1)

        h_pie = QHBoxLayout()
        h_pie.addStretch()
        self.btn_salir = QPushButton("Salir", self)
        self.btn_salir.setObjectName("btn_salir")
        self.btn_salir.clicked.connect(self.close)
        h_pie.addWidget(self.btn_salir)
        layout_raiz.addLayout(h_pie)

    def _establecer_controles_activos(self, habilitado: bool):
        autorizado_pc, _, _ = verificar_permiso_respaldo_pc()
        self.btn_crear_zip.setEnabled(habilitado and autorizado_pc)
        self.btn_salir.setEnabled(habilitado)

    def ejecutar_respaldo_zip(self):
        autorizado_pc, _, msg_pc = verificar_permiso_respaldo_pc()
        if not autorizado_pc:
            QMessageBox.warning(self, "Acceso Restringido", msg_pc)
            return

        nombre_sug = f"respaldo_rsa_sismologia_{datetime.now().strftime('%Y%m%d_%H%M')}.zip"
        ruta_zip, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar respaldo del programa como...",
            os.path.join(self.raiz_proyecto, nombre_sug),
            "Archivos ZIP (*.zip)",
        )
        if not ruta_zip:
            return
        if not ruta_zip.lower().endswith(".zip"):
            ruta_zip += ".zip"

        self.txt_bitacora.clear()
        self.barra_progreso.setValue(0)
        self.lbl_estado_op.setText("Comprimiendo archivos...")
        self._establecer_controles_activos(False)

        self._hilo_activo = HiloRespaldoZip(self.raiz_proyecto, ruta_zip, self)
        self._hilo_activo.progreso.connect(self._al_avanzar_operacion)
        self._hilo_activo.terminado.connect(self._al_terminar_respaldo)
        self._hilo_activo.start()

    def _al_avanzar_operacion(self, porcentaje: int, detalle: str):
        self.barra_progreso.setValue(porcentaje)
        self.lbl_estado_op.setText(detalle)

    def _al_terminar_respaldo(self, ok: bool, mensaje: str, stats: dict):
        self._establecer_controles_activos(True)
        if ok:
            self.barra_progreso.setValue(100)
            self.lbl_estado_op.setText(mensaje)
            self.txt_bitacora.appendPlainText(
                f"✓ {mensaje}\n"
                f"• Archivos comprimidos: {stats.get('incluidos', 0)}\n"
                f"• Elementos excluidos (VW Backup / Vectorworks / __pycache__): {stats.get('excluidos', 0)}"
            )
            QMessageBox.information(self, "Respaldo Completado", mensaje)
        else:
            self.lbl_estado_op.setText(mensaje)
            self.txt_bitacora.appendPlainText(f"✗ {mensaje}")
            QMessageBox.critical(self, "Error en Respaldo", mensaje)

    def limpiar_estado(self):
        if self._hilo_activo is not None and self._hilo_activo.isRunning():
            self._hilo_activo.wait(2000)
        self._hilo_activo = None

    def closeEvent(self, event):
        self.limpiar_estado()
        self.cerrado.emit()
        super().closeEvent(event)


class Restaurar_programa(QWidget):
    """
    Módulo abierto a cualquier equipo para descomprimir/actualizar el programa
    desde un archivo ZIP respetando la estructura de directorios y copiando
    únicamente archivos nuevos o más recientes.
    """
    cerrado = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ACTUALIZAR / RECUPERAR PROGRAMA DESDE ZIP - RSA")
        self.setStyleSheet(ESTILO_PANEL_CONFIG)
        self.raiz_proyecto = os.path.abspath(ruta_proyecto)
        self._hilo_activo = None

        layout_raiz = QVBoxLayout(self)
        layout_raiz.setContentsMargins(12, 10, 12, 10)
        layout_raiz.setSpacing(10)

        grp_rest = QGroupBox("1. SELECCIÓN DE RESPALDO (.ZIP) Y CARPETA DESTINO", self)
        grid_r = QGridLayout(grp_rest)

        self.edt_zip_origen = QLineEdit(grp_rest)
        self.edt_zip_origen.setPlaceholderText("Seleccione el archivo .zip de respaldo...")
        self.btn_buscar_zip = QPushButton("Examinar ZIP...", grp_rest)
        self.btn_buscar_zip.clicked.connect(self.seleccionar_zip_origen)

        self.edt_dir_destino = QLineEdit(self.raiz_proyecto, grp_rest)
        self.btn_buscar_dest = QPushButton("Carpeta destino...", grp_rest)
        self.btn_buscar_dest.clicked.connect(self.seleccionar_carpeta_destino)

        lbl_nota_inc = QLabel(
            "<b>Actualización ágil:</b> solo se copian archivos nuevos o con fecha de modificación "
            "más reciente que la versión existente en destino; las versiones iguales o más antiguas se omiten, "
            "respetando íntegramente la estructura de directorios.",
            grp_rest,
        )
        lbl_nota_inc.setWordWrap(True)
        lbl_nota_inc.setStyleSheet("font-weight: normal; color: #1e3a8a;")

        self.btn_restaurar_zip = QPushButton("Restaurar / Actualizar desde ZIP", grp_rest)
        self.btn_restaurar_zip.setObjectName("btn_primario")
        self.btn_restaurar_zip.clicked.connect(self.ejecutar_restauracion_zip)

        grid_r.addWidget(QLabel("Archivo ZIP:"), 0, 0)
        grid_r.addWidget(self.edt_zip_origen, 0, 1)
        grid_r.addWidget(self.btn_buscar_zip, 0, 2)
        grid_r.addWidget(QLabel("Carpeta destino:"), 1, 0)
        grid_r.addWidget(self.edt_dir_destino, 1, 1)
        grid_r.addWidget(self.btn_buscar_dest, 1, 2)
        grid_r.addWidget(lbl_nota_inc, 2, 0, 1, 3)
        grid_r.addWidget(self.btn_restaurar_zip, 3, 0, 1, 3)
        layout_raiz.addWidget(grp_rest)

        grp_prog = QGroupBox("2. PROGRESO Y BITÁCORA DE ACTUALIZACIÓN", self)
        v_prog = QVBoxLayout(grp_prog)
        self.lbl_estado_op = QLabel("En espera.", grp_prog)
        self.lbl_estado_op.setStyleSheet("font-weight: normal; color: #37474f;")
        self.barra_progreso = QProgressBar(grp_prog)
        self.barra_progreso.setRange(0, 100)
        self.barra_progreso.setValue(0)
        self.txt_bitacora = QPlainTextEdit(grp_prog)
        self.txt_bitacora.setReadOnly(True)
        self.txt_bitacora.setMinimumHeight(180)
        v_prog.addWidget(self.lbl_estado_op)
        v_prog.addWidget(self.barra_progreso)
        v_prog.addWidget(self.txt_bitacora, 1)
        layout_raiz.addWidget(grp_prog, 1)

        h_pie = QHBoxLayout()
        h_pie.addStretch()
        self.btn_salir = QPushButton("Salir", self)
        self.btn_salir.setObjectName("btn_salir")
        self.btn_salir.clicked.connect(self.close)
        h_pie.addWidget(self.btn_salir)
        layout_raiz.addLayout(h_pie)

    def _establecer_controles_activos(self, habilitado: bool):
        self.btn_buscar_zip.setEnabled(habilitado)
        self.btn_buscar_dest.setEnabled(habilitado)
        self.btn_restaurar_zip.setEnabled(habilitado)
        self.btn_salir.setEnabled(habilitado)

    def seleccionar_zip_origen(self):
        ruta, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar respaldo ZIP",
            self.raiz_proyecto,
            "Archivos ZIP (*.zip)",
        )
        if ruta:
            self.edt_zip_origen.setText(ruta)

    def seleccionar_carpeta_destino(self):
        carpeta = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar carpeta destino para restaurar",
            self.edt_dir_destino.text().strip() or self.raiz_proyecto,
        )
        if carpeta:
            self.edt_dir_destino.setText(carpeta)

    def ejecutar_restauracion_zip(self):
        ruta_zip = self.edt_zip_origen.text().strip()
        carpeta_dest = self.edt_dir_destino.text().strip()
        if not ruta_zip or not os.path.isfile(ruta_zip):
            QMessageBox.warning(self, "Validación", "Seleccione un archivo .zip válido.")
            return
        if not carpeta_dest:
            QMessageBox.warning(self, "Validación", "Indique la carpeta destino.")
            return

        resp = QMessageBox.question(
            self,
            "Confirmar actualización incremental",
            f"Se extraerán únicamente los archivos nuevos o más recientes desde:\n{ruta_zip}\n\n"
            f"Hacia:\n{carpeta_dest}\n\n¿Desea continuar?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if resp != QMessageBox.Yes:
            return

        self.txt_bitacora.clear()
        self.barra_progreso.setValue(0)
        self.lbl_estado_op.setText("Verificando fechas y extrayendo archivos más nuevos...")
        self._establecer_controles_activos(False)

        self._hilo_activo = HiloRestaurarZip(ruta_zip, carpeta_dest, self)
        self._hilo_activo.progreso.connect(self._al_avanzar_operacion)
        self._hilo_activo.terminado.connect(self._al_terminar_restauracion)
        self._hilo_activo.start()

    def _al_avanzar_operacion(self, porcentaje: int, detalle: str):
        self.barra_progreso.setValue(porcentaje)
        self.lbl_estado_op.setText(detalle)

    def _al_terminar_restauracion(self, ok: bool, mensaje: str, stats: dict):
        self._establecer_controles_activos(True)
        if ok:
            self.barra_progreso.setValue(100)
            self.lbl_estado_op.setText(mensaje)
            resumen = (
                f"✓ {mensaje}\n"
                f"• Total en ZIP: {stats.get('total', 0)}\n"
                f"• Archivos nuevos copiados: {stats.get('nuevos', 0)}\n"
                f"• Archivos actualizados (más recientes): {stats.get('actualizados', 0)}\n"
                f"• Archivos omitidos (iguales o más antiguos): {stats.get('omitidos', 0)}"
            )
            self.txt_bitacora.appendPlainText(resumen)
            QMessageBox.information(self, "Actualización Completada", resumen)
        else:
            self.lbl_estado_op.setText(mensaje)
            self.txt_bitacora.appendPlainText(f"✗ {mensaje}")
            QMessageBox.critical(self, "Error en Actualización", mensaje)

    def limpiar_estado(self):
        if self._hilo_activo is not None and self._hilo_activo.isRunning():
            self._hilo_activo.wait(2000)
        self._hilo_activo = None

    def closeEvent(self, event):
        self.limpiar_estado()
        self.cerrado.emit()
        super().closeEvent(event)


# =========================================================================================
# 3. CONFIGURACIÓN DE ENLACES DIGITALES (datos/digitales.csv — Extensible)
# =========================================================================================
class Configurar_digitales(QWidget):
    cerrado = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("CONFIGURACIÓN DE ENLACES DIGITALES - RSA")
        self.setStyleSheet(ESTILO_PANEL_CONFIG)
        self.ruta_csv = os.path.join(ruta_datos, "digitales.csv")
        _, self.catalogo_estaciones = _leer_catalogo_estaciones_completo()
        self.mapa_por_num = {str(f[0]).strip(): f"{f[2]} - {f[1]}" for f in self.catalogo_estaciones}

        filas_raw = lectura_archivo(self.ruta_csv) or []
        self.cabecera = filas_raw[0] if filas_raw else ["Est. Digital", "Numero", "Habilitado"]
        self.filas_digitales = [list(r[:3]) for r in filas_raw[1:] if r and len(r) >= 3]

        layout_raiz = QHBoxLayout(self)
        layout_raiz.setContentsMargins(8, 8, 8, 8)

        # Panel izquierdo: Formulario para editar o agregar enlaces digitales
        panel_izq = QWidget(self)
        panel_izq.setFixedWidth(360)
        v_izq = QVBoxLayout(panel_izq)

        grp_form = QGroupBox("EDICIÓN / NUEVO ENLACE DIGITAL", panel_izq)
        form = QFormLayout(grp_form)

        self.edt_enlace = QLineEdit(grp_form)
        self.edt_enlace.setPlaceholderText("Ej: TENG\\mseed o CHA01\\mseed")
        self.cmb_estacion = QComboBox(grp_form)
        for f in self.catalogo_estaciones:
            self.cmb_estacion.addItem(f"{f[0]} — {f[2]} — {f[1]}", str(f[0]).strip())
        self.chk_habilitado = QCheckBox("Enlace Habilitado (1)", grp_form)
        self.chk_habilitado.setChecked(True)

        form.addRow("Ruta / Identificador Digital:", self.edt_enlace)
        form.addRow("Estación Asociada (Numero):", self.cmb_estacion)
        form.addRow("Estado:", self.chk_habilitado)
        v_izq.addWidget(grp_form)

        h_acc = QHBoxLayout()
        self.btn_actualizar = QPushButton("Actualizar Seleccionado", panel_izq)
        self.btn_actualizar.clicked.connect(self.actualizar_seleccionado)
        self.btn_agregar = QPushButton("+ Agregar Nuevo", panel_izq)
        self.btn_agregar.clicked.connect(self.agregar_nuevo)
        h_acc.addWidget(self.btn_actualizar)
        h_acc.addWidget(self.btn_agregar)
        v_izq.addLayout(h_acc)

        self.btn_eliminar = QPushButton("Eliminar Enlace Seleccionado", panel_izq)
        self.btn_eliminar.clicked.connect(self.eliminar_seleccionado)
        v_izq.addWidget(self.btn_eliminar)
        v_izq.addWidget(_crear_etiqueta_estado_seguridad(panel_izq))
        v_izq.addStretch()

        self.btn_guardar = QPushButton("Guardar digitales.csv", panel_izq)
        self.btn_guardar.setObjectName("btn_primario")
        self.btn_guardar.clicked.connect(self.guardar_digitales)
        self.btn_salir = QPushButton("Salir", panel_izq)
        self.btn_salir.setObjectName("btn_salir")
        self.btn_salir.clicked.connect(self.close)
        v_izq.addWidget(self.btn_guardar)
        v_izq.addWidget(self.btn_salir)

        # Panel derecho: Tabla de enlaces digitales
        panel_der = QWidget(self)
        v_der = QVBoxLayout(panel_der)
        self.tabla = QTableWidget(panel_der)
        self.tabla.setColumnCount(4)
        self.tabla.setHorizontalHeaderLabels([
            "Est. Digital", "Numero", "Estación en Catálogo", "Habilitado"
        ])
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.itemSelectionChanged.connect(self._al_seleccionar)
        v_der.addWidget(self.tabla)

        layout_raiz.addWidget(panel_izq, 0)
        layout_raiz.addWidget(panel_der, 1)
        self._poblar_tabla()
        if self.tabla.rowCount() > 0:
            self.tabla.selectRow(0)

    def _poblar_tabla(self):
        self.tabla.setRowCount(len(self.filas_digitales))
        for r_idx, fila in enumerate(self.filas_digitales):
            est_dig, num_str, hab_str = str(fila[0]).strip(), str(fila[1]).strip(), str(fila[2]).strip()
            desc_est = self.mapa_por_num.get(num_str, "No encontrada")
            valores = [est_dig, num_str, desc_est, hab_str]
            color_f = QColor("#ecfdf5") if hab_str == "1" else QColor("#ffffff")
            for c_idx, val in enumerate(valores):
                it = QTableWidgetItem(val)
                it.setBackground(QBrush(color_f))
                self.tabla.setItem(r_idx, c_idx, it)

    def _al_seleccionar(self):
        sel = self.tabla.selectionModel().selectedRows()
        if not sel:
            return
        idx = sel[0].row()
        if not (0 <= idx < len(self.filas_digitales)):
            return
        f = self.filas_digitales[idx]
        self.edt_enlace.setText(str(f[0]).strip())
        idx_c = self.cmb_estacion.findData(str(f[1]).strip())
        if idx_c >= 0:
            self.cmb_estacion.setCurrentIndex(idx_c)
        self.chk_habilitado.setChecked(str(f[2]).strip() == "1")

    def actualizar_seleccionado(self):
        sel = self.tabla.selectionModel().selectedRows()
        if not sel:
            return
        idx = sel[0].row()
        enlace = self.edt_enlace.text().strip()
        if not enlace:
            QMessageBox.warning(self, "Validación", "Ingrese el identificador de Est. Digital.")
            return
        num_est = str(self.cmb_estacion.currentData()).strip()
        hab_str = "1" if self.chk_habilitado.isChecked() else "0"
        self.filas_digitales[idx] = [enlace, num_est, hab_str]
        self._poblar_tabla()
        self.tabla.selectRow(idx)

    def agregar_nuevo(self):
        enlace = self.edt_enlace.text().strip()
        if not enlace:
            QMessageBox.warning(self, "Validación", "Ingrese el identificador para el nuevo enlace digital.")
            return
        num_est = str(self.cmb_estacion.currentData()).strip()
        hab_str = "1" if self.chk_habilitado.isChecked() else "0"
        self.filas_digitales.append([enlace, num_est, hab_str])
        self._poblar_tabla()
        self.tabla.selectRow(len(self.filas_digitales) - 1)

    def eliminar_seleccionado(self):
        sel = self.tabla.selectionModel().selectedRows()
        if not sel:
            return
        idx = sel[0].row()
        if 0 <= idx < len(self.filas_digitales):
            self.filas_digitales.pop(idx)
            self._poblar_tabla()

    def guardar_digitales(self):
        def _validar_digitales(filas_totales):
            datos = filas_totales[1:]
            if not datos:
                return False, "Debe existir al menos un enlace digital registrado."
            for r in datos:
                if not str(r[0]).strip():
                    return False, "Existe un enlace digital con identificador vacío."
                if str(r[1]).strip() not in self.mapa_por_num:
                    return False, f"El número de estación {r[1]} no existe en estaciones.csv."
            return True, ""

        _guardar_config_con_seguridad(
            self,
            self.ruta_csv,
            [self.cabecera] + self.filas_digitales,
            "digitales.csv (Enlaces digitales)",
            validador_extra=_validar_digitales,
        )

    def limpiar_estado(self):
        pass

    def closeEvent(self, event):
        self.limpiar_estado()
        self.cerrado.emit()
        super().closeEvent(event)


# ==============================================================================
# 7. RESPALDO Y RESTAURACIÓN DEL PROGRAMA (ZIP - SOLO PC ADMINISTRADOR)
# ==============================================================================

CARPETAS_RESPALDO_PROGRAMA = ("datos", "modulos externos", "src")
CARPETAS_EXCLUIDAS_RESPALDO = {"__pycache__", "vw backup"}
EXTENSIONES_EXCLUIDAS_RESPALDO = {".vwx", ".vwxw", ".vwt", ".mcd", ".pyc", ".pyo"}


def recolectar_archivos_respaldo(raiz_origen: str):
    """
    Recorre `datos/`, `modulos externos/` y `src/` dentro de `raiz_origen`
    excluyendo carpetas de caché (`__pycache__`), respaldos Vectorworks (`VW Backup`)
    y extensiones excluidas (`.vwx`, `.vwxw`, `.vwt`, `.mcd`, `.pyc`, `.pyo`).

    Retorna:
        tuple[list[tuple[str, str]], int]: `(lista_(ruta_abs, ruta_rel_zip), conteo_excluidos)`
    """
    raiz_path = Path(raiz_origen).resolve()
    archivos_incluir = []
    conteo_excluidos = 0

    for carpeta_base in CARPETAS_RESPALDO_PROGRAMA:
        dir_objetivo = raiz_path / carpeta_base
        if not dir_objetivo.is_dir():
            continue
        for actual, subdirs, nombres in os.walk(dir_objetivo):
            subdirs_filtrados = []
            for d in subdirs:
                if d.strip().lower() in CARPETAS_EXCLUIDAS_RESPALDO:
                    conteo_excluidos += 1
                else:
                    subdirs_filtrados.append(d)
            subdirs[:] = sorted(subdirs_filtrados, key=str.lower)

            for nom in sorted(nombres, key=str.lower):
                ext = os.path.splitext(nom)[1].lower()
                if ext in EXTENSIONES_EXCLUIDAS_RESPALDO:
                    conteo_excluidos += 1
                    continue
                ruta_abs = os.path.join(actual, nom)
                ruta_rel = os.path.relpath(ruta_abs, raiz_path).replace("\\", "/")
                archivos_incluir.append((ruta_abs, ruta_rel))

    return archivos_incluir, conteo_excluidos


class HiloRespaldoZip(QThread):
    """Hilo de trabajo para comprimir el programa en formato ZIP sin bloquear la UI."""

    progreso = pyqtSignal(int, str)
    terminado = pyqtSignal(bool, str, dict)

    def __init__(self, raiz_origen: str, ruta_zip_destino: str, parent=None):
        super().__init__(parent)
        self.raiz_origen = raiz_origen
        self.ruta_zip_destino = ruta_zip_destino

    def run(self):
        ruta_tmp = self.ruta_zip_destino + ".tmp"
        try:
            archivos, excluidos = recolectar_archivos_respaldo(self.raiz_origen)
            total = len(archivos)
            if total == 0:
                self.terminado.emit(
                    False,
                    "No se encontraron archivos válidos en datos/, modulos externos/ o src/.",
                    {"incluidos": 0, "excluidos": excluidos},
                )
                return

            os.makedirs(os.path.dirname(os.path.abspath(self.ruta_zip_destino)), exist_ok=True)
            with zipfile.ZipFile(ruta_tmp, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
                for idx, (ruta_abs, ruta_rel) in enumerate(archivos, start=1):
                    zf.write(ruta_abs, arcname=ruta_rel)
                    pct = int((idx * 100) / total)
                    self.progreso.emit(pct, ruta_rel)

            os.replace(ruta_tmp, self.ruta_zip_destino)
            tam_mb = os.path.getsize(self.ruta_zip_destino) / (1024.0 * 1024.0)
            self.terminado.emit(
                True,
                f"Respaldo generado correctamente ({tam_mb:.2f} MB).",
                {"incluidos": total, "excluidos": excluidos, "tam_mb": tam_mb},
            )
        except Exception as e:
            try:
                if os.path.exists(ruta_tmp):
                    os.remove(ruta_tmp)
            except Exception:
                pass
            self.terminado.emit(False, f"Error generando el respaldo ZIP: {e}", {})


class HiloRestaurarZip(QThread):
    """
    Hilo de trabajo para descomprimir un respaldo ZIP respetando la estructura
    de directorios y copiando únicamente archivos nuevos o más recientes.
    """

    progreso = pyqtSignal(int, str)
    terminado = pyqtSignal(bool, str, dict)

    def __init__(self, ruta_zip_origen: str, carpeta_destino: str, parent=None):
        super().__init__(parent)
        self.ruta_zip_origen = ruta_zip_origen
        self.carpeta_destino = carpeta_destino

    def run(self):
        try:
            raiz_dest = os.path.abspath(self.carpeta_destino)
            os.makedirs(raiz_dest, exist_ok=True)

            with zipfile.ZipFile(self.ruta_zip_origen, "r") as zf:
                entradas = [info for info in zf.infolist() if not info.is_dir()]
                total = len(entradas)
                if total == 0:
                    self.terminado.emit(
                        False,
                        "El archivo ZIP seleccionado no contiene archivos.",
                        {},
                    )
                    return

                nuevos = 0
                actualizados = 0
                omitidos = 0

                for idx, info in enumerate(entradas, start=1):
                    nombre_rel = info.filename.replace("\\", "/").lstrip("/")
                    dest_abs = os.path.abspath(os.path.join(raiz_dest, *nombre_rel.split("/")))

                    # Protección contra rutas maliciosas fuera de carpeta_destino (Zip Slip)
                    if os.path.commonpath([raiz_dest, dest_abs]) != raiz_dest:
                        omitidos += 1
                        continue

                    mtime_zip = datetime(*info.date_time).timestamp()
                    existe_previo = os.path.isfile(dest_abs)

                    if existe_previo:
                        mtime_local = os.path.getmtime(dest_abs)
                        # Tolerancia de 2 s por resolución DOS de fechas en archivos ZIP
                        if mtime_zip <= mtime_local + 2.0:
                            omitidos += 1
                            pct = int((idx * 100) / total)
                            self.progreso.emit(pct, f"Omitido (actual/antiguo): {nombre_rel}")
                            continue

                    os.makedirs(os.path.dirname(dest_abs), exist_ok=True)
                    with zf.open(info, "r") as f_src, open(dest_abs, "wb") as f_dst:
                        shutil.copyfileobj(f_src, f_dst)
                    os.utime(dest_abs, (mtime_zip, mtime_zip))

                    if existe_previo:
                        actualizados += 1
                        estado_txt = f"Actualizado: {nombre_rel}"
                    else:
                        nuevos += 1
                        estado_txt = f"Nuevo: {nombre_rel}"

                    pct = int((idx * 100) / total)
                    self.progreso.emit(pct, estado_txt)

            self.terminado.emit(
                True,
                "Restauración / actualización completada.",
                {
                    "total": total,
                    "nuevos": nuevos,
                    "actualizados": actualizados,
                    "omitidos": omitidos,
                },
            )
        except Exception as e:
            self.terminado.emit(False, f"Error restaurando desde ZIP: {e}", {})


class Respaldar_programa(QWidget):
    cerrado = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("RESPALDO Y ACTUALIZACIÓN DEL PROGRAMA (ZIP) - RSA")
        self.setStyleSheet(ESTILO_PANEL_CONFIG)
        self.raiz_proyecto = os.path.abspath(ruta_proyecto)
        self._hilo_activo = None

        layout_raiz = QVBoxLayout(self)
        layout_raiz.setContentsMargins(12, 10, 12, 10)
        layout_raiz.setSpacing(10)

        autorizado_pc, nombre_pc, msg_pc = verificar_permiso_respaldo_pc()
        lbl_seg = QLabel(
            f"Equipo actual: <b>{nombre_pc}</b> — {msg_pc}",
            self,
        )
        lbl_seg.setWordWrap(True)
        if autorizado_pc:
            lbl_seg.setStyleSheet(
                "background:#e8f5e9; color:#1b5e20; border:1px solid #81c784; "
                "border-radius:4px; padding:6px 10px;"
            )
        else:
            lbl_seg.setStyleSheet(
                "background:#ffebee; color:#b71c1c; border:1px solid #e57373; "
                "border-radius:4px; padding:6px 10px;"
            )
        layout_raiz.addWidget(lbl_seg)

        # 1. Sección de creación de respaldo ZIP
        grp_backup = QGroupBox("1. GENERAR RESPALDO DEL PROGRAMA (.ZIP)", self)
        v_bkp = QVBoxLayout(grp_backup)
        lbl_info_bkp = QLabel(
            f"<b>Origen:</b> <code>{self.raiz_proyecto}</code><br>"
            "<b>Carpetas incluidas:</b> <code>datos/</code>, <code>modulos externos/</code> y <code>src/</code> "
            "(respetando íntegramente su estructura de directorios).<br>"
            "<b>Exclusiones automáticas:</b> GitHub/Agente, <code>datos/mapas/VW Backup/</code>, "
            "archivos de Vectorworks (<code>*.vwx</code>, <code>*.vwxw</code>, <code>*.vwt</code>, <code>*.mcd</code>) "
            "y caché Python (<code>__pycache__/</code>, <code>*.pyc</code>).",
            grp_backup,
        )
        lbl_info_bkp.setWordWrap(True)
        lbl_info_bkp.setStyleSheet("font-weight: normal; color: #263238;")
        v_bkp.addWidget(lbl_info_bkp)

        h_bkp_btn = QHBoxLayout()
        self.btn_crear_zip = QPushButton("Generar Respaldo ZIP (Guardar como...)", grp_backup)
        self.btn_crear_zip.setObjectName("btn_primario")
        self.btn_crear_zip.setEnabled(autorizado_pc)
        self.btn_crear_zip.clicked.connect(self.ejecutar_respaldo_zip)
        h_bkp_btn.addWidget(self.btn_crear_zip)
        h_bkp_btn.addStretch()
        v_bkp.addLayout(h_bkp_btn)
        layout_raiz.addWidget(grp_backup)

        # 2. Progreso y bitácora
        grp_prog = QGroupBox("2. PROGRESO Y BITÁCORA DE OPERACIÓN", self)
        v_prog = QVBoxLayout(grp_prog)
        self.lbl_estado_op = QLabel("En espera.", grp_prog)
        self.lbl_estado_op.setStyleSheet("font-weight: normal; color: #37474f;")
        self.barra_progreso = QProgressBar(grp_prog)
        self.barra_progreso.setRange(0, 100)
        self.barra_progreso.setValue(0)
        self.txt_bitacora = QPlainTextEdit(grp_prog)
        self.txt_bitacora.setReadOnly(True)
        self.txt_bitacora.setMinimumHeight(180)
        v_prog.addWidget(self.lbl_estado_op)
        v_prog.addWidget(self.barra_progreso)
        v_prog.addWidget(self.txt_bitacora, 1)
        layout_raiz.addWidget(grp_prog, 1)

        h_pie = QHBoxLayout()
        h_pie.addStretch()
        self.btn_salir = QPushButton("Salir", self)
        self.btn_salir.setObjectName("btn_salir")
        self.btn_salir.clicked.connect(self.close)
        h_pie.addWidget(self.btn_salir)
        layout_raiz.addLayout(h_pie)

    def _establecer_controles_activos(self, habilitado: bool):
        autorizado_pc, _, _ = verificar_permiso_respaldo_pc()
        self.btn_crear_zip.setEnabled(habilitado and autorizado_pc)
        self.btn_salir.setEnabled(habilitado)

    def ejecutar_respaldo_zip(self):
        autorizado_pc, _, msg_pc = verificar_permiso_respaldo_pc()
        if not autorizado_pc:
            QMessageBox.warning(self, "Acceso Restringido", msg_pc)
            return

        nombre_sug = f"respaldo_rsa_sismologia_{datetime.now().strftime('%Y%m%d_%H%M')}.zip"
        ruta_zip, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar respaldo del programa como...",
            os.path.join(self.raiz_proyecto, nombre_sug),
            "Archivos ZIP (*.zip)",
        )
        if not ruta_zip:
            return
        if not ruta_zip.lower().endswith(".zip"):
            ruta_zip += ".zip"

        self.txt_bitacora.clear()
        self.barra_progreso.setValue(0)
        self.lbl_estado_op.setText("Comprimiendo archivos...")
        self._establecer_controles_activos(False)

        self._hilo_activo = HiloRespaldoZip(self.raiz_proyecto, ruta_zip, self)
        self._hilo_activo.progreso.connect(self._al_avanzar_operacion)
        self._hilo_activo.terminado.connect(self._al_terminar_respaldo)
        self._hilo_activo.start()

    def _al_avanzar_operacion(self, porcentaje: int, detalle: str):
        self.barra_progreso.setValue(porcentaje)
        self.lbl_estado_op.setText(detalle)

    def _al_terminar_respaldo(self, ok: bool, mensaje: str, stats: dict):
        self._establecer_controles_activos(True)
        if ok:
            self.barra_progreso.setValue(100)
            self.lbl_estado_op.setText(mensaje)
            self.txt_bitacora.appendPlainText(
                f"✓ {mensaje}\n"
                f"• Archivos comprimidos: {stats.get('incluidos', 0)}\n"
                f"• Elementos excluidos (VW Backup / Vectorworks / __pycache__): {stats.get('excluidos', 0)}"
            )
            QMessageBox.information(self, "Respaldo Completado", mensaje)
        else:
            self.lbl_estado_op.setText(mensaje)
            self.txt_bitacora.appendPlainText(f"✗ {mensaje}")
            QMessageBox.critical(self, "Error en Respaldo", mensaje)

    def limpiar_estado(self):
        if self._hilo_activo is not None and self._hilo_activo.isRunning():
            self._hilo_activo.wait(2000)
        self._hilo_activo = None

    def closeEvent(self, event):
        self.limpiar_estado()
        self.cerrado.emit()
        super().closeEvent(event)


class Restaurar_programa(QWidget):
    """
    Módulo abierto a cualquier equipo para descomprimir/actualizar el programa
    desde un archivo ZIP respetando la estructura de directorios y copiando
    únicamente archivos nuevos o más recientes.
    """
    cerrado = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ACTUALIZAR / RECUPERAR PROGRAMA DESDE ZIP - RSA")
        self.setStyleSheet(ESTILO_PANEL_CONFIG)
        self.raiz_proyecto = os.path.abspath(ruta_proyecto)
        self._hilo_activo = None

        layout_raiz = QVBoxLayout(self)
        layout_raiz.setContentsMargins(12, 10, 12, 10)
        layout_raiz.setSpacing(10)

        grp_rest = QGroupBox("1. SELECCIÓN DE RESPALDO (.ZIP) Y CARPETA DESTINO", self)
        grid_r = QGridLayout(grp_rest)

        self.edt_zip_origen = QLineEdit(grp_rest)
        self.edt_zip_origen.setPlaceholderText("Seleccione el archivo .zip de respaldo...")
        self.btn_buscar_zip = QPushButton("Examinar ZIP...", grp_rest)
        self.btn_buscar_zip.clicked.connect(self.seleccionar_zip_origen)

        self.edt_dir_destino = QLineEdit(self.raiz_proyecto, grp_rest)
        self.btn_buscar_dest = QPushButton("Carpeta destino...", grp_rest)
        self.btn_buscar_dest.clicked.connect(self.seleccionar_carpeta_destino)

        lbl_nota_inc = QLabel(
            "<b>Actualización ágil:</b> solo se copian archivos nuevos o con fecha de modificación "
            "más reciente que la versión existente en destino; las versiones iguales o más antiguas se omiten, "
            "respetando íntegramente la estructura de directorios.",
            grp_rest,
        )
        lbl_nota_inc.setWordWrap(True)
        lbl_nota_inc.setStyleSheet("font-weight: normal; color: #1e3a8a;")

        self.btn_restaurar_zip = QPushButton("Restaurar / Actualizar desde ZIP", grp_rest)
        self.btn_restaurar_zip.setObjectName("btn_primario")
        self.btn_restaurar_zip.clicked.connect(self.ejecutar_restauracion_zip)

        grid_r.addWidget(QLabel("Archivo ZIP:"), 0, 0)
        grid_r.addWidget(self.edt_zip_origen, 0, 1)
        grid_r.addWidget(self.btn_buscar_zip, 0, 2)
        grid_r.addWidget(QLabel("Carpeta destino:"), 1, 0)
        grid_r.addWidget(self.edt_dir_destino, 1, 1)
        grid_r.addWidget(self.btn_buscar_dest, 1, 2)
        grid_r.addWidget(lbl_nota_inc, 2, 0, 1, 3)
        grid_r.addWidget(self.btn_restaurar_zip, 3, 0, 1, 3)
        layout_raiz.addWidget(grp_rest)

        grp_prog = QGroupBox("2. PROGRESO Y BITÁCORA DE ACTUALIZACIÓN", self)
        v_prog = QVBoxLayout(grp_prog)
        self.lbl_estado_op = QLabel("En espera.", grp_prog)
        self.lbl_estado_op.setStyleSheet("font-weight: normal; color: #37474f;")
        self.barra_progreso = QProgressBar(grp_prog)
        self.barra_progreso.setRange(0, 100)
        self.barra_progreso.setValue(0)
        self.txt_bitacora = QPlainTextEdit(grp_prog)
        self.txt_bitacora.setReadOnly(True)
        self.txt_bitacora.setMinimumHeight(180)
        v_prog.addWidget(self.lbl_estado_op)
        v_prog.addWidget(self.barra_progreso)
        v_prog.addWidget(self.txt_bitacora, 1)
        layout_raiz.addWidget(grp_prog, 1)

        h_pie = QHBoxLayout()
        h_pie.addStretch()
        self.btn_salir = QPushButton("Salir", self)
        self.btn_salir.setObjectName("btn_salir")
        self.btn_salir.clicked.connect(self.close)
        h_pie.addWidget(self.btn_salir)
        layout_raiz.addLayout(h_pie)

    def _establecer_controles_activos(self, habilitado: bool):
        self.btn_buscar_zip.setEnabled(habilitado)
        self.btn_buscar_dest.setEnabled(habilitado)
        self.btn_restaurar_zip.setEnabled(habilitado)
        self.btn_salir.setEnabled(habilitado)

    def seleccionar_zip_origen(self):
        ruta, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar respaldo ZIP",
            self.raiz_proyecto,
            "Archivos ZIP (*.zip)",
        )
        if ruta:
            self.edt_zip_origen.setText(ruta)

    def seleccionar_carpeta_destino(self):
        carpeta = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar carpeta destino para restaurar",
            self.edt_dir_destino.text().strip() or self.raiz_proyecto,
        )
        if carpeta:
            self.edt_dir_destino.setText(carpeta)

    def ejecutar_restauracion_zip(self):
        ruta_zip = self.edt_zip_origen.text().strip()
        carpeta_dest = self.edt_dir_destino.text().strip()
        if not ruta_zip or not os.path.isfile(ruta_zip):
            QMessageBox.warning(self, "Validación", "Seleccione un archivo .zip válido.")
            return
        if not carpeta_dest:
            QMessageBox.warning(self, "Validación", "Indique la carpeta destino.")
            return

        resp = QMessageBox.question(
            self,
            "Confirmar actualización incremental",
            f"Se extraerán únicamente los archivos nuevos o más recientes desde:\n{ruta_zip}\n\n"
            f"Hacia:\n{carpeta_dest}\n\n¿Desea continuar?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if resp != QMessageBox.Yes:
            return

        self.txt_bitacora.clear()
        self.barra_progreso.setValue(0)
        self.lbl_estado_op.setText("Verificando fechas y extrayendo archivos más nuevos...")
        self._establecer_controles_activos(False)

        self._hilo_activo = HiloRestaurarZip(ruta_zip, carpeta_dest, self)
        self._hilo_activo.progreso.connect(self._al_avanzar_operacion)
        self._hilo_activo.terminado.connect(self._al_terminar_restauracion)
        self._hilo_activo.start()

    def _al_avanzar_operacion(self, porcentaje: int, detalle: str):
        self.barra_progreso.setValue(porcentaje)
        self.lbl_estado_op.setText(detalle)

    def _al_terminar_restauracion(self, ok: bool, mensaje: str, stats: dict):
        self._establecer_controles_activos(True)
        if ok:
            self.barra_progreso.setValue(100)
            self.lbl_estado_op.setText(mensaje)
            resumen = (
                f"✓ {mensaje}\n"
                f"• Total en ZIP: {stats.get('total', 0)}\n"
                f"• Archivos nuevos copiados: {stats.get('nuevos', 0)}\n"
                f"• Archivos actualizados (más recientes): {stats.get('actualizados', 0)}\n"
                f"• Archivos omitidos (iguales o más antiguos): {stats.get('omitidos', 0)}"
            )
            self.txt_bitacora.appendPlainText(resumen)
            QMessageBox.information(self, "Actualización Completada", resumen)
        else:
            self.lbl_estado_op.setText(mensaje)
            self.txt_bitacora.appendPlainText(f"✗ {mensaje}")
            QMessageBox.critical(self, "Error en Actualización", mensaje)

    def limpiar_estado(self):
        if self._hilo_activo is not None and self._hilo_activo.isRunning():
            self._hilo_activo.wait(2000)
        self._hilo_activo = None

    def closeEvent(self, event):
        self.limpiar_estado()
        self.cerrado.emit()
        super().closeEvent(event)


# =========================================================================================
# 4. CONFIGURACIÓN DE RESPONSABLES Y DRIVES VIRTUALES (datos/responsables.csv — Extensible)
# =========================================================================================
class Configurar_responsables(QWidget):
    cerrado = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("CONFIGURACIÓN DE RESPONSABLES Y UNIDADES VIRTUALES - RSA")
        self.setStyleSheet(ESTILO_PANEL_CONFIG)
        self.ruta_csv = os.path.join(ruta_datos, "responsables.csv")
        filas_raw = lectura_archivo(self.ruta_csv) or []
        self.filas_responsables = [list(r[:3]) for r in filas_raw if r and len(r) >= 3]

        layout_raiz = QHBoxLayout(self)
        layout_raiz.setContentsMargins(8, 8, 8, 8)

        panel_izq = QWidget(self)
        panel_izq.setFixedWidth(360)
        v_izq = QVBoxLayout(panel_izq)

        grp_form = QGroupBox("RESPONSABLE Y UNIDADES VIRTUALES (PROCESOV2)", panel_izq)
        form = QFormLayout(grp_form)

        self.edt_nombre = QLineEdit(grp_form)
        self.edt_nombre.setPlaceholderText("Nombre completo del responsable")
        self.edt_drive1 = QLineEdit(grp_form)
        self.edt_drive1.setPlaceholderText("Ej: K:\\")
        self.edt_drive2 = QLineEdit(grp_form)
        self.edt_drive2.setPlaceholderText("Ej: L:\\")
        self.chk_autorizado_cfg_pc = QCheckBox(
            "Autorizado por Admin (RSA) para editar Configuración en este PC", grp_form
        )

        form.addRow("Nombre Responsable:", self.edt_nombre)
        form.addRow("Unidad Virtual 1 (.sis/.fas):", self.edt_drive1)
        form.addRow("Unidad Virtual 2 (fastHypo):", self.edt_drive2)
        form.addRow("Permiso Configuración PC:", self.chk_autorizado_cfg_pc)
        v_izq.addWidget(grp_form)

        h_acc = QHBoxLayout()
        self.btn_actualizar = QPushButton("Actualizar Seleccionado", panel_izq)
        self.btn_actualizar.clicked.connect(self.actualizar_seleccionado)
        self.btn_agregar = QPushButton("+ Agregar Responsable", panel_izq)
        self.btn_agregar.clicked.connect(self.agregar_nuevo)
        h_acc.addWidget(self.btn_actualizar)
        h_acc.addWidget(self.btn_agregar)
        v_izq.addLayout(h_acc)

        self.btn_eliminar = QPushButton("Eliminar Responsable Seleccionado", panel_izq)
        self.btn_eliminar.clicked.connect(self.eliminar_seleccionado)
        v_izq.addWidget(self.btn_eliminar)
        v_izq.addWidget(_crear_etiqueta_estado_seguridad(panel_izq))
        v_izq.addStretch()

        self.btn_guardar = QPushButton("Guardar responsables.csv y permisos PC", panel_izq)
        self.btn_guardar.setObjectName("btn_primario")
        self.btn_guardar.clicked.connect(self.guardar_responsables)
        self.btn_salir = QPushButton("Salir", panel_izq)
        self.btn_salir.setObjectName("btn_salir")
        self.btn_salir.clicked.connect(self.close)
        v_izq.addWidget(self.btn_guardar)
        v_izq.addWidget(self.btn_salir)

        panel_der = QWidget(self)
        v_der = QVBoxLayout(panel_der)
        self.tabla = QTableWidget(panel_der)
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels([
            "Responsable", "Unidad Virtual 1", "Unidad Virtual 2",
            "Estado Unidades en PC", "Autorizado Config. en este PC"
        ])
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.itemSelectionChanged.connect(self._al_seleccionar)
        v_der.addWidget(self.tabla)

        cfg_pc = cargar_config_local_pc()
        self.usuarios_autorizados_pc = set(
            str(u).strip() for u in (cfg_pc.get("usuarios_autorizados_config") or ["RSA"])
        )
        self.usuarios_autorizados_pc.add("RSA")

        layout_raiz.addWidget(panel_izq, 0)
        layout_raiz.addWidget(panel_der, 1)
        self._poblar_tabla()
        if self.tabla.rowCount() > 0:
            self.tabla.selectRow(0)

    @staticmethod
    def _normalizar_drive(d: str) -> str:
        t = (d or "").strip()
        if len(t) == 1 and t.isalpha():
            return f"{t.upper()}:\\"
        if len(t) == 2 and t[1] == ":":
            return f"{t.upper()}\\"
        return t

    def _poblar_tabla(self):
        self.tabla.setRowCount(len(self.filas_responsables))
        for r_idx, fila in enumerate(self.filas_responsables):
            nom, d1, d2 = str(fila[0]).strip(), str(fila[1]).strip(), str(fila[2]).strip()
            ok1 = os.path.isdir(d1)
            ok2 = os.path.isdir(d2)
            estado = "✓ Conectadas" if (ok1 and ok2) else "No montadas"
            es_aut = (nom == "RSA") or (nom in self.usuarios_autorizados_pc)
            txt_aut = "★ Administrador (RSA)" if nom == "RSA" else ("✓ Autorizado en este PC" if es_aut else "No autorizado")
            for c_idx, val in enumerate([nom, d1, d2, estado, txt_aut]):
                it = QTableWidgetItem(val)
                if nom == "RSA" or es_aut:
                    f = it.font()
                    f.setBold(True)
                    it.setFont(f)
                self.tabla.setItem(r_idx, c_idx, it)

    def _al_seleccionar(self):
        sel = self.tabla.selectionModel().selectedRows()
        if not sel:
            return
        idx = sel[0].row()
        if not (0 <= idx < len(self.filas_responsables)):
            return
        f = self.filas_responsables[idx]
        nom = str(f[0]).strip()
        self.edt_nombre.setText(nom)
        self.edt_drive1.setText(str(f[1]).strip())
        self.edt_drive2.setText(str(f[2]).strip())
        self.chk_autorizado_cfg_pc.setChecked(nom == "RSA" or nom in self.usuarios_autorizados_pc)
        self.chk_autorizado_cfg_pc.setEnabled(nom != "RSA")

    def actualizar_seleccionado(self):
        sel = self.tabla.selectionModel().selectedRows()
        if not sel:
            return
        idx = sel[0].row()
        nom_orig = str(self.filas_responsables[idx][0]).strip()
        nom = "RSA" if nom_orig == "RSA" else self.edt_nombre.text().strip()
        d1 = self._normalizar_drive(self.edt_drive1.text())
        d2 = self._normalizar_drive(self.edt_drive2.text())
        if not nom or not d1 or not d2:
            QMessageBox.warning(self, "Validación", "Complete el nombre y las dos unidades virtuales.")
            return
        self.filas_responsables[idx] = [nom, d1, d2]
        if nom == "RSA" or self.chk_autorizado_cfg_pc.isChecked():
            self.usuarios_autorizados_pc.add(nom)
        else:
            self.usuarios_autorizados_pc.discard(nom)
        self._poblar_tabla()
        self.tabla.selectRow(idx)

    def agregar_nuevo(self):
        nom = self.edt_nombre.text().strip()
        d1 = self._normalizar_drive(self.edt_drive1.text())
        d2 = self._normalizar_drive(self.edt_drive2.text())
        if not nom or not d1 or not d2:
            QMessageBox.warning(self, "Validación", "Complete el nombre y las dos unidades virtuales.")
            return
        self.filas_responsables.append([nom, d1, d2])
        if self.chk_autorizado_cfg_pc.isChecked():
            self.usuarios_autorizados_pc.add(nom)
        self._poblar_tabla()
        self.tabla.selectRow(len(self.filas_responsables) - 1)

    def eliminar_seleccionado(self):
        sel = self.tabla.selectionModel().selectedRows()
        if not sel:
            return
        idx = sel[0].row()
        nom = str(self.filas_responsables[idx][0]).strip()
        if nom == "RSA":
            QMessageBox.warning(self, "Protegido", "El usuario maestro «RSA» es obligatorio y no puede eliminarse.")
            return
        self.usuarios_autorizados_pc.discard(nom)
        self.filas_responsables.pop(idx)
        self._poblar_tabla()

    def guardar_responsables(self):
        def _validar_resp(filas_totales):
            if not any(str(r[0]).strip() == "RSA" for r in filas_totales):
                return False, "El usuario maestro «RSA» debe permanecer siempre en responsables.csv."
            return True, ""

        ok = _guardar_config_con_seguridad(
            self,
            self.ruta_csv,
            self.filas_responsables,
            "responsables.csv y permisos de configuración en este PC",
            validador_extra=_validar_resp,
        )
        if ok:
            lista_aut = ["RSA"] + sorted(u for u in self.usuarios_autorizados_pc if u != "RSA")
            guardar_config_local_pc({"usuarios_autorizados_config": lista_aut})

    def limpiar_estado(self):
        pass

    def closeEvent(self, event):
        self.limpiar_estado()
        self.cerrado.emit()
        super().closeEvent(event)


# ==============================================================================
# 7. RESPALDO Y RESTAURACIÓN DEL PROGRAMA (ZIP - SOLO PC ADMINISTRADOR)
# ==============================================================================

CARPETAS_RESPALDO_PROGRAMA = ("datos", "modulos externos", "src")
CARPETAS_EXCLUIDAS_RESPALDO = {"__pycache__", "vw backup"}
EXTENSIONES_EXCLUIDAS_RESPALDO = {".vwx", ".vwxw", ".vwt", ".mcd", ".pyc", ".pyo"}


def recolectar_archivos_respaldo(raiz_origen: str):
    """
    Recorre `datos/`, `modulos externos/` y `src/` dentro de `raiz_origen`
    excluyendo carpetas de caché (`__pycache__`), respaldos Vectorworks (`VW Backup`)
    y extensiones excluidas (`.vwx`, `.vwxw`, `.vwt`, `.mcd`, `.pyc`, `.pyo`).

    Retorna:
        tuple[list[tuple[str, str]], int]: `(lista_(ruta_abs, ruta_rel_zip), conteo_excluidos)`
    """
    raiz_path = Path(raiz_origen).resolve()
    archivos_incluir = []
    conteo_excluidos = 0

    for carpeta_base in CARPETAS_RESPALDO_PROGRAMA:
        dir_objetivo = raiz_path / carpeta_base
        if not dir_objetivo.is_dir():
            continue
        for actual, subdirs, nombres in os.walk(dir_objetivo):
            subdirs_filtrados = []
            for d in subdirs:
                if d.strip().lower() in CARPETAS_EXCLUIDAS_RESPALDO:
                    conteo_excluidos += 1
                else:
                    subdirs_filtrados.append(d)
            subdirs[:] = sorted(subdirs_filtrados, key=str.lower)

            for nom in sorted(nombres, key=str.lower):
                ext = os.path.splitext(nom)[1].lower()
                if ext in EXTENSIONES_EXCLUIDAS_RESPALDO:
                    conteo_excluidos += 1
                    continue
                ruta_abs = os.path.join(actual, nom)
                ruta_rel = os.path.relpath(ruta_abs, raiz_path).replace("\\", "/")
                archivos_incluir.append((ruta_abs, ruta_rel))

    return archivos_incluir, conteo_excluidos


class HiloRespaldoZip(QThread):
    """Hilo de trabajo para comprimir el programa en formato ZIP sin bloquear la UI."""

    progreso = pyqtSignal(int, str)
    terminado = pyqtSignal(bool, str, dict)

    def __init__(self, raiz_origen: str, ruta_zip_destino: str, parent=None):
        super().__init__(parent)
        self.raiz_origen = raiz_origen
        self.ruta_zip_destino = ruta_zip_destino

    def run(self):
        ruta_tmp = self.ruta_zip_destino + ".tmp"
        try:
            archivos, excluidos = recolectar_archivos_respaldo(self.raiz_origen)
            total = len(archivos)
            if total == 0:
                self.terminado.emit(
                    False,
                    "No se encontraron archivos válidos en datos/, modulos externos/ o src/.",
                    {"incluidos": 0, "excluidos": excluidos},
                )
                return

            os.makedirs(os.path.dirname(os.path.abspath(self.ruta_zip_destino)), exist_ok=True)
            with zipfile.ZipFile(ruta_tmp, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
                for idx, (ruta_abs, ruta_rel) in enumerate(archivos, start=1):
                    zf.write(ruta_abs, arcname=ruta_rel)
                    pct = int((idx * 100) / total)
                    self.progreso.emit(pct, ruta_rel)

            os.replace(ruta_tmp, self.ruta_zip_destino)
            tam_mb = os.path.getsize(self.ruta_zip_destino) / (1024.0 * 1024.0)
            self.terminado.emit(
                True,
                f"Respaldo generado correctamente ({tam_mb:.2f} MB).",
                {"incluidos": total, "excluidos": excluidos, "tam_mb": tam_mb},
            )
        except Exception as e:
            try:
                if os.path.exists(ruta_tmp):
                    os.remove(ruta_tmp)
            except Exception:
                pass
            self.terminado.emit(False, f"Error generando el respaldo ZIP: {e}", {})


class HiloRestaurarZip(QThread):
    """
    Hilo de trabajo para descomprimir un respaldo ZIP respetando la estructura
    de directorios y copiando únicamente archivos nuevos o más recientes.
    """

    progreso = pyqtSignal(int, str)
    terminado = pyqtSignal(bool, str, dict)

    def __init__(self, ruta_zip_origen: str, carpeta_destino: str, parent=None):
        super().__init__(parent)
        self.ruta_zip_origen = ruta_zip_origen
        self.carpeta_destino = carpeta_destino

    def run(self):
        try:
            raiz_dest = os.path.abspath(self.carpeta_destino)
            os.makedirs(raiz_dest, exist_ok=True)

            with zipfile.ZipFile(self.ruta_zip_origen, "r") as zf:
                entradas = [info for info in zf.infolist() if not info.is_dir()]
                total = len(entradas)
                if total == 0:
                    self.terminado.emit(
                        False,
                        "El archivo ZIP seleccionado no contiene archivos.",
                        {},
                    )
                    return

                nuevos = 0
                actualizados = 0
                omitidos = 0

                for idx, info in enumerate(entradas, start=1):
                    nombre_rel = info.filename.replace("\\", "/").lstrip("/")
                    dest_abs = os.path.abspath(os.path.join(raiz_dest, *nombre_rel.split("/")))

                    # Protección contra rutas maliciosas fuera de carpeta_destino (Zip Slip)
                    if os.path.commonpath([raiz_dest, dest_abs]) != raiz_dest:
                        omitidos += 1
                        continue

                    mtime_zip = datetime(*info.date_time).timestamp()
                    existe_previo = os.path.isfile(dest_abs)

                    if existe_previo:
                        mtime_local = os.path.getmtime(dest_abs)
                        # Tolerancia de 2 s por resolución DOS de fechas en archivos ZIP
                        if mtime_zip <= mtime_local + 2.0:
                            omitidos += 1
                            pct = int((idx * 100) / total)
                            self.progreso.emit(pct, f"Omitido (actual/antiguo): {nombre_rel}")
                            continue

                    os.makedirs(os.path.dirname(dest_abs), exist_ok=True)
                    with zf.open(info, "r") as f_src, open(dest_abs, "wb") as f_dst:
                        shutil.copyfileobj(f_src, f_dst)
                    os.utime(dest_abs, (mtime_zip, mtime_zip))

                    if existe_previo:
                        actualizados += 1
                        estado_txt = f"Actualizado: {nombre_rel}"
                    else:
                        nuevos += 1
                        estado_txt = f"Nuevo: {nombre_rel}"

                    pct = int((idx * 100) / total)
                    self.progreso.emit(pct, estado_txt)

            self.terminado.emit(
                True,
                "Restauración / actualización completada.",
                {
                    "total": total,
                    "nuevos": nuevos,
                    "actualizados": actualizados,
                    "omitidos": omitidos,
                },
            )
        except Exception as e:
            self.terminado.emit(False, f"Error restaurando desde ZIP: {e}", {})


class Respaldar_programa(QWidget):
    cerrado = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("RESPALDO Y ACTUALIZACIÓN DEL PROGRAMA (ZIP) - RSA")
        self.setStyleSheet(ESTILO_PANEL_CONFIG)
        self.raiz_proyecto = os.path.abspath(ruta_proyecto)
        self._hilo_activo = None

        layout_raiz = QVBoxLayout(self)
        layout_raiz.setContentsMargins(12, 10, 12, 10)
        layout_raiz.setSpacing(10)

        autorizado_pc, nombre_pc, msg_pc = verificar_permiso_respaldo_pc()
        lbl_seg = QLabel(
            f"Equipo actual: <b>{nombre_pc}</b> — {msg_pc}",
            self,
        )
        lbl_seg.setWordWrap(True)
        if autorizado_pc:
            lbl_seg.setStyleSheet(
                "background:#e8f5e9; color:#1b5e20; border:1px solid #81c784; "
                "border-radius:4px; padding:6px 10px;"
            )
        else:
            lbl_seg.setStyleSheet(
                "background:#ffebee; color:#b71c1c; border:1px solid #e57373; "
                "border-radius:4px; padding:6px 10px;"
            )
        layout_raiz.addWidget(lbl_seg)

        # 1. Sección de creación de respaldo ZIP
        grp_backup = QGroupBox("1. GENERAR RESPALDO DEL PROGRAMA (.ZIP)", self)
        v_bkp = QVBoxLayout(grp_backup)
        lbl_info_bkp = QLabel(
            f"<b>Origen:</b> <code>{self.raiz_proyecto}</code><br>"
            "<b>Carpetas incluidas:</b> <code>datos/</code>, <code>modulos externos/</code> y <code>src/</code> "
            "(respetando íntegramente su estructura de directorios).<br>"
            "<b>Exclusiones automáticas:</b> GitHub/Agente, <code>datos/mapas/VW Backup/</code>, "
            "archivos de Vectorworks (<code>*.vwx</code>, <code>*.vwxw</code>, <code>*.vwt</code>, <code>*.mcd</code>) "
            "y caché Python (<code>__pycache__/</code>, <code>*.pyc</code>).",
            grp_backup,
        )
        lbl_info_bkp.setWordWrap(True)
        lbl_info_bkp.setStyleSheet("font-weight: normal; color: #263238;")
        v_bkp.addWidget(lbl_info_bkp)

        h_bkp_btn = QHBoxLayout()
        self.btn_crear_zip = QPushButton("Generar Respaldo ZIP (Guardar como...)", grp_backup)
        self.btn_crear_zip.setObjectName("btn_primario")
        self.btn_crear_zip.setEnabled(autorizado_pc)
        self.btn_crear_zip.clicked.connect(self.ejecutar_respaldo_zip)
        h_bkp_btn.addWidget(self.btn_crear_zip)
        h_bkp_btn.addStretch()
        v_bkp.addLayout(h_bkp_btn)
        layout_raiz.addWidget(grp_backup)

        # 2. Progreso y bitácora
        grp_prog = QGroupBox("2. PROGRESO Y BITÁCORA DE OPERACIÓN", self)
        v_prog = QVBoxLayout(grp_prog)
        self.lbl_estado_op = QLabel("En espera.", grp_prog)
        self.lbl_estado_op.setStyleSheet("font-weight: normal; color: #37474f;")
        self.barra_progreso = QProgressBar(grp_prog)
        self.barra_progreso.setRange(0, 100)
        self.barra_progreso.setValue(0)
        self.txt_bitacora = QPlainTextEdit(grp_prog)
        self.txt_bitacora.setReadOnly(True)
        self.txt_bitacora.setMinimumHeight(180)
        v_prog.addWidget(self.lbl_estado_op)
        v_prog.addWidget(self.barra_progreso)
        v_prog.addWidget(self.txt_bitacora, 1)
        layout_raiz.addWidget(grp_prog, 1)

        h_pie = QHBoxLayout()
        h_pie.addStretch()
        self.btn_salir = QPushButton("Salir", self)
        self.btn_salir.setObjectName("btn_salir")
        self.btn_salir.clicked.connect(self.close)
        h_pie.addWidget(self.btn_salir)
        layout_raiz.addLayout(h_pie)

    def _establecer_controles_activos(self, habilitado: bool):
        autorizado_pc, _, _ = verificar_permiso_respaldo_pc()
        self.btn_crear_zip.setEnabled(habilitado and autorizado_pc)
        self.btn_salir.setEnabled(habilitado)

    def ejecutar_respaldo_zip(self):
        autorizado_pc, _, msg_pc = verificar_permiso_respaldo_pc()
        if not autorizado_pc:
            QMessageBox.warning(self, "Acceso Restringido", msg_pc)
            return

        nombre_sug = f"respaldo_rsa_sismologia_{datetime.now().strftime('%Y%m%d_%H%M')}.zip"
        ruta_zip, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar respaldo del programa como...",
            os.path.join(self.raiz_proyecto, nombre_sug),
            "Archivos ZIP (*.zip)",
        )
        if not ruta_zip:
            return
        if not ruta_zip.lower().endswith(".zip"):
            ruta_zip += ".zip"

        self.txt_bitacora.clear()
        self.barra_progreso.setValue(0)
        self.lbl_estado_op.setText("Comprimiendo archivos...")
        self._establecer_controles_activos(False)

        self._hilo_activo = HiloRespaldoZip(self.raiz_proyecto, ruta_zip, self)
        self._hilo_activo.progreso.connect(self._al_avanzar_operacion)
        self._hilo_activo.terminado.connect(self._al_terminar_respaldo)
        self._hilo_activo.start()

    def _al_avanzar_operacion(self, porcentaje: int, detalle: str):
        self.barra_progreso.setValue(porcentaje)
        self.lbl_estado_op.setText(detalle)

    def _al_terminar_respaldo(self, ok: bool, mensaje: str, stats: dict):
        self._establecer_controles_activos(True)
        if ok:
            self.barra_progreso.setValue(100)
            self.lbl_estado_op.setText(mensaje)
            self.txt_bitacora.appendPlainText(
                f"✓ {mensaje}\n"
                f"• Archivos comprimidos: {stats.get('incluidos', 0)}\n"
                f"• Elementos excluidos (VW Backup / Vectorworks / __pycache__): {stats.get('excluidos', 0)}"
            )
            QMessageBox.information(self, "Respaldo Completado", mensaje)
        else:
            self.lbl_estado_op.setText(mensaje)
            self.txt_bitacora.appendPlainText(f"✗ {mensaje}")
            QMessageBox.critical(self, "Error en Respaldo", mensaje)

    def limpiar_estado(self):
        if self._hilo_activo is not None and self._hilo_activo.isRunning():
            self._hilo_activo.wait(2000)
        self._hilo_activo = None

    def closeEvent(self, event):
        self.limpiar_estado()
        self.cerrado.emit()
        super().closeEvent(event)


class Restaurar_programa(QWidget):
    """
    Módulo abierto a cualquier equipo para descomprimir/actualizar el programa
    desde un archivo ZIP respetando la estructura de directorios y copiando
    únicamente archivos nuevos o más recientes.
    """
    cerrado = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ACTUALIZAR / RECUPERAR PROGRAMA DESDE ZIP - RSA")
        self.setStyleSheet(ESTILO_PANEL_CONFIG)
        self.raiz_proyecto = os.path.abspath(ruta_proyecto)
        self._hilo_activo = None

        layout_raiz = QVBoxLayout(self)
        layout_raiz.setContentsMargins(12, 10, 12, 10)
        layout_raiz.setSpacing(10)

        grp_rest = QGroupBox("1. SELECCIÓN DE RESPALDO (.ZIP) Y CARPETA DESTINO", self)
        grid_r = QGridLayout(grp_rest)

        self.edt_zip_origen = QLineEdit(grp_rest)
        self.edt_zip_origen.setPlaceholderText("Seleccione el archivo .zip de respaldo...")
        self.btn_buscar_zip = QPushButton("Examinar ZIP...", grp_rest)
        self.btn_buscar_zip.clicked.connect(self.seleccionar_zip_origen)

        self.edt_dir_destino = QLineEdit(self.raiz_proyecto, grp_rest)
        self.btn_buscar_dest = QPushButton("Carpeta destino...", grp_rest)
        self.btn_buscar_dest.clicked.connect(self.seleccionar_carpeta_destino)

        lbl_nota_inc = QLabel(
            "<b>Actualización ágil:</b> solo se copian archivos nuevos o con fecha de modificación "
            "más reciente que la versión existente en destino; las versiones iguales o más antiguas se omiten, "
            "respetando íntegramente la estructura de directorios.",
            grp_rest,
        )
        lbl_nota_inc.setWordWrap(True)
        lbl_nota_inc.setStyleSheet("font-weight: normal; color: #1e3a8a;")

        self.btn_restaurar_zip = QPushButton("Restaurar / Actualizar desde ZIP", grp_rest)
        self.btn_restaurar_zip.setObjectName("btn_primario")
        self.btn_restaurar_zip.clicked.connect(self.ejecutar_restauracion_zip)

        grid_r.addWidget(QLabel("Archivo ZIP:"), 0, 0)
        grid_r.addWidget(self.edt_zip_origen, 0, 1)
        grid_r.addWidget(self.btn_buscar_zip, 0, 2)
        grid_r.addWidget(QLabel("Carpeta destino:"), 1, 0)
        grid_r.addWidget(self.edt_dir_destino, 1, 1)
        grid_r.addWidget(self.btn_buscar_dest, 1, 2)
        grid_r.addWidget(lbl_nota_inc, 2, 0, 1, 3)
        grid_r.addWidget(self.btn_restaurar_zip, 3, 0, 1, 3)
        layout_raiz.addWidget(grp_rest)

        grp_prog = QGroupBox("2. PROGRESO Y BITÁCORA DE ACTUALIZACIÓN", self)
        v_prog = QVBoxLayout(grp_prog)
        self.lbl_estado_op = QLabel("En espera.", grp_prog)
        self.lbl_estado_op.setStyleSheet("font-weight: normal; color: #37474f;")
        self.barra_progreso = QProgressBar(grp_prog)
        self.barra_progreso.setRange(0, 100)
        self.barra_progreso.setValue(0)
        self.txt_bitacora = QPlainTextEdit(grp_prog)
        self.txt_bitacora.setReadOnly(True)
        self.txt_bitacora.setMinimumHeight(180)
        v_prog.addWidget(self.lbl_estado_op)
        v_prog.addWidget(self.barra_progreso)
        v_prog.addWidget(self.txt_bitacora, 1)
        layout_raiz.addWidget(grp_prog, 1)

        h_pie = QHBoxLayout()
        h_pie.addStretch()
        self.btn_salir = QPushButton("Salir", self)
        self.btn_salir.setObjectName("btn_salir")
        self.btn_salir.clicked.connect(self.close)
        h_pie.addWidget(self.btn_salir)
        layout_raiz.addLayout(h_pie)

    def _establecer_controles_activos(self, habilitado: bool):
        self.btn_buscar_zip.setEnabled(habilitado)
        self.btn_buscar_dest.setEnabled(habilitado)
        self.btn_restaurar_zip.setEnabled(habilitado)
        self.btn_salir.setEnabled(habilitado)

    def seleccionar_zip_origen(self):
        ruta, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar respaldo ZIP",
            self.raiz_proyecto,
            "Archivos ZIP (*.zip)",
        )
        if ruta:
            self.edt_zip_origen.setText(ruta)

    def seleccionar_carpeta_destino(self):
        carpeta = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar carpeta destino para restaurar",
            self.edt_dir_destino.text().strip() or self.raiz_proyecto,
        )
        if carpeta:
            self.edt_dir_destino.setText(carpeta)

    def ejecutar_restauracion_zip(self):
        ruta_zip = self.edt_zip_origen.text().strip()
        carpeta_dest = self.edt_dir_destino.text().strip()
        if not ruta_zip or not os.path.isfile(ruta_zip):
            QMessageBox.warning(self, "Validación", "Seleccione un archivo .zip válido.")
            return
        if not carpeta_dest:
            QMessageBox.warning(self, "Validación", "Indique la carpeta destino.")
            return

        resp = QMessageBox.question(
            self,
            "Confirmar actualización incremental",
            f"Se extraerán únicamente los archivos nuevos o más recientes desde:\n{ruta_zip}\n\n"
            f"Hacia:\n{carpeta_dest}\n\n¿Desea continuar?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if resp != QMessageBox.Yes:
            return

        self.txt_bitacora.clear()
        self.barra_progreso.setValue(0)
        self.lbl_estado_op.setText("Verificando fechas y extrayendo archivos más nuevos...")
        self._establecer_controles_activos(False)

        self._hilo_activo = HiloRestaurarZip(ruta_zip, carpeta_dest, self)
        self._hilo_activo.progreso.connect(self._al_avanzar_operacion)
        self._hilo_activo.terminado.connect(self._al_terminar_restauracion)
        self._hilo_activo.start()

    def _al_avanzar_operacion(self, porcentaje: int, detalle: str):
        self.barra_progreso.setValue(porcentaje)
        self.lbl_estado_op.setText(detalle)

    def _al_terminar_restauracion(self, ok: bool, mensaje: str, stats: dict):
        self._establecer_controles_activos(True)
        if ok:
            self.barra_progreso.setValue(100)
            self.lbl_estado_op.setText(mensaje)
            resumen = (
                f"✓ {mensaje}\n"
                f"• Total en ZIP: {stats.get('total', 0)}\n"
                f"• Archivos nuevos copiados: {stats.get('nuevos', 0)}\n"
                f"• Archivos actualizados (más recientes): {stats.get('actualizados', 0)}\n"
                f"• Archivos omitidos (iguales o más antiguos): {stats.get('omitidos', 0)}"
            )
            self.txt_bitacora.appendPlainText(resumen)
            QMessageBox.information(self, "Actualización Completada", resumen)
        else:
            self.lbl_estado_op.setText(mensaje)
            self.txt_bitacora.appendPlainText(f"✗ {mensaje}")
            QMessageBox.critical(self, "Error en Actualización", mensaje)

    def limpiar_estado(self):
        if self._hilo_activo is not None and self._hilo_activo.isRunning():
            self._hilo_activo.wait(2000)
        self._hilo_activo = None

    def closeEvent(self, event):
        self.limpiar_estado()
        self.cerrado.emit()
        super().closeEvent(event)


# =========================================================================================
# 5. CONFIGURACIÓN DE MAPAS Y REGIONES CON VISOR GIS INTERACTIVO (datos/mapas/mapas.csv)
# =========================================================================================
class Configurar_mapas(QWidget):
    cerrado = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("CONFIGURACIÓN DE MAPAS Y REGIONES GIS - RSA")
        self.setStyleSheet(ESTILO_PANEL_CONFIG)
        self.ruta_csv = os.path.join(ruta_datos, "mapas", "mapas.csv")
        _, self.catalogo_estaciones = _leer_catalogo_estaciones_completo()

        filas_raw = lectura_archivo(self.ruta_csv) or []
        self.cabecera = (
            filas_raw[0]
            if filas_raw
            else ["nombre", "lat_min", "lat_max", "long_min", "long_max", "salto", "estaciones"]
        )
        self.filas_mapas = []
        for r in filas_raw[1:]:
            if not r:
                continue
            r_norm = list(r) + [""] * max(0, 7 - len(r))
            self.filas_mapas.append(r_norm[:7])

        self._bloqueando_eventos_ui = False

        layout_raiz = QHBoxLayout(self)
        layout_raiz.setContentsMargins(8, 8, 8, 8)
        splitter = QSplitter(Qt.Horizontal, self)
        layout_raiz.addWidget(splitter)

        # Panel izquierdo envuelto en QScrollArea para evitar recortes verticales en pantallas bajas
        scroll_izq = QScrollArea(self)
        scroll_izq.setWidgetResizable(True)
        scroll_izq.setFrameShape(QScrollArea.NoFrame)
        scroll_izq.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_izq.setMinimumWidth(510)
        scroll_izq.setMaximumWidth(620)

        panel_izq = QWidget(scroll_izq)
        v_izq = QVBoxLayout(panel_izq)
        v_izq.setContentsMargins(4, 4, 6, 6)

        grp_lista = QGroupBox("1. REGIONES Y MAPAS REGISTRADOS (mapas.csv)", panel_izq)
        v_lista = QVBoxLayout(grp_lista)
        v_lista.setContentsMargins(6, 6, 6, 8)
        self.tabla_mapas = QTableWidget(grp_lista)
        self.tabla_mapas.setColumnCount(7)
        self.tabla_mapas.setHorizontalHeaderLabels(self.cabecera)
        self.tabla_mapas.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla_mapas.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabla_mapas.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla_mapas.setMinimumHeight(250)
        self.tabla_mapas.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.tabla_mapas.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.tabla_mapas.verticalHeader().setDefaultSectionSize(24)
        self.tabla_mapas.horizontalHeader().setStretchLastSection(True)
        self.tabla_mapas.itemSelectionChanged.connect(self._al_seleccionar_mapa)
        v_lista.addWidget(self.tabla_mapas, 1)
        v_izq.addWidget(grp_lista, 3)

        grp_limites = QGroupBox("2. ENCUADRE GEOGRÁFICO Y GRILLA (INTERACTIVO CON GIS)", panel_izq)
        grid = QGridLayout(grp_limites)
        self.edt_nombre_mapa = QLineEdit(grp_limites)
        self.spn_lat_min = QDoubleSpinBox(grp_limites)
        self.spn_lat_max = QDoubleSpinBox(grp_limites)
        self.spn_lon_min = QDoubleSpinBox(grp_limites)
        self.spn_lon_max = QDoubleSpinBox(grp_limites)
        for sp_lat in (self.spn_lat_min, self.spn_lat_max):
            sp_lat.setRange(-15.0, 10.0)
            sp_lat.setDecimals(2)
            sp_lat.setSingleStep(0.1)
            sp_lat.valueChanged.connect(self._al_cambiar_spin_coordenadas)
        for sp_lon in (self.spn_lon_min, self.spn_lon_max):
            sp_lon.setRange(-95.0, -70.0)
            sp_lon.setDecimals(2)
            sp_lon.setSingleStep(0.1)
            sp_lon.valueChanged.connect(self._al_cambiar_spin_coordenadas)

        self.spn_salto = QDoubleSpinBox(grp_limites)
        self.spn_salto.setRange(0.05, 5.0)
        self.spn_salto.setDecimals(2)
        self.spn_salto.setSingleStep(0.1)
        self.spn_salto.valueChanged.connect(self._al_cambiar_spin_coordenadas)

        grid.addWidget(QLabel("Nombre Mapa:"), 0, 0)
        grid.addWidget(self.edt_nombre_mapa, 0, 1, 1, 3)
        grid.addWidget(QLabel("Lat. Mín (°):"), 1, 0)
        grid.addWidget(self.spn_lat_min, 1, 1)
        grid.addWidget(QLabel("Lat. Máx (°):"), 1, 2)
        grid.addWidget(self.spn_lat_max, 1, 3)
        grid.addWidget(QLabel("Long. Mín (°):"), 2, 0)
        grid.addWidget(self.spn_lon_min, 2, 1)
        grid.addWidget(QLabel("Long. Máx (°):"), 2, 2)
        grid.addWidget(self.spn_lon_max, 2, 3)
        grid.addWidget(QLabel("Salto Grilla (°):"), 3, 0)
        grid.addWidget(self.spn_salto, 3, 1)

        self.chk_vista_recortada = QCheckBox("Zoom al área del mapa", grp_limites)
        self.chk_vista_recortada.toggled.connect(self.redibujar_gis)
        grid.addWidget(self.chk_vista_recortada, 3, 2, 1, 2)
        v_izq.addWidget(grp_limites)

        grp_est = QGroupBox("3. ESTACIONES ASOCIADAS AL INFORME DE ESTE MAPA", panel_izq)
        v_est = QVBoxLayout(grp_est)
        lbl_ayuda_est = QLabel(
            "Marque en la lista o haga clic sobre un triángulo en el mapa GIS para "
            "incluir/excluir estaciones en la columna «estaciones»:",
            grp_est,
        )
        lbl_ayuda_est.setWordWrap(True)
        lbl_ayuda_est.setStyleSheet("font-weight: normal; font-size: 8.5pt; color: #37474f;")
        v_est.addWidget(lbl_ayuda_est)

        self.lista_estaciones_chk = QListWidget(grp_est)
        self.lista_estaciones_chk.setMinimumHeight(115)
        self.lista_estaciones_chk.setMaximumHeight(135)
        self.lista_estaciones_chk.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        for f_est in self.catalogo_estaciones:
            num_e = str(f_est[0]).strip()
            nom_e = str(f_est[1]).strip()
            cod_e = str(f_est[2]).strip()
            hab_e = " [Activa]" if str(f_est[5]).strip() == "1" else ""
            item = QListWidgetItem(f"{num_e} — {cod_e} — {nom_e}{hab_e}")
            item.setData(Qt.UserRole, num_e)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.lista_estaciones_chk.addItem(item)
        self.lista_estaciones_chk.itemChanged.connect(self._al_cambiar_check_estacion)
        v_est.addWidget(self.lista_estaciones_chk)
        v_izq.addWidget(grp_est, 1)

        h_crud = QHBoxLayout()
        self.btn_aplicar = QPushButton("Aplicar a Fila", panel_izq)
        self.btn_aplicar.clicked.connect(self.aplicar_mapa_actual)
        self.btn_agregar = QPushButton("+ Nuevo Mapa", panel_izq)
        self.btn_agregar.clicked.connect(self.agregar_nuevo_mapa)
        self.btn_eliminar = QPushButton("Eliminar", panel_izq)
        self.btn_eliminar.clicked.connect(self.eliminar_mapa_actual)
        h_crud.addWidget(self.btn_aplicar)
        h_crud.addWidget(self.btn_agregar)
        h_crud.addWidget(self.btn_eliminar)
        v_izq.addLayout(h_crud)
        v_izq.addWidget(_crear_etiqueta_estado_seguridad(panel_izq))

        h_fin = QHBoxLayout()
        self.btn_guardar = QPushButton("Guardar mapas.csv", panel_izq)
        self.btn_guardar.setObjectName("btn_primario")
        self.btn_guardar.clicked.connect(self.guardar_mapas_csv)
        self.btn_salir = QPushButton("Salir", panel_izq)
        self.btn_salir.setObjectName("btn_salir")
        self.btn_salir.clicked.connect(self.close)
        h_fin.addWidget(self.btn_guardar)
        h_fin.addWidget(self.btn_salir)
        v_izq.addLayout(h_fin)

        # Panel derecho: Visor GIS interactivo con RectangleSelector y clic sobre estaciones
        panel_der = QWidget(self)
        v_der = QVBoxLayout(panel_der)
        v_der.setContentsMargins(4, 4, 4, 4)

        lbl_banner_gis = QLabel(
            "<b>VISOR GIS INTERACTIVO:</b> Arrastre con el ratón sobre el mapa para dibujar el rectángulo "
            "(<code>lat_min, lat_max, long_min, long_max</code>) o haga clic derecho sobre una estación (▲) para asociarla.",
            panel_der,
        )
        lbl_banner_gis.setWordWrap(True)
        lbl_banner_gis.setStyleSheet(
            "background-color: #eff6ff; border: 1px solid #93c5fd; border-radius: 4px; padding: 6px; color: #1e3a8a;"
        )
        v_der.addWidget(lbl_banner_gis)

        self.figura = Figure(figsize=(8, 7), dpi=100)
        self.canvas = FigureCanvas(self.figura)
        self.toolbar_gis = NavigationToolbar2QT(self.canvas, panel_der)
        v_der.addWidget(self.toolbar_gis)
        v_der.addWidget(self.canvas, 1)

        self.ax = self.figura.add_subplot(111)
        self.selector_rectangulo = RectangleSelector(
            self.ax,
            self._al_dibujar_rectangulo_gis,
            useblit=True,
            button=[1],
            minspanx=0.05,
            minspany=0.05,
            spancoords='data',
            interactive=True,
        )
        self.canvas.mpl_connect('button_press_event', self._al_clic_mapa_estacion)

        scroll_izq.setWidget(panel_izq)
        splitter.addWidget(scroll_izq)
        splitter.addWidget(panel_der)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        self._poblar_tabla_mapas()
        if self.tabla_mapas.rowCount() > 0:
            self.tabla_mapas.selectRow(0)

    def _poblar_tabla_mapas(self):
        self.tabla_mapas.setRowCount(len(self.filas_mapas))
        for r_idx, fila in enumerate(self.filas_mapas):
            for c_idx, val in enumerate(fila):
                it = QTableWidgetItem(str(val))
                if r_idx < 5 and c_idx == 0:
                    f = it.font()
                    f.setBold(True)
                    it.setFont(f)
                self.tabla_mapas.setItem(r_idx, c_idx, it)
        self.tabla_mapas.resizeColumnsToContents()

    def _obtener_estaciones_marcadas_str(self) -> str:
        seleccionadas = []
        for i in range(self.lista_estaciones_chk.count()):
            it = self.lista_estaciones_chk.item(i)
            if it.checkState() == Qt.Checked:
                seleccionadas.append(str(it.data(Qt.UserRole)))
        return " ".join(seleccionadas)

    def _al_seleccionar_mapa(self):
        sel = self.tabla_mapas.selectionModel().selectedRows()
        if not sel:
            return
        idx = sel[0].row()
        if not (0 <= idx < len(self.filas_mapas)):
            return
        f = self.filas_mapas[idx]
        self._bloqueando_eventos_ui = True
        try:
            self.edt_nombre_mapa.setText(str(f[0]).strip())
            self.edt_nombre_mapa.setReadOnly(idx < 5)
            self.spn_lat_min.setValue(float(f[1]))
            self.spn_lat_max.setValue(float(f[2]))
            self.spn_lon_min.setValue(float(f[3]))
            self.spn_lon_max.setValue(float(f[4]))
            self.spn_salto.setValue(max(0.05, float(f[5])))
            est_set = set(str(f[6]).strip().split())
            for i in range(self.lista_estaciones_chk.count()):
                it = self.lista_estaciones_chk.item(i)
                num_e = str(it.data(Qt.UserRole))
                it.setCheckState(Qt.Checked if num_e in est_set else Qt.Unchecked)
        except Exception:
            pass
        finally:
            self._bloqueando_eventos_ui = False
        self.redibujar_gis()

    def _al_cambiar_spin_coordenadas(self):
        if self._bloqueando_eventos_ui:
            return
        self.redibujar_gis()

    def _al_cambiar_check_estacion(self, _item):
        if self._bloqueando_eventos_ui:
            return
        self.redibujar_gis()

    def _al_dibujar_rectangulo_gis(self, eclick, erelease):
        if eclick.xdata is None or erelease.xdata is None:
            return
        lon1, lon2 = sorted([round(float(eclick.xdata), 2), round(float(erelease.xdata), 2)])
        lat1, lat2 = sorted([round(float(eclick.ydata), 2), round(float(erelease.ydata), 2)])
        self._bloqueando_eventos_ui = True
        try:
            self.spn_lon_min.setValue(lon1)
            self.spn_lon_max.setValue(lon2)
            self.spn_lat_min.setValue(lat1)
            self.spn_lat_max.setValue(lat2)
        finally:
            self._bloqueando_eventos_ui = False
        self.redibujar_gis()

    def _al_clic_mapa_estacion(self, event):
        # Clic derecho cerca de una estación en el mapa la marca/desmarca
        if event.button != 3 or event.xdata is None or event.ydata is None:
            return
        mejor_num = None
        menor_dist = 0.08
        for f_est in self.catalogo_estaciones:
            try:
                lon_e = float(f_est[18])
                lat_e = float(f_est[19])
                if lon_e == 0 and lat_e == 0:
                    continue
                d = ((lon_e - event.xdata) ** 2 + (lat_e - event.ydata) ** 2) ** 0.5
                if d < menor_dist:
                    menor_dist = d
                    mejor_num = str(f_est[0]).strip()
            except Exception:
                continue
        if mejor_num is not None:
            for i in range(self.lista_estaciones_chk.count()):
                it = self.lista_estaciones_chk.item(i)
                if str(it.data(Qt.UserRole)) == mejor_num:
                    nuevo = Qt.Unchecked if it.checkState() == Qt.Checked else Qt.Checked
                    it.setCheckState(nuevo)
                    break

    def redibujar_gis(self):
        self.ax.clear()
        gdf_ec, gdf_prov = _obtener_capas_base_gis()
        self.ax.set_facecolor("#e0f2fe")
        if gdf_ec is not None:
            gdf_ec.plot(ax=self.ax, color="#f8fafc", edgecolor="#475569", linewidth=0.9, zorder=1)
        if gdf_prov is not None:
            gdf_prov.plot(ax=self.ax, facecolor="none", edgecolor="#94a3b8", linewidth=0.6, linestyle="--", zorder=2)

        lat_min = self.spn_lat_min.value()
        lat_max = self.spn_lat_max.value()
        lon_min = self.spn_lon_min.value()
        lon_max = self.spn_lon_max.value()
        salto = max(0.05, self.spn_salto.value())
        nombre_m = self.edt_nombre_mapa.text().strip() or "Mapa"

        # Dibujar el recuadro de la región configurada
        ancho = lon_max - lon_min
        alto = lat_max - lat_min
        if ancho > 0 and alto > 0:
            rect = Rectangle(
                (lon_min, lat_min),
                ancho,
                alto,
                linewidth=2.2,
                edgecolor="#dc2626",
                facecolor=(220 / 255, 38 / 255, 38 / 255, 0.10),
                zorder=4,
                label=f"Encuadre «{nombre_m}» ({ancho:.2f}° × {alto:.2f}°)",
            )
            self.ax.add_patch(rect)

        # Dibujar estaciones (en rojo/grande las asociadas al mapa, en gris/azul las demás con coordenadas)
        est_marcadas = set(self._obtener_estaciones_marcadas_str().split())
        lons_sel, lats_sel, eti_sel = [], [], []
        lons_otras, lats_otras = [], []
        for f_est in self.catalogo_estaciones:
            try:
                num_e = str(f_est[0]).strip()
                cod_e = str(f_est[2]).strip()
                lon_e = float(f_est[18])
                lat_e = float(f_est[19])
                if lon_e == 0 and lat_e == 0:
                    continue
                if num_e in est_marcadas:
                    lons_sel.append(lon_e)
                    lats_sel.append(lat_e)
                    eti_sel.append(f"{cod_e}({num_e})")
                elif str(f_est[5]).strip() == "1":
                    lons_otras.append(lon_e)
                    lats_otras.append(lat_e)
            except Exception:
                continue

        if lons_otras:
            self.ax.scatter(
                lons_otras, lats_otras, marker="^", s=36, color="#64748b", alpha=0.65,
                zorder=5, label="Otras estaciones activas"
            )
        if lons_sel:
            self.ax.scatter(
                lons_sel, lats_sel, marker="^", s=85, color="#15803d", edgecolors="#ffffff",
                linewidths=0.9, zorder=6, label=f"Estaciones del mapa ({len(lons_sel)})"
            )
            for x_e, y_e, txt_e in zip(lons_sel, lats_sel, eti_sel):
                self.ax.annotate(
                    txt_e, (x_e, y_e), textcoords="offset points", xytext=(4, 4),
                    fontsize=7.5, fontweight="bold", color="#14532d", zorder=7
                )

        if self.chk_vista_recortada.isChecked() and ancho > 0 and alto > 0:
            self.ax.set_xlim(lon_min, lon_max)
            self.ax.set_ylim(lat_min, lat_max)
            import numpy as np
            self.ax.set_xticks(np.arange(lon_min, lon_max + salto * 0.5, salto))
            self.ax.set_yticks(np.arange(lat_min, lat_max + salto * 0.5, salto))
        else:
            pad_lon = max(0.6, ancho * 0.35)
            pad_lat = max(0.6, alto * 0.35)
            self.ax.set_xlim(min(-81.8, lon_min - pad_lon), max(-75.0, lon_max + pad_lon))
            self.ax.set_ylim(min(-5.5, lat_min - pad_lat), max(1.6, lat_max + pad_lat))

        self.ax.grid(True, linestyle=":", alpha=0.6, color="#64748b")
        self.ax.set_xlabel("Longitud (°)")
        self.ax.set_ylabel("Latitud (°)")
        self.ax.set_title(
            f"Región: {nombre_m} | Lat [{lat_min:.2f}, {lat_max:.2f}] | Long [{lon_min:.2f}, {lon_max:.2f}] | Salto {salto:g}°",
            fontsize=10, fontweight="bold", color="#1e3a8a"
        )
        self.ax.legend(loc="upper left", fontsize=8)
        self.figura.tight_layout()
        self.canvas.draw_idle()

    def aplicar_mapa_actual(self):
        sel = self.tabla_mapas.selectionModel().selectedRows()
        if not sel:
            return
        idx = sel[0].row()
        nom = self.edt_nombre_mapa.text().strip()
        if not nom:
            QMessageBox.warning(self, "Validación", "El nombre del mapa no puede estar vacío.")
            return
        est_str = self._obtener_estaciones_marcadas_str()
        self.filas_mapas[idx] = [
            nom,
            f"{self.spn_lat_min.value():g}",
            f"{self.spn_lat_max.value():g}",
            f"{self.spn_lon_min.value():g}",
            f"{self.spn_lon_max.value():g}",
            f"{self.spn_salto.value():g}",
            est_str if est_str else " ",
        ]
        self._poblar_tabla_mapas()
        self.tabla_mapas.selectRow(idx)
        it_sel = self.tabla_mapas.item(idx, 0)
        if it_sel is not None:
            self.tabla_mapas.scrollToItem(it_sel)

    def agregar_nuevo_mapa(self):
        nom = self.edt_nombre_mapa.text().strip()
        if not nom or any(str(f[0]).strip().lower() == nom.lower() for f in self.filas_mapas):
            nom = f"NuevaRegion_{len(self.filas_mapas) + 1}"
            self.edt_nombre_mapa.setText(nom)
        est_str = self._obtener_estaciones_marcadas_str()
        nueva = [
            nom,
            f"{self.spn_lat_min.value():g}",
            f"{self.spn_lat_max.value():g}",
            f"{self.spn_lon_min.value():g}",
            f"{self.spn_lon_max.value():g}",
            f"{self.spn_salto.value():g}",
            est_str if est_str else " ",
        ]
        self.filas_mapas.append(nueva)
        self._poblar_tabla_mapas()
        ultimo = len(self.filas_mapas) - 1
        self.tabla_mapas.selectRow(ultimo)
        it_ult = self.tabla_mapas.item(ultimo, 0)
        if it_ult is not None:
            self.tabla_mapas.scrollToItem(it_ult)

    def eliminar_mapa_actual(self):
        sel = self.tabla_mapas.selectionModel().selectedRows()
        if not sel:
            return
        idx = sel[0].row()
        if idx < 5:
            QMessageBox.warning(
                self,
                "Mapa Estructural Protegido",
                "Los 5 primeros mapas (Region, Ecuador, Facultad, Fuentes, Reportes) son perfiles estructurales del sistema y no pueden eliminarse.",
            )
            return
        self.filas_mapas.pop(idx)
        self._poblar_tabla_mapas()
        nuevo_idx = min(idx, len(self.filas_mapas) - 1)
        if nuevo_idx >= 0:
            self.tabla_mapas.selectRow(nuevo_idx)

    def guardar_mapas_csv(self):
        self.aplicar_mapa_actual()

        def _validar_mapas(filas_totales):
            datos = filas_totales[1:]
            base_esperados = ["Region", "Ecuador", "Facultad", "Fuentes", "Reportes"]
            if len(datos) < 5 or [str(datos[i][0]).strip() for i in range(5)] != base_esperados:
                return False, "Los 5 primeros mapas deben ser exactamente: Region, Ecuador, Facultad, Fuentes, Reportes."
            for r in datos:
                try:
                    lat_i, lat_f = float(r[1]), float(r[2])
                    lon_i, lon_f = float(r[3]), float(r[4])
                    salto_v = float(r[5])
                    if lat_i >= lat_f or lon_i >= lon_f or salto_v <= 0:
                        return False, f"El mapa «{r[0]}» tiene límites inválidos (lat_min >= lat_max o long_min >= long_max)."
                except Exception:
                    return False, f"El mapa «{r[0]}» contiene coordenadas no numéricas."
            return True, ""

        _guardar_config_con_seguridad(
            self,
            self.ruta_csv,
            [self.cabecera] + self.filas_mapas,
            "mapas.csv (Regiones y encuadres GIS)",
            validador_extra=_validar_mapas,
        )

    def limpiar_estado(self):
        try:
            if hasattr(self, 'figura') and self.figura is not None:
                self.figura.clf()
        except Exception:
            pass

    def closeEvent(self, event):
        self.limpiar_estado()
        self.cerrado.emit()
        super().closeEvent(event)


# ==============================================================================
# 7. RESPALDO Y RESTAURACIÓN DEL PROGRAMA (ZIP - SOLO PC ADMINISTRADOR)
# ==============================================================================

CARPETAS_RESPALDO_PROGRAMA = ("datos", "modulos externos", "src")
CARPETAS_EXCLUIDAS_RESPALDO = {"__pycache__", "vw backup"}
EXTENSIONES_EXCLUIDAS_RESPALDO = {".vwx", ".vwxw", ".vwt", ".mcd", ".pyc", ".pyo"}


def recolectar_archivos_respaldo(raiz_origen: str):
    """
    Recorre `datos/`, `modulos externos/` y `src/` dentro de `raiz_origen`
    excluyendo carpetas de caché (`__pycache__`), respaldos Vectorworks (`VW Backup`)
    y extensiones excluidas (`.vwx`, `.vwxw`, `.vwt`, `.mcd`, `.pyc`, `.pyo`).

    Retorna:
        tuple[list[tuple[str, str]], int]: `(lista_(ruta_abs, ruta_rel_zip), conteo_excluidos)`
    """
    raiz_path = Path(raiz_origen).resolve()
    archivos_incluir = []
    conteo_excluidos = 0

    for carpeta_base in CARPETAS_RESPALDO_PROGRAMA:
        dir_objetivo = raiz_path / carpeta_base
        if not dir_objetivo.is_dir():
            continue
        for actual, subdirs, nombres in os.walk(dir_objetivo):
            subdirs_filtrados = []
            for d in subdirs:
                if d.strip().lower() in CARPETAS_EXCLUIDAS_RESPALDO:
                    conteo_excluidos += 1
                else:
                    subdirs_filtrados.append(d)
            subdirs[:] = sorted(subdirs_filtrados, key=str.lower)

            for nom in sorted(nombres, key=str.lower):
                ext = os.path.splitext(nom)[1].lower()
                if ext in EXTENSIONES_EXCLUIDAS_RESPALDO:
                    conteo_excluidos += 1
                    continue
                ruta_abs = os.path.join(actual, nom)
                ruta_rel = os.path.relpath(ruta_abs, raiz_path).replace("\\", "/")
                archivos_incluir.append((ruta_abs, ruta_rel))

    return archivos_incluir, conteo_excluidos


class HiloRespaldoZip(QThread):
    """Hilo de trabajo para comprimir el programa en formato ZIP sin bloquear la UI."""

    progreso = pyqtSignal(int, str)
    terminado = pyqtSignal(bool, str, dict)

    def __init__(self, raiz_origen: str, ruta_zip_destino: str, parent=None):
        super().__init__(parent)
        self.raiz_origen = raiz_origen
        self.ruta_zip_destino = ruta_zip_destino

    def run(self):
        ruta_tmp = self.ruta_zip_destino + ".tmp"
        try:
            archivos, excluidos = recolectar_archivos_respaldo(self.raiz_origen)
            total = len(archivos)
            if total == 0:
                self.terminado.emit(
                    False,
                    "No se encontraron archivos válidos en datos/, modulos externos/ o src/.",
                    {"incluidos": 0, "excluidos": excluidos},
                )
                return

            os.makedirs(os.path.dirname(os.path.abspath(self.ruta_zip_destino)), exist_ok=True)
            with zipfile.ZipFile(ruta_tmp, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
                for idx, (ruta_abs, ruta_rel) in enumerate(archivos, start=1):
                    zf.write(ruta_abs, arcname=ruta_rel)
                    pct = int((idx * 100) / total)
                    self.progreso.emit(pct, ruta_rel)

            os.replace(ruta_tmp, self.ruta_zip_destino)
            tam_mb = os.path.getsize(self.ruta_zip_destino) / (1024.0 * 1024.0)
            self.terminado.emit(
                True,
                f"Respaldo generado correctamente ({tam_mb:.2f} MB).",
                {"incluidos": total, "excluidos": excluidos, "tam_mb": tam_mb},
            )
        except Exception as e:
            try:
                if os.path.exists(ruta_tmp):
                    os.remove(ruta_tmp)
            except Exception:
                pass
            self.terminado.emit(False, f"Error generando el respaldo ZIP: {e}", {})


class HiloRestaurarZip(QThread):
    """
    Hilo de trabajo para descomprimir un respaldo ZIP respetando la estructura
    de directorios y copiando únicamente archivos nuevos o más recientes.
    """

    progreso = pyqtSignal(int, str)
    terminado = pyqtSignal(bool, str, dict)

    def __init__(self, ruta_zip_origen: str, carpeta_destino: str, parent=None):
        super().__init__(parent)
        self.ruta_zip_origen = ruta_zip_origen
        self.carpeta_destino = carpeta_destino

    def run(self):
        try:
            raiz_dest = os.path.abspath(self.carpeta_destino)
            os.makedirs(raiz_dest, exist_ok=True)

            with zipfile.ZipFile(self.ruta_zip_origen, "r") as zf:
                entradas = [info for info in zf.infolist() if not info.is_dir()]
                total = len(entradas)
                if total == 0:
                    self.terminado.emit(
                        False,
                        "El archivo ZIP seleccionado no contiene archivos.",
                        {},
                    )
                    return

                nuevos = 0
                actualizados = 0
                omitidos = 0

                for idx, info in enumerate(entradas, start=1):
                    nombre_rel = info.filename.replace("\\", "/").lstrip("/")
                    dest_abs = os.path.abspath(os.path.join(raiz_dest, *nombre_rel.split("/")))

                    # Protección contra rutas maliciosas fuera de carpeta_destino (Zip Slip)
                    if os.path.commonpath([raiz_dest, dest_abs]) != raiz_dest:
                        omitidos += 1
                        continue

                    mtime_zip = datetime(*info.date_time).timestamp()
                    existe_previo = os.path.isfile(dest_abs)

                    if existe_previo:
                        mtime_local = os.path.getmtime(dest_abs)
                        # Tolerancia de 2 s por resolución DOS de fechas en archivos ZIP
                        if mtime_zip <= mtime_local + 2.0:
                            omitidos += 1
                            pct = int((idx * 100) / total)
                            self.progreso.emit(pct, f"Omitido (actual/antiguo): {nombre_rel}")
                            continue

                    os.makedirs(os.path.dirname(dest_abs), exist_ok=True)
                    with zf.open(info, "r") as f_src, open(dest_abs, "wb") as f_dst:
                        shutil.copyfileobj(f_src, f_dst)
                    os.utime(dest_abs, (mtime_zip, mtime_zip))

                    if existe_previo:
                        actualizados += 1
                        estado_txt = f"Actualizado: {nombre_rel}"
                    else:
                        nuevos += 1
                        estado_txt = f"Nuevo: {nombre_rel}"

                    pct = int((idx * 100) / total)
                    self.progreso.emit(pct, estado_txt)

            self.terminado.emit(
                True,
                "Restauración / actualización completada.",
                {
                    "total": total,
                    "nuevos": nuevos,
                    "actualizados": actualizados,
                    "omitidos": omitidos,
                },
            )
        except Exception as e:
            self.terminado.emit(False, f"Error restaurando desde ZIP: {e}", {})


class Respaldar_programa(QWidget):
    cerrado = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("RESPALDO Y ACTUALIZACIÓN DEL PROGRAMA (ZIP) - RSA")
        self.setStyleSheet(ESTILO_PANEL_CONFIG)
        self.raiz_proyecto = os.path.abspath(ruta_proyecto)
        self._hilo_activo = None

        layout_raiz = QVBoxLayout(self)
        layout_raiz.setContentsMargins(12, 10, 12, 10)
        layout_raiz.setSpacing(10)

        autorizado_pc, nombre_pc, msg_pc = verificar_permiso_respaldo_pc()
        lbl_seg = QLabel(
            f"Equipo actual: <b>{nombre_pc}</b> — {msg_pc}",
            self,
        )
        lbl_seg.setWordWrap(True)
        if autorizado_pc:
            lbl_seg.setStyleSheet(
                "background:#e8f5e9; color:#1b5e20; border:1px solid #81c784; "
                "border-radius:4px; padding:6px 10px;"
            )
        else:
            lbl_seg.setStyleSheet(
                "background:#ffebee; color:#b71c1c; border:1px solid #e57373; "
                "border-radius:4px; padding:6px 10px;"
            )
        layout_raiz.addWidget(lbl_seg)

        # 1. Sección de creación de respaldo ZIP
        grp_backup = QGroupBox("1. GENERAR RESPALDO DEL PROGRAMA (.ZIP)", self)
        v_bkp = QVBoxLayout(grp_backup)
        lbl_info_bkp = QLabel(
            f"<b>Origen:</b> <code>{self.raiz_proyecto}</code><br>"
            "<b>Carpetas incluidas:</b> <code>datos/</code>, <code>modulos externos/</code> y <code>src/</code> "
            "(respetando íntegramente su estructura de directorios).<br>"
            "<b>Exclusiones automáticas:</b> GitHub/Agente, <code>datos/mapas/VW Backup/</code>, "
            "archivos de Vectorworks (<code>*.vwx</code>, <code>*.vwxw</code>, <code>*.vwt</code>, <code>*.mcd</code>) "
            "y caché Python (<code>__pycache__/</code>, <code>*.pyc</code>).",
            grp_backup,
        )
        lbl_info_bkp.setWordWrap(True)
        lbl_info_bkp.setStyleSheet("font-weight: normal; color: #263238;")
        v_bkp.addWidget(lbl_info_bkp)

        h_bkp_btn = QHBoxLayout()
        self.btn_crear_zip = QPushButton("Generar Respaldo ZIP (Guardar como...)", grp_backup)
        self.btn_crear_zip.setObjectName("btn_primario")
        self.btn_crear_zip.setEnabled(autorizado_pc)
        self.btn_crear_zip.clicked.connect(self.ejecutar_respaldo_zip)
        h_bkp_btn.addWidget(self.btn_crear_zip)
        h_bkp_btn.addStretch()
        v_bkp.addLayout(h_bkp_btn)
        layout_raiz.addWidget(grp_backup)

        # 2. Progreso y bitácora
        grp_prog = QGroupBox("2. PROGRESO Y BITÁCORA DE OPERACIÓN", self)
        v_prog = QVBoxLayout(grp_prog)
        self.lbl_estado_op = QLabel("En espera.", grp_prog)
        self.lbl_estado_op.setStyleSheet("font-weight: normal; color: #37474f;")
        self.barra_progreso = QProgressBar(grp_prog)
        self.barra_progreso.setRange(0, 100)
        self.barra_progreso.setValue(0)
        self.txt_bitacora = QPlainTextEdit(grp_prog)
        self.txt_bitacora.setReadOnly(True)
        self.txt_bitacora.setMinimumHeight(180)
        v_prog.addWidget(self.lbl_estado_op)
        v_prog.addWidget(self.barra_progreso)
        v_prog.addWidget(self.txt_bitacora, 1)
        layout_raiz.addWidget(grp_prog, 1)

        h_pie = QHBoxLayout()
        h_pie.addStretch()
        self.btn_salir = QPushButton("Salir", self)
        self.btn_salir.setObjectName("btn_salir")
        self.btn_salir.clicked.connect(self.close)
        h_pie.addWidget(self.btn_salir)
        layout_raiz.addLayout(h_pie)

    def _establecer_controles_activos(self, habilitado: bool):
        autorizado_pc, _, _ = verificar_permiso_respaldo_pc()
        self.btn_crear_zip.setEnabled(habilitado and autorizado_pc)
        self.btn_salir.setEnabled(habilitado)

    def ejecutar_respaldo_zip(self):
        autorizado_pc, _, msg_pc = verificar_permiso_respaldo_pc()
        if not autorizado_pc:
            QMessageBox.warning(self, "Acceso Restringido", msg_pc)
            return

        nombre_sug = f"respaldo_rsa_sismologia_{datetime.now().strftime('%Y%m%d_%H%M')}.zip"
        ruta_zip, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar respaldo del programa como...",
            os.path.join(self.raiz_proyecto, nombre_sug),
            "Archivos ZIP (*.zip)",
        )
        if not ruta_zip:
            return
        if not ruta_zip.lower().endswith(".zip"):
            ruta_zip += ".zip"

        self.txt_bitacora.clear()
        self.barra_progreso.setValue(0)
        self.lbl_estado_op.setText("Comprimiendo archivos...")
        self._establecer_controles_activos(False)

        self._hilo_activo = HiloRespaldoZip(self.raiz_proyecto, ruta_zip, self)
        self._hilo_activo.progreso.connect(self._al_avanzar_operacion)
        self._hilo_activo.terminado.connect(self._al_terminar_respaldo)
        self._hilo_activo.start()

    def _al_avanzar_operacion(self, porcentaje: int, detalle: str):
        self.barra_progreso.setValue(porcentaje)
        self.lbl_estado_op.setText(detalle)

    def _al_terminar_respaldo(self, ok: bool, mensaje: str, stats: dict):
        self._establecer_controles_activos(True)
        if ok:
            self.barra_progreso.setValue(100)
            self.lbl_estado_op.setText(mensaje)
            self.txt_bitacora.appendPlainText(
                f"✓ {mensaje}\n"
                f"• Archivos comprimidos: {stats.get('incluidos', 0)}\n"
                f"• Elementos excluidos (VW Backup / Vectorworks / __pycache__): {stats.get('excluidos', 0)}"
            )
            QMessageBox.information(self, "Respaldo Completado", mensaje)
        else:
            self.lbl_estado_op.setText(mensaje)
            self.txt_bitacora.appendPlainText(f"✗ {mensaje}")
            QMessageBox.critical(self, "Error en Respaldo", mensaje)

    def limpiar_estado(self):
        if self._hilo_activo is not None and self._hilo_activo.isRunning():
            self._hilo_activo.wait(2000)
        self._hilo_activo = None

    def closeEvent(self, event):
        self.limpiar_estado()
        self.cerrado.emit()
        super().closeEvent(event)


class Restaurar_programa(QWidget):
    """
    Módulo abierto a cualquier equipo para descomprimir/actualizar el programa
    desde un archivo ZIP respetando la estructura de directorios y copiando
    únicamente archivos nuevos o más recientes.
    """
    cerrado = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ACTUALIZAR / RECUPERAR PROGRAMA DESDE ZIP - RSA")
        self.setStyleSheet(ESTILO_PANEL_CONFIG)
        self.raiz_proyecto = os.path.abspath(ruta_proyecto)
        self._hilo_activo = None

        layout_raiz = QVBoxLayout(self)
        layout_raiz.setContentsMargins(12, 10, 12, 10)
        layout_raiz.setSpacing(10)

        grp_rest = QGroupBox("1. SELECCIÓN DE RESPALDO (.ZIP) Y CARPETA DESTINO", self)
        grid_r = QGridLayout(grp_rest)

        self.edt_zip_origen = QLineEdit(grp_rest)
        self.edt_zip_origen.setPlaceholderText("Seleccione el archivo .zip de respaldo...")
        self.btn_buscar_zip = QPushButton("Examinar ZIP...", grp_rest)
        self.btn_buscar_zip.clicked.connect(self.seleccionar_zip_origen)

        self.edt_dir_destino = QLineEdit(self.raiz_proyecto, grp_rest)
        self.btn_buscar_dest = QPushButton("Carpeta destino...", grp_rest)
        self.btn_buscar_dest.clicked.connect(self.seleccionar_carpeta_destino)

        lbl_nota_inc = QLabel(
            "<b>Actualización ágil:</b> solo se copian archivos nuevos o con fecha de modificación "
            "más reciente que la versión existente en destino; las versiones iguales o más antiguas se omiten, "
            "respetando íntegramente la estructura de directorios.",
            grp_rest,
        )
        lbl_nota_inc.setWordWrap(True)
        lbl_nota_inc.setStyleSheet("font-weight: normal; color: #1e3a8a;")

        self.btn_restaurar_zip = QPushButton("Restaurar / Actualizar desde ZIP", grp_rest)
        self.btn_restaurar_zip.setObjectName("btn_primario")
        self.btn_restaurar_zip.clicked.connect(self.ejecutar_restauracion_zip)

        grid_r.addWidget(QLabel("Archivo ZIP:"), 0, 0)
        grid_r.addWidget(self.edt_zip_origen, 0, 1)
        grid_r.addWidget(self.btn_buscar_zip, 0, 2)
        grid_r.addWidget(QLabel("Carpeta destino:"), 1, 0)
        grid_r.addWidget(self.edt_dir_destino, 1, 1)
        grid_r.addWidget(self.btn_buscar_dest, 1, 2)
        grid_r.addWidget(lbl_nota_inc, 2, 0, 1, 3)
        grid_r.addWidget(self.btn_restaurar_zip, 3, 0, 1, 3)
        layout_raiz.addWidget(grp_rest)

        grp_prog = QGroupBox("2. PROGRESO Y BITÁCORA DE ACTUALIZACIÓN", self)
        v_prog = QVBoxLayout(grp_prog)
        self.lbl_estado_op = QLabel("En espera.", grp_prog)
        self.lbl_estado_op.setStyleSheet("font-weight: normal; color: #37474f;")
        self.barra_progreso = QProgressBar(grp_prog)
        self.barra_progreso.setRange(0, 100)
        self.barra_progreso.setValue(0)
        self.txt_bitacora = QPlainTextEdit(grp_prog)
        self.txt_bitacora.setReadOnly(True)
        self.txt_bitacora.setMinimumHeight(180)
        v_prog.addWidget(self.lbl_estado_op)
        v_prog.addWidget(self.barra_progreso)
        v_prog.addWidget(self.txt_bitacora, 1)
        layout_raiz.addWidget(grp_prog, 1)

        h_pie = QHBoxLayout()
        h_pie.addStretch()
        self.btn_salir = QPushButton("Salir", self)
        self.btn_salir.setObjectName("btn_salir")
        self.btn_salir.clicked.connect(self.close)
        h_pie.addWidget(self.btn_salir)
        layout_raiz.addLayout(h_pie)

    def _establecer_controles_activos(self, habilitado: bool):
        self.btn_buscar_zip.setEnabled(habilitado)
        self.btn_buscar_dest.setEnabled(habilitado)
        self.btn_restaurar_zip.setEnabled(habilitado)
        self.btn_salir.setEnabled(habilitado)

    def seleccionar_zip_origen(self):
        ruta, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar respaldo ZIP",
            self.raiz_proyecto,
            "Archivos ZIP (*.zip)",
        )
        if ruta:
            self.edt_zip_origen.setText(ruta)

    def seleccionar_carpeta_destino(self):
        carpeta = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar carpeta destino para restaurar",
            self.edt_dir_destino.text().strip() or self.raiz_proyecto,
        )
        if carpeta:
            self.edt_dir_destino.setText(carpeta)

    def ejecutar_restauracion_zip(self):
        ruta_zip = self.edt_zip_origen.text().strip()
        carpeta_dest = self.edt_dir_destino.text().strip()
        if not ruta_zip or not os.path.isfile(ruta_zip):
            QMessageBox.warning(self, "Validación", "Seleccione un archivo .zip válido.")
            return
        if not carpeta_dest:
            QMessageBox.warning(self, "Validación", "Indique la carpeta destino.")
            return

        resp = QMessageBox.question(
            self,
            "Confirmar actualización incremental",
            f"Se extraerán únicamente los archivos nuevos o más recientes desde:\n{ruta_zip}\n\n"
            f"Hacia:\n{carpeta_dest}\n\n¿Desea continuar?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if resp != QMessageBox.Yes:
            return

        self.txt_bitacora.clear()
        self.barra_progreso.setValue(0)
        self.lbl_estado_op.setText("Verificando fechas y extrayendo archivos más nuevos...")
        self._establecer_controles_activos(False)

        self._hilo_activo = HiloRestaurarZip(ruta_zip, carpeta_dest, self)
        self._hilo_activo.progreso.connect(self._al_avanzar_operacion)
        self._hilo_activo.terminado.connect(self._al_terminar_restauracion)
        self._hilo_activo.start()

    def _al_avanzar_operacion(self, porcentaje: int, detalle: str):
        self.barra_progreso.setValue(porcentaje)
        self.lbl_estado_op.setText(detalle)

    def _al_terminar_restauracion(self, ok: bool, mensaje: str, stats: dict):
        self._establecer_controles_activos(True)
        if ok:
            self.barra_progreso.setValue(100)
            self.lbl_estado_op.setText(mensaje)
            resumen = (
                f"✓ {mensaje}\n"
                f"• Total en ZIP: {stats.get('total', 0)}\n"
                f"• Archivos nuevos copiados: {stats.get('nuevos', 0)}\n"
                f"• Archivos actualizados (más recientes): {stats.get('actualizados', 0)}\n"
                f"• Archivos omitidos (iguales o más antiguos): {stats.get('omitidos', 0)}"
            )
            self.txt_bitacora.appendPlainText(resumen)
            QMessageBox.information(self, "Actualización Completada", resumen)
        else:
            self.lbl_estado_op.setText(mensaje)
            self.txt_bitacora.appendPlainText(f"✗ {mensaje}")
            QMessageBox.critical(self, "Error en Actualización", mensaje)

    def limpiar_estado(self):
        if self._hilo_activo is not None and self._hilo_activo.isRunning():
            self._hilo_activo.wait(2000)
        self._hilo_activo = None

    def closeEvent(self, event):
        self.limpiar_estado()
        self.cerrado.emit()
        super().closeEvent(event)


# =========================================================================================
# 6. EXPLICACIÓN Y ADMINISTRACIÓN DE LA ESTRUCTURA DE DIRECTORIOS (..\DIA\..)
# =========================================================================================
HTML_GUIA_ESTRUCTURA_DIA = """
<style>
    body { font-family: 'Segoe UI', Arial, sans-serif; font-size: 12.5px; color: #1e293b; line-height: 1.5; }
    h2 { color: #1e3a8a; border-bottom: 2px solid #93c5fd; padding-bottom: 4px; }
    h3 { color: #0f4c81; margin-top: 14px; margin-bottom: 6px; }
    pre { background-color: #0f172a; color: #f8fafc; padding: 12px; border-radius: 6px; font-family: Consolas, monospace; font-size: 11.5px; }
    table { border-collapse: collapse; width: 100%; margin: 8px 0; font-size: 12px; }
    th { background-color: #dbeafe; color: #1e3a8a; text-align: left; padding: 6px 8px; border: 1px solid #93c5fd; }
    td { padding: 5px 8px; border: 1px solid #cbd5e1; vertical-align: top; }
    code { background-color: #f1f5f9; padding: 1px 4px; border-radius: 3px; font-family: Consolas, monospace; color: #0f172a; }
</style>
<h2>Arquitectura y Organización del Directorio de Trabajo <code>..\\DIA\\</code></h2>
<p>
El repositorio operativo <b><code>DIA</code></b> (por defecto <code>G:/Mi unidad/DIA/</code> y recordado localmente en cada equipo mediante
<code>config_local_pc.json</code>) organiza jerárquicamente todas las señales continuas, eventos extraídos, localizaciones hipocentrales,
catálogos consolidados y boletines PDF/GIS de la Red Sísmica de Alerta (RSA).
</p>

<h3>1. Árbol Jerárquico Completo (Años, Meses, Semanas, Períodos y Días)</h3>
<pre>
DIA/
└── AAAA/                                     (Ej: 2026/)
    ├── reportes/                             (Reportes consolidados anuales, semanales y de períodos)
    │   ├── &lt;Zona&gt;/                           (Ej: Ecuador/, Chanlud/, Labrado/, Enjambre_Sismico/...)
    │   │   ├── AAAA_cat.csv                  (Catálogo sísmico anual consolidado)
    │   │   ├── AAAA_rep.csv                  (Listado de eventos reportados del año)
    │   │   ├── AAAA_res.csv                  (Resumen estadístico anual por día)
    │   │   ├── AAAA_rep_total.csv            (Estadísticas por responsable y turno)
    │   │   ├── AAAA.xml                      (Árbol XML de eventos y estaciones del año)
    │   │   ├── AAAA_pdf1.pdf                 (Boletín PDF anual)
    │   │   └── AAAA_cat.shp/.shx/.dbf/.prj/.qmd/.metadata.json  (Capas GIS UTM 17S EPSG:32717)
    │   ├── semanal/
    │   │   └── semanaWW/&lt;Zona&gt;/              (Consolidados y reportes de la Semana ISO WW)
    │   └── periodos/
    │       └── AAAA_MM_DD_AAAA_MM_DD/&lt;Zona&gt;/ (Reportes de rangos de fechas y Enjambres/Réplicas)
    │
    └── AAAA_MM/                              (Carpeta mensual, ej: 2026_11/)
        ├── reporte/
        │   └── &lt;Zona&gt;/                       (Reportes mensuales por región + Shapes GIS automáticos)
        │       ├── &lt;Mes&gt; del &lt;AAAA&gt;_cat.csv
        │       ├── &lt;Mes&gt; del &lt;AAAA&gt;_cat.shp / .shx / .dbf / .prj / .cpg / .qmd / .metadata.json
        │       └── &lt;Mes&gt; del &lt;AAAA&gt;_pdf1.pdf
        │
        └── AAAA_MM_DD/                       (Carpeta diaria, ej: 2026_11_15/)
            ├── mseed/
            │   ├── registros/                (Registros continuos 24h: EST_AAAAMMDD_000000.mseed)
            │   └── eventos/                  (Trazas recortadas por evento: EST_AAAAMMDD_hhmmss.mseed)
            ├── dia/                          (Archivos binarios .sis y de fases .fas para ProcesoV2)
            ├── fastHypo/                     (Salidas hipocentrales de HYPO71: MMDDhhmm.rsa, Phase, L, P, S)
            ├── procesamiento/                (Historial de intentos de localización: *_proc.csv)
            ├── acelerogramas/                (Reportes y exportaciones acelerográficas del día)
            ├── reportes/                     (Control de turnos: AAMMDD_tiempos.csv, AAMMDD_resp.csv y PDFs individuales)
            ├── AAMMDD000000_marcas.json      (Marcas de eventos picadas en el registro continuo)
            ├── AAMMDD_aux.csv                (Catálogo auxiliar generado durante la extracción)
            ├── AAMMDD000000.csv              (Matriz maestra del día con tokens por estación en offset +3)
            ├── AAMMDD000000_cat.csv          (Catálogo hipocentral diario de sismos localizados)
            ├── AAMMDD000000_rep.csv          (Resumen de eventos clasificados del día)
            ├── AAMMDD000000_res.csv          (Conteos diarios por tipo de evento)
            └── AAMMDD000000.xml              (Base XML diaria de eventos y parámetros por estación)
</pre>

<h3>2. Descripción de las 7 Subcarpetas Operativas de Cada Día (<code>AAAA_MM_DD/</code>)</h3>
<table>
    <tr>
        <th>Subcarpeta</th>
        <th>Clave en <code>obtener_directorios()</code></th>
        <th>Contenido y Propósito Sismológico</th>
    </tr>
    <tr>
        <td><b><code>mseed/registros/</code></b></td>
        <td><code>Directorio_registros</code></td>
        <td>Almacena los archivos MiniSEED continuos de 24 horas (<code>EST_AAAAMMDD_000000.mseed</code>) leídos por <b>Marcar</b> y <b>Extraer</b>.</td>
    </tr>
    <tr>
        <td><b><code>mseed/eventos/</code></b></td>
        <td><code>Directorio_eventos</code></td>
        <td>Contiene las ventanas MiniSEED recortadas en compresión STEIM1 para cada evento extraído (<code>EST_AAAAMMDD_hhmmss.mseed</code>).</td>
    </tr>
    <tr>
        <td><b><code>dia/</code></b></td>
        <td><code>Directorio_dia</code></td>
        <td>Guarda los archivos binarios multicanal <code>.sis</code> y de picado de fases <code>.fas</code> que se sincronizan con las unidades virtuales en <b>Procesamiento</b>.</td>
    </tr>
    <tr>
        <td><b><code>fastHypo/</code></b></td>
        <td><code>Directorio_fastHypo</code></td>
        <td>Almacena los resultados de inversión hipocentral generados por <i>ProcesoV2 / HYPO71</i> (<code>.rsa</code>, <code>Phase</code>, <code>L</code>, <code>P</code>, <code>S</code>).</td>
    </tr>
    <tr>
        <td><b><code>procesamiento/</code></b></td>
        <td><code>Directorio_procesamiento</code></td>
        <td>Registra la bitácora histórica de intentos de localización de cada sismo (<code>AAMMDD_hhmmss_proc.csv</code>).</td>
    </tr>
    <tr>
        <td><b><code>acelerogramas/</code></b></td>
        <td><code>Directorio_acelerogramas</code></td>
        <td>Almacena los datos y gráficas de aceleración corregida (PGA, PGV, PGD) de estaciones acelerográficas.</td>
    </tr>
    <tr>
        <td><b><code>reportes/</code></b></td>
        <td><code>Directorio_reportes</code></td>
        <td>Contiene el control de turnos y responsables (<code>AAMMDD_tiempos.csv</code>, <code>AAMMDD_resp.csv</code>) y los boletines PDF individuales de sismos.</td>
    </tr>
</table>
"""


class Configurar_estructura_dia(QWidget):
    cerrado = pyqtSignal()

    def __init__(self, directorio_trabajo="G:/Mi unidad/DIA/", parent=None):
        super().__init__(parent)
        self.setWindowTitle("ESTRUCTURA DE DIRECTORIOS Y MANEJO DE ..\\DIA\\ - RSA")
        self.setStyleSheet(ESTILO_PANEL_CONFIG)
        self.directorio_trabajo = directorio_trabajo or "G:/Mi unidad/DIA/"
        self.estructura_json_actual = None
        self.directorio_escaneado = None

        layout_raiz = QHBoxLayout(self)
        layout_raiz.setContentsMargins(8, 8, 8, 8)

        # Panel izquierdo: Referencia de solo lectura del directorio ..\DIA\ y simulador de rutas por fecha
        panel_izq = QWidget(self)
        panel_izq.setFixedWidth(365)
        v_izq = QVBoxLayout(panel_izq)

        grp_dir = QGroupBox("1. DIRECTORIO DE TRABAJO DE REFERENCIA (..\\DIA\\)", panel_izq)
        v_dir = QVBoxLayout(grp_dir)
        self.edt_dir_dia = QLineEdit(self.directorio_trabajo, grp_dir)
        self.edt_dir_dia.setReadOnly(True)
        self.lbl_estado_dir = QLabel("", grp_dir)
        self.lbl_estado_dir.setWordWrap(True)
        lbl_nota_ref = QLabel(
            "Módulo estrictamente instructivo (solo lectura). La estructura ..\\DIA\\ "
            "se genera en la estación de registro continuo; la selección de ruta y usuario "
            "de trabajo se realiza en el menú Inicio.",
            grp_dir,
        )
        lbl_nota_ref.setWordWrap(True)
        lbl_nota_ref.setStyleSheet("color:#475569; font-size:11px;")
        v_dir.addWidget(self.edt_dir_dia)
        v_dir.addWidget(self.lbl_estado_dir)
        v_dir.addWidget(lbl_nota_ref)
        v_izq.addWidget(grp_dir)

        grp_fecha = QGroupBox("2. SIMULADOR DE RUTAS CANÓNICAS POR FECHA (SOLO LECTURA)", panel_izq)
        v_fecha = QVBoxLayout(grp_fecha)
        h_f = QHBoxLayout()
        h_f.addWidget(QLabel("Fecha a consultar:", grp_fecha))
        self.date_inspeccion = QDateEdit(QDate.currentDate(), grp_fecha)
        self.date_inspeccion.setCalendarPopup(True)
        self.date_inspeccion.setDisplayFormat("yyyy-MM-dd")
        self.date_inspeccion.dateChanged.connect(self.diagnosticar_fecha)
        h_f.addWidget(self.date_inspeccion, 1)
        v_fecha.addLayout(h_f)

        self.txt_diagnostico_dia = QPlainTextEdit(grp_fecha)
        self.txt_diagnostico_dia.setReadOnly(True)
        self.txt_diagnostico_dia.setMaximumHeight(240)
        v_fecha.addWidget(self.txt_diagnostico_dia)
        v_izq.addWidget(grp_fecha)

        v_izq.addStretch()
        self.btn_salir = QPushButton("Salir", panel_izq)
        self.btn_salir.setObjectName("btn_salir")
        self.btn_salir.clicked.connect(self.close)
        v_izq.addWidget(self.btn_salir)

        # Panel derecho: QTabWidget con (Tab 1) Guía Completa de la Estructura ..\DIA\ y (Tab 2) Explorador / Escáner de Árbol en Disco
        self.tabs_der = QTabWidget(self)
        self.visor_guia = QTextBrowser(self)
        self.visor_guia.setHtml(HTML_GUIA_ESTRUCTURA_DIA)
        self.tabs_der.addTab(self.visor_guia, "📘 Explicación Completa de la Estructura ..\\DIA\\")

        tab_escaner = QWidget(self)
        v_esc = QVBoxLayout(tab_escaner)
        h_esc_top = QHBoxLayout()
        h_esc_top.addWidget(QLabel("Carpeta a escanear:", tab_escaner))
        self.edt_ruta_escanear = QLineEdit(self.directorio_trabajo, tab_escaner)
        btn_exam_esc = QPushButton("Examinar...", tab_escaner)
        btn_exam_esc.clicked.connect(self._examinar_carpeta_escaneo)
        btn_ejec_esc = QPushButton("Escanear Árbol", tab_escaner)
        btn_ejec_esc.setObjectName("btn_primario")
        btn_ejec_esc.clicked.connect(self.escanear_arbol_directorio)
        btn_exp_txt = QPushButton("Exportar TXT...", tab_escaner)
        btn_exp_txt.clicked.connect(self.exportar_arbol_txt)
        btn_exp_json = QPushButton("Exportar JSON...", tab_escaner)
        btn_exp_json.clicked.connect(self.exportar_arbol_json)
        h_esc_top.addWidget(self.edt_ruta_escanear, 1)
        h_esc_top.addWidget(btn_exam_esc)
        h_esc_top.addWidget(btn_ejec_esc)
        h_esc_top.addWidget(btn_exp_txt)
        h_esc_top.addWidget(btn_exp_json)
        v_esc.addLayout(h_esc_top)

        self.salida_arbol = QPlainTextEdit(tab_escaner)
        self.salida_arbol.setReadOnly(True)
        self.salida_arbol.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.salida_arbol.setFont(QFont("Consolas", 9))
        v_esc.addWidget(self.salida_arbol, 1)
        self.tabs_der.addTab(tab_escaner, "🌳 Explorador e Inventario del Árbol en Disco (TXT / JSON)")

        layout_raiz.addWidget(panel_izq, 0)
        layout_raiz.addWidget(self.tabs_der, 1)

        self._actualizar_estado_ruta()
        self.diagnosticar_fecha()

    def _actualizar_estado_ruta(self):
        ruta = self.edt_dir_dia.text().strip()
        existe = os.path.isdir(ruta)
        if existe:
            self.lbl_estado_dir.setText("<span style='color:#15803d; font-weight:bold;'>✓ Directorio DIA accesible en este equipo.</span>")
        else:
            self.lbl_estado_dir.setText("<span style='color:#b91c1c; font-weight:bold;'>⚠ La ruta indicada no existe actualmente en este equipo.</span>")

    def diagnosticar_fecha(self):
        f_qt = self.date_inspeccion.date()
        arch_semilla = os.path.join(self.edt_dir_dia.text().strip(), f_qt.toString("yyyyMMdd000000"))
        try:
            dirs = obtener_directorios(arch_semilla)
            claves_sub = [
                ("Directorio_base", "Carpeta Raíz del Día"),
                ("Directorio_registros", "mseed/registros"),
                ("Directorio_eventos", "mseed/eventos"),
                ("Directorio_dia", "dia (.sis/.fas)"),
                ("Directorio_fastHypo", "fastHypo (.rsa)"),
                ("Directorio_procesamiento", "procesamiento (*_proc.csv)"),
                ("Directorio_acelerogramas", "acelerogramas"),
                ("Directorio_reportes", "reportes (_tiempos/_resp)"),
            ]
            lineas = [f"Fecha: {f_qt.toString('yyyy/MM/dd')}"]
            for clave, etiq in claves_sub:
                r_sub = dirs.get(clave, "")
                ok = os.path.isdir(r_sub)
                marca = "✓ EXISTE" if ok else "✗ No creada"
                lineas.append(f"[{marca}] {etiq}:\n    {r_sub}")
            self.txt_diagnostico_dia.setPlainText("\n".join(lineas))
            if os.path.isdir(dirs.get("Directorio_base", "")):
                self.edt_ruta_escanear.setText(dirs["Directorio_base"])
        except Exception as e:
            self.txt_diagnostico_dia.setPlainText(f"No se pudo resolver la estructura: {e}")

    def _examinar_carpeta_escaneo(self):
        carpeta = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta a escanear", self.edt_ruta_escanear.text())
        if carpeta:
            self.edt_ruta_escanear.setText(carpeta)

    def escanear_arbol_directorio(self):
        ruta = Path(self.edt_ruta_escanear.text().strip())
        if not ruta.exists() or not ruta.is_dir():
            QMessageBox.warning(self, "Ruta inválida", "La carpeta indicada para escanear no existe.")
            return
        self.directorio_escaneado = ruta
        lineas = [f"{ruta.resolve()}/", f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ""]
        raiz_json = {"nombre": ruta.name, "tipo": "directorio", "contenido": []}

        def _listar(d: Path):
            try:
                with os.scandir(d) as it:
                    ents = [e for e in it if e.is_dir(follow_symlinks=False) or e.is_file(follow_symlinks=False)]
                ents.sort(key=lambda x: x.name.lower())
                return ents
            except Exception:
                return []

        pila = [(ruta, "", raiz_json, _listar(ruta), 0)]
        max_lineas = 5000
        while pila and len(lineas) < max_lineas:
            dir_act, pref, nodo_j, entradas, i = pila.pop()
            if i >= len(entradas):
                continue
            ent = entradas[i]
            es_ult = (i == len(entradas) - 1)
            ramal = "└── " if es_ult else "├── "
            pila.append((dir_act, pref, nodo_j, entradas, i + 1))
            if ent.is_dir(follow_symlinks=False):
                lineas.append(f"{pref}{ramal}{ent.name}/")
                nodo_hijo = {"nombre": ent.name, "tipo": "directorio", "contenido": []}
                nodo_j["contenido"].append(nodo_hijo)
                pref_h = pref + ("    " if es_ult else "│   ")
                pila.append((Path(ent.path), pref_h, nodo_hijo, _listar(Path(ent.path)), 0))
            else:
                try:
                    st = Path(ent.path).stat()
                    mod = datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    mod = ""
                lineas.append(f"{pref}{ramal}{ent.name} (modificado: {mod})")
                nodo_j["contenido"].append({"nombre": ent.name, "tipo": "archivo", "modificado": mod})

        self.estructura_json_actual = raiz_json
        self.salida_arbol.setPlainText("\n".join(lineas))

    def exportar_arbol_txt(self):
        contenido = self.salida_arbol.toPlainText().strip()
        if not contenido:
            QMessageBox.information(self, "Aviso", "Primero escanee un directorio.")
            return
        nombre, _ = QFileDialog.getSaveFileName(self, "Guardar TXT...", "estructura_dia.txt", "Texto (*.txt)")
        if nombre:
            Path(nombre).write_text(contenido, encoding="utf-8")

    def exportar_arbol_json(self):
        if not self.estructura_json_actual:
            QMessageBox.information(self, "Aviso", "Primero escanee un directorio.")
            return
        nombre, _ = QFileDialog.getSaveFileName(self, "Guardar JSON...", "estructura_dia.json", "JSON (*.json)")
        if nombre:
            Path(nombre).write_text(json.dumps(self.estructura_json_actual, ensure_ascii=False, indent=2), encoding="utf-8")

    def limpiar_estado(self):
        pass

    def closeEvent(self, event):
        self.limpiar_estado()
        self.cerrado.emit()
        super().closeEvent(event)


# ==============================================================================
# 7. RESPALDO Y RESTAURACIÓN DEL PROGRAMA (ZIP - SOLO PC ADMINISTRADOR)
# ==============================================================================

CARPETAS_RESPALDO_PROGRAMA = ("datos", "modulos externos", "src")
CARPETAS_EXCLUIDAS_RESPALDO = {"__pycache__", "vw backup"}
EXTENSIONES_EXCLUIDAS_RESPALDO = {".vwx", ".vwxw", ".vwt", ".mcd", ".pyc", ".pyo"}


def recolectar_archivos_respaldo(raiz_origen: str):
    """
    Recorre `datos/`, `modulos externos/` y `src/` dentro de `raiz_origen`
    excluyendo carpetas de caché (`__pycache__`), respaldos Vectorworks (`VW Backup`)
    y extensiones excluidas (`.vwx`, `.vwxw`, `.vwt`, `.mcd`, `.pyc`, `.pyo`).

    Retorna:
        tuple[list[tuple[str, str]], int]: `(lista_(ruta_abs, ruta_rel_zip), conteo_excluidos)`
    """
    raiz_path = Path(raiz_origen).resolve()
    archivos_incluir = []
    conteo_excluidos = 0

    for carpeta_base in CARPETAS_RESPALDO_PROGRAMA:
        dir_objetivo = raiz_path / carpeta_base
        if not dir_objetivo.is_dir():
            continue
        for actual, subdirs, nombres in os.walk(dir_objetivo):
            subdirs_filtrados = []
            for d in subdirs:
                if d.strip().lower() in CARPETAS_EXCLUIDAS_RESPALDO:
                    conteo_excluidos += 1
                else:
                    subdirs_filtrados.append(d)
            subdirs[:] = sorted(subdirs_filtrados, key=str.lower)

            for nom in sorted(nombres, key=str.lower):
                ext = os.path.splitext(nom)[1].lower()
                if ext in EXTENSIONES_EXCLUIDAS_RESPALDO:
                    conteo_excluidos += 1
                    continue
                ruta_abs = os.path.join(actual, nom)
                ruta_rel = os.path.relpath(ruta_abs, raiz_path).replace("\\", "/")
                archivos_incluir.append((ruta_abs, ruta_rel))

    return archivos_incluir, conteo_excluidos


class HiloRespaldoZip(QThread):
    """Hilo de trabajo para comprimir el programa en formato ZIP sin bloquear la UI."""

    progreso = pyqtSignal(int, str)
    terminado = pyqtSignal(bool, str, dict)

    def __init__(self, raiz_origen: str, ruta_zip_destino: str, parent=None):
        super().__init__(parent)
        self.raiz_origen = raiz_origen
        self.ruta_zip_destino = ruta_zip_destino

    def run(self):
        ruta_tmp = self.ruta_zip_destino + ".tmp"
        try:
            archivos, excluidos = recolectar_archivos_respaldo(self.raiz_origen)
            total = len(archivos)
            if total == 0:
                self.terminado.emit(
                    False,
                    "No se encontraron archivos válidos en datos/, modulos externos/ o src/.",
                    {"incluidos": 0, "excluidos": excluidos},
                )
                return

            os.makedirs(os.path.dirname(os.path.abspath(self.ruta_zip_destino)), exist_ok=True)
            with zipfile.ZipFile(ruta_tmp, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
                for idx, (ruta_abs, ruta_rel) in enumerate(archivos, start=1):
                    zf.write(ruta_abs, arcname=ruta_rel)
                    pct = int((idx * 100) / total)
                    self.progreso.emit(pct, ruta_rel)

            os.replace(ruta_tmp, self.ruta_zip_destino)
            tam_mb = os.path.getsize(self.ruta_zip_destino) / (1024.0 * 1024.0)
            self.terminado.emit(
                True,
                f"Respaldo generado correctamente ({tam_mb:.2f} MB).",
                {"incluidos": total, "excluidos": excluidos, "tam_mb": tam_mb},
            )
        except Exception as e:
            try:
                if os.path.exists(ruta_tmp):
                    os.remove(ruta_tmp)
            except Exception:
                pass
            self.terminado.emit(False, f"Error generando el respaldo ZIP: {e}", {})


class HiloRestaurarZip(QThread):
    """
    Hilo de trabajo para descomprimir un respaldo ZIP respetando la estructura
    de directorios y copiando únicamente archivos nuevos o más recientes.
    """

    progreso = pyqtSignal(int, str)
    terminado = pyqtSignal(bool, str, dict)

    def __init__(self, ruta_zip_origen: str, carpeta_destino: str, parent=None):
        super().__init__(parent)
        self.ruta_zip_origen = ruta_zip_origen
        self.carpeta_destino = carpeta_destino

    def run(self):
        try:
            raiz_dest = os.path.abspath(self.carpeta_destino)
            os.makedirs(raiz_dest, exist_ok=True)

            with zipfile.ZipFile(self.ruta_zip_origen, "r") as zf:
                entradas = [info for info in zf.infolist() if not info.is_dir()]
                total = len(entradas)
                if total == 0:
                    self.terminado.emit(
                        False,
                        "El archivo ZIP seleccionado no contiene archivos.",
                        {},
                    )
                    return

                nuevos = 0
                actualizados = 0
                omitidos = 0

                for idx, info in enumerate(entradas, start=1):
                    nombre_rel = info.filename.replace("\\", "/").lstrip("/")
                    dest_abs = os.path.abspath(os.path.join(raiz_dest, *nombre_rel.split("/")))

                    # Protección contra rutas maliciosas fuera de carpeta_destino (Zip Slip)
                    if os.path.commonpath([raiz_dest, dest_abs]) != raiz_dest:
                        omitidos += 1
                        continue

                    mtime_zip = datetime(*info.date_time).timestamp()
                    existe_previo = os.path.isfile(dest_abs)

                    if existe_previo:
                        mtime_local = os.path.getmtime(dest_abs)
                        # Tolerancia de 2 s por resolución DOS de fechas en archivos ZIP
                        if mtime_zip <= mtime_local + 2.0:
                            omitidos += 1
                            pct = int((idx * 100) / total)
                            self.progreso.emit(pct, f"Omitido (actual/antiguo): {nombre_rel}")
                            continue

                    os.makedirs(os.path.dirname(dest_abs), exist_ok=True)
                    with zf.open(info, "r") as f_src, open(dest_abs, "wb") as f_dst:
                        shutil.copyfileobj(f_src, f_dst)
                    os.utime(dest_abs, (mtime_zip, mtime_zip))

                    if existe_previo:
                        actualizados += 1
                        estado_txt = f"Actualizado: {nombre_rel}"
                    else:
                        nuevos += 1
                        estado_txt = f"Nuevo: {nombre_rel}"

                    pct = int((idx * 100) / total)
                    self.progreso.emit(pct, estado_txt)

            self.terminado.emit(
                True,
                "Restauración / actualización completada.",
                {
                    "total": total,
                    "nuevos": nuevos,
                    "actualizados": actualizados,
                    "omitidos": omitidos,
                },
            )
        except Exception as e:
            self.terminado.emit(False, f"Error restaurando desde ZIP: {e}", {})


class Respaldar_programa(QWidget):
    cerrado = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("RESPALDO Y ACTUALIZACIÓN DEL PROGRAMA (ZIP) - RSA")
        self.setStyleSheet(ESTILO_PANEL_CONFIG)
        self.raiz_proyecto = os.path.abspath(ruta_proyecto)
        self._hilo_activo = None

        layout_raiz = QVBoxLayout(self)
        layout_raiz.setContentsMargins(12, 10, 12, 10)
        layout_raiz.setSpacing(10)

        autorizado_pc, nombre_pc, msg_pc = verificar_permiso_respaldo_pc()
        lbl_seg = QLabel(
            f"Equipo actual: <b>{nombre_pc}</b> — {msg_pc}",
            self,
        )
        lbl_seg.setWordWrap(True)
        if autorizado_pc:
            lbl_seg.setStyleSheet(
                "background:#e8f5e9; color:#1b5e20; border:1px solid #81c784; "
                "border-radius:4px; padding:6px 10px;"
            )
        else:
            lbl_seg.setStyleSheet(
                "background:#ffebee; color:#b71c1c; border:1px solid #e57373; "
                "border-radius:4px; padding:6px 10px;"
            )
        layout_raiz.addWidget(lbl_seg)

        # 1. Sección de creación de respaldo ZIP
        grp_backup = QGroupBox("1. GENERAR RESPALDO DEL PROGRAMA (.ZIP)", self)
        v_bkp = QVBoxLayout(grp_backup)
        lbl_info_bkp = QLabel(
            f"<b>Origen:</b> <code>{self.raiz_proyecto}</code><br>"
            "<b>Carpetas incluidas:</b> <code>datos/</code>, <code>modulos externos/</code> y <code>src/</code> "
            "(respetando íntegramente su estructura de directorios).<br>"
            "<b>Exclusiones automáticas:</b> GitHub/Agente, <code>datos/mapas/VW Backup/</code>, "
            "archivos de Vectorworks (<code>*.vwx</code>, <code>*.vwxw</code>, <code>*.vwt</code>, <code>*.mcd</code>) "
            "y caché Python (<code>__pycache__/</code>, <code>*.pyc</code>).",
            grp_backup,
        )
        lbl_info_bkp.setWordWrap(True)
        lbl_info_bkp.setStyleSheet("font-weight: normal; color: #263238;")
        v_bkp.addWidget(lbl_info_bkp)

        h_bkp_btn = QHBoxLayout()
        self.btn_crear_zip = QPushButton("Generar Respaldo ZIP (Guardar como...)", grp_backup)
        self.btn_crear_zip.setObjectName("btn_primario")
        self.btn_crear_zip.setEnabled(autorizado_pc)
        self.btn_crear_zip.clicked.connect(self.ejecutar_respaldo_zip)
        h_bkp_btn.addWidget(self.btn_crear_zip)
        h_bkp_btn.addStretch()
        v_bkp.addLayout(h_bkp_btn)
        layout_raiz.addWidget(grp_backup)

        # 2. Progreso y bitácora
        grp_prog = QGroupBox("2. PROGRESO Y BITÁCORA DE OPERACIÓN", self)
        v_prog = QVBoxLayout(grp_prog)
        self.lbl_estado_op = QLabel("En espera.", grp_prog)
        self.lbl_estado_op.setStyleSheet("font-weight: normal; color: #37474f;")
        self.barra_progreso = QProgressBar(grp_prog)
        self.barra_progreso.setRange(0, 100)
        self.barra_progreso.setValue(0)
        self.txt_bitacora = QPlainTextEdit(grp_prog)
        self.txt_bitacora.setReadOnly(True)
        self.txt_bitacora.setMinimumHeight(180)
        v_prog.addWidget(self.lbl_estado_op)
        v_prog.addWidget(self.barra_progreso)
        v_prog.addWidget(self.txt_bitacora, 1)
        layout_raiz.addWidget(grp_prog, 1)

        h_pie = QHBoxLayout()
        h_pie.addStretch()
        self.btn_salir = QPushButton("Salir", self)
        self.btn_salir.setObjectName("btn_salir")
        self.btn_salir.clicked.connect(self.close)
        h_pie.addWidget(self.btn_salir)
        layout_raiz.addLayout(h_pie)

    def _establecer_controles_activos(self, habilitado: bool):
        autorizado_pc, _, _ = verificar_permiso_respaldo_pc()
        self.btn_crear_zip.setEnabled(habilitado and autorizado_pc)
        self.btn_salir.setEnabled(habilitado)

    def ejecutar_respaldo_zip(self):
        autorizado_pc, _, msg_pc = verificar_permiso_respaldo_pc()
        if not autorizado_pc:
            QMessageBox.warning(self, "Acceso Restringido", msg_pc)
            return

        nombre_sug = f"respaldo_rsa_sismologia_{datetime.now().strftime('%Y%m%d_%H%M')}.zip"
        ruta_zip, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar respaldo del programa como...",
            os.path.join(self.raiz_proyecto, nombre_sug),
            "Archivos ZIP (*.zip)",
        )
        if not ruta_zip:
            return
        if not ruta_zip.lower().endswith(".zip"):
            ruta_zip += ".zip"

        self.txt_bitacora.clear()
        self.barra_progreso.setValue(0)
        self.lbl_estado_op.setText("Comprimiendo archivos...")
        self._establecer_controles_activos(False)

        self._hilo_activo = HiloRespaldoZip(self.raiz_proyecto, ruta_zip, self)
        self._hilo_activo.progreso.connect(self._al_avanzar_operacion)
        self._hilo_activo.terminado.connect(self._al_terminar_respaldo)
        self._hilo_activo.start()

    def _al_avanzar_operacion(self, porcentaje: int, detalle: str):
        self.barra_progreso.setValue(porcentaje)
        self.lbl_estado_op.setText(detalle)

    def _al_terminar_respaldo(self, ok: bool, mensaje: str, stats: dict):
        self._establecer_controles_activos(True)
        if ok:
            self.barra_progreso.setValue(100)
            self.lbl_estado_op.setText(mensaje)
            self.txt_bitacora.appendPlainText(
                f"✓ {mensaje}\n"
                f"• Archivos comprimidos: {stats.get('incluidos', 0)}\n"
                f"• Elementos excluidos (VW Backup / Vectorworks / __pycache__): {stats.get('excluidos', 0)}"
            )
            QMessageBox.information(self, "Respaldo Completado", mensaje)
        else:
            self.lbl_estado_op.setText(mensaje)
            self.txt_bitacora.appendPlainText(f"✗ {mensaje}")
            QMessageBox.critical(self, "Error en Respaldo", mensaje)

    def limpiar_estado(self):
        if self._hilo_activo is not None and self._hilo_activo.isRunning():
            self._hilo_activo.wait(2000)
        self._hilo_activo = None

    def closeEvent(self, event):
        self.limpiar_estado()
        self.cerrado.emit()
        super().closeEvent(event)


class Restaurar_programa(QWidget):
    """
    Módulo abierto a cualquier equipo para descomprimir/actualizar el programa
    desde un archivo ZIP respetando la estructura de directorios y copiando
    únicamente archivos nuevos o más recientes.
    """
    cerrado = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ACTUALIZAR / RECUPERAR PROGRAMA DESDE ZIP - RSA")
        self.setStyleSheet(ESTILO_PANEL_CONFIG)
        self.raiz_proyecto = os.path.abspath(ruta_proyecto)
        self._hilo_activo = None

        layout_raiz = QVBoxLayout(self)
        layout_raiz.setContentsMargins(12, 10, 12, 10)
        layout_raiz.setSpacing(10)

        grp_rest = QGroupBox("1. SELECCIÓN DE RESPALDO (.ZIP) Y CARPETA DESTINO", self)
        grid_r = QGridLayout(grp_rest)

        self.edt_zip_origen = QLineEdit(grp_rest)
        self.edt_zip_origen.setPlaceholderText("Seleccione el archivo .zip de respaldo...")
        self.btn_buscar_zip = QPushButton("Examinar ZIP...", grp_rest)
        self.btn_buscar_zip.clicked.connect(self.seleccionar_zip_origen)

        self.edt_dir_destino = QLineEdit(self.raiz_proyecto, grp_rest)
        self.btn_buscar_dest = QPushButton("Carpeta destino...", grp_rest)
        self.btn_buscar_dest.clicked.connect(self.seleccionar_carpeta_destino)

        lbl_nota_inc = QLabel(
            "<b>Actualización ágil:</b> solo se copian archivos nuevos o con fecha de modificación "
            "más reciente que la versión existente en destino; las versiones iguales o más antiguas se omiten, "
            "respetando íntegramente la estructura de directorios.",
            grp_rest,
        )
        lbl_nota_inc.setWordWrap(True)
        lbl_nota_inc.setStyleSheet("font-weight: normal; color: #1e3a8a;")

        self.btn_restaurar_zip = QPushButton("Restaurar / Actualizar desde ZIP", grp_rest)
        self.btn_restaurar_zip.setObjectName("btn_primario")
        self.btn_restaurar_zip.clicked.connect(self.ejecutar_restauracion_zip)

        grid_r.addWidget(QLabel("Archivo ZIP:"), 0, 0)
        grid_r.addWidget(self.edt_zip_origen, 0, 1)
        grid_r.addWidget(self.btn_buscar_zip, 0, 2)
        grid_r.addWidget(QLabel("Carpeta destino:"), 1, 0)
        grid_r.addWidget(self.edt_dir_destino, 1, 1)
        grid_r.addWidget(self.btn_buscar_dest, 1, 2)
        grid_r.addWidget(lbl_nota_inc, 2, 0, 1, 3)
        grid_r.addWidget(self.btn_restaurar_zip, 3, 0, 1, 3)
        layout_raiz.addWidget(grp_rest)

        grp_prog = QGroupBox("2. PROGRESO Y BITÁCORA DE ACTUALIZACIÓN", self)
        v_prog = QVBoxLayout(grp_prog)
        self.lbl_estado_op = QLabel("En espera.", grp_prog)
        self.lbl_estado_op.setStyleSheet("font-weight: normal; color: #37474f;")
        self.barra_progreso = QProgressBar(grp_prog)
        self.barra_progreso.setRange(0, 100)
        self.barra_progreso.setValue(0)
        self.txt_bitacora = QPlainTextEdit(grp_prog)
        self.txt_bitacora.setReadOnly(True)
        self.txt_bitacora.setMinimumHeight(180)
        v_prog.addWidget(self.lbl_estado_op)
        v_prog.addWidget(self.barra_progreso)
        v_prog.addWidget(self.txt_bitacora, 1)
        layout_raiz.addWidget(grp_prog, 1)

        h_pie = QHBoxLayout()
        h_pie.addStretch()
        self.btn_salir = QPushButton("Salir", self)
        self.btn_salir.setObjectName("btn_salir")
        self.btn_salir.clicked.connect(self.close)
        h_pie.addWidget(self.btn_salir)
        layout_raiz.addLayout(h_pie)

    def _establecer_controles_activos(self, habilitado: bool):
        self.btn_buscar_zip.setEnabled(habilitado)
        self.btn_buscar_dest.setEnabled(habilitado)
        self.btn_restaurar_zip.setEnabled(habilitado)
        self.btn_salir.setEnabled(habilitado)

    def seleccionar_zip_origen(self):
        ruta, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar respaldo ZIP",
            self.raiz_proyecto,
            "Archivos ZIP (*.zip)",
        )
        if ruta:
            self.edt_zip_origen.setText(ruta)

    def seleccionar_carpeta_destino(self):
        carpeta = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar carpeta destino para restaurar",
            self.edt_dir_destino.text().strip() or self.raiz_proyecto,
        )
        if carpeta:
            self.edt_dir_destino.setText(carpeta)

    def ejecutar_restauracion_zip(self):
        ruta_zip = self.edt_zip_origen.text().strip()
        carpeta_dest = self.edt_dir_destino.text().strip()
        if not ruta_zip or not os.path.isfile(ruta_zip):
            QMessageBox.warning(self, "Validación", "Seleccione un archivo .zip válido.")
            return
        if not carpeta_dest:
            QMessageBox.warning(self, "Validación", "Indique la carpeta destino.")
            return

        resp = QMessageBox.question(
            self,
            "Confirmar actualización incremental",
            f"Se extraerán únicamente los archivos nuevos o más recientes desde:\n{ruta_zip}\n\n"
            f"Hacia:\n{carpeta_dest}\n\n¿Desea continuar?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if resp != QMessageBox.Yes:
            return

        self.txt_bitacora.clear()
        self.barra_progreso.setValue(0)
        self.lbl_estado_op.setText("Verificando fechas y extrayendo archivos más nuevos...")
        self._establecer_controles_activos(False)

        self._hilo_activo = HiloRestaurarZip(ruta_zip, carpeta_dest, self)
        self._hilo_activo.progreso.connect(self._al_avanzar_operacion)
        self._hilo_activo.terminado.connect(self._al_terminar_restauracion)
        self._hilo_activo.start()

    def _al_avanzar_operacion(self, porcentaje: int, detalle: str):
        self.barra_progreso.setValue(porcentaje)
        self.lbl_estado_op.setText(detalle)

    def _al_terminar_restauracion(self, ok: bool, mensaje: str, stats: dict):
        self._establecer_controles_activos(True)
        if ok:
            self.barra_progreso.setValue(100)
            self.lbl_estado_op.setText(mensaje)
            resumen = (
                f"✓ {mensaje}\n"
                f"• Total en ZIP: {stats.get('total', 0)}\n"
                f"• Archivos nuevos copiados: {stats.get('nuevos', 0)}\n"
                f"• Archivos actualizados (más recientes): {stats.get('actualizados', 0)}\n"
                f"• Archivos omitidos (iguales o más antiguos): {stats.get('omitidos', 0)}"
            )
            self.txt_bitacora.appendPlainText(resumen)
            QMessageBox.information(self, "Actualización Completada", resumen)
        else:
            self.lbl_estado_op.setText(mensaje)
            self.txt_bitacora.appendPlainText(f"✗ {mensaje}")
            QMessageBox.critical(self, "Error en Actualización", mensaje)

    def limpiar_estado(self):
        if self._hilo_activo is not None and self._hilo_activo.isRunning():
            self._hilo_activo.wait(2000)
        self._hilo_activo = None

    def closeEvent(self, event):
        self.limpiar_estado()
        self.cerrado.emit()
        super().closeEvent(event)
