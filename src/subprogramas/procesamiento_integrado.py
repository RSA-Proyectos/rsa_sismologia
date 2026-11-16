import sys
import os
from pathlib import Path
def extraer_hasta_directorio(ruta_completa, nombre_directorio):
    partes = Path(ruta_completa).parts
    if nombre_directorio in partes:
# %%
        indice = partes.index(nombre_directorio)

        ruta_recortada = Path(*partes[:indice + 1])
        return str(ruta_recortada) + '/'
    else:
        return ''
ruta_librerias=os.path.dirname(__file__)
ruta_proyecto=extraer_hasta_directorio(ruta_librerias, 'rsa_sismologia')
ruta_librerias = os.path.abspath(os.path.join(ruta_proyecto, 'src','librerias'))

# Insertar la ruta al inicio del sys.path
if ruta_librerias not in sys.path:
    sys.path.insert(0, ruta_librerias)

from rsa_io import leer_mseed,lectura_archivo,escritura_archivo,copiar_archivos,Guardar_dia
from rsa_procesamiento import archivos_fast,guardar_intento,guardar_informacion_diaria,ordenar_y_eliminar_duplicados,verificar_coincidencias,lectura_rsa
from rsa_utilidades import actualizar_periodos_emitidos_desde_fecha
from metodos_gis_rsa import widget_grafico_mpl
from metodos_rsa import (
    parametros_estaciones,
    grafico_evento_int,
    insertar_evento_otras_redes,
    cargar_dia,
    cargar_evento,
    buscar_evento_otra_red_en_linea,
    sincronizar_otras_redes_dia,
)
from metodos_gestion import obtener_directorios
from metodos_reportes_individuales import generar_reporte_sismo, generar_reporte_acelerograma
from rsa_pdf_catalogo import reporte_resumen_modos, construir_catalogo_temporal_turno


#from metodos_reportes_individuales import insertar_evento_otras_redes
from PyQt5.QtWidgets import (QMessageBox,QDialog,QLabel,QCheckBox,QPushButton,QComboBox,QSpinBox,QTextEdit,QVBoxLayout,QWidget,QRadioButton)
from PyQt5.QtGui import QColor, QBrush, QFont
from PyQt5 import uic
from datetime import datetime
from PyQt5.QtCore import QDate
from PyQt5.QtCore import Qt,QTimer
import time
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtCore import pyqtSignal
import xml.etree.ElementTree as ET


from PyQt5.QtWidgets import  QHBoxLayout

# =========================
#  MODOS DE REPORTE (1–7)
# =========================
MODO_PERIODO_FRANJAS          = 1   # M1 – Período por franjas (00–12, 12–18, 18–24) – Control interno
MODO_DIARIO_REVISION          = 2   # M2 – Diario de revisión (día/ad-hoc) con detalle y dummies locales
MODO_OFICIAL_DETALLADO        = 3   # M3 – Oficial detallado (solo catálogo) + página/resumen de responsables
MODO_OFICIAL_RESUMEN          = 4   # M4 – Oficial resumen (solo catálogo, sin detalle)
MODO_FACULTAD_RESUMEN         = 5   # M5 – Facultad resumen (Facultad/redes), sin detalle
MODO_INSTITUCIONAL_DETALLADO  = 6   # M6 – Institucional detallado (solo catálogo), sin extras ni responsables
MODO_INSTITUCIONAL_RESUMEN    = 7   # M7 – Institucional, sin detalle

def evaluar_estado_evento(self, nombre_evento):
    """
    Evalúa el estado técnico de un evento para determinar su categorización visual en el combo box:
    - Exclusivo para eventos clasificados como 'SISMO' (los demás van siempre en negro: 'NO_SISMO').
    - 'PENDIENTE' (Negro): El evento cuenta únicamente con el archivo .sis en la carpeta dia/ del host
      (no tiene .fas en dia/), lo cual implica necesariamente que aún no ha sido procesado.
    - 'INCONVENIENTE' (Rojo):
      1. No encuentra el archivo .sis en dia/.
      2. Habiendo pasado por procesamiento (existe .fas en dia/), presenta alguna falla:
         - No encuentra los archivos FAST (.rsa).
         - La lectura de la magnitud es 0 (o <= 0 / no determinada).
         - El valor del RMS es mayor a 1.4 (o no determinado).
    - 'EXITOSO' (Verde): Procesado correctamente (.sis, .fas y .rsa existen, Magnitud > 0 y RMS <= 1.4).

    Retorna:
        tuple[str, str]: (estado, tooltip_descriptivo)
    """
    base_nombre = Path(nombre_evento).name
    stem = Path(nombre_evento).stem
    stem_corto = stem[2:] if len(stem.replace('_', '')) == 14 else stem

    # Los colores (Verde y Rojo) son EXCLUSIVOS para eventos clasificados como SISMO.
    # Los demás tipos de evento (Ruido, FF, FC, etc.) siempre permanecen en negro.
    tipo_evento = None
    if hasattr(self, 'eventos') and self.eventos:
        for ev in self.eventos:
            if ev and len(ev) > 2 and Path(ev[1]).name == base_nombre:
                tipo_evento = ev[2]
                break

    if tipo_evento is not None and tipo_evento != 'SISMO':
        return 'NO_SISMO', f"Evento clasificado como {tipo_evento}"

    # 1. Resolver rutas exactas de archivos asociados (.sis, .fas en dia/ y .rsa en fastHypo/)
    archivo_sis = ""
    archivo_fas = ""
    archivo_rsa = ""

    # Resolver mediante archivos_fast + verificar_coincidencias (maneja sufijos a/b/c y ss >= 50)
    try:
        rutas_base = archivos_fast(nombre_evento, self.directorio_trabajo, '', modo_minuto_fast='auto')
        if hasattr(self, 'eventos') and self.eventos:
            rutas = verificar_coincidencias(self.eventos, nombre_evento, rutas_base)
        else:
            rutas = rutas_base
        if len(rutas) >= 3:
            if os.path.isfile(rutas[0]):
                archivo_sis = rutas[0]
            if os.path.isfile(rutas[1]):
                archivo_fas = rutas[1]
            if os.path.isfile(rutas[2]):
                archivo_rsa = rutas[2]
    except Exception:
        rutas = []

    # Verificación directa en self.directorios del día activo por si difiere la ruta relativa
    if hasattr(self, 'directorios') and isinstance(self.directorios, dict):
        dir_dia_act = self.directorios.get('Directorio_dia', '')
        dir_fast_act = self.directorios.get('Directorio_fastHypo', '')
        if dir_dia_act and os.path.exists(dir_dia_act):
            if not archivo_sis:
                for cand in [
                    os.path.join(dir_dia_act, f"{stem}.sis"),
                    os.path.join(dir_dia_act, f"{stem_corto}.sis"),
                    os.path.join(dir_dia_act, base_nombre),
                ]:
                    if os.path.isfile(cand):
                        archivo_sis = cand
                        break

            if not archivo_fas:
                for cand_f in [
                    os.path.join(dir_dia_act, f"{stem}.fas"),
                    os.path.join(dir_dia_act, f"{stem_corto}.fas"),
                ]:
                    if os.path.isfile(cand_f):
                        archivo_fas = cand_f
                        break

        if not archivo_rsa and dir_fast_act and os.path.exists(dir_fast_act) and len(rutas) >= 3 and rutas[2]:
            cand_rsa = os.path.join(dir_fast_act, Path(rutas[2]).name)
            if os.path.isfile(cand_rsa):
                archivo_rsa = cand_rsa

    existe_sis = bool(archivo_sis and os.path.isfile(archivo_sis))
    existe_fas = bool(archivo_fas and os.path.isfile(archivo_fas))
    existe_fast = bool(archivo_rsa and os.path.isfile(archivo_rsa))

    # 2. Regla fundamental de negocio:
    # - Si no tiene ni siquiera .sis en dia/ -> ROJO (Inconveniente: falta extracción de .sis).
    # - Si en dia/ SOLO tiene el archivo .sis (no existe .fas), implica necesariamente
    #   que el evento AÚN NO HA SIDO PROCESADO -> SIEMPRE EN NEGRO (PENDIENTE).
    if not existe_sis:
        return 'INCONVENIENTE', "Inconveniente: No encuentra archivo .sis en dia/"

    if not existe_fas:
        return 'PENDIENTE', "Evento pendiente de procesamiento (solo .sis en host)"

    # 3. A partir de aquí el evento tiene .sis y .fas en el host (ya pasó por procesamiento).
    # Extraer Magnitud y RMS para validar calidad del procesamiento.
    sismo_catalogo = None
    if hasattr(self, 'catalogo') and self.catalogo:
        for fila in self.catalogo:
            if fila and len(fila) > 18 and fila[18] != 'ruta':
                if Path(fila[18]).name == base_nombre or Path(fila[18]).stem == stem:
                    sismo_catalogo = fila
                    break

    arch_proc = ""
    proc_rows = []
    try:
        if hasattr(self, 'directorios') and isinstance(self.directorios, dict):
            dir_proc = self.directorios.get('Directorio_procesamiento', '')
            if dir_proc and os.path.exists(dir_proc):
                for f_p in os.listdir(dir_proc):
                    if f_p.lower().endswith('_proc.csv') and (stem in f_p or stem_corto in f_p):
                        arch_proc = os.path.join(dir_proc, f_p)
                        break
        if not arch_proc:
            dirs_proc = obtener_directorios(os.path.join(self.directorio_trabajo, nombre_evento))
            arch_proc = dirs_proc.get('archivo_procesamiento', '')
        if arch_proc and os.path.exists(arch_proc):
            proc_rows = lectura_archivo(arch_proc)
    except Exception:
        pass

    es_evento_actual = (
        hasattr(self, 'evento_procesar')
        and self.evento_procesar
        and Path(self.evento_procesar[1]).stem == stem
    )
    tiene_proc_en_memoria = bool(
        es_evento_actual
        and hasattr(self, 'procesamiento')
        and self.procesamiento
        and len(self.procesamiento) > 2
        and any(len(r) > 2 and r[2] not in ("Inicio", " ") for r in self.procesamiento[1:])
    )

    val_mag = None
    val_rms = None

    # Prioridad A: catálogo oficial en memoria
    if sismo_catalogo:
        try:
            val_rms = float(sismo_catalogo[10])
        except (ValueError, TypeError, IndexError):
            pass
        try:
            val_mag = float(sismo_catalogo[15])
        except (ValueError, TypeError, IndexError):
            pass

    # Prioridad B: procesamiento en memoria si es el evento activo
    if (val_mag is None or val_rms is None) and tiene_proc_en_memoria:
        fila_mem = self.procesamiento[-1]
        if len(fila_mem) >= 7 and fila_mem[2] not in ("Inicio", "Fallido"):
            if val_mag is None:
                try:
                    val_mag = float(fila_mem[3])
                except (ValueError, TypeError, IndexError):
                    pass
            if val_rms is None:
                try:
                    val_rms = float(fila_mem[6])
                except (ValueError, TypeError, IndexError):
                    pass

    # Prioridad C: archivo de procesamiento en disco (*_proc.csv)
    if (val_mag is None or val_rms is None) and proc_rows and len(proc_rows) >= 2:
        fila_disco = proc_rows[-1]
        if len(fila_disco) >= 7 and fila_disco[2] not in ("Inicio", "Fallido"):
            if val_mag is None:
                try:
                    val_mag = float(fila_disco[3])
                except (ValueError, TypeError, IndexError):
                    pass
            if val_rms is None:
                try:
                    val_rms = float(fila_disco[6])
                except (ValueError, TypeError, IndexError):
                    pass

    # Prioridad D: lectura directa del archivo RSA si existe
    if (val_mag is None or val_rms is None) and existe_fast:
        try:
            res_rsa = lectura_rsa(nombre_evento, self.directorio_trabajo, '')
            if res_rsa and res_rsa != 1 and len(res_rsa) > 0 and len(res_rsa[0]) > 15:
                datos_s = res_rsa[0]
                if val_rms is None:
                    try:
                        val_rms = float(datos_s[10])
                    except (ValueError, TypeError, IndexError):
                        pass
                if val_mag is None:
                    try:
                        val_mag = float(datos_s[15])
                    except (ValueError, TypeError, IndexError):
                        pass
        except Exception:
            pass

    # 4. Evaluar condiciones de inconveniente (ROJO) para eventos ya procesados
    inconvenientes = []
    if not existe_fast:
        inconvenientes.append("No encuentra archivos FAST (.rsa)")
    if val_mag is None or val_mag <= 0.0:
        inconvenientes.append("Lectura de magnitud es 0")
    if val_rms is None:
        inconvenientes.append("RMS no determinado")
    elif val_rms > 1.4:
        inconvenientes.append(f"RMS mayor a 1.4 ({val_rms:.2f})")

    if inconvenientes:
        return 'INCONVENIENTE', "Inconveniente en procesamiento: " + ", ".join(inconvenientes)

    # 5. Procesado exitoso (VERDE)
    return 'EXITOSO', f"Evento procesado exitosamente (Mag: {val_mag:.1f}, RMS: {val_rms:.2f})"


def aplicar_estilo_item_evento(self, idx, nombre_evento):
    """
    Aplica formato visual (color, peso tipográfico y tooltip) al ítem del combo de eventos:
    - EXITOSO: Verde (#009600) + Negrita + Tooltip con Mag y RMS.
    - INCONVENIENTE: Rojo (#C80000) + Negrita + Tooltip con detalles del inconveniente.
    - PENDIENTE: Negro / estilo base + Fuente normal + Tooltip de pendiente.
    """
    estado, tooltip = evaluar_estado_evento(self, nombre_evento)

    if estado == 'EXITOSO':
        self.ui.cmbx_eventos.setItemData(idx, QBrush(QColor(0, 150, 0)), Qt.ForegroundRole)
        font = QFont()
        font.setBold(True)
        self.ui.cmbx_eventos.setItemData(idx, font, Qt.FontRole)
        self.ui.cmbx_eventos.setItemData(idx, tooltip, Qt.ToolTipRole)
    elif estado == 'INCONVENIENTE':
        self.ui.cmbx_eventos.setItemData(idx, QBrush(QColor(200, 0, 0)), Qt.ForegroundRole)
        font = QFont()
        font.setBold(True)
        self.ui.cmbx_eventos.setItemData(idx, font, Qt.FontRole)
        self.ui.cmbx_eventos.setItemData(idx, tooltip, Qt.ToolTipRole)
    else:
        self.ui.cmbx_eventos.setItemData(idx, QBrush(QColor(0, 0, 0)), Qt.ForegroundRole)
        font = QFont()
        font.setBold(False)
        self.ui.cmbx_eventos.setItemData(idx, font, Qt.FontRole)
        self.ui.cmbx_eventos.setItemData(idx, tooltip, Qt.ToolTipRole)


def evento_esta_procesado(self, nombre_evento):
    """
    Determina si un evento ya ha sido procesado exitosamente.
    Preserva compatibilidad con llamadores existentes.
    """
    estado, _ = evaluar_estado_evento(self, nombre_evento)
    return estado == 'EXITOSO'


def cargar_combo_eventos(self, text):
    self.sismos_procesar = []
    self.ui.cmbx_eventos.clear()
    for i in range(0, len(self.eventos)):
        if text == 'TODOS' or self.eventos[i][2] == text:
            aux_sismo = (int(self.eventos[i][0]), self.eventos[i][1])  # aux_sismo tiene el numero de evento del csv y todo el registro
            self.sismos_procesar.append(aux_sismo)
            idx = self.ui.cmbx_eventos.count()
            self.ui.cmbx_eventos.addItem(self.eventos[i][1])
            tipo_ev = self.eventos[i][2]
            if tipo_ev == 'SISMO':
                aplicar_estilo_item_evento(self, idx, self.eventos[i][1])
            else:
                self.ui.cmbx_eventos.setItemData(idx, QBrush(QColor(0, 0, 0)), Qt.ForegroundRole)
                font = QFont()
                font.setBold(False)
                self.ui.cmbx_eventos.setItemData(idx, font, Qt.FontRole)
                self.ui.cmbx_eventos.setItemData(idx, f"Evento clasificado como {tipo_ev}", Qt.ToolTipRole)
    self.preparar_evento('')


# ---------------------------------------------------------------
# HILO DE MONITOREO DE ARCHIVO - SEGURO PARA PyQt5
# ---------------------------------------------------------------
from PyQt5.QtCore import QThread
import os


class FileMonitorThread(QThread):
    archivo_cambiado = pyqtSignal(str)

    def __init__(self, archivos_monitoreo, parent=None):
        super().__init__(parent)
        if isinstance(archivos_monitoreo, list):
            self.archivos_monitoreo = archivos_monitoreo
        else:
            self.archivos_monitoreo = [archivos_monitoreo]
        self.ultimos_mtime = {}

    def sleep_interruptible(self, segundos):
        for _ in range(int(segundos * 10)):
            if self.isInterruptionRequested():
                return True
            time.sleep(0.1)
        return False

    def run(self):
        print("HILO: monitoreando", self.archivos_monitoreo)

        while not self.isInterruptionRequested():
            for ruta in self.archivos_monitoreo:
                if not ruta:
                    continue

                if os.path.exists(ruta):
                    try:
                        mtime = os.path.getmtime(ruta)
                    except Exception:
                        continue

                    if ruta not in self.ultimos_mtime:
                        self.ultimos_mtime[ruta] = mtime
                        self.archivo_cambiado.emit(ruta)
                    elif mtime != self.ultimos_mtime[ruta]:
                        self.ultimos_mtime[ruta] = mtime
                        self.archivo_cambiado.emit(ruta)

            if self.sleep_interruptible(1):
                return



def verificar_drives_virtuales(responsable_evento):
    responsables = os.path.abspath(os.path.join(ruta_proyecto,'datos','responsables.csv'))
    responsables=lectura_archivo(responsables)
   
    for responsable in responsables:
        if responsable[0]==responsable_evento:
            lista_drives=responsable[1:]
    for drive in lista_drives:
        if os.path.isdir(drive):
            pass
        else:
            return False
    return True


# ============================
#  EN PROCESAR_EVENTO (QMainWindow o QWidget)
# ============================

class Procesar_evento(QWidget):  
    cerrado = pyqtSignal()

    def __init__(self, archivo, directorio_trabajo, responsable, horario, parent=None):
        super().__init__(parent)

        # -----------------------------
        # 1) ESTADO BÁSICO DEL OBJETO
        # -----------------------------
        self.archivo = archivo                        # Ruta o nombre AAAAMMDD_hhmmss.sis
        self.directorio_trabajo = directorio_trabajo  # Directorio ..\DIA\
        self.responsable = responsable                # Responsable global
        self.horario = horario                        # Texto "00:00 - 12:00", etc.
        self.parametros = parametros_estaciones()     # Parámetros de estaciones
        self.pagina = 0
        self.registro_tiempo = 0
        self.canales_habilitados = []
        self.numero_estaciones = 0
        self.lbl_directorio_trabajo = self.directorio_trabajo
        self.estaciones_eventos = []
        self.estaciones_eventos_total = []
        self.filtros_estaciones = []
        self.bandera_marcas = 1
        self.revision_procesamiento = False
        self.en_estaciones = False

        # Variables de procesamiento
        self.procesamiento = []          # Lista de filas del archivo *_proc.csv
        self.evento_procesar = ''        # Fila seleccionada de self.eventos
        self.indice_evento_procesar = -1
        self.eventos = []
        self.eventos_reporte = []
        self.catalogo = []
        self.evento_canales = []
        self.responsables = []
        self.resumen = []
        self.vector = []
        self.root = None
        self.archivo_estaciones = ''
        self.directorios = {}
        self.archivos_procesamiento_real = []
        self.archivos_procesamiento_virtual = []
        self.responsable_evento = ''
        self.archivo_reporte = ''
        self.trCanal = None

        # Control del mapa y redibujado diferido
        self.widget_central_activo = None

        # Control del hilo de monitoreo
        self.file_monitor = None

        # -----------------------------
        # 2) CREACIÓN DE LOS PANELES
        # -----------------------------
        layout_principal = QHBoxLayout(self)

        # PANEL IZQUIERDO: UI principal
        self.panel_izquierdo = QWidget(self)
        self.panel_izquierdo.setFixedWidth(250)
        layout_izq = QVBoxLayout(self.panel_izquierdo)
        layout_izq.setContentsMargins(0, 0, 0, 0)

        ruta_ui = os.path.abspath(os.path.join(ruta_proyecto, 'src', 'ui', 'Proceso.ui'))
        self.ui = uic.loadUi(ruta_ui)
        layout_izq.addWidget(self.ui)
        layout_principal.addWidget(self.panel_izquierdo, 0)

        # PANEL CENTRAL: para incrustar estaciones_
        self.panel_central = QWidget(self)
        self.layout_central = QVBoxLayout(self.panel_central)
        self.layout_central.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.layout_central.setContentsMargins(0, 0, 0, 0)
        self.panel_central.setVisible(False)
        layout_principal.addWidget(self.panel_central, 0)

        # PANEL DERECHO: mapa GIS embebido (oculto hasta entrar a procesamiento)
        self.panel_derecho = QWidget(self)
        layout_der = QVBoxLayout(self.panel_derecho)
        layout_der.setContentsMargins(0, 0, 0, 0)
        self.widget_mapa = widget_grafico_mpl(self)
        self.widget_mapa.setVisible(False)
        layout_der.addWidget(self.widget_mapa)
        layout_principal.addWidget(self.panel_derecho, 1)

        # Visor matplotlib "propio" (por compatibilidad con código existente)
        self.visor = Figure(figsize=(8, 4), dpi=100)
        self.canvas = FigureCanvas(self.visor)
        self.canvas.setVisible(False)

        # -----------------------------
        # 3) CONFIGURACIÓN INICIAL GUI
        # -----------------------------
        self.setLayout(layout_principal)
        self.setWindowTitle("PROCESAMIENTO")
        self.ui.Lbl_directorio.setText(self.directorio_trabajo)
        self.ui.grupo_carga.setEnabled(False)

        # Botones
        self.ui.Btn_eventos.clicked.connect(self.guardar_evento)
        self.ui.Btn_Salir.clicked.connect(self.Salir_)
        self.ui.Btn_procesar.clicked.connect(self.procesar_)
        self.ui.Btn_reportar.clicked.connect(self.reportar_)
        self.ui.Btn_acelerograma.clicked.connect(self.acelerograma_)
        self.ui.Btn_insertar.clicked.connect(self.insertar_)

        # Combos
        self.ui.Cmb_bx_tipo_evento.activated[str].connect(self.cambio_evento)
        self.ui.cmbx_t_evento.activated[str].connect(self.cargar_tipo_evento)
        self.ui.cmbx_eventos.activated[str].connect(self.preparar_evento)

        # Radio buttons y modo inicial/revisión
        d = datetime.today()
        d_qt = QDate(d.year, d.month, d.day)

        nombre_base = Path(self.archivo).stem          # AAAAMMDD_hhmmss
        cadena_fecha = nombre_base.split('_', 1)[0]    # AAAAMMDD
        anio = int(cadena_fecha[0:4])
        mes = int(cadena_fecha[4:6])
        dia = int(cadena_fecha[6:8])
        qdate_archivo = QDate(anio, mes, dia)

        if qdate_archivo == d_qt:
            self.ui.radioButton_inicial.setChecked(True)
        else:
            self.ui.radioButton_revision.setChecked(True)

        self.ui.radioButton_inicial.toggled.connect(self.seleccionar_inicial)
        self.ui.radioButton_revision.toggled.connect(self.seleccionar_revision)

        # Cargar parámetros de estaciones habilitadas
        self.canales_habilitados = []
        for i in range(0, 101):
            if self.parametros['HAB_CANAL'][i] == '1':
                self.canales_habilitados.append(i)
        self.numero_estaciones = len(self.canales_habilitados)

        # -----------------------------
        # 4) CARGA DEL DÍA Y EVENTOS
        # -----------------------------
        self.Abrir_archivo()  # Carga self.directorios, día, catálogo, etc.


    def mostrar_submensaje(self, texto, forzar=False):
        """
        Actualiza Lbl_submensajes únicamente cuando NO está activa la revisión
        del archivo PDF temporal (o cuando se fuerza desde Salir_).
        """
        if getattr(self, 'revision_procesamiento', False) and not forzar:
            return
        self.ui.Lbl_submensajes.setText(texto)

    def _obtener_responsable_virtual(self) -> str:
        """
        Retorna el responsable cuyas unidades virtuales deben utilizarse para
        lectura/escritura de archivos FAST (.sis, .fas, .rsa).
        Cuando el usuario activo de la sesión es 'RSA', utiliza las unidades
        virtuales configuradas para 'RSA' aunque el turno original pertenezca a otro operador.
        """
        if (self.responsable or "").strip() == "RSA":
            return "RSA"
        return (self.responsable_evento or self.responsable or "RSA").strip()

    def _tiene_permiso_sobre_evento_actual(self) -> bool:
        """
        Verifica si el usuario activo puede modificar/procesar el evento seleccionado.
        El usuario 'RSA' tiene permiso sobre todos los turnos; un operador individual
        solo sobre sus propios turnos o turnos aún asignados a 'RSA'/vacíos.
        """
        resp_act = (self.responsable or "").strip()
        if resp_act == "RSA":
            return True
        resp_ev = (self.responsable_evento or "").strip()
        return resp_ev in ("", "RSA", resp_act)

    def activar_hilo(self):
        """
        Activa el hilo de monitoreo del archivo .rsa del evento.
        Si ss >= 50, monitorea dos posibilidades:
            - minuto +1
            - minuto real
        """
        if self.evento_procesar[2] != "SISMO":
            self.mostrar_submensaje("Evento no es SISMO — monitoreo no requerido.")
            return

        resp_virtual = self._obtener_responsable_virtual()
        if not verificar_drives_virtuales(resp_virtual):
            self.mostrar_submensaje("El Virtual no está conectado — monitoreo deshabilitado.")
            return

        try:
            archivo = self.evento_procesar[1]
            base_evento = Path(archivo).stem.replace('_', '')

            if len(base_evento) == 12:
                ss_evento = int(base_evento[10:12])
            else:
                ss_evento = int(base_evento[12:14])

            if ss_evento >= 50:
                lista_fast_siguiente = archivos_fast(
                    archivo,
                    self.directorio_trabajo,
                    resp_virtual,
                    modo_minuto_fast='siguiente'
                )
                lista_fast_real = archivos_fast(
                    archivo,
                    self.directorio_trabajo,
                    resp_virtual,
                    modo_minuto_fast='real'
                )
                archivos_monitoreo = [lista_fast_siguiente[2], lista_fast_real[2]]
            else:
                lista_fast_real = archivos_fast(
                    archivo,
                    self.directorio_trabajo,
                    resp_virtual,
                    modo_minuto_fast='real'
                )
                archivos_monitoreo = [lista_fast_real[2]]

        except Exception as e:
            print("Error al obtener archivos FAST:", e)
            self.mostrar_submensaje("Error al obtener archivos FAST")
            return

        self.mostrar_submensaje(
            "Monitorizando archivo(s) RSA…\n" + "\n".join(archivos_monitoreo)
        )

        if hasattr(self, "file_monitor") and self.file_monitor is not None:
            try:
                self.file_monitor.requestInterruption()
                self.file_monitor.wait()
            except Exception:
                pass

        self.archivo_rsa_actual = ''
        self.file_monitor = FileMonitorThread(archivos_monitoreo, parent=self)
        self.file_monitor.archivo_cambiado.connect(self.recalcular_procesamiento)
        self.file_monitor.start()





    def _estaciones_piden_actualizar_mapa(self):
        """
        estaciones_ solicita actualización de ubicación.
        Redibuja usando el procesamiento actual.
        """
        self.actualizar_mapa(self.procesamiento)



    def _estaciones_devuelven_cambios(self, habilitados, filtros_nuevos):
        """
        estaciones_ envía estaciones habilitadas y nuevos filtros.

        Aquí solo actualizamos estructuras internas.
        El guardado en archivos se hace cuando el usuario guarda evento.
        """
        try:
            # 1. Actualizar lista de estaciones habilitadas
            self.estaciones_eventos = habilitados[:]  # lista de índices reales

            # 2. Actualizar los filtros modificados
            self.filtros_estaciones = filtros_nuevos[:]  # lista "OOffss"

            # 3. Actualizar las estructuras del evento en memoria
            idx_evento = self.indice_evento_procesar

            for i, canal_real in enumerate(self.estaciones_eventos_total):
                aux_cadena = self.eventos[idx_evento][canal_real + 3]

                # Valor habilitado
                hab = '1' if canal_real in habilitados else '0'

                # filtro concatenado
                filtro = filtros_nuevos[i]

                # nueva cadena final
                nueva = aux_cadena[:5] + hab + filtro

                self.eventos[idx_evento][canal_real + 3] = nueva

            # 4. Señal discreta en pantalla
            self.mostrar_submensaje("Cambios almacenados (no guardados en disco aún).")
            escritura_archivo(self.directorios['archivo_csv'], self.eventos) 
        except Exception as e:
            print("Error en _estaciones_devuelven_cambios:", e)






    def _estaciones_cerraron(self):
        """
        estaciones_ se cerró correctamente.
        """
        try:
            if hasattr(self, "file_monitor") and self.file_monitor is not None and self.file_monitor.isRunning():
                self.file_monitor.requestInterruption()
                self.file_monitor.wait()
                print("Hilo detenido.")
        except Exception as e:
            print("Error deteniendo hilo:", e)

        self.file_monitor = None

        try:
            if hasattr(self, "timer_verificar") and self.timer_verificar.isActive():
                self.timer_verificar.stop()
                print("Timer verificar detenido.")
        except Exception as e:
            print("Error deteniendo timer_verificar:", e)

        try:
            escritura_archivo(self.directorios["archivo_procesamiento"], self.procesamiento)
            print("Procesamiento final guardado.")
        except Exception as e:
            print("Error guardando procesamiento final:", e)

        if self.evento_procesar and self.evento_procesar[2] == 'SISMO':
            try:
                archivo = self.evento_procesar[1]
                rutas_real_base = archivos_fast(
                    archivo,
                    self.directorio_trabajo,
                    '',
                    modo_minuto_fast='real'
                )

                if self.archivo_rsa_actual:
                    nombre_rsa = Path(self.archivo_rsa_actual).stem.rstrip('abc')
                    mm_fast = nombre_rsa[0:2]
                    dd_fast = nombre_rsa[2:4]
                    hh_fast = nombre_rsa[4:6]
                    minu_fast = nombre_rsa[6:8]

                    dir_fast_real = os.path.dirname(rutas_real_base[2])

                    rutas_real_base[2] = os.path.join(dir_fast_real, f"{mm_fast}{dd_fast}{hh_fast}{minu_fast}.rsa")
                    rutas_real_base[3] = os.path.join(dir_fast_real, f"Phase{dd_fast}{hh_fast[0]}.{hh_fast[1]}{minu_fast}")

                    base_lp = f"{mm_fast}{dd_fast}{hh_fast}.{minu_fast}"
                    rutas_real_base[4] = os.path.join(dir_fast_real, base_lp + "L")
                    rutas_real_base[5] = os.path.join(dir_fast_real, base_lp + "P")
                    rutas_real_base[6] = os.path.join(dir_fast_real, base_lp + "S")

                    if hasattr(self, 'archivos_procesamiento_virtual') and self.archivos_procesamiento_virtual and len(self.archivos_procesamiento_virtual) >= 7:
                        dir_fast_virtual = os.path.dirname(self.archivos_procesamiento_virtual[2])
                        self.archivos_procesamiento_virtual[2] = self.archivo_rsa_actual
                        self.archivos_procesamiento_virtual[3] = os.path.join(dir_fast_virtual, f"Phase{dd_fast}{hh_fast[0]}.{hh_fast[1]}{minu_fast}")
                        self.archivos_procesamiento_virtual[4] = os.path.join(dir_fast_virtual, base_lp + "L")
                        self.archivos_procesamiento_virtual[5] = os.path.join(dir_fast_virtual, base_lp + "P")
                        self.archivos_procesamiento_virtual[6] = os.path.join(dir_fast_virtual, base_lp + "S")

                self.archivos_procesamiento_real = verificar_coincidencias(
                    self.eventos,
                    archivo,
                    rutas_real_base
                )

                print(self.archivos_procesamiento_virtual, self.archivos_procesamiento_real)

                copiar_archivos(
                    self.archivos_procesamiento_virtual,
                    self.archivos_procesamiento_real
                )
                print("Copiado Virtual → Real.")

            except Exception as e:
                print("Error copiando Virtual → Real:", e)

            try:
                for ruta in self.archivos_procesamiento_virtual:
                    if os.path.exists(ruta):
                        os.remove(ruta)
                print("Archivos del Virtual eliminados.")
            except Exception as e:
                print("Error limpiando Virtual:", e)

        self.en_estaciones = False

        try:
            self.limpiar_panel_central()
        except Exception as e:
            print("Error limpiando panel central:", e)

        try:
            evento_sel = self.ui.cmbx_eventos.currentText()
            self.sincronizar_archivos_dia_y_periodos()

            idx_actual = self.ui.cmbx_eventos.currentIndex()
            if idx_actual >= 0 and self.evento_procesar:
                aplicar_estilo_item_evento(self, idx_actual, self.evento_procesar[1])
            if evento_sel:
                self.ui.cmbx_eventos.setCurrentText(evento_sel)
                self.preparar_evento(evento_sel)
            print("Evento recargado.")
        except Exception as e:
            print("Error recargando evento:", e)

        self.bandera_procesamiento = 0
        self.ui.grupo_carga.setEnabled(True)
        print("Cierre finalizado.")








    def _estaciones_cerraron__(self):
        """
        estaciones_ se cerró correctamente.
        Aquí ya NO se verifica si los archivos están en uso, porque
        esa validación se hace en closeEvent() de estaciones_.
        """

        # 1) Detener hilo
        try:
            if hasattr(self, "file_monitor") and self.file_monitor is not None and self.file_monitor.isRunning():
                self.file_monitor.requestInterruption()
                self.file_monitor.wait()
                print("Hilo detenido.")
        except Exception as e:
            print("Error deteniendo hilo:", e)

        self.file_monitor = None

        # 2) Detener timer de verificación
        try:
            if hasattr(self, "timer_verificar") and self.timer_verificar.isActive():
                self.timer_verificar.stop()
                print("Timer verificar detenido.")
        except Exception as e:
            print("Error deteniendo timer_verificar:", e)

        # 3) Guardar procesamiento final
        try:
            escritura_archivo(self.directorios["archivo_procesamiento"], self.procesamiento)
            print("Procesamiento final guardado.")
        except Exception as e:
            print("Error guardando procesamiento final:", e)

        # 4) Copiar y borrar archivos del Virtual (ya verificado antes)
        if self.evento_procesar and self.evento_procesar[2] == 'SISMO':
            
            try:
                copiar_archivos(
                    self.archivos_procesamiento_virtual,
                    self.archivos_procesamiento_real
                )
                print("Copiado Virtual → Real.")
                print(self.archivos_procesamiento_virtual,
                self.archivos_procesamiento_real)
            except Exception as e:
                print("Error copiando Virtual → Real:", e)

            try:
                for ruta in self.archivos_procesamiento_virtual:
                    if os.path.exists(ruta):
                        os.remove(ruta)
                print("Archivos del Virtual eliminados.")
            except Exception as e:
                print("Error limpiando Virtual:", e)

        # 5) Estado interno y limpiar panel
        self.en_estaciones = False
        try:
            self.limpiar_panel_central()
        except Exception as e:
            print("Error limpiando panel central:", e)

        # 6) Recargar evento
        try:
            evento_sel = self.ui.cmbx_eventos.currentText()
            self.sincronizar_archivos_dia_y_periodos()

            idx_actual = self.ui.cmbx_eventos.currentIndex()
            if idx_actual >= 0 and self.evento_procesar:
                aplicar_estilo_item_evento(self, idx_actual, self.evento_procesar[1])
            if evento_sel:
                self.ui.cmbx_eventos.setCurrentText(evento_sel)
                self.preparar_evento(evento_sel)
            print("Evento recargado.")
        except Exception as e:
            print("Error recargando evento:", e)

        # 7) Rehabilitar controles
        self.bandera_procesamiento = 0
        self.ui.grupo_carga.setEnabled(True)
        print("Cierre finalizado.")

    def limpiar_panel_central(self):
        """
        Elimina cualquier widget incrustado en el panel central y oculta los visores
        del panel derecho mientras no se esté dentro de procesamiento.
        """
        if self.widget_central_activo is not None:
            self.widget_central_activo.setParent(None)
            self.widget_central_activo.deleteLater()
            self.widget_central_activo = None
        self.panel_central.setVisible(False)
        if hasattr(self, 'canvas') and self.canvas is not None:
            self.canvas.setVisible(False)
        if hasattr(self, 'widget_mapa') and self.widget_mapa is not None:
            self.widget_mapa.setVisible(False)

    def incrustar_estaciones(self):
        """
        Incrusta estaciones_ en el panel central y conecta sus señales.
        """
        from PyQt5.QtWidgets import QSizePolicy
        self.ui.grupo_carga.setEnabled(False)
        # limpiar panel central
        self.limpiar_panel_central()
        self.pagina = 0
        self.panel_central.setVisible(True)
        if self.panel_derecho.layout().indexOf(self.widget_mapa) == -1:
            self.panel_derecho.layout().addWidget(self.widget_mapa)
        self.widget_mapa.setVisible(True)

        # crear instancia
        self.widget_central_activo = estaciones_(
            self.estaciones_eventos,
            self.filtros_estaciones,
            self._obtener_responsable_virtual(),
            parent=self
            )

        # conectar señales de estaciones_
        self.widget_central_activo.senal_actualizar_mapa.connect(
            self._estaciones_piden_actualizar_mapa
            )
        self.widget_central_activo.senal_cambios_estaciones.connect(
            self._estaciones_devuelven_cambios
            )
        self.widget_central_activo.senal_cerrar.connect(
            self._estaciones_cerraron
            )
        self.widget_central_activo.senal_cambio_vista.connect(
            self.invertir_mapa_seniales
            )


        # incrustar widget
        self.layout_central.addWidget(self.widget_central_activo)
        self.widget_central_activo.setSizePolicy(
            QSizePolicy.Fixed,
            QSizePolicy.Fixed
            )

        # En este punto NO se actualiza el mapa,
        # estaciones_ lo pedirá vía señal.



    def invertir_mapa_seniales(self, modo):
        # Limpia el panel derecho
        for i in reversed(range(self.panel_derecho.layout().count())):
            w = self.panel_derecho.layout().itemAt(i).widget()
            if w:
                w.setVisible(False)
                w.setParent(None)

        if modo == "mapa":
            # Insertar nuevamente el widget_mapa
            self.panel_derecho.layout().addWidget(self.widget_mapa)
            self.widget_mapa.setVisible(True)
            self.actualizar_mapa(self.procesamiento)


        else:  # "senales"
            self.pagina = 0
            self.panel_derecho.layout().addWidget(self.canvas)
            self.canvas.setVisible(True)
            if self.widget_central_activo is not None:
                self.widget_central_activo.Graficar_()



    # ==========================================================
    #  BLOQUE: MANEJO DE VIRTUAL + HILO MONITOR
    # ==========================================================

    def iniciar_espera_archivos_virtual(self):
        """
        Espera NO BLOQUEANTE hasta que existan los archivos del Virtual.
        Cuando aparecen:
            - se detiene el timer de verificación
            - inicia el hilo de monitoreo sobre el .fas (virtual)
        """

        # Archivo base del evento
        archivo = self.evento_procesar[1]
        self.mostrar_submensaje("Esperando archivos del Virtual…")

        # Crear un solo QTimer controlable
        self.timer_verificar = QTimer(self)
        self.timer_verificar.setInterval(800)

        def verificar():
            resp_virtual = self._obtener_responsable_virtual()
            # 1) Verificar que existan los drives del virtual
            if not verificar_drives_virtuales(resp_virtual):
                return  # seguir verificando en el próximo ciclo

            # 2) Obtener rutas Virtual (archivos FAST)
            archivos_v = archivos_fast(
                archivo,
                self.directorio_trabajo,
                resp_virtual
            )
            archivo_monitoreo = archivos_v[2]  # Ruta del archivo .fas

            # 3) Esperar a que exista el archivo .fas
            if not os.path.exists(archivo_monitoreo):
                return  # seguir verificando

            # 4) Archivos listos → Detener timer y arrancar hilo
            self.timer_verificar.stop()
            self.mostrar_submensaje(
                "Archivos del Virtual encontrados, iniciando monitoreo…"
            )
            self.iniciar_monitor_virtual()

        # Conectar el método verificar al timer
        self.timer_verificar.timeout.connect(verificar)

        # Iniciar verificación cíclica
        self.timer_verificar.start()



    def iniciar_monitor_virtual(self):
        """
        Inicia el hilo de monitoreo del archivo .rsa en el Virtual.
        """
        if not self.evento_procesar:
            return

        archivo = self.evento_procesar[1]
        archivos_v = archivos_fast(
            archivo,
            self.directorio_trabajo,
            self._obtener_responsable_virtual()
        )
        archivo_monitoreo = archivos_v[2]   # .rsa

        if not self.directorios:
            self.directorios = obtener_directorios(self.archivo)

        self.detener_monitor_virtual()

        self.file_monitor = FileMonitorThread(archivo_monitoreo, parent=self)
        self.file_monitor.archivo_cambiado.connect(self.recalcular_procesamiento)
        self.file_monitor.start()



    def detener_monitor_virtual(self):
        """
        Detiene el hilo de monitoreo, si está activo.
        """
        if self.file_monitor is not None and self.file_monitor.isRunning():
            self.file_monitor.requestInterruption()
            self.file_monitor.wait()
            self.file_monitor = None



    def intento_es_diferente(self, procesamiento_anterior, procesamiento_nuevo):
        """
        Compara la última fila del procesamiento nuevo con la última fila
        del procesamiento anterior, ignorando el índice y la fecha de grabación.
        """

        if not procesamiento_anterior or len(procesamiento_anterior) <= 1:
            return True

        if not procesamiento_nuevo or len(procesamiento_nuevo) <= 1:
            return False

        ultima_fila_anterior = procesamiento_anterior[-1]
        ultima_fila_nueva = procesamiento_nuevo[-1]

        firma_anterior = ultima_fila_anterior[2:]
        firma_nueva = ultima_fila_nueva[2:]

        return firma_anterior != firma_nueva



    def recalcular_procesamiento(self, ruta_cambiada=None):
        """
        Llamado cuando el hilo detecta un cambio en el archivo .rsa.
        Aquí se recalcula el procesamiento y solo se graba si el intento
        nuevo es diferente del último ya almacenado.
        """

# Nota importante:
# Este método recibe `ruta_cambiada` porque la señal del hilo
# `archivo_cambiado.emit(ruta)` envía automáticamente la ruta del .rsa
# que cambió. PyQt pasa ese valor a este método por la conexión:
#     self.file_monitor.archivo_cambiado.connect(self.recalcular_procesamiento)
#
# Aunque `ruta_cambiada` no se usa para decidir qué archivo leer,
# sí debe estar en la firma del método para recibir correctamente
# el argumento enviado por la señal.
#
# La lógica real del procesamiento NO se basa directamente en esa ruta.
# En cambio, vuelve a resolver el archivo correcto mediante:
#     guardar_intento(...) -> lectura_rsa(...)
#
# En resumen:
# - el hilo detecta y avisa qué archivo cambió;
# - este método recibe ese aviso;
# - pero el procesamiento real se recalcula desde el evento actual.

        try:
            if ruta_cambiada:
                self.archivo_rsa_actual = ruta_cambiada
                print("RSA detectado por el hilo:", self.archivo_rsa_actual)

            procesamiento_base = [fila[:] for fila in self.procesamiento]

            nuevo_proc = guardar_intento(
                self.evento_procesar[1],
                self.directorio_trabajo,
                self._obtener_responsable_virtual(),
                [fila[:] for fila in self.procesamiento],
                self.archivo_rsa_actual
            )

            if not self.intento_es_diferente(procesamiento_base, nuevo_proc):
                self.mostrar_submensaje("RSA sin cambios útiles. No se agregó nuevo intento.")
                print("GUI: intento repetido detectado, no se guarda.")
                return

            escritura_archivo(self.directorios["archivo_procesamiento"], nuevo_proc)
            self.procesamiento = nuevo_proc
            self.actualizar_mapa(nuevo_proc)
            idx_actual = self.ui.cmbx_eventos.currentIndex()
            if idx_actual >= 0 and self.evento_procesar:
                aplicar_estilo_item_evento(self, idx_actual, self.evento_procesar[1])
                self.actualizar_estilo_combo_actual()

            self.mostrar_submensaje("Procesamiento actualizado desde RSA.")
            print("GUI: procesamiento actualizado y mapa redibujado.")

        except Exception as e:
            print("Error en recalcular_procesamiento:", e)
            self.mostrar_submensaje("Error al actualizar procesamiento.")




    def seleccionar_inicial(self, estado):
        """
        Modo inicial seleccionado.
        (De momento no altera lógica interna, pero se deja para extensiones).
        """
        if estado:
            # Aquí podrías activar banderas específicas de modo inicial
            pass

    def seleccionar_revision(self, estado):
        """
        Modo revisión seleccionado.
        """
        if estado:
            # Aquí podrías activar banderas específicas de modo revisión
            pass

    def actualizar_mapa(self, procesamiento):
        """
        Redibuja inmediatamente usando los datos del procesamiento.
        """
        try:
            if not procesamiento:
                self.widget_mapa.plot([], self.directorios['archivo_estaciones'])
                self.mostrar_submensaje("Mapa listo — sin intento aún.")
                return

            bandera = self.widget_mapa.plot(
                procesamiento,
                self.directorios['archivo_estaciones']
            )

            # Manejo de textos
            if isinstance(bandera, (list, tuple)):
                if bandera[0]:
                    self.mostrar_submensaje("Procesar con 6 fases mínimo.")
                elif bandera[1]:
                    self.mostrar_submensaje("Procesar con fases claras.")
                else:
                    self.mostrar_submensaje("No Procesar.")

        except Exception as e:
            print("Error al redibujar mapa:", e)
            self.mostrar_submensaje("Error al dibujar mapa.")

    def limpiar_estado(self):
        """
        Limpia figuras, visores y referencias básicas antes de cerrar.
        """
        try:
            self.detener_monitor_virtual()

            if hasattr(self, 'canvas') and self.canvas is not None:
                self.canvas.deleteLater()
                self.canvas = None
            if hasattr(self, 'visor') and self.visor is not None:
                self.visor.clf()
                self.visor = None

            if hasattr(self, 'lista_eventos'):
                self.lista_eventos.clear()
        except Exception as e:
            print(f"Error en limpieza de Procesar_evento: {e}")

    def cambiar_coeficientes_(self):
        """
        Abre la ventana de cambio de coeficientes de filtro.
        """
        self.cambio_coeficientes_filtro = Cambio_Coeficientes_Filtro(self.canales_habilitados)

    # ==========================================================
    #  BLOQUE: CARGA DEL DÍA Y EVENTOS
    # ==========================================================

    def Abrir_archivo(self):
        """
        Carga el día, inicializa combos y estructuras básicas.
        """
        # Combos de tipos de evento
        self.ui.Cmb_bx_tipo_evento.clear()
        lista_filtros = ["Ruido", "FF", "FC", "TELESISMO", "SISMO",
                         "INDEFINIDO", "Evento_local", "CONTROL", "REVISION", "TODOS"]
        self.ui.Cmb_bx_tipo_evento.addItems(lista_filtros)
        self.ui.cmbx_t_evento.addItems(lista_filtros)
        self.ui.cmbx_t_evento.setCurrentText('SISMO')

        # Cargar directorios del día
        self.directorios = obtener_directorios(self.archivo)
        self.ui.grupo_carga.setEnabled(True)

        # Cargar día completo
        (self.eventos_reporte,
         self.catalogo,
         self.eventos,
         self.vector,
         self.evento_canales,
         self.root,
         self.responsables,
         self.resumen) = cargar_dia(self.directorios)

        # Cargar lista de eventos de tipo "SISMO" en el combo
        cargar_combo_eventos(self, 'SISMO')

        self.archivo_estaciones = self.directorios['archivo_estaciones']
        self.ck_box_hab_canal = {}
        self.lbl_nombre = {}
        self.lbl_codigo = {}
        self.ck_box_hab_canal = [0 for _ in range(16)]

    def guardar_evento(self):
        """
        Guarda en disco los CSV principales del día.
        """
        escritura_archivo(self.directorios['archivo_csv'], self.eventos)
        escritura_archivo(self.directorios['archivo_reporte'], self.eventos_reporte)
        escritura_archivo(self.directorios['archivo_catalogo'], self.catalogo)

    def sincronizar_archivos_dia_y_periodos(self):
        """
        Recarga la información consolidada del día mediante `cargar_dia()`, escribe
        todos los archivos oficiales del día (`_rep.csv`, `_cat.csv`, `.csv`,
        `_resp.csv`, `_res.csv`, `.xml`) mediante `Guardar_dia()` y propaga en cascada
        la actualización hacia la Semana ISO, el Mes y el Año correspondientes en
        `Ecuador` (únicamente si sus archivos `_cat.csv` ya fueron emitidos, sin
        regenerar PDFs).
        """
        (self.eventos_reporte,
         self.catalogo,
         self.eventos,
         self.vector,
         self.evento_canales,
         self.root,
         self.responsables,
         self.resumen) = cargar_dia(self.directorios)
        try:
            self.catalogo, self.eventos_reporte, _ = sincronizar_otras_redes_dia(
                self.directorios,
                self.catalogo,
                self.eventos_reporte,
                self.eventos,
            )
        except Exception:
            pass
        Guardar_dia(
            self.eventos_reporte,
            self.catalogo,
            self.eventos,
            self.root,
            self.responsables,
            self.resumen,
            self.directorios,
        )
        actualizar_periodos_emitidos_desde_fecha(
            self.directorios.get('archivo_csv', self.archivo),
            self.directorio_trabajo,
        )

    def actualizar_estilo_combo_actual(self):
        """Actualiza el color del texto del QComboBox según el estado del evento seleccionado"""
        idx_actual = self.ui.cmbx_eventos.currentIndex()
        if idx_actual >= 0:
            color_item = self.ui.cmbx_eventos.itemData(idx_actual, Qt.ForegroundRole)
            if color_item and isinstance(color_item, QBrush):
                color_rgb = color_item.color()
                if color_rgb == QColor(200, 0, 0):
                    self.ui.cmbx_eventos.setStyleSheet("QComboBox { color: #C80000; font-weight: bold; }")
                    return
                elif color_rgb == QColor(0, 150, 0):
                    self.ui.cmbx_eventos.setStyleSheet("QComboBox { color: #009600; font-weight: bold; }")
                    return
            self.ui.cmbx_eventos.setStyleSheet("")

    def preparar_evento(self, text):
        """
        Escoge el evento actual desde el combo y prepara estructuras internas
        de estaciones, filtros y archivo de procesamiento.
        """
        self.evento_procesar = ''
        for i, evento in enumerate(self.eventos):
            if evento[1] == self.ui.cmbx_eventos.currentText():
                self.indice_evento_procesar = i
                self.evento_procesar = evento
                self.parametro = evento[0] + "  " + evento[1] + "  " + evento[2]
                break
        if not self.evento_procesar:
            return

        aux = int(self.evento_procesar[1][-10:-4])
        if aux < 120000:
            indice_hora = 0
        elif aux < 180000:
            indice_hora = 1
        else:
            indice_hora = 2

        horario = ["00:00 - 12:00", "12:00 - 18:00", "18:00 - 24:00"]
        self.responsable_evento = self.responsables[indice_hora+1][0]
        self.ui.Cmb_bx_tipo_evento.setCurrentText(self.evento_procesar[2])
        self.ui.txt_responsables.setText(self.responsable_evento)
        self.ui.txt_horario.setText(horario[indice_hora])

        # Estaciones y filtros asociados al evento
        self.estaciones_eventos = []
        self.filtros_estaciones = []
        for i in range(3, len(self.evento_procesar)):
            if self.evento_procesar[i] != '-':
                self.filtros_estaciones.append(self.evento_procesar[i][-6:])
                self.estaciones_eventos.append(i - 3)
        (self.indice,
         self.indice_local,
         self.indice_catalogo,
         self.archivo_escogido,
         self.evento_reporte_escogido,
         self.canales,
         self.trCanal,
         self.archivo_reporte,
         self.parametros['HAB_GRAFICO'],
         self.estaciones_eventos) = cargar_evento(
            self.parametro,
            self.eventos_reporte,
            self.catalogo,
            self.eventos,
            self.evento_canales,
            self.directorio_trabajo,
            self.directorios['Directorio_reportes']
        )
        self.estaciones_eventos_total = self.estaciones_eventos

        # Cada vez que se prepara evento, limpiar procesamiento actual
        self.procesamiento = []
        if self.en_estaciones:
            self.actualizar_mapa(self.procesamiento)

        es_no_reportable = self.evento_procesar[2] in ('Ruido', 'CONTROL')
        tiene_permiso = self._tiene_permiso_sobre_evento_actual()
        if hasattr(self.ui, 'Btn_procesar'):
            self.ui.Btn_procesar.setEnabled(tiene_permiso)
        if hasattr(self.ui, 'Btn_eventos'):
            self.ui.Btn_eventos.setEnabled(tiene_permiso)
        if hasattr(self.ui, 'Cmb_bx_tipo_evento'):
            self.ui.Cmb_bx_tipo_evento.setEnabled(tiene_permiso)
        if hasattr(self.ui, 'Btn_reportar'):
            self.ui.Btn_reportar.setEnabled((not es_no_reportable) and tiene_permiso)
        if hasattr(self.ui, 'Btn_acelerograma'):
            self.ui.Btn_acelerograma.setEnabled((not es_no_reportable) and tiene_permiso)
        if hasattr(self.ui, 'Btn_insertar'):
            self.ui.Btn_insertar.setEnabled((not es_no_reportable) and tiene_permiso)

        if not tiene_permiso:
            self.mostrar_submensaje(
                f"Turno de «{self.responsable_evento}» — ingrese como «RSA» para modificar."
            )

        self.actualizar_estilo_combo_actual()

    def asegurar_extraccion_sis(self, nombre_evento):
        """
        Garantiza que un evento reclasificado a SISMO cuente con su archivo binario .sis
        en la carpeta dia/. Si no existe, lo extrae utilizando los datos de archivo_auxiliar
        y los registros continuos .mseed.
        """
        stem = Path(nombre_evento).stem
        dir_dia = self.directorios.get('Directorio_dia', '')
        archivo_sis = os.path.join(dir_dia, f"{stem}.sis")

        if os.path.exists(archivo_sis):
            print(f"Archivo .sis ya existe para {nombre_evento}: {archivo_sis}")
            return True

        print(f"Archivo .sis no existe para {nombre_evento}. Iniciando extracción automática...")

        # 1. Localizar el evento en archivo_auxiliar (AAMMDD_aux.csv)
        arch_aux = self.directorios.get('archivo_auxiliar', '')
        filas_aux = lectura_archivo(arch_aux) if arch_aux and os.path.exists(arch_aux) else []
        fila_aux = None
        idx_aux = -1

        for i, fila in enumerate(filas_aux):
            if fila and len(fila) > 1 and Path(fila[1]).stem == stem:
                fila_aux = fila
                idx_aux = i
                break

        if fila_aux:
            fila_aux[2] = 'SISMO'
            filas_aux[idx_aux] = fila_aux
            try:
                escritura_archivo(arch_aux, filas_aux)
            except Exception as e:
                print(f"Aviso actualizando archivo_auxiliar: {e}")
        else:
            # Si no estaba en auxiliar, intentar construir fila básica desde la marca de tiempo
            try:
                base_limpia = stem.replace('_', '')
                if len(base_limpia) == 12:
                    hh, mm, ss = int(base_limpia[6:8]), int(base_limpia[8:10]), int(base_limpia[10:12])
                elif len(base_limpia) == 14:
                    hh, mm, ss = int(base_limpia[8:10]), int(base_limpia[10:12]), int(base_limpia[12:14])
                else:
                    hh, mm, ss = 12, 0, 0

                segundos_marca = hh * 3600 + mm * 60 + ss
                t_ini_calc = max(0, segundos_marca - 20)
                t_fin_calc = segundos_marca + 100
                fila_aux = [
                    '0',
                    f"{stem}.sis",
                    'SISMO',
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    str(t_ini_calc),
                    str(t_fin_calc),
                    self.responsable_evento if hasattr(self, 'responsable_evento') else '',
                    "",
                    str(segundos_marca)
                ]
                filas_aux.append(fila_aux)
                if arch_aux:
                    escritura_archivo(arch_aux, filas_aux)
            except Exception as e:
                print(f"No se pudo construir fila auxiliar para {nombre_evento}: {e}")
                return False

        # 2. Ejecutar extracción mediante rsa_utilidades.extraccion
        try:
            from rsa_utilidades import extraccion
            evento_extraido = extraccion(fila_aux, [], self.archivo, False)

            if os.path.exists(archivo_sis):
                print(f"Extracción exitosa. Archivo .sis generado en: {archivo_sis}")
                if evento_extraido and len(evento_extraido) > 3:
                    for idx_ev, ev in enumerate(self.eventos):
                        if Path(ev[1]).stem == stem:
                            self.eventos[idx_ev] = evento_extraido
                            break
                    escritura_archivo(self.directorios['archivo_csv'], self.eventos)

                QMessageBox.information(
                    self.window(),
                    "Extracción Exitosa",
                    f"Se ha extraído exitosamente el archivo .sis para el evento:\n{stem}.sis\n\nEl evento ya está listo para ser procesado."
                )
                return True
            else:
                QMessageBox.warning(
                    self.window(),
                    "Aviso de Extracción",
                    f"No se pudo generar el archivo .sis para:\n{stem}.sis\n\nVerifique que los registros continuos .mseed del día estén disponibles."
                )
                return False
        except Exception as e:
            print(f"Error ejecutando extraccion para {nombre_evento}: {e}")
            QMessageBox.warning(
                self.window(),
                "Error de Extracción",
                f"Ocurrió un error al extraer el archivo .sis:\n{e}"
            )
            return False

    def cambio_evento(self, text):
        """
        Cambia el tipo de evento del registro actual.
        Si se reclasifica a SISMO, garantiza la extracción del archivo .sis.
        """
        message_box = QMessageBox(
            QMessageBox.Question,
            "¡Importante!",
            "  Va a cambiar el tipo evento\n",
            QMessageBox.Yes | QMessageBox.No,
            self.window()
        )
        result = message_box.exec_()
        if result == QMessageBox.Yes:
            nuevo_tipo = self.ui.Cmb_bx_tipo_evento.currentText()
            evento_modificado = None
            for i, evento in enumerate(self.eventos):
                if self.evento_procesar and self.evento_procesar[1] == evento[1]:
                    self.eventos[i][2] = nuevo_tipo
                    evento_modificado = self.eventos[i]
                    break

            # Si se cambia a SISMO, verificar y extraer .sis si no existe en disco
            if nuevo_tipo == 'SISMO' and evento_modificado:
                self.asegurar_extraccion_sis(evento_modificado[1])

            escritura_archivo(self.directorios['archivo_csv'], self.eventos)
            self.sincronizar_archivos_dia_y_periodos()

            # Refrescar la lista de eventos para reflejar el nuevo estado visual
            cargar_combo_eventos(self, self.ui.cmbx_t_evento.currentText())
            if evento_modificado:
                self.ui.cmbx_eventos.setCurrentText(evento_modificado[1])
                self.preparar_evento(evento_modificado[1])

    def cargar_tipo_evento(self, text):
        """
        Carga en el combo de eventos solo los de un cierto tipo.
        """
        cargar_combo_eventos(self, text)

    # ==========================================================
    #  BLOQUE: PROCESAMIENTO DEL EVENTO
    # ==========================================================
    def procesar_(self, text):
        """
        Prepara archivos de procesamiento y abre la ventana de estaciones.
        Maneja la copia de archivos virtual/real solo cuando es SISMO.
        """

        if not self.evento_procesar:
            return

        if not self._tiene_permiso_sobre_evento_actual():
            QMessageBox.warning(
                self.window(),
                "Acceso Restringido por Responsable",
                f"Este evento pertenece al turno asignado a «{self.responsable_evento}».\n\n"
                f"Para procesar o modificar eventos de otros responsables, debe ingresar con el usuario «RSA».",
            )
            return

        archivo = self.evento_procesar[1]
        resp_virtual = self._obtener_responsable_virtual()

        # Construcción ruta base del evento
        self.archivo = os.path.join(
            self.directorios["Directorio_trabajo"],
            archivo[:8] + archivo[9:15]
        )

        # Cargar estructura de directorios del día
        self.directorios = obtener_directorios(self.archivo)

        # ==============================================================
        # (1) Cargar archivo de procesamiento EXISTENTE (si lo hay)
        # ==============================================================


        # Asegurar que el directorio de procesamiento existe
        try:
            Path(self.directorios['Directorio_procesamiento']).mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

        if os.path.exists(self.directorios["archivo_procesamiento"]):
            # Cargar procesamiento histórico
            print("Evento procesado")
            self.procesamiento = lectura_archivo(self.directorios["archivo_procesamiento"])
            self.procesamiento = guardar_intento(
                self.evento_procesar[1],
                self.directorio_trabajo,
                resp_virtual,
                self.procesamiento
                )
            
        else:
            # Crear procesamiento inicial
            print("Evento nuevo")
            self.procesamiento = [
                [' ', "Fecha_Hora", "Prof.(km)", "Magn.", "Lat.", "Long.", "rms"]
            ]
            ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.procesamiento.append(['0', ahora, "Inicio", " ", " ", " ", " "])

            # Guardar archivo inicial
            escritura_archivo(self.directorios["archivo_procesamiento"], self.procesamiento)
        # ==============================================================
        # (2) MOSTRAR Y ACTUALIZAR MAPA INMEDIATAMENTE (ANTES DE ACTIVAR HILO)
        # ==============================================================
        self.en_estaciones = True
        self.invertir_mapa_seniales("mapa")


        # ==============================================================
        # (3) Manejo Virtual SOLO si es SISMO
        # ==============================================================

        if self.evento_procesar[2] == 'SISMO':

            # Verificar conexión del Virtual
            self.bandera_virtual = verificar_drives_virtuales(resp_virtual)

            if not self.bandera_virtual:
                msg = QMessageBox(
                    QMessageBox.Information,
                    "¡AVISO IMPORTANTE!",
                    "Debe estar conectado el Virtual\n para ejecutar ProcesoV2"
                )
                msg.setWindowFlags(msg.windowFlags() | Qt.WindowStaysOnTopHint)
                msg.exec_()

            else:

                # Rutas base Virtual y Real
                self.archivos_procesamiento_virtual = archivos_fast(
                    archivo,
                    self.directorio_trabajo,
                    resp_virtual
                )

                self.archivos_procesamiento_real_base = archivos_fast(
                    archivo,
                    self.directorio_trabajo,
                    ''
                )

                # Rutas reales definitivas en host (con posible sufijo)
                self.archivos_procesamiento_real = verificar_coincidencias(
                    self.eventos,
                    archivo,
                    self.archivos_procesamiento_real_base.copy()
                )

                # --------------------------------------------------
                # Copia REAL -> VIRTUAL
                # Solo .sis y .fas si existe
                # En virtual NO se requieren sufijos
                # --------------------------------------------------
                origen_real_virtual = [self.archivos_procesamiento_real_base[0]]
                destino_real_virtual = [self.archivos_procesamiento_virtual[0]]

                if os.path.exists(self.archivos_procesamiento_real_base[1]):
                    origen_real_virtual.append(self.archivos_procesamiento_real_base[1])
                    destino_real_virtual.append(self.archivos_procesamiento_virtual[1])

                print("Print real  -  virtual:\n",origen_real_virtual,destino_real_virtual)
                copiar_archivos(
                    origen_real_virtual,
                    destino_real_virtual
                )

                # ==================================================
                # (4) Activar hilo SOLO DESPUÉS DE DIBUJAR MAPA
                # ==================================================
                self.activar_hilo()

        else:
            # Evento NO SISMO → solo mensaje
            self.bandera_virtual = False
            msg = QMessageBox(
                QMessageBox.Information,
                "¡AVISO IMPORTANTE!",
                "Modificacion de aportes de estaciones y filtros"
            )
            msg.setWindowFlags(msg.windowFlags() | Qt.WindowStaysOnTopHint)
            msg.exec_()

        # ==============================================================
        # (5) Finalmente abrir estaciones_ dentro del panel central
        # ==============================================================

        self.en_estaciones = True
        self.incrustar_estaciones()


    # ==========================================================
    #  BLOQUE: REPORTES E INSERCIÓN
    # ==========================================================

    def reportar_(self):
        """
        Genera el reporte individual del sismo actual.
        """
        if not self.catalogo or not getattr(self, 'evento_reporte_escogido', None):
            return
        generar_reporte_sismo(
            self.catalogo,
            self.evento_reporte_escogido,
            self.canales,
            self.trCanal,
            self.archivo_reporte,
            self.directorio_trabajo
        )

    def acelerograma_(self):
        """
        Abre el selector de estaciones y genera los reportes acelerográficos del evento actual.
        """
        if not getattr(self, 'eventos', None) or not getattr(self, 'evento_reporte_escogido', None):
            return
        generar_reporte_acelerograma(
            self.eventos,
            self.indice_local - 1,
            self.catalogo,
            self.evento_reporte_escogido,
            self.archivo_escogido
        )

    def insertar_(self, text=False):
        """
        Abre el diálogo de inserción de eventos de otras redes, persiste el
        catálogo actualizado en disco y sincroniza en cascada sin perder datos.
        """
        if not getattr(self, 'evento_reporte_escogido', None):
            return
        evento_sel = self.ui.cmbx_eventos.currentText()
        reporte_(self).exec_()
        self.catalogo = ordenar_y_eliminar_duplicados(self.catalogo, 0)
        self.guardar_evento()
        (self.catalogo,
         self.eventos_reporte) = guardar_informacion_diaria(
            self.directorios['archivo_csv'],
            self.directorio_trabajo,
            self.catalogo,
            self.eventos
        )
        self.catalogo = ordenar_y_eliminar_duplicados(self.catalogo, 0)
        self.guardar_evento()
        self.sincronizar_archivos_dia_y_periodos()
        if evento_sel:
            self.ui.cmbx_eventos.setCurrentText(evento_sel)
            self.preparar_evento(evento_sel)

    # ==========================================================
    #  BLOQUE: SALIDA Y CIERRE
    # ==========================================================

    def Salir_(self):
        """
        Genera un reporte temporal para revisión y controla el flujo de salida.
        Preserva íntegramente el estado y acceso a procesamiento para que el usuario
        pueda corregir cualquier evento durante la revisión del PDF.
        """
        print("Saliendo sin procesamiento", self.horario)

        # Reglas de interfaz: radio buttons y checkbox de detalles
        if self.ui.radioButton_inicial.isChecked():
            self.ui.checkBox_detalles.setChecked(True)
            self.ui.checkBox_detalles.setEnabled(False)
        elif self.ui.radioButton_revision.isChecked():
            self.ui.checkBox_detalles.setEnabled(True)

        # Sincronizar de forma transparente con IGEPN y USGS si hay conexión a internet,
        # y luego actualizar todos los archivos oficiales del día (_cat.csv, _rep.csv,
        # _res.csv, _resp.csv, .csv, .xml) y propagar en cascada a Semana, Mes y Año
        try:
            self.catalogo, self.eventos_reporte, _ = sincronizar_otras_redes_dia(
                self.directorios,
                self.catalogo,
                self.eventos_reporte,
                self.eventos,
            )
        except Exception:
            pass
        self.sincronizar_archivos_dia_y_periodos()
        tree = ET.ElementTree(self.root)

        if not self.ui.checkBox_detalles.isChecked():
            self.close()
            return

        evento_actual_combo = self.ui.cmbx_eventos.currentText()
        nombre_limpio = Path(self.archivo).stem.replace('_', '')
        prefijo_fecha = nombre_limpio[:8]

        if self.horario in ('00:00 - 12:00', '12:00 - 18:00', '18:00 - 24:00'):
            rango_horario_str = self.horario[:2] + '_' + self.horario[8:10]
        else:
            rango_horario_str = '00_24'

        base_temporal = (
            prefijo_fecha + '_' +
            rango_horario_str + '_' +
            self.responsable
        )
        archivo_reporte_temporal = os.path.join(
            self.directorios['Directorio_base'],
            base_temporal + '.pdf'
        )
        archivo_catalogo_temporal = os.path.join(
            self.directorios['Directorio_base'],
            base_temporal + '_cat.csv'
        )
        self.archivo_catalogo_temporal = archivo_catalogo_temporal

        fecha = QDate(int(prefijo_fecha[0:4]), int(prefijo_fecha[4:6]), int(prefijo_fecha[6:8]))

        # Restaurar y sincronizar el estado completo del combo y del evento activo
        # para mantener exactamente el mismo acceso a procesamiento durante la revisión del PDF
        for idx_c in range(self.ui.cmbx_eventos.count()):
            nom_ev = self.ui.cmbx_eventos.itemText(idx_c)
            aplicar_estilo_item_evento(self, idx_c, nom_ev)

        if evento_actual_combo:
            self.ui.cmbx_eventos.setCurrentText(evento_actual_combo)
            self.preparar_evento(evento_actual_combo)
        self.ui.grupo_carga.setEnabled(True)

        resumen_responsables = self.responsables[0][:] if self.responsables else []
        fila_turno_resp = None
        if self.responsables and len(self.responsables) >= 4:
            if self.horario == '00:00 - 12:00':
                fila_turno_resp = self.responsables[1]
                resumen_responsables.append(fila_turno_resp)
            elif self.horario == '12:00 - 18:00':
                fila_turno_resp = self.responsables[2]
                resumen_responsables.append(fila_turno_resp)
            elif self.horario == '18:00 - 24:00':
                fila_turno_resp = self.responsables[3]
                resumen_responsables.append(fila_turno_resp)
            else:
                # Caso 'Todo el día': incluir las 3 filas de turnos del día
                resumen_responsables.extend(self.responsables[1:4])

        if not self.revision_procesamiento:
            subtitulo_reporte = "Reporte temporal"
            mapa_resumen = 1
            tipo_mapa = 0
            resumen_responsables_rep = 0
            bandera_relleno = True
            modo_reporte = MODO_PERIODO_FRANJAS
            bandera_firma = False

            # Construir desde cero el catálogo temporal exclusivo del turno seleccionado
            # incluyendo tanto los sismos procesados como los dummies de todos los demás
            # eventos del período (sin alterar self.catalogo ni el _cat.csv oficial)
            catalogo_temporal = construir_catalogo_temporal_turno(
                self.catalogo,
                eventos=self.eventos_reporte,
                horario=self.horario,
                insertar_no_procesado=True
            )
            escritura_archivo(archivo_catalogo_temporal, catalogo_temporal)

            # Resumen temporal de conteos exclusivo para el turno seleccionado
            if fila_turno_resp and len(fila_turno_resp) >= 10:
                resumen_temporal = [
                    ["SISMO", "FF", "FC", "TELESISMOS", "Local_CONTROL", "INDEFINIDO", "Ruido"],
                    [
                        int(fila_turno_resp[3]),  # SIS.
                        int(fila_turno_resp[4]),  # FF
                        int(fila_turno_resp[5]),  # FC
                        int(fila_turno_resp[7]),  # TEL.
                        int(fila_turno_resp[8]),  # Local_CONTROL.
                        int(fila_turno_resp[6]),  # IND.
                        int(fila_turno_resp[9]),  # Ruido
                    ]
                ]
            else:
                resumen_temporal = [list(f) for f in self.resumen] if self.resumen else []

            # Verificar que el PDF temporal previo no esté bloqueado en el lector antes de regenerarlo
            if os.path.exists(archivo_reporte_temporal):
                for _ in range(3):
                    try:
                        os.remove(archivo_reporte_temporal)
                        break
                    except PermissionError:
                        mensaje = " Archivo " + archivo_reporte_temporal + " en uso\nCiérrelo para actualizar el reporte."
                        QMessageBox.information(self, "AVISO", mensaje)

            reporte_resumen_modos(
                archivo_reporte_temporal,
                subtitulo_reporte,
                fecha,
                fecha,
                catalogo_temporal,
                resumen_temporal,
                mapa_resumen,
                tipo_mapa,
                modo_reporte,
                [],
                self.directorio_trabajo,
                tree,
                resumen_responsables_rep,
                self.eventos_reporte,
                bandera_firma,
                bandera_relleno,
                self.horario
            )

            os.startfile(archivo_reporte_temporal)
            self.revision_procesamiento = True
            mensaje_html = (
                f"<span style='font-size:14pt; font-weight:700; color:#B00020;'>"
                f"¡Revise el archivo!</span><br>"
                f"<span style='font-size:12pt;'>{archivo_reporte_temporal}</span>"
            )
            self.ui.Lbl_submensajes.setText(mensaje_html)
            return
        else:
            self.ui.Lbl_submensajes.setText("")

        aux = "Se revisó archivo reporte\n" + archivo_reporte_temporal
        message_box = QMessageBox(
            QMessageBox.Question,
            "¡Importante!",
            aux,
            QMessageBox.Yes | QMessageBox.No,
            self.window()
        )
        result = message_box.exec_()

        if result == QMessageBox.Yes:
            for _ in range(3):
                try:
                    if os.path.exists(archivo_reporte_temporal):
                        os.remove(archivo_reporte_temporal)
                    if os.path.exists(archivo_catalogo_temporal):
                        os.remove(archivo_catalogo_temporal)
                    break
                except PermissionError:
                    mensaje = " Archivo " + archivo_reporte_temporal + " en uso\nCiérrelo"
                    QMessageBox.information(self, "AVISO", mensaje)
        else:
            self.revision_procesamiento = False
            return

        self.close()

    def closeEvent(self, event):
        """
        Cierre limpio:
          - Elimina archivo de catálogo temporal del turno si existiera
          - Detiene hilo de monitoreo
          - Limpia panel central
          - Limpia estado gráfico
          - Emite señal de cerrado
        Sin operaciones pesadas de IO ni aperturas de ventanas.
        """
        cat_tmp = getattr(self, 'archivo_catalogo_temporal', None)
        if cat_tmp and os.path.exists(cat_tmp):
            try:
                os.remove(cat_tmp)
            except Exception:
                pass
        self.detener_monitor_virtual()
        self.limpiar_panel_central()
        self.limpiar_estado()
        self.cerrado.emit()
        super().closeEvent(event)


class Cambio_Coeficientes_Filtro(QWidget):
    def __init__(self,canales_habilitados):
        super().__init__()
        self.setWindowTitle("Cambio de coeficientes")
        self.setGeometry(100, 100, 400, 600)
        self.parametros=parametros_estaciones()
        self.ck_box_hab_canal={}
        self.lbl_nombre={}
        self.lbl_codigo={}
        self.ck_box_hab_canal = {}
        self.ck_box_filtro = {}
        self.lbl_grafico_0=QLabel("ESTACIONL",self)
        self.lbl_grafico_0.setGeometry(40, 20, 61, 16)  #setGeometry(x, y, width, height)
        self.lbl_grafico_1=QLabel("CÓDIGO",self)
        self.lbl_grafico_1.setGeometry(138, 20, 50, 16)
        self.lbl_grafico_4=QLabel("FILTRO",self)
        self.lbl_grafico_4.setGeometry(204, 20, 51, 16)
        self.lbl_grafico_5=QLabel("ORDEN",self)
        self.lbl_grafico_5.setGeometry(252, 20, 51, 16)
        self.lbl_grafico_6=QLabel("f inf.",self)
        self.lbl_grafico_6.setGeometry(295, 20, 51, 16)
        self.lbl_grafico_7=QLabel("f sup.",self)
        self.lbl_grafico_7.setGeometry(334, 20, 51, 16)
        self.spbox_fil_orden={}
        self.spbox_fil_finf={}
        self.spbox_fil_fsup={}
        self.spbox_canal={}
        self.canales_habilitados=canales_habilitados
        self.numero_estaciones=len(canales_habilitados)
        for i in range(0, self.numero_estaciones):
            canal_=int(self.canales_habilitados[i])
            val_orden=2
            val_inf=1
            val_sup=10
            self.lbl_nombre[i]=QLabel(self.parametros['NOMBRE'][canal_],self)
            self.lbl_nombre[i].setGeometry(15, i*25+35, 150, 24)  #setGeometry(x, y, width, height)
            self.lbl_codigo[i]=QLabel(self.parametros['CODIGO'][canal_],self)
            self.lbl_codigo[i].setGeometry(150, i*25+35, 150, 24)  #setGeometry(x, y, width, height)
            self.ck_box_filtro[i]=QCheckBox(self)
            self.ck_box_filtro[i].setGeometry(208, i*25+35, 150, 24)  #setGeometry(x, y, width, height)
            self.ck_box_filtro[i].setChecked(False)
            self.spbox_fil_orden[i]=QSpinBox(self)
            self.spbox_fil_orden[i].setGeometry(252, i*25+35, 40, 24)
            self.spbox_fil_orden[i].setRange(1, 10)
            self.spbox_fil_orden[i].setValue(val_orden)
            self.spbox_fil_finf[i]=QSpinBox(self)
            self.spbox_fil_finf[i].setGeometry(294, i*25+35, 40, 24)
            self.spbox_fil_finf[i].setRange(1, 10)
            self.spbox_fil_finf[i].setValue(val_inf)
            self.spbox_fil_fsup[i]=QSpinBox(self)
            self.spbox_fil_fsup[i].setGeometry(334, i*25+35, 40, 24)
            self.spbox_fil_fsup[i].setRange(5, 20)
            self.spbox_fil_fsup[i].setValue(val_sup)        
        self.show()

class estaciones_(QWidget):
    """
    Widget de edición de estaciones, filtros y graficado.
    Sin manejo de archivos pesados ni hilos.

    Envía al padre:
        - cambios de filtros
        - cambios de habilitación
        - solicitud de actualización de ubicación
    """

    # Señales hacia Procesar_evento
    senal_cerrar = pyqtSignal()
    #senal_recalcular_procesamiento = pyqtSignal()
    senal_actualizar_mapa = pyqtSignal()
    senal_cambios_estaciones = pyqtSignal(list, list)  # (indices habilitados, filtros)
    senal_cambio_vista = pyqtSignal(str)   # "mapa" o "senales"

    def __init__(self, estaciones_eventos, filtros, responsable, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ESTACIONES")
        self.parent = parent
        self.parametros = parametros_estaciones()
        self.estaciones_eventos = estaciones_eventos[:]        # lista de índices de estaciones (0..N)
        self.filtros = filtros[:]                              # lista de strings “OOffss” por estación
        self.responsable = responsable
        self.numero_estaciones = len(self.estaciones_eventos)

        self.setFixedSize(495, 550)

        # Estructuras internas
        self.ck_box_hab_canal = {}
        self.lbl_nombre = {}
        self.lbl_codigo = {}
        self.ck_box_filtro = {}
        self.spbox_fil_orden = {}
        self.spbox_fil_finf = {}
        self.spbox_fil_fsup = {}
        self.spbox_canal = {}

        # --------------------------------------------------------
        #  MAQUETADO
        # --------------------------------------------------------
        self._crear_cabeceras()
        self._crear_tabla_estaciones()
        self._crear_botones_accion()

        # Control de mapa inicial
        QTimer.singleShot(200, self._emitir_ubicacion_inicial)

    # ===============================================================
    #  CREAR CABECERAS
    # ===============================================================

    def _crear_cabeceras(self):
        QLabel("ESTACIÓN", self).setGeometry(15, 20, 80, 16)
        QLabel("CÓDIGO", self).setGeometry(145, 20, 60, 16)
        QLabel("HAB", self).setGeometry(205, 20, 35, 16)
        QLabel("CANAL", self).setGeometry(242, 20, 50, 16)
        QLabel("FILTRO", self).setGeometry(305, 20, 50, 16)
        QLabel("ORD", self).setGeometry(360, 20, 40, 16)
        QLabel("f inf", self).setGeometry(405, 20, 40, 16)
        QLabel("f sup", self).setGeometry(445, 20, 40, 16)

    # ===============================================================
    #  TABLA DE ESTACIONES
    # ===============================================================

    def _crear_tabla_estaciones(self):
        """
        Crea los widgets para cada estación (labels, checkbox, spinboxes).
        """
        for fila in range(self.numero_estaciones):
            canal_real = int(self.estaciones_eventos[fila])
            nombre = self.parametros['NOMBRE'][canal_real]
            codigo = self.parametros['CODIGO'][canal_real]
            dato = self.parent.evento_procesar[canal_real + 3]

            # Nombre
            self.lbl_nombre[fila] = QLabel(nombre, self)
            self.lbl_nombre[fila].setGeometry(15, fila * 25 + 45, 130, 20)

            # Código
            self.lbl_codigo[fila] = QLabel(codigo, self)
            self.lbl_codigo[fila].setGeometry(148, fila * 25 + 45, 55, 20)

            # Habilitación
            self.ck_box_hab_canal[fila] = QCheckBox(self)
            self.ck_box_hab_canal[fila].setGeometry(208, fila * 25 + 45, 20, 20)
            self.ck_box_hab_canal[fila].setChecked(dato[5:6] == '1')

            # Canal físico (1,2,3)
            self.spbox_canal[fila] = QSpinBox(self)
            self.spbox_canal[fila].setGeometry(245, fila * 25 + 45, 40, 20)
            self.spbox_canal[fila].setRange(1, 3)
            self.spbox_canal[fila].setValue(int(dato[4:5]))

            # Filtro
            orden = int(self.filtros[fila][0:2])
            finf = int(self.filtros[fila][2:4])
            fsup = int(self.filtros[fila][4:6])

            self.ck_box_filtro[fila] = QCheckBox(self)
            self.ck_box_filtro[fila].setGeometry(312, fila * 25 + 45, 20, 20)
            self.ck_box_filtro[fila].setChecked(orden != 0)

            # Orden
            self.spbox_fil_orden[fila] = QSpinBox(self)
            self.spbox_fil_orden[fila].setGeometry(355, fila * 25 + 45, 40, 20)
            self.spbox_fil_orden[fila].setRange(1, 10)
            self.spbox_fil_orden[fila].setValue(orden if orden else 2)

            # Frecuencia inferior
            self.spbox_fil_finf[fila] = QSpinBox(self)
            self.spbox_fil_finf[fila].setGeometry(400, fila * 25 + 45, 40, 20)
            self.spbox_fil_finf[fila].setRange(1, 10)
            self.spbox_fil_finf[fila].setValue(finf if orden else 1)

            # Frecuencia superior
            self.spbox_fil_fsup[fila] = QSpinBox(self)
            self.spbox_fil_fsup[fila].setGeometry(445, fila * 25 + 45, 40, 20)
            self.spbox_fil_fsup[fila].setRange(5, 20)
            self.spbox_fil_fsup[fila].setValue(fsup if orden else 10)

    # ===============================================================
    #  BOTONES
    # ===============================================================

    def _crear_botones_accion(self):
        # Botón eventual de avance de página (solo visible cuando se selecciona "Señales")
        self.Btn_pagina = QPushButton("Av. Pág", self)
        self.Btn_pagina.setGeometry(190, 500, 85, 25)
        self.Btn_pagina.setVisible(False)
        self.Btn_pagina.clicked.connect(self.cambio_pagina)

        # Salir (reubicado a la izquierda dentro del ancho de la tabla para ampliar zona gráfica)
        self.Btn_salir = QPushButton("Salir", self)
        self.Btn_salir.setGeometry(405, 500, 80, 25)
        self.Btn_salir.clicked.connect(self.close)
        
        # ----------- OPCIONES DE VISTA -----------
        self.radio_mapa = QRadioButton("Mapa", self)
        self.radio_mapa.setGeometry(15, 500, 75, 25)
        self.radio_mapa.setChecked(True)
        self.radio_mapa.toggled.connect(self._al_cambiar_vista_mapa)

        self.radio_senales = QRadioButton("Señales", self)
        self.radio_senales.setGeometry(95, 500, 85, 25)
        self.radio_senales.toggled.connect(self._al_cambiar_vista_senales)

    def _al_cambiar_vista_mapa(self, estado):
        if estado:
            self.Btn_pagina.setVisible(False)
            self.senal_cambio_vista.emit("mapa")

    def _al_cambiar_vista_senales(self, estado):
        if estado:
            self.Btn_pagina.setVisible(True)
            self.senal_cambio_vista.emit("senales")

    def cambio_pagina(self):
        self.parent.pagina = self.parent.pagina + 1
        auxiliar = self.parent.pagina * 6
        if auxiliar >= len(self.estaciones_eventos):
            self.parent.pagina = 0
        self.Graficar_()

    # ===============================================================
    #  UBICACIÓN / MAPA
    # ===============================================================

    def _emitir_ubicacion_inicial(self):
        """Se usa cuando aparece la ventana por primera vez."""
        self.senal_actualizar_mapa.emit()

    def _emitir_ubicacion(self):
        """Llama al padre para actualizar mapa."""
        self.senal_actualizar_mapa.emit()

    # ===============================================================
    #  GRAFICAR SEÑALES
    # ===============================================================

    def Graficar_(self):

        try:
            archivo = self.parent.evento_procesar[1]
            archivo = os.path.join(
                self.parent.directorio_trabajo,
                archivo[:8] + archivo[9:15]
            )

            trc = leer_mseed(archivo, 1)
            self.trCanal = trc

            t0 = trc[self.estaciones_eventos[0]][0].stats.starttime
            t1 = trc[self.estaciones_eventos[0]][0].stats.endtime

            grafico_evento_int(
                self.parent.visor,
                trc,
                t0,
                t1,
                self.estaciones_eventos,
                self.parametros['HAB_GRAFICO'],
                0,
                self.parent.pagina
            )
        except Exception as e:
            print("Error en graficar:", e)

    # ===============================================================
    #  SALIDA Y GUARDADO DE CAMBIOS
    # ===============================================================

    def _recopilar_cambios(self):
        """
        Devuelve:
         - lista de estaciones habilitadas
         - lista de filtros concatenados
        """
        habilitados = []
        filtros_nuevos = []

        for i in range(self.numero_estaciones):
            canal_real = int(self.estaciones_eventos[i])

            # habilitación
            if self.ck_box_hab_canal[i].isChecked():
                habilitados.append(canal_real)

            # filtro
            if self.ck_box_filtro[i].isChecked():
                orden = self.spbox_fil_orden[i].value()
                fi = self.spbox_fil_finf[i].value()
                fs = self.spbox_fil_fsup[i].value()
                filtros_nuevos.append(f"{orden:02}{fi:02}{fs:02}")
            else:
                filtros_nuevos.append("000000")

        return habilitados, filtros_nuevos

    def closeEvent(self, event):
        """
        Antes de cerrar estaciones_ verificamos si los archivos del Virtual
        están en uso. Si lo están → NO se cierra y NO se emite senal_cerrar.
        """

        archivos_bloqueados = []

        for ruta in self.parent.archivos_procesamiento_virtual:
            if not os.path.exists(ruta):
                continue

            # Detectar bloqueo (ProcesoV2)
            try:
                os.rename(ruta, ruta)
            except Exception:
                archivos_bloqueados.append(ruta)

        if archivos_bloqueados:
            lista = "\n".join(archivos_bloqueados)
            msg = QMessageBox(
                QMessageBox.Warning,
                "Archivo en uso",
                "Los siguientes archivos están abiertos en ProcesoV2 "
                "y deben cerrarse antes de continuar:\n\n" + lista
            )
            msg.exec_()
            event.ignore()   # NO cerrar
            return           # NO emitir señales

        # Si NO están ocupados → permitir cierre y emitir señal
        try:
            habil, filtros = self._recopilar_cambios()
            self.senal_cambios_estaciones.emit(habil, filtros)
            self.senal_cerrar.emit()
        except Exception as e:
            print("Error en closeEvent estaciones_:", e)

        super().closeEvent(event)


class reporte_(QDialog):
    def __init__(self, parent=None):
        super(reporte_, self).__init__(parent)
        self.parent = parent
        # Cargar la interfaz desde el archivo .ui directamente en esta instancia
        ruta_ui = os.path.join(ruta_proyecto, "src", "ui", "secundaria.ui")
        ruta_ui = os.path.abspath(ruta_ui)
        uic.loadUi(ruta_ui, self)
        self.setFixedSize(520, 290)
        nombre_ev = ""
        if self.parent and getattr(self.parent, 'evento_reporte_escogido', None):
            nombre_ev = str(self.parent.evento_reporte_escogido[0][1]).strip()
        self.setWindowTitle(f"OTRAS REDES — Evento: {nombre_ev}" if nombre_ev else "OTRAS REDES")

        self.lbl_grafico_0 = QLabel("Página principal", self)
        self.lbl_grafico_0.setGeometry(25, 15, 220, 21)
        self.lbl_grafico_1 = QLabel("Página secundaria", self)
        self.lbl_grafico_1.setGeometry(25, 162, 220, 21)
        self.lbl_grafico_2 = QLabel("RED", self)
        self.lbl_grafico_2.setGeometry(290, 82, 80, 30)
        self.lbl_grafico_3 = QLabel("TIPO DE MAGNITUD", self)
        self.lbl_grafico_3.setGeometry(280, 126, 110, 30)

        self.textEdit = QTextEdit(self)
        self.textEdit.setGeometry(25, 38, 240, 120)
        self.textEdit_2 = QTextEdit(self)
        self.textEdit_2.setGeometry(25, 185, 240, 35)

        self.Btn_limpiar = QPushButton("Limpiar/Iniciar", self)
        self.Btn_limpiar.setGeometry(390, 38, 111, 31)
        self.Btn_limpiar.setEnabled(True)
        self.Btn_limpiar.clicked.connect(self.Limpiar_)
        self.Btn_limpiar.clearFocus()

        self.cmbx_red = QComboBox(self)
        self.cmbx_red.setGeometry(390, 86, 111, 24)
        self.cmbx_tipo_mag = QComboBox(self)
        self.cmbx_tipo_mag.setGeometry(390, 130, 111, 24)
        lista_filtros = [" ", "IGEPN", "USGS", "Otras redes"]
        self.cmbx_red.addItems(lista_filtros)
        lista_filtros = [" ", "M", "MLv", "Md", "Mc", "Mw", "Mb"]
        self.cmbx_tipo_mag.addItems(lista_filtros)
        self.cmbx_red.currentIndexChanged.connect(self.al_cambiar_red)

        self.Btn_insertar = QPushButton("Insertar", self)
        self.Btn_insertar.setGeometry(390, 185, 111, 35)
        self.Btn_insertar.setEnabled(True)
        self.Btn_insertar.clicked.connect(self.Insertar_)
        self.Btn_insertar.clearFocus()

        self.lbl_estado_redes = QLabel("", self)
        self.lbl_estado_redes.setGeometry(25, 232, 476, 45)
        self.lbl_estado_redes.setWordWrap(True)
        self.actualizar_resumen_redes()

    def al_cambiar_red(self, indice_red):
        """
        Al seleccionar IGEPN o USGS, consulta automáticamente en línea si existe
        un sismo coincidente (±60 s) para el evento actual y precarga los datos.
        """
        if indice_red not in (1, 2):
            return
        if self.textEdit.toPlainText().strip():
            return
        if not self.parent or not getattr(self.parent, 'evento_reporte_escogido', None):
            return
        nombre_ev = str(self.parent.evento_reporte_escogido[0][1]).strip()
        nombre_red = "IGEPN" if indice_red == 1 else "USGS"
        sismo_web = buscar_evento_otra_red_en_linea(nombre_ev, self.parent.catalogo, nombre_red)
        if sismo_web:
            self.textEdit.setPlainText(sismo_web["texto_formateado"])
            idx_mag = self.cmbx_tipo_mag.findText(sismo_web["tipo_mag"])
            if idx_mag >= 0:
                self.cmbx_tipo_mag.setCurrentIndex(idx_mag)
            self.lbl_estado_redes.setStyleSheet("color: #0055A5; font-weight: bold;")
            self.lbl_estado_redes.setText(
                f"Encontrado automáticamente en {nombre_red} (Mag {sismo_web['magnitud']} {sismo_web['tipo_mag']}, "
                f"Prof {sismo_web['profundidad']} km). Presione 'Insertar' para guardar."
            )
        else:
            self.actualizar_resumen_redes()

    def actualizar_resumen_redes(self):
        if not self.parent or not getattr(self.parent, 'evento_reporte_escogido', None):
            return
        nombre_ev = str(self.parent.evento_reporte_escogido[0][1]).strip()
        registros_ext = [
            f"{f[17]} (Mag {f[15]} {f[16]}, Prof {f[9]} km, Lat {f[7]}, Long {f[8]})"
            for f in (self.parent.catalogo or [])
            if f and len(f) > 18 and f[0] != 'Id'
            and str(f[18]).strip() == nombre_ev
            and str(f[0]).strip()[-2:] != '00'
        ]
        if registros_ext:
            self.lbl_estado_redes.setStyleSheet("color: #006400; font-weight: bold;")
            self.lbl_estado_redes.setText("Registrado en catálogo: " + " | ".join(registros_ext))
        else:
            self.lbl_estado_redes.setStyleSheet("color: #555555;")
            self.lbl_estado_redes.setText("Sin registros de otras redes asociados a este evento aún.")

    def closeEvent(self, event):
        if self.cmbx_red.currentIndex() > 0 and self.textEdit.toPlainText().strip():
            self.Insertar_()
        escritura_archivo(self.parent.directorios['archivo_reporte'], self.parent.eventos_reporte)
        escritura_archivo(self.parent.directorios['archivo_catalogo'], self.parent.catalogo)

    def Limpiar_(self):
        self.textEdit.clear()
        self.textEdit_2.clear()
        self.cmbx_red.setCurrentIndex(0)
        self.cmbx_tipo_mag.setCurrentIndex(0)

    def Insertar_(self):
        red_ = self.cmbx_red.currentIndex()
        magnitud_ = self.cmbx_tipo_mag.currentIndex()
        tipo_magnitud = self.cmbx_tipo_mag.currentText()
        texto = self.textEdit.toPlainText()
        texto2 = self.textEdit_2.toPlainText()
        self.parent.catalogo, self.parent.eventos_reporte = insertar_evento_otras_redes(
            self.parent.catalogo,
            self.parent.indice_catalogo,
            self.parent.eventos_reporte,
            red_,
            magnitud_,
            tipo_magnitud,
            texto,
            texto2,
            self.parent.evento_reporte_escogido,
            self.parent.indice,
            self.parent.indice_local
        )
        escritura_archivo(self.parent.directorios['archivo_reporte'], self.parent.eventos_reporte)
        escritura_archivo(self.parent.directorios['archivo_catalogo'], self.parent.catalogo)
        self.actualizar_resumen_redes()
        self.textEdit.clear()
        self.textEdit_2.clear()
        self.cmbx_red.setCurrentIndex(0)
        self.cmbx_tipo_mag.setCurrentIndex(0)
