"""
=========================================================================================
MÓDULO DE AYUDA CONTEXTUAL JERÁRQUICA Y SENSIBLE AL ESTADO — RSA
=========================================================================================
Despliega la guía operativa exacta de acuerdo con:
  1. NIVEL 1 (Menú Principal): Muestra ÚNICAMENTE las pestañas del menú superior que
     están habilitadas (`isEnabled()`) en el estado actual (Inicial, Modo Diario por
     turno o Modo Período consolidado). Nunca mezcla pestañas deshabilitadas.
  2. NIVEL 2 y 3 (Adentro de un Submenú / Subprograma): Inspecciona en tiempo real los
     widgets, grupos, botones y paneles visibles del subprograma activo para mostrar
     como vista principal la ayuda exacta del paso/sub-estado en el que se encuentra el
     operador, permitiendo además consultar las demás etapas internas de ese mismo
     subprograma mediante pestañas locales (`QTabWidget`).
=========================================================================================
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget,
    QTextBrowser, QPushButton, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


# =========================================================================================
# 1. HOJA DE ESTILOS CSS PARA EL RENDERIZADO HTML DE LAS GUÍAS
# =========================================================================================
ESTILO_HTML_AYUDA = """
<style>
    body {
        font-family: 'Segoe UI', Arial, sans-serif;
        font-size: 13px;
        color: #1f2937;
        line-height: 1.5;
        margin: 8px;
    }
    h2 {
        color: #1e3a8a;
        border-bottom: 2px solid #93c5fd;
        padding-bottom: 4px;
        margin-top: 2px;
        margin-bottom: 8px;
    }
    h3 {
        color: #0f4c81;
        margin-top: 12px;
        margin-bottom: 6px;
    }
    p {
        margin-top: 4px;
        margin-bottom: 8px;
    }
    ul, ol {
        margin-top: 4px;
        margin-bottom: 10px;
        padding-left: 22px;
    }
    li {
        margin-bottom: 5px;
    }
    .caja-estado-vivo {
        background-color: #ecfdf5;
        border: 1px solid #6ee7b7;
        border-left: 5px solid #059669;
        padding: 9px 12px;
        margin: 6px 0 12px 0;
        border-radius: 4px;
    }
    .caja-flujo {
        background-color: #eff6ff;
        border-left: 4px solid #2563eb;
        padding: 8px 12px;
        margin: 8px 0;
    }
    .caja-alerta {
        background-color: #fef3c7;
        border-left: 4px solid #d97706;
        padding: 8px 12px;
        margin: 8px 0;
    }
    .caja-critica {
        background-color: #fef2f2;
        border-left: 4px solid #dc2626;
        padding: 8px 12px;
        margin: 8px 0;
    }
    table {
        border-collapse: collapse;
        width: 100%;
        margin: 8px 0 12px 0;
        font-size: 12px;
    }
    th {
        background-color: #dbeafe;
        color: #1e3a8a;
        text-align: left;
        padding: 6px 8px;
        border: 1px solid #93c5fd;
    }
    td {
        padding: 5px 8px;
        border: 1px solid #cbd5e1;
        vertical-align: top;
    }
    .negro { color: #111827; font-weight: bold; }
    .verde { color: #15803d; font-weight: bold; }
    .rojo  { color: #b91c1c; font-weight: bold; }
    .azul  { color: #1d4ed8; font-weight: bold; }
    code {
        background-color: #f1f5f9;
        padding: 1px 4px;
        border-radius: 3px;
        font-family: Consolas, monospace;
    }
</style>
"""


# =========================================================================================
# 2. CONSTRUCTORES DE AYUDA PARA EL NIVEL 1 (MENÚ PRINCIPAL — SOLO PESTAÑAS HABILITADAS)
# =========================================================================================
def _construir_ayuda_nivel_menu(ventana_principal) -> dict:
    """
    Genera la estructura de ayuda cuando el usuario se encuentra en el Nivel 1
    (Menú Principal, sin ningún subprograma cargado en el centro).
    Inspecciona en tiempo real qué pestañas (`menu_*.isEnabled()`) están activas
    y muestra ÚNICAMENTE la documentación de las pestañas habilitadas.
    """
    datos_inicializados = getattr(ventana_principal, 'datos_inicializados', False)
    periodo = getattr(ventana_principal, 'periodo', '')

    # Verificar el estado real de habilitación de cada pestaña en la barra de menú
    hab_inicio = hasattr(ventana_principal, 'menu_inicio') and ventana_principal.menu_inicio.isEnabled()
    hab_config = hasattr(ventana_principal, 'menu_configuracion') and ventana_principal.menu_configuracion.isEnabled()
    hab_ingreso = hasattr(ventana_principal, 'menu_ingreso_datos') and ventana_principal.menu_ingreso_datos.isEnabled()
    hab_informes = hasattr(ventana_principal, 'menu_informes') and ventana_principal.menu_informes.isEnabled()
    hab_proc = hasattr(ventana_principal, 'menu_procesamiento') and ventana_principal.menu_procesamiento.isEnabled()
    hab_otros = hasattr(ventana_principal, 'menu_otros_informes') and ventana_principal.menu_otros_informes.isEnabled()

    # -------------------------------------------------------------------------
    # CASO 1.A: Estado A — Sin inicializar día (Pestañas 'Inicio' y 'Configuración' activas)
    # -------------------------------------------------------------------------
    if not datos_inicializados:
        html_inicio = """
        <h2>Pestaña Habilitada: Inicio</h2>
        <div class="caja-estado-vivo">
            <b>Estado actual del menú:</b> Aún no se ha inicializado la sesión de trabajo.
            Están habilitadas las pestañas <b>Inicio</b> y <b>Configuración</b>; las demás pestañas permanecen
            deshabilitadas hasta que defina si trabajará en modo <b>Diario</b> o en modo <b>Período</b>.
        </div>

        <h3>Opciones disponibles en la pestaña <code>Inicio</code>:</h3>
        <table>
            <tr>
                <th>Opción del Menú</th>
                <th>¿Qué hace y cuándo usarla?</th>
            </tr>
            <tr>
                <td><b>Inicialización de día</b></td>
                <td>
                    Abre el módulo de configuración de jornada. Allí deberá elegir:
                    <ul>
                        <li><b>Modo Diario (con turno 00–12, 12–18, 18–24 o Todo el día):</b> Habilitará en el menú principal las pestañas <b>Procesamiento</b> y <b>Otros Informes</b>.</li>
                        <li><b>Modo Período (consolidado):</b> Habilitará en el menú principal las pestañas <b>Ingreso de Datos</b> e <b>Informes</b>.</li>
                    </ul>
                </td>
            </tr>
            <tr>
                <td><b>Salir</b></td>
                <td>Como no hay ninguna sesión activa, cierra por completo el programa.</td>
            </tr>
        </table>
        """
        html_config_inicial = """
        <h2>Pestaña Habilitada: Configuración</h2>
        <div class="caja-flujo">
            Esta pestaña está habilitada en el <b>Estado Inicial (Estado A)</b> al igual que <b>Inicio</b>, y se deshabilita
            automáticamente en cuanto ingresa a <i>Inicialización de día</i> o inicia un flujo de trabajo.
        </div>

        <h3>Opciones disponibles en la pestaña <code>Configuración</code>:</h3>
        <table>
            <tr>
                <th>Opción del Menú</th>
                <th>Archivo / Función dentro del sistema</th>
            </tr>
            <tr>
                <td><b>Estaciones (<code>estaciones.csv</code>)</b></td>
                <td>Edición de los 101 registros constantes (<code>0..100</code>) de estaciones sísmicas y acelerográficas de la red.</td>
            </tr>
            <tr>
                <td><b>Estaciones analógicas (<code>analogicas.csv</code>)</b></td>
                <td>Asignación de los 16 canales constantes del sistema analógico seleccionándolos directamente desde el catálogo de <code>estaciones.csv</code>.</td>
            </tr>
            <tr>
                <td><b>Enlaces digitales (<code>digitales.csv</code>)</b></td>
                <td>Administración extensible de carpetas/enlaces digitales asociados al número de estación en <code>estaciones.csv</code> y su bandera <code>Habilitado</code>.</td>
            </tr>
            <tr>
                <td><b>Responsables (<code>responsables.csv</code>)</b></td>
                <td>Administración extensible de analistas responsables y sus unidades virtuales (<code>ProcesoV2</code>), protegiendo el usuario maestro <code>RSA</code>.</td>
            </tr>
            <tr>
                <td><b>Mapas y regiones GIS (<code>mapas.csv</code>)</b></td>
                <td>Configuración interactiva con visor GIS en vivo para definir los límites geográficos (<code>lat_min, lat_max, long_min, long_max</code>), el paso de grilla (<code>salto</code>) y las estaciones asociadas a cada mapa o proyecto.</td>
            </tr>
            <tr>
                <td><b>Estructura y directorio de trabajo (<code>..\\DIA\\</code>)</b></td>
                <td>Guía instructiva (solo lectura) del árbol jerárquico <code>DIA/</code> (años, meses, semanas, días y sus 7 subcarpetas), simulador de rutas canónicas por fecha y explorador de inventario en disco (<code>TXT</code> / <code>JSON</code>).</td>
            </tr>
            <tr>
                <td><b>Respaldo del programa (ZIP)</b></td>
                <td>Habilitado únicamente en la computadora del Administrador (<code>pc_administrador: true</code> en <code>config_local_pc.json</code>). Comprime <code>datos/</code>, <code>modulos externos/</code> y <code>src/</code> excluyendo <code>VW Backup</code>, Vectorworks y <code>__pycache__</code>.</td>
            </tr>
            <tr>
                <td><b>Actualizar / Recuperar desde respaldo (ZIP)</b></td>
                <td>Disponible para cualquier computadora en el Estado Inicial. Descomprime un respaldo <code>.zip</code> en la carpeta indicada respetando la estructura y copiando únicamente archivos nuevos o con fecha más reciente.</td>
            </tr>
        </table>
        """
        pestanas_iniciales = [('Pestaña: Inicio (Habilitada)', html_inicio)]
        if hab_config:
            pestanas_iniciales.append(('Pestaña: Configuración (Habilitada)', html_config_inicial))
        return {
            'ruta_ubicacion': 'Menú Principal  ▸  Estado Inicial (Sin sesión iniciada)',
            'subtitulo_estado': 'Están habilitadas las pestañas "Inicio" y "Configuración". Ingrese a "Inicialización de día" para activar los menús de trabajo.',
            'indice_activo': 0,
            'pestanas': pestanas_iniciales,
        }

    # -------------------------------------------------------------------------
    # CASO 1.B y 1.C: Estado B — Sesión activa (Mostrar SOLO pestañas habilitadas)
    # -------------------------------------------------------------------------
    pestanas_habilitadas = []

    if hab_proc:
        html_procesamiento = f"""
        <h2>Pestaña Habilitada: Procesamiento (Turno: {periodo})</h2>
        <div class="caja-estado-vivo">
            <b>Modo Diario Activo:</b> Usted inicializó el día con el turno <b>{periodo}</b>.
            Esta pestaña reúne en orden secuencial todas las herramientas para detectar, extraer,
            picar fases y localizar los eventos sísmicos de su turno.
        </div>

        <h3>Opciones de la pestaña <code>Procesamiento</code> (en orden de uso):</h3>
        <table>
            <tr>
                <th>Orden</th>
                <th>Submenú</th>
                <th>Función dentro del flujo sismológico</th>
            </tr>
            <tr>
                <td><b>1º</b></td>
                <td><b>Marcar</b></td>
                <td>Despliega el sismograma continuo de 24h en bloques de 2 horas (renglones de 6 min). Permite marcar con un clic (cruz) el tiempo de inicio de cada evento y guardarlo en <code>marcas.json</code>.</td>
            </tr>
            <tr>
                <td><b>2º</b></td>
                <td><b>Extraer</b></td>
                <td>Carga las marcas del turno, muestra las trazas multicanal, permite ajustar el corte inicial y final, seleccionar estaciones activas, clasificar el evento (<code>SISMO</code>, <code>FF</code>, <code>FC</code>, <code>Ruido</code>, etc.) y cortar los archivos <code>.mseed</code> y <code>.sis</code>.</td>
            </tr>
            <tr>
                <td><b>3º</b></td>
                <td><b>Procesamiento</b></td>
                <td>Permite seleccionar cada evento del día, configurar aportes de estaciones y filtros, monitorear en vivo la localización con <code>ProcesoV2</code> (Virtual), ver el epicentro en el mapa o las señales paginadas y, al salir, revisar el <b>PDF de control del turno (Modo M1)</b>.</td>
            </tr>
            <tr>
                <td><b>4º</b></td>
                <td><b>Fases</b></td>
                <td>Visualizador y picador interactivo de fases <b>P</b>, <b>S</b> y <b>Coda</b> para los eventos tipo <code>SISMO</code>, con sincronización directa de archivos <code>.fas</code> (HYPO71) y <code>.json</code>.</td>
            </tr>
            <tr>
                <td><b>5º</b></td>
                <td><b>Reextracción</b></td>
                <td>Ejecuta inmediatamente la reextracción por lotes (<code>extraer_dia</code>) de los eventos del día sin abrir ventana adicional.</td>
            </tr>
        </table>
        """
        pestanas_habilitadas.append(('Pestaña: Procesamiento', html_procesamiento))

    if hab_otros:
        html_otros_informes = """
        <h2>Pestaña Habilitada: Otros Informes</h2>
        <div class="caja-flujo">
            Esta pestaña está habilitada únicamente en <b>Modo Diario</b> para la auditoría y cierre de las 24 horas del día.
        </div>

        <h3>Opciones de la pestaña <code>Otros Informes</code>:</h3>
        <table>
            <tr>
                <th>Submenú</th>
                <th>Función dentro del flujo sismológico</th>
            </tr>
            <tr>
                <td><b>Reporte diario</b></td>
                <td>
                    Abre el módulo de revisión integral del día completo (los 3 turnos):
                    <ul>
                        <li>Permite graficar y filtrar las señales de cualquier evento del día.</li>
                        <li>Permite reclasificar eventos (botón <code>Modificar</code>) e insertar datos de otras redes (IGEPN/USGS).</li>
                        <li>Permite evaluar la calidad y nivel de ruido de las estaciones.</li>
                        <li>Al pulsar <b>Guardar</b>, actualiza los CSV/XML del día y emite el <b>PDF de Revisión Diaria (Modo M2)</b>.</li>
                    </ul>
                </td>
            </tr>
        </table>
        """
        pestanas_habilitadas.append(('Pestaña: Otros Informes', html_otros_informes))

    if hab_ingreso:
        html_ingreso_datos = """
        <h2>Pestaña Habilitada: Ingreso de Datos</h2>
        <div class="caja-estado-vivo">
            <b>Modo Período Activo:</b> Esta pestaña se habilita cuando inicializa el sistema en modo <b>Período</b>,
            permitiendo incorporar registros de estaciones fuera de línea e integrar catálogos de redes externas en masa.
        </div>

        <h3>Opciones de la pestaña <code>Ingreso de Datos</code>:</h3>
        <table>
            <tr>
                <th>Submenú</th>
                <th>Función dentro del sistema</th>
            </tr>
            <tr>
                <td><b>Ingresar datos de estación en registro continuo</b></td>
                <td>Incorporación de registros continuos MiniSEED provenientes de estaciones fuera de línea.</td>
            </tr>
            <tr>
                <td><b>Ingresar eventos de estaciones acelerográficas</b></td>
                <td>Incorporación de eventos acelerográficos en formato EVT hacia los directorios de trabajo.</td>
            </tr>
            <tr>
                <td><b>Cargar datos de IGEPN</b></td>
                <td>Abre la ventana de integración para pegar bloques de texto de <b>13 columnas</b> del catálogo del IGEPN. Busca automáticamente coincidencias (&lt; 60 s) con eventos de la RSA y los anexa al archivo <code>_cat.csv</code> de cada día.</td>
            </tr>
            <tr>
                <td><b>Cargar datos de USGS</b></td>
                <td>Abre la ventana de integración para pegar bloques de texto de <b>21 columnas</b> del catálogo del USGS y asociarlos (&lt; 60 s) a los catálogos diarios de la RSA.</td>
            </tr>
            <tr>
                <td><b>Reconstrucción de eventos</b></td>
                <td>Proceso masivo por período que reconstruye los <code>.mseed</code> de eventos (y opcionalmente <code>.sis</code>), sincroniza los tokens faltantes en <code>AAAAMMDD000000.csv</code> respetando siempre la clasificación definitiva (nunca sobrescribe reclasificaciones con el <code>_aux.csv</code>) y regenera los consolidados diarios (<code>_cat.csv</code>, <code>_rep.csv</code>, <code>_res.csv</code>, <code>.xml</code> y opcionalmente el PDF diario).</td>
            </tr>
        </table>
        """
        pestanas_habilitadas.append(('Pestaña: Ingreso de Datos', html_ingreso_datos))

    if hab_informes:
        html_informes = """
        <h2>Pestaña Habilitada: Informes</h2>
        <div class="caja-flujo">
            Esta pestaña concentra la generación de boletines acumulados (semanales, mensuales, anuales o por rango de fechas),
            reportes de enjambres/réplicas y capas Shapefile GIS integradas.
        </div>

        <h3>Opciones de la pestaña <code>Informes</code>:</h3>
        <table>
            <tr>
                <th>Submenú</th>
                <th>Función dentro del sistema</th>
            </tr>
            <tr>
                <td><b>Reporte periodo</b></td>
                <td>
                    Módulo principal de consolidación de catálogos, generación automática de capas <b>Shapefile GIS</b> (<code>.shp</code>, <code>.shx</code>, <code>.dbf</code>, <code>.prj</code>, <code>.cpg</code>, <code>.metadata.json</code>, <code>.qmd</code> en UTM 17S) y emisión de reportes PDF según el <b>Mapa/Zona</b> escogido:
                    <ul>
                        <li><b>Ecuador:</b> Boletín Oficial RSA Detallado (<b>M3</b>) o Resumen (<b>M4</b>).</li>
                        <li><b>Facultad:</b> Boletín Institucional Facultad / Redes Sociales (<b>M5</b>).</li>
                        <li><b>Proyectos / GADs (Chanlud, Labrado, Austro, etc.):</b> Informes Institucionales Detallados (<b>M6</b>) o Resumen (<b>M7</b>) con opción de firma.</li>
                        <li><b>Region / Fuentes / Reportes:</b> Portadas cartográficas especiales (<b>M0</b>).</li>
                    </ul>
                </td>
            </tr>
            <tr>
                <td><b>Reporte enjambre</b></td>
                <td>
                    Módulo especializado para aislar y reportar <b>enjambres sísmicos</b> o secuencias de <b>sismo principal y réplicas</b> en un <b>período en días</b> y dentro de un <b>lugar geométrico</b> (<b>Círculo</b> por centro y radio en km, <b>Rectángulo</b> o <b>Polígono libre</b> dibujado sobre el mapa GIS interactivo), generando informes PDF en ReportLab.
                </td>
            </tr>
        </table>
        """
        pestanas_habilitadas.append(('Pestaña: Informes', html_informes))

    if hab_inicio:
        html_inicio_activo = """
        <h2>Pestaña Habilitada: Inicio (Control de Sesión)</h2>
        <div class="caja-flujo">
            Mientras tiene una sesión inicializada (Diaria o por Período), la opción <i>Inicialización de día</i> se oculta
            y queda activa la opción <b>Salir</b> para cerrar la sesión actual.
        </div>

        <h3>Opciones activas en <code>Inicio</code>:</h3>
        <table>
            <tr>
                <th>Opción</th>
                <th>¿Qué hace en este momento?</th>
            </tr>
            <tr>
                <td><b>Salir</b></td>
                <td>
                    <b>No cierra el programa:</b> Cierra únicamente la sesión actual (Diaria o de Período) y regresa la ventana
                    al <b>Estado Inicial</b>, volviendo a habilitar <code>Inicio &rarr; Inicialización de día</code> para que pueda
                    cambiar de fecha, de turno o pasar entre Modo Diario y Modo Período.
                </td>
            </tr>
        </table>
        """
        pestanas_habilitadas.append(('Pestaña: Inicio', html_inicio_activo))

    modo_str = f"Modo Diario (Turno {periodo})" if periodo != '' else "Modo Período (Consolidado)"
    nombres_hab = ", ".join(t[0].replace('Pestaña: ', '') for t in pestanas_habilitadas)
    return {
        'ruta_ubicacion': f'Menú Principal  ▸  {modo_str}',
        'subtitulo_estado': f'Pestañas habilitadas en este modo: {nombres_hab}. (Las demás pestañas están desactivadas por diseño).',
        'indice_activo': 0,
        'pestanas': pestanas_habilitadas
    }


# =========================================================================================
# 3. CONSTRUCTORES DE AYUDA PARA EL NIVEL 2 Y 3 (ADENTRO DE CADA SUBMENÚ Y SUS SUB-ESTADOS)
# =========================================================================================

def _ayuda_subprograma_inicio(widget) -> dict:
    """Ayuda sensible al estado interno de `Inicio_proceso` (`inicio.py`)."""
    es_diario = True
    if hasattr(widget, 'radioButton_periodo') and widget.radioButton_periodo.isChecked():
        es_diario = False

    fecha_sel = widget.dia.selectedDate().toString("yyyy-MM-dd") if hasattr(widget, 'dia') else ""
    turno_sel = widget.cmbx_periodo.currentText() if (es_diario and hasattr(widget, 'cmbx_periodo')) else "Completo / Acumulado"
    resp_sel = widget.cmbx_resposables.currentText() if hasattr(widget, 'cmbx_resposables') else ""

    html_diario = f"""
    <h2>Inicialización en Modo Diario (Por Turno)</h2>
    <div class="caja-estado-vivo">
        <b>Selección actual en pantalla:</b> Modo <b>Diario</b> | Fecha: <code>{fecha_sel}</code> |
        Turno: <code>{turno_sel}</code> | Responsable: <code>{resp_sel}</code>.
    </div>

    <h3>¿Qué está habilitado y qué debo hacer aquí?</h3>
    <ol>
        <li><b>Directorio Base (Botón <code>Drive / Directorio</code>):</b> Verifique que apunte a la carpeta raíz <code>DIA</code>.</li>
        <li><b>Calendario (Habilitado):</b> Haga clic sobre el día que va a procesar. Al seleccionar una fecha, observe el <b>Panel Derecho de Diagnóstico</b>:
            <ul>
                <li>Le indica si existen las carpetas del día y cuántos eventos hay en los turnos <code>00–12</code>, <code>12–18</code> y <code>18–24</code>.</li>
                <li>Muestra en tarjetas verdes/grises cuáles de las 12 estaciones continuas tienen archivo <code>.mseed</code> disponible en ese día.</li>
            </ul>
        </li>
        <li><b>Selector de Período / Turno (Habilitado):</b> Escoja la franja horaria que le corresponde (<code>00:00 - 12:00</code>, <code>12:00 - 18:00</code> o <code>18:00 - 24:00</code>).</li>
        <li><b>Selector de Responsable:</b> Elija su código de operador.</li>
        <li><b>Botón <code>Iniciar</code>:</b> Al pulsarlo se cerrará esta pantalla y en el menú superior se habilitarán exclusivamente las pestañas <b>Procesamiento</b> y <b>Otros Informes</b>.</li>
    </ol>
    """

    html_periodo = f"""
    <h2>Inicialización en Modo Período (Consolidado)</h2>
    <div class="caja-estado-vivo">
        <b>Selección actual en pantalla:</b> Modo <b>Período Completo</b> | Responsable: <code>{resp_sel}</code>.<br>
        <i>En este modo el calendario y el selector de turno horario se deshabilitan automáticamente porque el rango de fechas se escogerá dentro del módulo de informes.</i>
    </div>

    <h3>¿Qué debo hacer aquí?</h3>
    <ol>
        <li>Verifique que el <b>Directorio</b> apunte a la carpeta raíz <code>DIA</code> y que el <b>Responsable</b> sea el correcto.</li>
        <li>Pulse el botón <b><code>Iniciar</code></b>.</li>
        <li>Al hacerlo, en el menú principal se habilitarán exclusivamente las pestañas:
            <ul>
                <li><b>Configuración:</b> Para cargar datos del IGEPN o USGS en los catálogos.</li>
                <li><b>Informes:</b> Para entrar a <b>Reporte periodo</b> y generar informes semanales, mensuales, anuales o institucionales (Modos M0, M3–M7).</li>
            </ul>
        </li>
    </ol>
    """

    return {
        'ruta_ubicacion': 'Inicio  ▸  Inicialización de día',
        'subtitulo_estado': (
            f'Estado activo: Radio "Diario" seleccionado (Calendario y Turno {turno_sel} habilitados).'
            if es_diario else
            'Estado activo: Radio "Período" seleccionado (Calendario y Turno deshabilitados).'
        ),
        'indice_activo': 0 if es_diario else 1,
        'pestanas': [
            ('1. Modo Diario (Con Turno)', html_diario),
            ('2. Modo Período (Consolidado)', html_periodo),
        ]
    }


def _ayuda_subprograma_marcar(widget) -> dict:
    """Ayuda para `Marcar_evento` (`marcar_eventos.py`)."""
    estacion_actual = "Ninguna seleccionada"
    if hasattr(widget, 'lista_mseed') and widget.lista_mseed.currentItem():
        estacion_actual = widget.lista_mseed.currentItem().text()
    num_marcas = len(getattr(widget, 'marcas', []))

    html = f"""
    <h2>Marcar Eventos en Registro Continuo (24 Horas)</h2>
    <div class="caja-estado-vivo">
        <b>Estado actual en pantalla:</b> Estación visualizada: <code>{estacion_actual}</code> |
        Marcas registradas en el día: <b>{num_marcas}</b>.
    </div>

    <h3>¿Cómo usar los controles de esta pantalla?</h3>
    <ol>
        <li><b>Lista de Estaciones (Izquierda):</b> Haga clic en cualquiera de los archivos <code>.mseed</code> continuos del día para visualizar su registro. Al cambiar de estación, las marcas hechas se conservan y guardan automáticamente.</li>
        <li><b>Visualizador de 2 Horas (20 líneas de 6 minutos):</b>
            <ul>
                <li>Cada renglón horizontal representa <b>6 minutos</b> de señal continua.</li>
                <li>Use los botones de navegación de bloque (<code>&lt;&lt;</code> / <code>&gt;&gt;</code>) o la barra de período para recorrer las 24 horas.</li>
                <li>Use <code>Shift + Rueda del ratón</code> si desea desplazarse horizontalmente.</li>
            </ul>
        </li>
        <li><b>Ajuste de Amplitud (Ganancia):</b> Use los botones de amplificación (<code>x2</code> / <code>x0.5</code>) si la traza tiene poca o demasiada amplitud visual.</li>
        <li><b>Crear o Borrar Marcas sobre el Gráfico (Clic Izquierdo):</b>
            <ul>
                <li><b>Para CREAR una marca:</b> Haga clic izquierdo exactamente al inicio del evento sísmico; se dibujará una cruz (<code>+</code>) con la hora UTC.</li>
                <li><b>Para BORRAR una marca:</b> Haga clic izquierdo muy cerca (a menos de <b>2 segundos</b>) de una cruz existente y esta desaparecerá.</li>
            </ul>
        </li>
        <li><b>Botón <code>Salir</code>:</b> Guarda todas las marcas en <code>marcas.json</code> y regresa al menú principal para que pueda pasar a <b>Procesamiento &rarr; Extraer</b>.</li>
    </ol>
    """
    return {
        'ruta_ubicacion': 'Procesamiento  ▸  Marcar Eventos',
        'subtitulo_estado': f'Estación activa: {estacion_actual} ({num_marcas} marcas registradas en el día).',
        'indice_activo': 0,
        'pestanas': [
            ('Guía de Marcado Continuo', html),
        ]
    }


def _ayuda_subprograma_extraer(widget) -> dict:
    """
    Ayuda sensible a las 3 etapas dinámicas de `Extraer_evento` (`extraer_integrado.py`):
      - Etapa 0: `grupo_evento` deshabilitado (esperando cargar marca u hora fija).
      - Etapa 1: `grupo_cortar` habilitado (posicionando el inicio del evento antes de cortar).
      - Etapa 2: `grupo_guardar` y `grupo_desplazar` habilitados (ajustando duración y guardando).
    """
    grupo_ev_hab = hasattr(widget, 'grupo_evento') and widget.grupo_evento.isEnabled()
    grupo_cortar_hab = hasattr(widget, 'grupo_cortar') and widget.grupo_cortar.isEnabled()
    grupo_guardar_hab = hasattr(widget, 'grupo_guardar') and widget.grupo_guardar.isEnabled()
    marca_texto = widget.cmbx_eventos.currentText() if hasattr(widget, 'cmbx_eventos') else ""

    if not grupo_ev_hab:
        indice_activo = 0
        subtitulo = f'Etapa 1 activa: Visor en espera. Seleccione una marca ({marca_texto}) y pulse "Eventos" para graficar.'
    elif grupo_cortar_hab:
        indice_activo = 1
        subtitulo = f'Etapa 2 activa: Posicionando ventana inicial de {marca_texto}. Ajuste el inicio y pulse "Cortar".'
    else:
        indice_activo = 2
        subtitulo = f'Etapa 3 activa: Ajustando duración final y clasificación de {marca_texto}. Pulse "Guardar" al terminar.'

    html_etapa_1 = f"""
    <h2>Etapa 1: Selección y Carga de Marca (Estado Inicial de Extracción)</h2>
    <div class="caja-estado-vivo">
        <b>¿Por qué el área gráfica está en blanco y los botones inferiores están bloqueados?</b><br>
        Porque el sistema está esperando que usted elija qué marca desea cargar en memoria.
        Actualmente tiene seleccionada en la lista: <code>{marca_texto}</code>.
    </div>

    <h3>¿Qué puedo hacer en este paso?</h3>
    <ol>
        <li><b>Opción A — Cargar una marca de la lista (Grupo Superior):</b>
            <ul>
                <li>Seleccione en el desplegable una marca perteneciente a su turno horario (las marcas ya extraídas aparecen deshabilitadas y el sistema salta automáticamente a la siguiente marca pendiente).</li>
                <li>Pulse el botón <b><code>Eventos</code></b> para cargar las señales continuas (&plusmn;7 minutos alrededor de la marca) y pasar a la <b>Etapa 2 (Corte)</b>.</li>
            </ul>
        </li>
        <li><b>Opción B — Extraer en una Hora Fija Manual:</b>
            <ul>
                <li>Si desea extraer un evento que no estaba en la lista de marcas, elija <b>Hora</b>, <b>Minuto</b> y <b>Segundo</b> y pulse <b><code>Extraer Fijo</code></b>.</li>
            </ul>
        </li>
        <li><b>Opción C — Finalizar y cortar archivos del turno (Botón <code>Salir</code>):</b>
            <ul>
                <li>Cuando ya haya revisado y guardado todas las marcas de su turno, pulse <b><code>Salir</code></b>.</li>
                <li>Aparecerá la pregunta <b>&laquo;¿Guardar informe? Solo guardar definitivo de 12H, 18H o 24H&raquo;</b>: si responde <b>Sí</b>, ejecutará <code>extraer_dia</code> creando los archivos <code>.mseed</code> recortados, el catálogo <code>.csv</code> del día y los archivos <code>.sis</code>.</li>
            </ul>
        </li>
    </ol>
    """

    html_etapa_2 = f"""
    <h2>Etapa 2: Posicionamiento del Inicio y Corte (Antes de pulsar «Cortar»)</h2>
    <div class="caja-estado-vivo">
        <b>Estado actual en pantalla:</b> Señales cargadas para <code>{marca_texto}</code> (ventana amplia de &plusmn;7 min con líneas de referencia).
        Están habilitados los controles de <b>Filtro</b>, <b>Av. Pág</b>, <b>Estaciones</b> y el grupo <b>Cortar</b>.
    </div>

    <h3>Controles habilitados en esta etapa:</h3>
    <ol>
        <li><b>Recorrer páginas de estaciones (<code>Av. Pág</code>):</b> Muestra las estaciones en bloques de 6 por página. Pulse <b>Av. Pág</b> para ver el resto de estaciones.</li>
        <li><b>Aplicar Filtro Pasabanda (<code>f inf</code>, <code>f sup</code>, <code>orden</code> + botón <code>Filtrar</code>):</b> Útil para limpiar ruido y distinguir claramente el arribo de la onda P. Use <b><code>Recargar</code></b> si desea volver a la señal sin filtrar.</li>
        <li><b>Botón <code>Estaciones</code>:</b> Abre una subventana donde puede marcar/desmarcar qué estaciones se grafican (<code>PLOT</code>), qué canal usar (<code>1, 2, 3</code>) y qué filtro individual asignar a cada estación.</li>
        <li><b>Desplazar el inicio del evento (Grupo <code>Cortar</code>):</b>
            <ul>
                <li>Use los botones <code>+6m</code> / <code>-6m</code>, <code>+30s</code> / <code>-30s</code>, <code>+10s</code> / <code>-10s</code>, <code>+2s</code> / <code>-2s</code> para mover toda la ventana hasta que el inicio del sismo quede bien ubicado respecto a la línea de corte.</li>
            </ul>
        </li>
        <li><b>Pulsar <code>Cortar</code>:</b> Fija el punto de inicio del recorte (+410 s respecto al borde izquierdo), bloquea este grupo y habilita la <b>Etapa 3 (Duración, Tipo de Evento y Guardar)</b>.</li>
    </ol>
    """

    html_etapa_3 = f"""
    <h2>Etapa 3: Ajuste de Duración Final, Clasificación y Guardado</h2>
    <div class="caja-estado-vivo">
        <b>Estado actual en pantalla:</b> Inicio del evento ya recortado para <code>{marca_texto}</code>.
        Ahora están habilitados el grupo de <b>Duración (Desplazar fin)</b> y el grupo <b>Guardar</b>.
    </div>

    <h3>Pasos finales para registrar este evento:</h3>
    <ol>
        <li><b>Ajustar la duración del recorte (Botones de minutos):</b>
            <ul>
                <li>Use <code>+3m</code> / <code>-3m</code>, <code>+1m</code> / <code>-1m</code>, <code>+0.5m</code> / <code>-0.5m</code> (30 s) y <code>+0.2m</code> / <code>-0.2m</code> (10 s) para alargar o acortar el final de la ventana de modo que abarque toda la coda del evento sin exceso de ruido.</li>
            </ul>
        </li>
        <li><b>Verificar Estaciones Aportantes (Botón <code>Estaciones</code>):</b>
            <ul>
                <li>Si aún no lo hizo, abra <b>Estaciones</b> y deje marcadas (<code>PLOT</code>) únicamente las estaciones donde se registró el evento; esas estaciones quedarán con bandera de aporte <code>1</code> en el token del evento.</li>
            </ul>
        </li>
        <li><b>Seleccionar el Tipo de Evento:</b>
            <ul>
                <li><code>SISMO</code>: Evento sísmico que pasará a localización hipocentral (generará archivo <code>.sis</code>).</li>
                <li><code>FF</code> (Fuera de Foco), <code>FC</code> (Fuera de Cobertura), <code>TELESISMO</code>, <code>Evento_local</code>, <code>CONTROL</code>, <code>INDEFINIDO</code> o <code>Ruido</code>.</li>
            </ul>
        </li>
        <li><b>Pulsar <code>Guardar</code>:</b> Almacena el evento en <code>_aux.csv</code>, limpia el visor y selecciona automáticamente la siguiente marca pendiente de su turno.</li>
    </ol>
    """

    return {
        'ruta_ubicacion': 'Procesamiento  ▸  Extraer Eventos',
        'subtitulo_estado': subtitulo,
        'indice_activo': indice_activo,
        'pestanas': [
            ('Etapa 1: Cargar Marca', html_etapa_1),
            ('Etapa 2: Posicionar y Cortar', html_etapa_2),
            ('Etapa 3: Duración y Guardar', html_etapa_3),
        ]
    }


def _ayuda_subprograma_procesamiento(widget) -> dict:
    """
    Ayuda sensible a los 4 sub-estados dinámicos de `Procesar_evento` (`procesamiento_integrado.py`):
      - Sub-estado 0: Vista base (sin panel de estaciones ni mapa desplegados).
      - Sub-estado 1: Adentro de `Procesar` (tabla `estaciones_` visible) con el radio `Mapa` activo.
      - Sub-estado 2: Adentro de `Procesar` (tabla `estaciones_` visible) con el radio `Señales` activo (+ botón `Av. Pág`).
      - Sub-estado 3: En revisión obligatoria del PDF temporal del turno (`revision_procesamiento == True`, mensaje «¡Revise el archivo!»).
    """
    en_estaciones = bool(getattr(widget, 'en_estaciones', False))
    en_revision_pdf = bool(getattr(widget, 'revision_procesamiento', False))
    est_widget = getattr(widget, 'widget_central_activo', None)
    viendo_senales = False
    if en_estaciones and est_widget is not None and hasattr(est_widget, 'radio_senales'):
        viendo_senales = bool(est_widget.radio_senales.isChecked())

    evento_sel = ""
    tipo_sel = ""
    horario_ev = ""
    resp_ev = ""
    if hasattr(widget, 'ui'):
        evento_sel = widget.ui.cmbx_eventos.currentText()
        tipo_sel = widget.ui.Cmb_bx_tipo_evento.currentText()
        horario_ev = widget.ui.txt_horario.toPlainText() if hasattr(widget.ui.txt_horario, 'toPlainText') else ""
        resp_ev = widget.ui.txt_responsables.toPlainText() if hasattr(widget.ui.txt_responsables, 'toPlainText') else ""

    if en_revision_pdf and not en_estaciones:
        indice_activo = 3
        subtitulo = 'Estado activo: Revisión del PDF temporal del turno («¡Revise el archivo!»). Puede corregir eventos o pulsar Salir para terminar.'
    elif en_estaciones and not viendo_senales:
        indice_activo = 1
        subtitulo = f'Estado activo: Procesando {evento_sel} — Tabla de Estaciones + Vista de MAPA y monitoreo del Virtual.'
    elif en_estaciones and viendo_senales:
        indice_activo = 2
        subtitulo = f'Estado activo: Procesando {evento_sel} — Tabla de Estaciones + Vista de SEÑALES (Botón "Av. Pág" habilitado).'
    else:
        indice_activo = 0
        subtitulo = f'Estado activo: Panel de selección de evento ({evento_sel}). El mapa y las estaciones se desplegarán al pulsar "Procesar".'

    html_vista_base = f"""
    <h2>1. Selección de Evento (Antes de entrar a Procesar)</h2>
    <div class="caja-estado-vivo">
        <b>¿Por qué la zona derecha está vacía en este momento?</b><br>
        Al ingresar a <b>Procesamiento</b> no se muestra ningún mapa ni tabla de estaciones para mantener limpia la interfaz
        hasta que usted escoja un evento (actualmente: <code>{evento_sel or 'Ninguno'}</code>, tipo <code>{tipo_sel}</code>,
        turno <code>{horario_ev}</code>, responsable <code>{resp_ev}</code>) y pulse el botón <b><code>Procesar</code></b>.
    </div>

    <h3>Significado de los colores en la lista desplegable de Eventos (<code>cmbx_eventos</code>):</h3>
    <table>
        <tr>
            <th>Color en el Combo</th>
            <th>Diagnóstico Automático del Evento</th>
            <th>¿Qué debe hacer el operador?</th>
        </tr>
        <tr>
            <td><span class="negro">&#9632; NEGRO (Normal)</span></td>
            <td><b>Pendiente de procesar</b> (tiene archivo <code>.sis</code> en <code>dia/</code> pero aún no tiene <code>.fas</code>), o bien es un evento distinto de <code>SISMO</code> (<code>FF</code>, <code>FC</code>, <code>Ruido</code>).</td>
            <td>Si es un <code>SISMO</code> de su turno, selecciónelo y pulse <b><code>Procesar</code></b> para localizarlo con <code>ProcesoV2</code>.</td>
        </tr>
        <tr>
            <td><span class="verde">&#9632; VERDE (Negrita)</span></td>
            <td><b>Procesado Exitoso:</b> Cuenta con <code>.sis</code>, <code>.fas</code> y <code>.rsa</code> completos, <b>Magnitud &gt; 0</b> y <b>RMS &le; 1.4</b>.</td>
            <td>Ya está correctamente localizado (puede pasar el cursor encima para ver su Mag y RMS, o reprocesarlo si desea afinarlo).</td>
        </tr>
        <tr>
            <td><span class="rojo">&#9632; ROJO (Negrita)</span></td>
            <td><b>Con Inconveniente:</b> No encuentra el archivo <code>.sis</code>, o ya pasó por procesamiento pero no tiene archivo <code>.rsa</code>, su <b>Magnitud es 0</b> o su <b>RMS &gt; 1.4</b>.</td>
            <td>Requiere atención: selecciónelo y pulse <b><code>Procesar</code></b> para corregir fases/estaciones en <code>ProcesoV2</code> (si le faltaba <code>.sis</code>, puede reclasificarlo a <code>SISMO</code> para extraerlo automáticamente).</td>
        </tr>
    </table>

    <h3>Controles del Panel Izquierdo:</h3>
    <ul>
        <li><b>Filtro superior de lista (<code>cmbx_t_evento</code>):</b> Por defecto muestra solo los eventos tipo <code>SISMO</code>. Cámbielo a <code>TODOS</code>, <code>FF</code>, <code>FC</code>, etc., si desea inspeccionar o reclasificar otros registros del día.</li>
        <li><b>Cambiar tipo del evento actual (<code>Cmb_bx_tipo_evento</code>):</b> Permite reclasificar el evento seleccionado. <i>Nota: Si cambia un evento (ej. <code>FF</code> o <code>INDEFINIDO</code>) a <code>SISMO</code> y no tenía archivo <code>.sis</code>, el sistema lo extrae automáticamente desde los registros continuos.</i></li>
        <li><b>Botón <code>Procesar</code>:</b> Despliega en el centro la <b>Tabla de Estaciones</b>, muestra a la derecha el <b>Mapa GIS</b>, copia los archivos <code>.sis</code>/<code>.fas</code> al disco Virtual y activa el monitoreo en tiempo real de <code>ProcesoV2</code>.</li>
        <li><b>Botón <code>Reportar</code>:</b> Genera el PDF individual del sismo seleccionado.</li>
        <li><b>Botón <code>Insertar</code>:</b> Abre la subventana para pegar datos del <code>IGEPN</code> o <code>USGS</code> correspondientes a este evento.</li>
        <li><b>Botón <code>Guardar</code> (Eventos):</b> Guarda inmediatamente en disco los cambios en los CSV del día.</li>
        <li><b>Botón <code>Salir</code>:</b> Inicia el cierre generando primero el <b>PDF temporal de su turno (Modo M1)</b> para revisión obligatoria.</li>
    </ul>
    """

    html_en_mapa = f"""
    <h2>2. Dentro de «Procesar» — Tabla de Estaciones + Vista de MAPA</h2>
    <div class="caja-estado-vivo">
        <b>Estado activo en pantalla:</b> Usted pulsó <b>Procesar</b> sobre el evento <code>{evento_sel}</code>.
        El panel izquierdo quedó bloqueado temporalmente, en el centro se desplegó la tabla de <b>Estaciones</b> y a la derecha
        está activo el radio button <b><code>Mapa</code></b>.
    </div>

    <h3>¿Qué se hace en esta vista?</h3>
    <ol>
        <li><b>Monitoreo en vivo con <code>ProcesoV2</code> (Disco Virtual):</b>
            <ul>
                <li>Al entrar aquí, el sistema copió el archivo <code>.sis</code> (y <code>.fas</code> si existía) hacia la unidad Virtual del responsable (<code>{resp_ev}</code>).</li>
                <li>Cada vez que usted guarda una localización en <code>ProcesoV2</code> (generando el archivo <code>.rsa</code>), el hilo monitor la detecta automáticamente, agrega el intento a <code>_proc.csv</code> y <b>redibuja el Mapa GIS en tiempo real</b>.</li>
                <li>En la esquina inferior derecha del mapa verá el recuadro con los datos actualizados del sismo (Fecha/Hora UTC, Lat, Lon, Prof, Mag y RMS), además de los anillos de cobertura de 50 km (rojo) y 150 km (verde).</li>
            </ul>
        </li>
        <li><b>Edición en la Tabla Central de Estaciones:</b>
            <ul>
                <li><b>Columna <code>HAB</code> (Check):</b> Marca o desmarca si la estación aporta (<code>1</code>) o no (<code>0</code>) al evento y a los informes.</li>
                <li><b>Columna <code>CANAL</code> (1..3):</b> Cambia el componente físico de la estación.</li>
                <li><b>Columnas <code>FILTRO</code>, <code>ORD</code>, <code>f inf</code>, <code>f sup</code>:</b> Activan y configuran el filtro pasabanda Butterworth individual de cada estación.</li>
            </ul>
        </li>
        <li><b>Cambiar a vista de formas de onda (Radio <code>Señales</code>):</b>
            <ul>
                <li>Si selecciona el radio button <b><code>Señales</code></b> en la parte inferior de la tabla, el mapa se reemplazará por el gráfico de sismogramas y aparecerá el botón <b><code>Av. Pág</code></b>.</li>
            </ul>
        </li>
        <li><b>Botón <code>Salir</code> (de la tabla de Estaciones):</b>
            <ul>
                <li><b>¡Importante!</b> Antes de pulsar este botón <code>Salir</code>, cierre el evento dentro de <code>ProcesoV2</code> para que los archivos del Virtual no estén bloqueados.</li>
                <li>Al salir de Estaciones, el sistema copia los archivos definitivos del Virtual al disco Real, limpia el Virtual, guarda los cambios de canales/filtros, oculta el mapa y actualiza el color del evento en el combo (pasando a <span class="verde">VERDE</span> si Mag &gt; 0 y RMS &le; 1.4).</li>
            </ul>
        </li>
    </ol>
    """

    html_en_senales = f"""
    <h2>3. Dentro de «Procesar» — Tabla de Estaciones + Vista de SEÑALES</h2>
    <div class="caja-estado-vivo">
        <b>Estado activo en pantalla:</b> Está dentro del procesamiento del evento <code>{evento_sel}</code>
        con el radio button <b><code>Señales</code></b> seleccionado y el botón <b><code>Av. Pág</code></b> visible.
    </div>

    <h3>Controles disponibles en la vista de Señales:</h3>
    <ol>
        <li><b>Botón <code>Av. Pág</code> (Avance de Página):</b>
            <ul>
                <li>Este botón aparece únicamente cuando está seleccionado el radio <b><code>Señales</code></b>.</li>
                <li>Cada clic avanza al siguiente bloque de <b>6 estaciones</b> (y al llegar al final vuelve a la primera página), permitiéndole inspeccionar todas las trazas del evento en una zona gráfica amplia.</li>
            </ul>
        </li>
        <li><b>Ajuste de Canales y Filtros en la Tabla Central:</b>
            <ul>
                <li>Según la calidad de las señales que observe a la derecha, puede activar/desactivar estaciones en la columna <b><code>HAB</code></b>, cambiar el <b><code>CANAL</code></b> (1, 2 o 3) o activar el <b><code>FILTRO</code></b> (Orden, <code>f inf</code>, <code>f sup</code>).</li>
            </ul>
        </li>
        <li><b>Regresar al Mapa o Salir:</b>
            <ul>
                <li>Marque el radio button <b><code>Mapa</code></b> para volver a ver la localización epicentral y ocultar <code>Av. Pág</code>.</li>
                <li>Pulse el botón <b><code>Salir</code></b> (abajo a la derecha de la tabla de estaciones) cuando haya cerrado el evento en <code>ProcesoV2</code> para guardar todos los cambios y regresar al panel izquierdo.</li>
            </ul>
        </li>
    </ol>
    """

    html_revision_pdf = """
    <h2>4. Etapa de Salida y Revisión Obligatoria del PDF (Modo M1)</h2>
    <div class="caja-critica">
        <b>Mensaje activo en pantalla: «¡Revise el archivo!»</b><br>
        Usted pulsó el botón <b>Salir</b> del panel izquierdo y el sistema acaba de generar y abrir en su lector
        el <b>PDF temporal de control de su turno horario (Modo M1)</b>.
    </div>

    <h3>¿Qué debo verificar en el PDF abierto y cómo proceder?</h3>
    <ol>
        <li><b>Inspeccione el PDF temporal:</b>
            <ul>
                <li>Revise la portada con los epicentros, la tabla de tiempos de su turno, la tabla del catálogo (incluyendo los eventos no procesados de su franja horaria) y las hojas de detalle de señales y acelerogramas.</li>
            </ul>
        </li>
        <li><b>Si encuentra algún error o desea afinar un sismo:</b>
            <ul>
                <li><b>¡Importante! Cierre primero la ventana del lector PDF</b> (Adobe Acrobat, Edge, etc.) para que el archivo no quede bloqueado en Windows.</li>
                <li>En el panel izquierdo (que sigue totalmente habilitado), seleccione cualquier sismo en el combo, pulse <b><code>Procesar</code></b>, <b><code>Insertar</code></b> o cambie su clasificación normalmente.</li>
                <li>Cuando termine la corrección, vuelva a pulsar <b><code>Salir</code></b> para regenerar y revisar el PDF actualizado.</li>
            </ul>
        </li>
        <li><b>Si el PDF está completamente correcto (Salida definitiva):</b>
            <ul>
                <li>Cierre la ventana del lector PDF.</li>
                <li>Pulse nuevamente el botón <b><code>Salir</code></b> del panel izquierdo.</li>
                <li>En el cuadro de diálogo <b>&laquo;Se revisó archivo reporte&raquo;</b>, responda <b>Sí</b>: el sistema borrará el archivo PDF temporal de revisión y regresará al Menú Principal.</li>
            </ul>
        </li>
    </ol>
    """

    return {
        'ruta_ubicacion': 'Procesamiento  ▸  Procesamiento de Eventos',
        'subtitulo_estado': subtitulo,
        'indice_activo': indice_activo,
        'pestanas': [
            ('1. Selección de Evento (Inicio)', html_vista_base),
            ('2. En Procesar: Vista MAPA', html_en_mapa),
            ('3. En Procesar: Vista SEÑALES', html_en_senales),
            ('4. Revisión PDF al Salir', html_revision_pdf),
        ]
    }


def _ayuda_subprograma_fases(widget) -> dict:
    """Ayuda sensible al estado de `FasesVentana` (`fases.py`)."""
    sismo_actual = widget.combo_sis.currentText() if hasattr(widget, 'combo_sis') else ""
    est_actual = ""
    if hasattr(widget, 'lista_mseed') and widget.lista_mseed.currentItem():
        est_actual = widget.lista_mseed.currentItem().text()

    html_vista_general = f"""
    <h2>1. Vista General Paginada (4 Estaciones) y Configuración por Estación</h2>
    <div class="caja-estado-vivo">
        <b>Estado actual en pantalla:</b> Sismo activo: <code>{sismo_actual or 'Ninguno'}</code> |
        Estación seleccionada en lista: <code>{est_actual or 'Ninguna'}</code>.
    </div>

    <h3>Controles de la ventana principal de Fases:</h3>
    <ol>
        <li><b>Selector de Sismo (<code>combo_sis</code>):</b> Lista únicamente los eventos del día clasificados como <code>SISMO</code>. Al elegir uno, lee automáticamente sus fases desde <code>.fas</code> (HYPO71) o <code>.json</code>.</li>
        <li><b>Filtros de visualización:</b>
            <ul>
                <li><b>Aplicar Filtro:</b> Activa o desactiva el filtrado Butterworth sobre las 4 trazas mostradas a la derecha.</li>
                <li><b>Solo estaciones aportantes:</b> Filtra la lista para mostrar únicamente las estaciones marcadas con aporte <code>1</code>.</li>
                <li><b>Botones <code>Anterior</code> / <code>Siguiente</code>:</b> Recorren las páginas de 4 en 4 estaciones.</li>
            </ul>
        </li>
        <li><b>Configuración CSV de la Estación Seleccionada (Token <code>EEEECBFFIISS</code>):</b>
            <ul>
                <li>Al hacer un clic en una estación de la lista, puede modificar su casilla <b>Aporta</b>, <b>Canal (1..3)</b>, <b>Orden de filtro</b>, <b>f inf</b> y <b>f sup</b>; los cambios se guardan directamente en el archivo CSV del día.</li>
            </ul>
        </li>
        <li><b>Parámetros HYPO71 de Fase:</b>
            <ul>
                <li>Permite ajustar <b>Tipo P</b> (<code>I</code> Impulsivo / <code>E</code> Emergente), <b>Polaridad P/S</b> (<code>+</code> / <code>-</code>) y <b>Pesos P/S</b> (<code>0</code> = 100% hasta <code>4</code> = 0% excluida).</li>
            </ul>
        </li>
        <li><b>Para picar o mover tiempos P, S y Coda:</b> Haga <b>doble clic</b> sobre una estación de la lista o directamente sobre su traza gráfica para abrir la <b>Ventana de Gráfico Ampliado</b> (ver Pestaña 2 de esta ayuda).</li>
    </ol>
    """

    html_ventana_ampliada = """
    <h2>2. Ventana de Gráfico Ampliado (Al hacer Doble Clic en una Estación)</h2>
    <div class="caja-flujo">
        Esta subventana se abre al hacer <b>doble clic</b> sobre cualquier traza o estación y permite picar con máxima precisión los arribos de onda.
    </div>

    <h3>Interacción con el ratón y barra superior:</h3>
    <ol>
        <li><b>Zoom con Clic Derecho:</b>
            <ul>
                <li>Haga <b>clic derecho y arrastre</b> para encerrar en un rectángulo la zona de arribo de la onda P o S y ampliarla.</li>
                <li>Haga <b>doble clic derecho</b> para restaurar la vista completa original (<i>Home</i>).</li>
            </ul>
        </li>
        <li><b>Picado de P, S y Coda con Clic Izquierdo:</b>
            <ul>
                <li>Seleccione qué fase desea marcar o arrastre con el <b>clic izquierdo</b> las líneas verticales de <b>P</b>, <b>S</b> y <b>Coda</b>.</li>
                <li>En la barra superior verá calcularse en vivo la diferencia <code>Ts - Tp</code> y la <b>distancia epicentral estimada en km</b>.</li>
            </ul>
        </li>
        <li><b>Cierre y Sincronización Automática:</b>
            <ul>
                <li>Al cerrar la subventana ampliada, el sistema guarda de forma automática y simultánea tanto el archivo <code>.json</code> como el archivo binario canónico <code>.fas</code> (16 ranuras HYPO71) del evento.</li>
            </ul>
        </li>
    </ol>
    """

    return {
        'ruta_ubicacion': 'Procesamiento  ▸  Marcar Fases Sísmicas',
        'subtitulo_estado': f'Sismo activo: {sismo_actual or "Sin sismos"} | Estación: {est_actual or "Seleccione una estación"}.',
        'indice_activo': 0,
        'pestanas': [
            ('1. Vista General y Parámetros', html_vista_general),
            ('2. Subventana de Picado (Doble Clic)', html_ventana_ampliada),
        ]
    }


def _ayuda_subprograma_otras_redes(widget) -> dict:
    """Ayuda sensible a la red seleccionada (`IGEPN` vs `USGS`) en `Otras_redes` (`otras_redes.py`)."""
    red_actual = getattr(widget, 'red', 'IGEPN')
    n_col = getattr(widget, 'n_columnas', 13)

    html = f"""
    <h2>Integración Masiva de Datos de {red_actual} ({n_col} Columnas)</h2>
    <div class="caja-estado-vivo">
        <b>Configuración activa en pantalla:</b> Red seleccionada: <b><code>{red_actual}</code></b> |
        Formato esperado: <b><code>{n_col} columnas</code></b> por evento.
    </div>

    <h3>Paso a paso para cargar los eventos:</h3>
    <ol>
        <li>Copie el bloque de texto de los sismos reportados por <b>{red_actual}</b> y péguelo dentro del cuadro de edición grande.</li>
        <li>Verifique que el selector <b>Red</b> muestre <code>{red_actual}</code> y que el número de columnas sea <code>{n_col}</code>.</li>
        <li>Pulse el botón <b><code>Leer</code></b>:
            <ul>
                <li>Por cada evento pegado, el sistema abre la carpeta de la fecha correspondiente en <code>DIA</code>.</li>
                <li>Busca en el archivo diario si existe algún evento registrado por la RSA (<code>SISMO</code>, <code>FF</code> o <code>FC</code>) cuya hora difiera en <b>menos de 60 segundos</b>.</li>
                <li>Si encuentra coincidencia, vincula el evento externo con el archivo <code>.sis</code> de la RSA, lo inserta en el catálogo <code>_cat.csv</code>, elimina duplicados y regenera los archivos del día.</li>
            </ul>
        </li>
        <li>Al finalizar, el cuadro de texto se limpiará indicando que los eventos fueron procesados. Pulse <b><code>Salir</code></b> para volver al menú principal.</li>
    </ol>
    """
    return {
        'ruta_ubicacion': f'Configuración  ▸  Cargar datos de {red_actual}',
        'subtitulo_estado': f'Módulo configurado para recibir bloques de texto de {red_actual} ({n_col} columnas).',
        'indice_activo': 0,
        'pestanas': [
            (f'Guía de Carga {red_actual}', html),
        ]
    }


def _ayuda_subprograma_reporte_diario(widget) -> dict:
    """Ayuda sensible al estado de `Reporte_diario` (`reporte_diario.py`)."""
    bandera_ev = getattr(widget, 'bandera_evento', 1)
    ev_texto = widget.cmbx_evento_escogido.currentText() if hasattr(widget, 'cmbx_evento_escogido') else ""
    tipo_actual = widget.cmbx_evento.currentText() if hasattr(widget, 'cmbx_evento') else ""
    btn_graf_hab = hasattr(widget, 'Btn_graficar') and widget.Btn_graficar.isEnabled()

    html_principal = f"""
    <h2>1. Auditoría de Eventos del Día y Emisión del PDF Diario (Modo M2)</h2>
    <div class="caja-estado-vivo">
        <b>Estado actual en pantalla:</b> Evento seleccionado: <code>{ev_texto or 'Ninguno'}</code> |
        Clasificación actual: <code>{tipo_actual or 'N/A'}</code> |
        Botones de graficado: <b>{'Habilitados' if btn_graf_hab else 'Deshabilitados (evento tipo Ruido o sin seleccionar)'}</b>.
    </div>

    <h3>Controles disponibles según el evento seleccionado:</h3>
    <ol>
        <li><b>Selector de Evento (<code>cmbx_evento_escogido</code>):</b> Al escoger cualquier evento de la lista del día, se cargan sus datos de fecha/hora y se habilitan los controles correspondientes.</li>
        <li><b>Visualización de Señales (Habilitada si el evento NO es <code>Ruido</code>):</b>
            <ul>
                <li><b><code>Graficar</code>:</b> Dibuja las primeras 6 estaciones del evento en el visor derecho.</li>
                <li><b><code>Av. Pág</code>:</b> Avanza en bloques de 6 estaciones para revisar el resto de la red.</li>
                <li><b><code>Filtrar</code>:</b> Aplica el filtro Butterworth configurado en los controles de orden y frecuencia.</li>
            </ul>
        </li>
        <li><b>Reclasificar el Evento (Selector de tipo + botón <code>Modificar</code>):</b>
            <ul>
                <li>Si al inspeccionar las señales decide cambiar el tipo (por ejemplo, de <code>INDEFINIDO</code> a <code>FF</code> o <code>Ruido</code>), elija el nuevo tipo en el desplegable y pulse <b><code>Modificar</code></b>.</li>
            </ul>
        </li>
        <li><b>Asociar Datos de Otra Red (Cuadros de texto + <code>Red</code> + <code>Tipo Mag</code> + <code>Insertar</code>):</b>
            <ul>
                <li>Permite pegar los datos de localización del <code>IGEPN</code> o <code>USGS</code> para el evento activo y pulsar <b><code>Insertar</code></b> (usa <code>Limpiar</code> para reactivar los cuadros si desea ingresar otra red).</li>
            </ul>
        </li>
        <li><b>Reportes Individuales (<code>Reporte Sismo</code> y <code>Acelerograma</code>):</b> Emiten un PDF individual solo para el evento seleccionado.</li>
        <li><b>Botón <code>Guardar</code> (Cierre del Día):</b>
            <ul>
                <li>Guarda en disco los archivos CSV y XML actualizados del día y genera el <b>PDF de Revisión Diaria (Modo M2)</b>, con portada etiquetada (Mag/Hora en cada epicentro), resumen de tiempos de los 3 turnos y detalle completo de sismos y eventos locales.</li>
            </ul>
        </li>
    </ol>
    """

    html_calidad = """
    <h2>2. Subventana «Calidad de Estación» (Botón Estación)</h2>
    <div class="caja-flujo">
        Al pulsar el botón <b><code>Estación</code></b> se evalúan los registros continuos de 24 horas (<code>calidad_estacion</code>)
        y se abre la ventana de diagnóstico de operatividad y ruido.
    </div>

    <h3>¿Cómo usar la subventana de Calidad de Estación?</h3>
    <ol>
        <li><b>Columnas mostradas por estación:</b>
            <ul>
                <li><b><code>PLOT</code> (Check):</b> Marque las estaciones cuyo nivel de señal/ruido de 24h desee graficar.</li>
                <li><b><code>EVALUAC.</code>:</b> Valor numérico calculado automáticamente sobre las trazas continuas.</li>
                <li><b><code>ENLACE</code> (0..100%):</b> Porcentaje de disponibilidad del enlace de telemetría.</li>
                <li><b><code>COMP.</code> (Comportamiento):</b> Relación entre evaluación y enlace.</li>
                <li><b><code>DET.</code> (Detalle):</b> Motivo operativo (<code>1. OK</code>, <code>2. Enlace caído</code>, <code>3. Mantenimiento</code>, etc.).</li>
            </ul>
        </li>
        <li><b>Botones inferiores:</b>
            <ul>
                <li><b><code>Graficar</code>:</b> Muestra la gráfica de 24h con la línea roja del umbral de ruido de cada estación marcada en <code>PLOT</code>.</li>
                <li><b><code>Calcular</code>:</b> Recalcula la columna de comportamiento tras ajustar el porcentaje de enlace.</li>
                <li><b><code>Salir</code>:</b> Calcula y guarda la matriz en el archivo de comportamiento del día.</li>
            </ul>
        </li>
    </ol>
    """

    return {
        'ruta_ubicacion': 'Otros Informes  ▸  Reporte Diario',
        'subtitulo_estado': (
            f'Evento cargado: {ev_texto} (Tipo: {tipo_actual}).'
            if bandera_ev == 0 else
            'Seleccione un evento en la lista desplegable o pulse "Guardar" para generar el PDF Diario (Modo M2).'
        ),
        'indice_activo': 0,
        'pestanas': [
            ('1. Auditoría y PDF Diario (Modo M2)', html_principal),
            ('2. Subventana: Calidad de Estación', html_calidad),
        ]
    }


def _ayuda_subprograma_reporte_periodo(widget) -> dict:
    """
    Ayuda organizada por las 4 zonas funcionales de la nueva interfaz `Reporte_periodo` (`reporte_acumulado.py`):
      1. Zona 1 (Izquierda Superior): Escogimiento de Período (Año, Mes, Semana o Rango de Fechas con RadioButtons
         excluyentes) y Fuente de Consolidación (Día por día vs En base a reportes existentes _cat.csv).
      2. Zona 2 (Derecha Superior): Región cartográfica, Capa temática de Mapa (.emf) y Filtros Sismológicos
         (Profundidad por estratos o por rango en km, Magnitud por umbral o rango en Md, y N° Mínimo de Estaciones
         para mecanismos focales).
      3. Zona 3 (Izquierda Media): Reportes Especiales por Estación (CSV de amplitudes máximas por tipo de evento
         y Selector Múltiple de Estaciones .mseed).
      4. Zona 4 (Derecha Inferior): Condiciones de Impresión del Informe PDF (Reporte Detallado/Resumen, Firma,
         Relleno de círculos en el mapa) y botón Guardar.
    """
    guardar_hab = hasattr(widget, 'Btn_guardar') and widget.Btn_guardar.isEnabled()
    zona_actual = widget.cmbx_zona.currentText().strip() if hasattr(widget, 'cmbx_zona') else "Ecuador"
    idx_mapa = widget.cmbx_zona.currentIndex() if hasattr(widget, 'cmbx_zona') else 1
    mapa_estilo = widget.cmbx_mapa.currentText().strip() if hasattr(widget, 'cmbx_mapa') else "1.Básico"
    mag_actual = widget.cmbx_magnitud.currentText().strip() if hasattr(widget, 'cmbx_magnitud') else "todos"
    nest_actual = widget.cmbx_n_estaciones.currentText().strip() if hasattr(widget, 'cmbx_n_estaciones') else "todos"
    con_detalle = bool(widget.ck_box_reporte.isChecked()) if hasattr(widget, 'ck_box_reporte') else False
    con_firma = (widget.ck_box_firma.checkState() == 2) if hasattr(widget, 'ck_box_firma') else False
    con_concentricos = (
        (hasattr(widget, 'rb_circulos_concentricos') and widget.rb_circulos_concentricos.isChecked())
        or (hasattr(widget, 'ck_box_concentricos') and widget.ck_box_concentricos.isChecked())
    )
    if con_concentricos:
        con_relleno = 2
    elif hasattr(widget, 'rb_circulos_sin_relleno') and widget.rb_circulos_sin_relleno.isChecked():
        con_relleno = False
    else:
        con_relleno = bool(widget.ck_box_relleno.isChecked()) if hasattr(widget, 'ck_box_relleno') else True
    filtro_activo = bool(widget.ck_box_filtro.isChecked()) if hasattr(widget, 'ck_box_filtro') else True
    tipo_ev_filtro = widget.Cmb_bx_tipo_evento.currentText().strip() if hasattr(widget, 'Cmb_bx_tipo_evento') else "Ruido"
    est_filtro = widget.Cmb_bx_estacion.currentText().strip() if hasattr(widget, 'Cmb_bx_estacion') else ""
    anio_sel = widget.comboBox_anio.currentText().strip() if hasattr(widget, 'comboBox_anio') else ""
    mes_sel = widget.comboBox_mes.currentText().strip() if hasattr(widget, 'comboBox_mes') else ""
    sem_sel = widget.comboBox_semana.currentText().strip() if hasattr(widget, 'comboBox_semana') else ""
    n_eventos_cat = max(0, len(getattr(widget, 'catalogo', [])) - 1)

    # Detectar opción de período seleccionada en vivo
    if hasattr(widget, 'rb_anio') and widget.rb_anio.isChecked():
        unidad_activa_txt = f"Año entero ({anio_sel})"
    elif hasattr(widget, 'rb_mes') and widget.rb_mes.isChecked():
        unidad_activa_txt = f"Mes ({mes_sel} de {anio_sel})"
    elif hasattr(widget, 'rb_semana') and widget.rb_semana.isChecked():
        unidad_activa_txt = f"Semana ISO ({sem_sel} de {anio_sel})"
    else:
        unidad_activa_txt = "Rango de Fechas (Inicio a Fin)"

    fuente_activa_txt = (
        "En base a reportes existentes (_cat.csv)"
        if (hasattr(widget, 'rb_fuente_catalogo') and widget.rb_fuente_catalogo.isChecked())
        else "Día por día (Carpetas diarias completas)"
    )

    # Detectar configuración de profundidad y magnitud en vivo
    if hasattr(widget, 'rb_prof_rango') and widget.rb_prof_rango.isChecked():
        prof_activa_txt = f"Rango numérico: {widget.spin_prof_min.value():.1f} a {widget.spin_prof_max.value():.1f} km"
    else:
        estratos = []
        if not hasattr(widget, 'ck_prof_sup') or widget.ck_prof_sup.isChecked():
            estratos.append("Superficial (<40 km)")
        if not hasattr(widget, 'ck_prof_med') or widget.ck_prof_med.isChecked():
            estratos.append("Medio (40–70 km)")
        if not hasattr(widget, 'ck_prof_pro') or widget.ck_prof_pro.isChecked():
            estratos.append("Profundo (>70 km)")
        prof_activa_txt = ", ".join(estratos) if estratos else "Ningún estrato marcado"

    if hasattr(widget, 'rb_mag_rango') and widget.rb_mag_rango.isChecked():
        mag_activa_txt = f"Rango numérico: {widget.spin_mag_min.value():.1f} a {widget.spin_mag_max.value():.1f} Md"
    else:
        mag_activa_txt = f"Umbral >= {mag_actual}" if mag_actual != "todos" else "Todas las magnitudes"

    # Consultar el catálogo centralizado de banderas en rsa_pdf_catalogo.py
    try:
        from rsa_pdf_catalogo import resolver_modo_por_zona, derivar_banderas_desde_modo
        modo_num = resolver_modo_por_zona(zona_actual, con_detalle=con_detalle)
        banderas_vivas = derivar_banderas_desde_modo(
            modo_num,
            mapa_=idx_mapa,
            bandera_firma=con_firma,
            bandera_relleno=con_relleno
        )
    except Exception:
        modo_num = 4
        banderas_vivas = {
            'codigo_modo': f'M{modo_num}',
            'nombre_modo': 'Boletín por Período',
            'para_quien': 'RSA',
            'imprimir_detalle': con_detalle,
            'incluir_responsables': True,
            'mostrar_tabla_resumen': True,
            'mostrar_grafico_barras': True,
            'incluir_firma': con_firma,
            'extras_tecnicos': False,
        }

    cod_modo = banderas_vivas.get('codigo_modo', f'M{modo_num}')
    nom_modo = banderas_vivas.get('nombre_modo', '')
    para_quien = banderas_vivas.get('para_quien', '')
    imprime_det = "SÍ (Fichas individuales + Hojas de señales 5x página + Acelerogramas)" if banderas_vivas.get('imprimir_detalle') else "NO (Solo boletín resumen sin hojas de señales)"
    imprime_extras = "SÍ (Cobertura 50/150 km, intentos previos, zoom de onda P, RMS y líneas de fase)" if banderas_vivas.get('extras_tecnicos') else "NO (Presentación limpia para destinatario externo)"
    imprime_resp = f"SÍ ({banderas_vivas.get('unidad_responsables', 'horas')})" if banderas_vivas.get('incluir_responsables') else "NO"
    imprime_barras = "SÍ" if banderas_vivas.get('mostrar_grafico_barras') else "NO"
    imprime_firma = "SÍ (Ing. Remigio Guevara — RSA)" if banderas_vivas.get('incluir_firma') else "NO"

    # Si aún no se ha cargado un período, abrir en la Zona 1; si ya se cargó, abrir en la Zona 2 (Filtros)
    indice_activo = 1 if guardar_hab else 0
    subtitulo = (
        f'Datos cargados ({n_eventos_cat} sismos en memoria, botón "Guardar" habilitado) — '
        f'REGIÓN actual: "{zona_actual}" -> Imprimirá {cod_modo} ({nom_modo}).'
        if guardar_hab else
        'Pantalla organizada en 4 zonas: 1) Período y Fuente, 2) Región, Mapa y Filtros, 3) Reportes por Estación y 4) Impresión PDF.'
    )

    # -------------------------------------------------------------------------
    # ZONA 1: ESCOGIMIENTO DE PERÍODO Y FUENTE DE CONSOLIDACIÓN
    # -------------------------------------------------------------------------
    html_zona_1 = f"""
    <h2>Zona 1: Escogimiento de Período y Fuente de Consolidación</h2>
    <div class="caja-estado-vivo">
        <b>Selección actual en Zona 1:</b><br>
        • <b>Período activo:</b> <code>{unidad_activa_txt}</code><br>
        • <b>Fuente de consolidación:</b> <code>{fuente_activa_txt}</code><br>
        • <b>Estado del catálogo:</b> {'Habilitado (' + str(n_eventos_cat) + ' sismos en memoria)' if guardar_hab else 'Sin cargar aún (pulse <code>Cargar Período Seleccionado</code>)'}.
    </div>

    <h3>A) Selección de Unidad de Período (RadioButtons Excluyentes):</h3>
    <p>Al elegir una opción, únicamente se habilita su control asociado para evitar ambigüedad:</p>
    <ul>
        <li><b><code>Año entero</code>:</b> Habilita el selector de año (<code>{anio_sel}</code>) para abarcar del <code>01/01/{anio_sel}</code> al <code>31/12/{anio_sel}</code>.</li>
        <li><b><code>Mes (del Año)</code>:</b> Habilita el año y el mes (<code>{mes_sel}</code>) del día 1 al último día del mes.</li>
        <li><b><code>Semana ISO</code>:</b> Habilita el año y la semana (<code>{sem_sel}</code>) abarcando los 7 días de lunes a domingo.</li>
        <li><b><code>Rango Fechas</code>:</b> Habilita los selectores de calendario <code>INICIO</code> y <code>FIN</code> para cualquier intervalo libre.</li>
    </ul>

    <h3>B) Fuente de Consolidación (RadioButtons Excluyentes):</h3>
    <table>
        <tr>
            <th>Opción</th>
            <th>¿Cómo consolida los datos al pulsar <code>Cargar Período Seleccionado</code>?</th>
        </tr>
        <tr>
            <td><b>1. Día por día (Carpetas diarias)</b></td>
            <td>Recorre cada carpeta diaria <code>DIA/AAAA/AAAA_MM/AAAA_MM_DD/</code> cargando catálogos (<code>_cat.csv</code>), eventos (<code>.csv</code>), resúmenes (<code>_res.csv</code>), tiempos de responsables y árboles XML.</td>
        </tr>
        <tr>
            <td><b>2. En base a reportes existentes (<code>_cat.csv</code>)</b></td>
            <td>
                Algoritmo acelerado: para cada año completo dentro del rango, busca primero si ya existe el cierre anual en
                <code>DIA/AAAA/reportes/Ecuador/AAAA_cat.csv</code> (y sus archivos compañeros) y lo carga de un solo golpe sin barrer los 365 días.
                Solo lee los <code>_cat.csv</code> diarios para meses o años que aún no tengan cierre anual.
            </td>
        </tr>
    </table>
    <p><b>Botón adicional <code>Abrir carpeta 'Ecuador' generada...</code>:</b> Permite elegir manualmente con el explorador de archivos cualquier carpeta llamada <code>Ecuador</code> de un reporte previo y cargarla al instante.</p>
    """

    # -------------------------------------------------------------------------
    # ZONA 2: REGIÓN CARTOGRÁFICA, CAPA DE MAPA (.EMF) Y FILTROS SISMOLÓGICOS
    # -------------------------------------------------------------------------
    html_zona_2 = f"""
    <h2>Zona 2: Región Cartográfica, Capa de Mapa (<code>.emf</code>) y Filtros Sismológicos</h2>
    <div class="caja-estado-vivo">
        <b>Configuración activa en Zona 2:</b>
        <ul>
            <li><b><code>REGIÓN</code>:</b> <code>{zona_actual}</code>  |  <b><code>MAPA</code>:</b> <code>{mapa_estilo}</code></li>
            <li><b>Casilla Maestra <code>Aplicar Filtros Sismológicos</code>:</b> <b>{'ACTIVA' if filtro_activo else 'DESACTIVADA (Solo recorte geográfico)'}</b></li>
            <li><b>Filtro de Profundidad:</b> <code>{prof_activa_txt}</code></li>
            <li><b>Filtro de Magnitud:</b> <code>{mag_activa_txt}</code></li>
            <li><b>Mínimo de Estaciones (Mecanismos Focales):</b> <code>&gt;= {nest_actual}</code></li>
        </ul>
    </div>

    <h3>1. Selectores Cartográficos (<code>REGIÓN</code> y <code>MAPA</code>):</h3>
    <ul>
        <li><b><code>REGIÓN</code> (<code>cmbx_zona</code>):</b> Define el polígono de recorte geográfico (<code>datos/mapas/mapas.csv</code>) y el modo de impresión del boletín PDF (<code>M0</code>, <code>M3</code>–<code>M7</code>). Al cambiar de región se restaura automáticamente el catálogo respaldado en memoria.</li>
        <li><b><code>MAPA</code> (<code>cmbx_mapa</code>):</b> Selecciona qué capa temática vectorial <code>&lt;REGION&gt;_&lt;índice&gt;.emf</code> se dibuja en la portada:
            <ul>
                <li><code>0 — 1.Básico (_0.emf)</code>: Mapa base limpio de contornos.</li>
                <li><code>1 — 1.Medio (_1.emf)</code>: Poblaciones, hidrografía y red vial base.</li>
                <li><code>2 — 3.Físico (_2.emf)</code>: Mapa físico con relieve topográfico.</li>
                <li><code>3 — 4.Nidos (_3.emf)</code>: Zonificación de <b>nidos sísmicos / fuentes sismogénicas</b> (disponible en proyectos como <code>Chanlud</code>, <code>Labrado</code>, <code>Huascachaca</code>, <code>Soldados</code>, <code>Ocana</code>, <code>Pichacay</code>, <code>Tundayme</code>).</li>
                <li><code>4 — 5.Fallas (_4.emf)</code>: Trazas de <b>fallas geológicas</b>.</li>
                <li><code>5 — 6.Combinados (_5.emf)</code>: Capas combinadas (relieve + fallas + nidos).</li>
            </ul>
            <i>(Si elige una capa que no exista físicamente para esa región, el sistema aplica fallback automático a <code>_0.emf</code> para evitar errores).</i>
        </li>
    </ul>

    <h3>2. Filtros Sismológicos (Aplicados tanto al Catálogo/Mapa PDF como al archivo XML):</h3>
    <ul>
        <li><b>Filtro de Profundidad Focal (km):</b> Permite elegir con <code>RadioButtons</code> entre:
            <ul>
                <li><b>Por estratos estándar RSA (CheckBoxes):</b> Marcar o combinar libremente <code>Superficial (&lt;40 km)</code>, <code>Medio (40–70 km)</code> y <code>Profundo (&gt;70 km)</code>.</li>
                <li><b>Por rango numérico en km:</b> Definir cualquier intervalo exacto (ej. <code>0.0 a 15.0 km</code> para sismicidad cortical somera en embalses, o <code>100.0 a 220.0 km</code> para nidos de subducción).</li>
            </ul>
        </li>
        <li><b>Filtro de Magnitud (Md):</b> Permite usar el umbral rápido (<code>todos</code>, <code>&gt;= 2.5</code> .. <code>6.5</code>) o un <b>rango numérico con decimales</b> (ej. <code>1.2 a 2.8 Md</code> para aislar microsismicidad).</li>
        <li><b>Candidatos para Mecanismos Focales (Acción independiente):</b> El cálculo de mecanismos focales se realiza <b>por evento</b> (como en SeisComP/SEISAN) y <b>nunca condiciona</b> los reportes convencionales emitidos con <code>Guardar</code>. El selector de mínimo de estaciones (<code>&gt;= 4..10</code>) y el botón <b><code>Exportar Candidatos (.csv / .xml)</code></b> exportan aparte los sismos candidatos a <code>mecanismos_focales/</code> sin alterar el catálogo ni el PDF del período.</li>
    </ul>
    """

    # -------------------------------------------------------------------------
    # ZONA 3: REPORTES ESPECIALES POR ESTACIÓN (CSV / MSEED)
    # -------------------------------------------------------------------------
    html_zona_3 = f"""
    <h2>Zona 3: Reportes Especiales por Estación (Independientes del Boletín PDF)</h2>
    <div class="caja-estado-vivo">
        <b>Selección actual en Zona 3:</b> Tipo de evento = <code>{tipo_ev_filtro}</code>  |  Estación = <code>{est_filtro}</code>.
    </div>

    <h3>1. Exportar Amplitudes Máximas por Estación y Tipo de Evento:</h3>
    <ul>
        <li>Seleccione el <b>Tipo de Evento</b> (<code>Ruido</code>, <code>FF</code>, <code>FC</code>, <code>TELESISMO</code>, <code>SISMO</code>, <code>INDEFINIDO</code>, <code>Evento_local</code>, <code>CONTROL</code> o <code>TODOS</code>) y la <b>Estación Habilitada</b> (ej. <code>{est_filtro}</code>).</li>
        <li>Al pulsar <b><code>Exportar Amplitudes CSV</code></b>, el sistema recorre el período seleccionado en la Zona 1, identifica los eventos donde esa estación tiene marca de aporte (<code>1</code> en posición 5 del token), abre sus archivos <code>.mseed</code>, multiplica por el factor de calibración y calcula la amplitud máxima absoluta de cada canal.</li>
        <li>Guarda el resultado directamente en <b><code>reportes/otros/&lt;CODIGO_ESTACION&gt;_&lt;TIPO&gt;_rep.csv</code></b> y muestra la ruta en el cuadro de estado.</li>
    </ul>

    <h3>2. Selector Múltiple de Estaciones (Consulta de archivos <code>.mseed</code>):</h3>
    <ul>
        <li>Al pulsar <b><code>Selector Múltiple de Estaciones</code></b>, se abre una ventana emergente con casillas para filtrar sensores <code>SISMICOS</code> y <code>ACELEROGRAFICOS</code> y botón <code>Marcar/Desmarcar todos</code>.</li>
        <li>Al pulsar <b><code>Ejecutar</code></b>, busca en todos los sismos del catálogo cargado qué estaciones de las marcadas registraron señal y despliega el listado de archivos <code>.mseed</code> en el panel de estado inferior izquierdo.</li>
    </ul>
    """

    # -------------------------------------------------------------------------
    # ZONA 4: CONDICIONES DE IMPRESIÓN DEL INFORME PDF Y GUARDADO
    # -------------------------------------------------------------------------
    html_zona_4 = f"""
    <h2>Zona 4: Condiciones de Impresión del Informe PDF y Guardado</h2>
    <div class="caja-estado-vivo">
        <b>Diagnóstico en vivo de lo que se imprimirá al pulsar <code>Guardar</code>:</b>
        <ul>
            <li><b>Modo de Reporte PDF activo:</b> <b><code>{cod_modo} — {nom_modo}</code></b></li>
            <li><b>Destinatario del informe:</b> {para_quien}</li>
            <li><b>Gráfico estadístico de barras:</b> {imprime_barras}  |  <b>Tabla de tiempos de responsables:</b> {imprime_resp}</li>
            <li><b>Casilla <code>Reporte Detallado</code>:</b> {imprime_det}</li>
            <li><b>Extras técnicos internos en el detalle:</b> {imprime_extras}</li>
            <li><b>Casilla <code>Incluir Firma Institucional</code>:</b> {imprime_firma}</li>
            <li><b>Estilo de Símbolos en el Mapa:</b> {'<b>CÍRCULOS CONCÉNTRICOS (9 halos difuminados de densidad/fuentes)</b>' if con_concentricos else ('<b>CÍRCULOS RELLENOS</b> (opacidad 0.7)' if con_relleno else '<b>SOLO CIRCUNFERENCIAS HUECAS</b> (sin relleno)')}</li>
        </ul>
    </div>

    <h3>Opciones de Impresión y las 3 Posibilidades de Simbología en el Mapa:</h3>
    <ul>
        <li><b><code>Reporte Detallado</code> (<code>ck_box_reporte</code>):</b>
            <ul>
                <li><b>Marcada (&#10004;):</b> Genera el informe <b>Detallado</b> (<b>M3</b> en <code>Ecuador</code> o <b>M6</b> en proyectos/GADs), incluyendo las fichas individuales y hojas de señales por cada sismo y acelerogramas.</li>
                <li><b>Desmarcada:</b> Genera únicamente el boletín <b>Resumen</b> (<b>M4</b> en <code>Ecuador</code> o <b>M7</b> en proyectos/GADs: portada, estadísticas y tabla del catálogo, sin hojas individuales).</li>
            </ul>
        </li>
        <li><b><code>Incluir Firma Institucional</code> (<code>ck_box_firma</code>):</b> Activa o desactiva la impresión del nombre y cargo del responsable al final de la tabla del catálogo.</li>
        <li><b>Tres posibilidades excluyentes de simbología en el mapa (<code>grupo_rb_simbologia</code>):</b>
            <ul>
                <li><b>1. <code>Círculos rellenos</code> (<code>rb_circulos_rellenos</code>):</b> Dibuja los círculos que representan los sismos sobre el mapa de portada y en la simbología con <b>relleno de color y opacidad 0.7</b>.</li>
                <li><b>2. <code>Círculos sin relleno</code> (<code>rb_circulos_sin_relleno</code>):</b> Dibuja únicamente la <b>circunferencia (contorno hueco sin relleno, <code>fillOpacity=0.0</code>)</b>, ideal para catálogos históricos o multianuales densos.</li>
                <li><b>3. <code>Círculos concéntricos</code> (<code>rb_circulos_concentricos</code>):</b> Dibuja <b>9 círculos concéntricos azules difuminados</b> por sismo e <b>imprime únicamente el mapa principal (Modo M0)</b> sin ningún detalle adicional (deshabilita automáticamente detalle y firma).</li>
            </ul>
        </li>
    </ul>

    <h3>Estructura Unificada de Carpetas de Guardado (<code>Guardar</code>):</h3>
    <table>
        <tr><th>Unidad de Período</th><th>Ruta donde se guarda el Informe</th><th>Nombre base de Archivos</th></tr>
        <tr>
            <td><b>1. Año (<code>rb_anio</code>)</b></td>
            <td><code>DIA/&lt;AAAA&gt;/reportes/&lt;Región&gt;/</code></td>
            <td><code>&lt;AAAA&gt;_pdf1.pdf</code>, <code>&lt;AAAA&gt;_cat.csv</code></td>
        </tr>
        <tr>
            <td><b>2. Mes (<code>rb_mes</code>)</b></td>
            <td><code>DIA/&lt;AAAA&gt;/&lt;AAAA_MM&gt;/reporte/&lt;Región&gt;/</code></td>
            <td><code>&lt;Mes&gt; del &lt;AAAA&gt;_pdf1.pdf</code></td>
        </tr>
        <tr>
            <td><b>3. Semana ISO (<code>rb_semana</code>)</b></td>
            <td><code>DIA/&lt;AAAA_fin&gt;/reportes/semanal/semana&lt;WW&gt;/&lt;Región&gt;/</code></td>
            <td><code>Semana &lt;WW&gt;_pdf1.pdf</code></td>
        </tr>
        <tr>
            <td><b>4. Período / Rango de Fechas (<code>rb_periodo</code>)</b></td>
            <td><code>DIA/&lt;AAAA_fin&gt;/reportes/periodos/&lt;AAAA_MM_DD_ini&gt;_&lt;AAAA_MM_DD_fin&gt;/&lt;Región&gt;/</code></td>
            <td><code>&lt;dd_mm_aaaa a dd_mm_aaaa&gt;_pdf1.pdf</code></td>
        </tr>
    </table>
    """

    return {
        'ruta_ubicacion': 'Informes  ▸  Reporte por Período (Organizado en 4 Zonas)',
        'subtitulo_estado': subtitulo,
        'indice_activo': indice_activo,
        'pestanas': [
            ('1. Zona Período y Fuente', html_zona_1),
            ('2. Zona Región, Mapa y Filtros', html_zona_2),
            ('3. Zona Reportes por Estación', html_zona_3),
            ('4. Zona Impresión PDF y Guardar', html_zona_4),
        ]
    }


def _ayuda_subprograma_reporte_enjambre(widget) -> dict:
    """
    Nivel 2/3: Subprograma 'Reporte_enjambre' (reporte_enjambre.py).
    Documenta las 3 zonas operativas (Período en Días, Lugar Geométrico y Mapa GIS,
    y Condiciones del Informe PDF en ReportLab) inspeccionando el estado en vivo.
    """
    catalogo_cargado = hasattr(widget, 'Btn_guardar') and widget.Btn_guardar.isEnabled()

    f_ini = widget.dateEdit_ini.date().toString('yyyy-MM-dd') if hasattr(widget, 'dateEdit_ini') else '---'
    f_fin = widget.dateEdit_fin.date().toString('yyyy-MM-dd') if hasattr(widget, 'dateEdit_fin') else '---'
    dias = widget.spin_duracion_dias.value() if hasattr(widget, 'spin_duracion_dias') else 1
    fuente_datos = 'Unidades Básicas Consolidadas (Anual/Mensual)' if (hasattr(widget, 'rb_unidades_basicas') and widget.rb_unidades_basicas.isChecked()) else 'Día por Día (Archivos diarios)'

    indice_mapa = widget.cmbx_zona.currentIndex() if hasattr(widget, 'cmbx_zona') else 0
    nombre_mapa = widget.cmbx_zona.currentText() if hasattr(widget, 'cmbx_zona') else 'Ecuador'
    tipo_lugar = widget.cmbx_tipo_lugar.currentText() if hasattr(widget, 'cmbx_tipo_lugar') else 'Círculo (Centro + Radio km)'

    ck_det = hasattr(widget, 'ck_box_reporte') and widget.ck_box_reporte.isChecked()
    ck_fir = hasattr(widget, 'ck_box_firma') and widget.ck_box_firma.isChecked()
    con_concentricos = hasattr(widget, 'rb_circulos_concentricos') and widget.rb_circulos_concentricos.isChecked()
    con_relleno = (not hasattr(widget, 'rb_circulos_sin_relleno')) or (not widget.rb_circulos_sin_relleno.isChecked())

    num_sismos_total = max(0, len(getattr(widget, 'catalogo_respaldo', [])) - 1)
    num_sismos_filtrados = max(0, len(getattr(widget, 'catalogo', [])) - 1)

    indice_activo = 1 if catalogo_cargado else 0
    subtitulo = (
        f"Período: {f_ini} al {f_fin} ({dias} días)  |  Mapa: {nombre_mapa}  |  "
        f"Lugar geométrico: {tipo_lugar}  |  Sismos en enjambre: {num_sismos_filtrados} de {num_sismos_total}"
    )

    html_zona_1 = f"""
    <h2>Zona 1: Período en Días y Fuente de Datos</h2>
    <div class="caja-estado-vivo">
        <b>Estado actual en Zona 1:</b><br>
        • <b>Rango seleccionado:</b> <code>{f_ini}</code> a <code>{f_fin}</code> (<b>{dias} día(s)</b> inclusivos).<br>
        • <b>Fuente de Datos activa:</b> <b>{fuente_datos}</b>.<br>
        • <b>Catálogo cargado:</b> <b>{num_sismos_total} sismos</b> en el período bruto.
    </div>

    <h3>Sincronización del Período en Días:</h3>
    <ul>
        <li>Puede elegir directamente la fecha <b>Desde</b> (<code>dateEdit_ini</code>) y <b>Hasta</b> (<code>dateEdit_fin</code>), o indicar directamente la cantidad en <b>Duración (días)</b> (<code>spin_duracion_dias</code>), la cual ajusta automáticamente la fecha final.</li>
        <li>Seleccione la fuente de lectura (<b>Unidades Básicas</b> para lectura rápida desde consolidados anuales/mensuales o <b>Día por día</b> desde los archivos diarios) y pulse <b><code>Cargar Catálogo del Período</code></b>.</li>
    </ul>
    """

    html_zona_2 = f"""
    <h2>Zona 2: Lugar Geométrico del Enjambre, Filtros y Mapa GIS Interactivo</h2>
    <div class="caja-estado-vivo">
        <b>Estado espacial y sísmico actual:</b><br>
        • <b>Mapa Base:</b> <code>{nombre_mapa}</code> (índice <code>{indice_mapa}</code>)<br>
        • <b>Lugar Geométrico activo:</b> <code>{tipo_lugar}</code><br>
        • <b>Sismos filtrados dentro del enjambre:</b> <b>{num_sismos_filtrados}</b> de <b>{num_sismos_total}</b> sismos del período.
    </div>

    <h3>Modos de Definición y Dibujo del Lugar Geométrico:</h3>
    <ul>
        <li><b>1. Círculo (Centro + Radio en km):</b> Defina <code>Lat centro</code>, <code>Lon centro</code> y <code>Radio (km)</code> manualmente o pulse <b><code>Dibujar en Mapa</code></b>: el <b>1er clic</b> en el mapa GIS fija el centro y el <b>2do clic</b> calcula automáticamente el radio geodésico en kilómetros.</li>
        <li><b>2. Rectángulo (Límites Lat / Lon):</b> Defina <code>Lat mín/máx</code> y <code>Lon mín/máx</code> o pulse <b><code>Dibujar en Mapa</code></b> y marque dos esquinas opuestas con 2 clics sobre el mapa GIS.</li>
        <li><b>3. Polígono libre (Clics en Mapa GIS):</b> Pulse <b><code>Dibujar en Mapa</code></b>, agregue cada vértice con <b>clic izquierdo</b> sobre el mapa GIS y cierre el polígono con <b>clic derecho</b> (mínimo 3 vértices).</li>
        <li><b>Modo Enjambre Sísmico vs. Sismo Principal y Réplicas:</b>
            <ul>
                <li><b><code>Enjambre Sísmico</code> (<code>rb_modo_enjambre</code>):</b> Grafica todos los sismos del área con la misma simbología escogida.</li>
                <li><b><code>Sismo Principal y Réplicas</code> (<code>rb_modo_replicas</code>):</b> Selecciona automáticamente el sismo de mayor magnitud (o el que usted elija en <code>cmbx_sismo_principal</code>), permite centrar el lugar geométrico en su epicentro (<code>Centrar en Sismo</code>), filtrar solo réplicas posteriores (<code>ck_solo_posteriores</code>) y dibuja el <b>Sismo Principal con los 5 círculos concéntricos rojos del reporte de evento individual</b> por encima de las réplicas.</li>
            </ul>
        </li>
        <li>El botón <b><code>Ampliar Mapa</code></b> abre el mapa GIS del enjambre en una ventana emergente redimensionable con barra de herramientas de zoom y paneo.</li>
    </ul>
    """

    html_zona_3 = f"""
    <h2>Zona 3: Condiciones del Informe PDF (ReportLab) y Guardado</h2>
    <div class="caja-estado-vivo">
        <b>Configuración de Impresión ReportLab:</b><br>
        • <b>Reporte Detallado (<code>ck_box_reporte</code>):</b> {'SÍ (incluye fichas individuales de sismos)' if ck_det else 'NO (solo resumen, estadísticas y tabla de catálogo)'}<br>
        • <b>Firma Institucional (<code>ck_box_firma</code>):</b> {'SÍ' if ck_fir else 'NO'}<br>
        • <b>Simbología en Mapa:</b> {'<b>CÍRCULOS CONCÉNTRICOS (Solo portada formato Facultad, 1 página)</b>' if con_concentricos else ('<b>CÍRCULOS RELLENOS</b>' if con_relleno else '<b>SOLO CIRCUNFERENCIAS HUECAS</b>')}
    </div>

    <h3>Generación del Informe PDF del Enjambre:</h3>
    <ul>
        <li>Al pulsar <b><code>Generar Informe PDF</code></b>, el sistema utiliza el motor institucional de <b>ReportLab</b> (<code>reporte_resumen_modos</code>) y traza automáticamente el contorno del <b>lugar geométrico del enjambre</b> (línea segmentada azul) sobre el mapa de portada <code>.emf</code> junto con los epicentros filtrados.</li>
        <li>Si escoge <b><code>Círculos concéntricos</code></b>, se genera <b>únicamente la primera hoja</b> con el formato compacto de la Facultad para resaltar la densidad espacial del nido o enjambre sísmico.</li>
        <li>Los archivos generados (<code>_pdf1.pdf</code>, <code>_cat.csv</code>, <code>_res.csv</code> y texto para redes) se guardan en <b><code>DIA/&lt;AAAA_fin&gt;/reportes/enjambres/&lt;AAAA_MM_DD_ini&gt;_&lt;AAAA_MM_DD_fin&gt;/&lt;Mapa&gt;/</code></b>.</li>
    </ul>
    """

    return {
        'ruta_ubicacion': 'Informes  ▸  Reporte de Enjambres Sísmicos (Período + Lugar Geométrico)',
        'subtitulo_estado': subtitulo,
        'indice_activo': indice_activo,
        'pestanas': [
            ('1. Zona Período en Días', html_zona_1),
            ('2. Lugar Geométrico y Mapa GIS', html_zona_2),
            ('3. Informe PDF (ReportLab)', html_zona_3),
        ]
    }


def _ayuda_subprograma_calibrar_md(widget) -> dict:
    """Ayuda contextual para el subprograma Calibrar_magnitud_md."""
    indice_activo = widget.tabs.currentIndex() if hasattr(widget, 'tabs') else 0
    html_1 = """
    <h2>1. Recolección de Eventos Bien Caracterizados</h2>
    <p>Seleccione el directorio <code>..\\DIA\\</code>, el rango de fechas y la prioridad de referencia
    (<b>USGS &gt; IGEPN &gt; RSA</b>). El sistema cruza los catálogos <code>*_cat.csv</code> con los archivos
    <code>.rsa</code> de <code>fastHypo/</code> aplicando los filtros de calidad (RMS, estaciones, coda y distancia).</p>
    <ul>
        <li>Puede desmarcar manualmente cualquier lectura dudosa en la columna <code>Incluir</code>.</li>
        <li>Puede exportar o importar el dataset en formato CSV para auditoría externa.</li>
    </ul>
    """
    html_2 = """
    <h2>2. Regresión Lineal Múltiple y Mag2000.txt</h2>
    <p>Ajusta la ecuación empírica de Lee et al. (1972) / <code>Iaspei.frm</code> por estación:</p>
    <p><code>Md = b1 + c1 * log10(Coda) + c2 * dist_km</code></p>
    <ul>
        <li><b>Filtrar atípicos (|r| &gt; 2σ):</b> descarta automáticamente lecturas contaminadas.</li>
        <li><b>Restringir c2 ≥ 0:</b> evita términos de distancia físicamente negativos.</li>
        <li>Al generar <code>Mag2000.txt</code>, se crea un respaldo automático si ya existía uno previo,
        junto con los CSV de dataset/coeficientes y el reporte técnico.</li>
    </ul>
    """
    html_3 = """
    <h2>3. Gráficas de Ajuste y Residuales</h2>
    <p>Inspeccione visualmente cada estación: en el panel izquierdo los puntos deben seguir la recta <b>1:1</b>
    dentro de la banda <b>±0.3</b>; en el derecho los residuales <code>Md - M_ref</code> deben centrarse en 0 sin tendencia con la distancia.</p>
    <p>Para la guía completa paso a paso, pulse el botón <b>Manual de Usuario</b> en la parte superior.</p>
    """
    return {
        'ruta_ubicacion': 'Configuración  ▸  Calibración de Magnitud de Duración (Md — Mag2000.txt)',
        'subtitulo_estado': 'Calibración empírica de coeficientes (b1, c1, c2) sobre eventos USGS / IGEPN / RSA.',
        'indice_activo': indice_activo,
        'pestanas': [
            ('1. Eventos Bien Caracterizados', html_1),
            ('2. Coeficientes y Mag2000.txt', html_2),
            ('3. Gráficas de Ajuste', html_3),
        ],
    }


# =========================================================================================
# 4. ORQUESTADOR DE INSPECCIÓN DE ESTADO EN TIEMPO REAL
# =========================================================================================
def _ayuda_subprograma_reconstruccion_eventos(widget) -> dict:
    """Ayuda contextual completa y sensible al estado para `Reconstruccion_eventos` (`reconstruccion_eventos.py`)."""
    dir_trab = getattr(widget, 'directorio_trabajo', 'C:/DIA/')
    f_ini_txt = widget.dateEdit_inicio.date().toString('dd/MM/yyyy') if hasattr(widget, 'dateEdit_inicio') else ''
    f_fin_txt = widget.dateEdit_fin.date().toString('dd/MM/yyyy') if hasattr(widget, 'dateEdit_fin') else ''
    solo_csv = widget.chk_solo_en_csv.isChecked() if hasattr(widget, 'chk_solo_en_csv') else True
    sobrescribir = widget.chk_sobrescribir.isChecked() if hasattr(widget, 'chk_sobrescribir') else True
    rec_sis = widget.chk_reconstruir_sis.isChecked() if hasattr(widget, 'chk_reconstruir_sis') else False
    reg_cons = widget.chk_regenerar_consolidado.isChecked() if hasattr(widget, 'chk_regenerar_consolidado') else True
    reg_pdf = widget.chk_regenerar_pdf_diario.isChecked() if hasattr(widget, 'chk_regenerar_pdf_diario') else False
    norm_4d = widget.chk_normalizar_4d.isChecked() if hasattr(widget, 'chk_normalizar_4d') else True

    html_guia = f"""
    <h2>Reconstrucción Integral de Eventos por Período</h2>
    <div class="caja-estado-vivo">
        <b>Estado actual configurado:</b><br>
        • <b>Directorio de trabajo:</b> <code>{dir_trab}</code><br>
        • <b>Período seleccionado:</b> {f_ini_txt} al {f_fin_txt}<br>
        • <b>Opciones activas:</b>
          Solo en CSV={('Sí' if solo_csv else 'No')} ·
          Sobrescribir={('Sí' if sobrescribir else 'No')} ·
          .sis={('Sí' if rec_sis else 'No')} ·
          Consolidado diario={('Sí' if reg_cons else 'No')} ·
          PDF diario={('Sí' if reg_pdf else 'No')} ·
          Año 4 dígitos={('Sí' if norm_4d else 'No')}
    </div>

    <p>Este módulo unifica en un solo proceso por período (semanas, meses o años) la <b>normalización a año de 4 dígitos</b>,
    la <b>reextracción de señales</b>, la <b>sincronización de tokens</b> y la <b>regeneración del consolidado diario</b>,
    ejecutándose en segundo plano con doble barra de progreso y botón de cancelación segura.</p>

    <h3>Explicación detallada de cada opción</h3>
    <table>
        <tr>
            <th>Opción</th>
            <th>Qué hace y cuándo usarla</th>
        </tr>
        <tr>
            <td><b>Solo reconstruir eventos presentes en <code>AAAAMMDD000000.csv</code></b><br><i>(Recomendado: Marcado)</i></td>
            <td>Usa las ventanas de tiempo <code>[t_inicio, t_final]</code> de <code>AAAAMMDD_aux.csv</code> únicamente para los eventos confirmados en <code>AAAAMMDD000000.csv</code>, aplicando siempre la <b>clasificación definitiva</b> del CSV principal (si un evento se cambió de <code>INDEFINIDO</code> a <code>SISMO</code> o a <code>Ruido</code>, esa clasificación se respeta estrictamente).</td>
        </tr>
        <tr>
            <td><b>Sobrescribir archivos <code>.mseed</code> existentes</b></td>
            <td>Si está <b>marcado</b>, reextrae todos los <code>.mseed</code> desde <code>mseed/registros/</code>. Si se <b>desmarca</b>, solo crea los <code>.mseed</code> que falten (mucho más rápido cuando únicamente se incorporó una estación nueva).</td>
        </tr>
        <tr>
            <td><b>Reconstruir también archivos <code>.sis</code></b><br><i>(Opcional: Desmarcado por defecto)</i></td>
            <td>Genera los archivos binarios <code>.sis</code> (64 Hz) en la carpeta <code>dia/</code> para eventos clasificados como <code>SISMO</code>. Como las estaciones incorporadas posteriormente suelen ser digitales, por defecto se omite para acelerar períodos largos.</td>
        </tr>
        <tr>
            <td><b>Regenerar consolidado diario (<code>_cat</code>, <code>_rep</code>, <code>_res</code>, <code>.xml</code>)</b><br><i>(Recomendado: Marcado)</i></td>
            <td>Tras actualizar <code>AAAAMMDD000000.csv</code>, ejecuta automáticamente <code>cargar_dia()</code> + <code>sincronizar_otras_redes_dia()</code> + <code>Guardar_dia()</code> y actualiza en cascada los reportes de Semana, Mes y Año ya emitidos (sin regenerar PDFs de período).</td>
        </tr>
        <tr>
            <td><b>Regenerar también el PDF del reporte diario</b><br><i>(Opcional: Desmarcado por defecto)</i></td>
            <td>Vuelve a emitir el archivo <code>AAAAMMDD000000_rep.pdf</code> de revisión diaria para cada día procesado. Recomendado solo para rangos cortos (días o semanas), ya que en rangos de varios años incrementa el tiempo de ejecución.</td>
        </tr>
        <tr>
            <td><b>Normalizar archivos y registros a año de 4 dígitos (<code>AAMMDD &rarr; AAAAMMDD</code>)</b><br><i>(Recomendado: Marcado)</i></td>
            <td>Elimina el arrastre histórico de nombres con año de 2 dígitos (2020–2024). Renombra de forma segura (sin sobrescribir destinos existentes) los archivos del día en raíz (<code>000000.csv</code>, <code>_cat</code>, <code>_rep</code>, <code>_res</code>, <code>.xml</code>, <code>_aux</code>, <code>_estaciones</code>, <code>_est</code>, <code>_marcas</code>, <code>_rep.pdf</code>), <code>reportes/</code> (<code>_resp</code>, <code>_tiempos</code>), <code>mseed/registros/</code>, <code>mseed/eventos/</code>, <code>dia/</code> (<code>.sis</code>, <code>.fas</code>) y <code>procesamiento/</code>, y promueve la columna 1 de <code>AAAAMMDD000000.csv</code> a <code>AAAAMMDD_hhmmss.sis</code>. <b>Nunca modifica <code>fastHypo/</code></b> (cuyos archivos no llevan año).</td>
        </tr>
    </table>
    """

    html_flujo = """
    <h2>Flujo Interno y Protección de Datos</h2>
    <div class="caja-flujo">
        <b>Orden exacto que ejecuta el sistema por cada día del período:</b>
        <ol>
            <li><b>Normalización a año de 4 dígitos (si está marcado):</b> antes de leer o escribir, migra en disco los nombres de 2 dígitos (<code>AAMMDD...</code>) a 4 dígitos (<code>AAAAMMDD...</code>) solo si el destino no existe (cero sobrescrituras, cero pérdida de datos) y deja intacta la carpeta <code>fastHypo/</code>.</li>
            <li><b>Respaldo previo en memoria de <code>AAAAMMDD000000.csv</code>:</b> guarda todas las clasificaciones definitivas (<code>SISMO</code>, <code>FF</code>, <code>FC</code>, <code>TELESISMO</code>, <code>Ruido</code>, etc.), todos los tokens <code>EEEECBFFIISS</code> ya procesados y los eventos que no figuren en <code>_aux.csv</code> (como eventos EVT o de otras redes), promoviendo además los nombres <code>AAMMDD_hhmmss.sis</code> a <code>AAAAMMDD_hhmmss.sis</code>.</li>
            <li><b>Extracción desde <code>mseed/registros/</code> (si existen registros continuos):</b> corta las ventanas <code>[t_inicio, t_final]</code> de <code>AAAAMMDD_aux.csv</code> usando la clasificación oficial de <code>AAAAMMDD000000.csv</code>. Los eventos clasificados como <code>Ruido</code> nunca se extraen.</li>
            <li><b>Sincronización automática contra <code>mseed/eventos/</code>:</b> incluso en días históricos donde ya no existan registros continuos en <code>mseed/registros/</code>, revisa si algún evento tiene <code>'-'</code> en <code>AAAAMMDD000000.csv</code> pese a tener un <code>.mseed</code> real en <code>mseed/eventos/</code>, y completa su token base (<code>EEEEC0000000</code>, no aportante por defecto) para evitar errores al revisar el día en Procesamiento.</li>
            <li><b>Actualización de <code>AAAAMMDD000000.csv</code>, creación/estandarización de <code>AAAAMMDD_aux.csv</code> y <code>archivo_tiempos</code>:</b> consolida, ordena cronológicamente y elimina duplicados. Además, <b>crea o completa automáticamente <code>AAAAMMDD_aux.csv</code></b> (9 columnas en formato de 4 dígitos) para todos los eventos del día —incluso en días históricos que nunca tuvieron <code>_aux.csv</code> ni registros continuos en <code>mseed/registros/</code>—, calculando sus ventanas reales <code>[t_inicio, t_final]</code> desde la cabecera de los <code>.mseed</code> en <code>mseed/eventos/</code> (o desde la hora del <code>.sis</code> + 60 s si no hay señal).</li>
            <li><b>Regeneración del consolidado diario y cascada (si está marcado):</b> reconstruye <code>_cat.csv</code>, <code>_rep.csv</code>, <code>_res.csv</code>, <code>_resp.csv</code> y <code>.xml</code> (ya en 4 dígitos) y actualiza los períodos emitidos.</li>
        </ol>
    </div>

    <div class="caja-alerta">
        <b>Protección de estaciones aportantes (<code>HAB</code>):</b> los tokens creados automáticamente al detectar un <code>.mseed</code> faltante se inicializan con <code>pos5 = '0'</code> (no aportante) para evitar que señales con ruido se grafiquen en informes oficiales. Para incluir una estación como aportante en los reportes acelerográficos, márquela con <code>HAB</code> en <b>Procesamiento integrado</b>.<br><br>
        <b>Días sin archivos:</b> Si un día del rango no tiene carpeta o no existe <code>AAAAMMDD000000.csv</code>, se omite de forma segura, queda registrado en la bitácora y el proceso continúa con el día siguiente sin interrumpirse.
    </div>
    """

    html_casos = """
    <h2>Casos de Uso Frecuentes</h2>
    <ul>
        <li><b>1. Se recuperaron registros continuos de una estación digital que estuvo fuera de línea:</b>
            <br>Copie los archivos diarios en <code>mseed/registros/</code>, seleccione el rango de fechas, <b>desmarque</b> <i>Sobrescribir .mseed existentes</i>, deje <b>desmarcado</b> <i>.sis</i> y <b>marcados</b> <i>Regenerar consolidado diario</i> y <i>Normalizar a año de 4 dígitos</i>. El sistema extraerá solo los eventos de la estación nueva, completará sus tokens en <code>AAAAMMDD000000.csv</code> y actualizará los consolidados.</li>
        <li><b>2. Error o inconsistencia por <code>'-'</code> en <code>AAAAMMDD000000.csv</code> cuando sí existen archivos <code>.mseed</code> en <code>mseed/eventos/</code>:</b>
            <br>Seleccione el día o período con <i>Regenerar consolidado diario</i> marcado. Aunque no existan registros continuos, el sistema sincronizará los tokens faltantes y dejará el día listo para abrirse en Procesamiento y Reportes.</li>
        <li><b>3. Migración definitiva de años históricos (2020–2024) de 2 dígitos a 4 dígitos (<code>AAMMDD &rarr; AAAAMMDD</code>):</b>
            <br>Seleccione el año o período histórico con <i>Normalizar archivos y registros a año de 4 dígitos</i> y <i>Regenerar consolidado diario</i> marcados (y <i>Sobrescribir .mseed</i> desmarcado si solo quiere migrar y sanear sin recorte). Toda la estructura del día y los catálogos quedarán estandarizados a 4 dígitos.</li>
        <li><b>4. Reconstrucción completa tras reclasificaciones masivas o corrección de un período:</b>
            <br>Marque <i>Solo reconstruir eventos presentes en AAAAMMDD000000.csv</i> y <i>Regenerar consolidado diario</i>; nunca perderá las clasificaciones cambiadas manualmente por los analistas.</li>
    </ul>
    """

    return {
        'ruta_ubicacion': 'Ingreso de Datos  ▸  Reconstrucción de eventos',
        'subtitulo_estado': (
            f"Período: {f_ini_txt} al {f_fin_txt}  |  Consolidado={'Sí' if reg_cons else 'No'}  |  "
            f"Año 4 dígitos={'Sí' if norm_4d else 'No'}  |  PDF diario={'Sí' if reg_pdf else 'No'}"
        ),
        'indice_activo': 0,
        'pestanas': [
            ('1. Guía y Opciones', html_guia),
            ('2. Flujo y Protección', html_flujo),
            ('3. Casos de Uso', html_casos),
        ],
    }


def construir_contexto_vivo(ventana_principal) -> dict:
    """
    Inspecciona el árbol actual de `ventana_principal` (`programa_integrado.py`):
      - Si no hay `widget_activo` (Nivel 1), devuelve únicamente las pestañas del menú
        superior que están habilitadas en ese momento.
      - Si hay un `widget_activo` (Nivel 2/3), inspecciona el estado interno de los
        controles de ese subprograma y devuelve sus pestañas internas posicionadas
        exactamente en el paso/sub-estado actual.
    """
    widget_activo = getattr(ventana_principal, 'widget_activo', None)

    if widget_activo is None:
        return _construir_ayuda_nivel_menu(ventana_principal)

    nombre_clase = widget_activo.__class__.__name__

    if nombre_clase == 'Inicio_proceso':
        return _ayuda_subprograma_inicio(widget_activo)
    if nombre_clase == 'Marcar_evento':
        return _ayuda_subprograma_marcar(widget_activo)
    if nombre_clase == 'Extraer_evento':
        return _ayuda_subprograma_extraer(widget_activo)
    if nombre_clase == 'Procesar_evento':
        return _ayuda_subprograma_procesamiento(widget_activo)
    if nombre_clase in ('VentanaPrincipal', 'FasesVentana'):
        return _ayuda_subprograma_fases(widget_activo)
    if nombre_clase == 'Otras_redes':
        return _ayuda_subprograma_otras_redes(widget_activo)
    if nombre_clase == 'Reconstruccion_eventos':
        return _ayuda_subprograma_reconstruccion_eventos(widget_activo)
    if nombre_clase == 'Reporte_diario':
        return _ayuda_subprograma_reporte_diario(widget_activo)
    if nombre_clase == 'Reporte_periodo':
        return _ayuda_subprograma_reporte_periodo(widget_activo)
    if nombre_clase == 'Reporte_enjambre':
        return _ayuda_subprograma_reporte_enjambre(widget_activo)
    if nombre_clase == 'Calibrar_magnitud_md':
        return _ayuda_subprograma_calibrar_md(widget_activo)

    # Fallback genérico si se agrega un widget futuro aún no catalogado
    return _construir_ayuda_nivel_menu(ventana_principal)


# =========================================================================================
# 5. DIÁLOGO DE AYUDA CONTEXTUAL JERÁRQUICA
# =========================================================================================
class DialogoAyudaContextual(QDialog):
    """
    Ventana modal de ayuda contextual que:
      1. Muestra en la cabecera la ruta exacta dentro del árbol de menús y el diagnóstico
         en vivo del sub-estado actual de la pantalla.
      2. Muestra ÚNICAMENTE las pestañas que corresponden al ámbito actual (en el menú
         principal: solo las pestañas habilitadas; dentro de un subprograma: solo las
         etapas o subventanas internas de ese subprograma, abriendo directamente la
         pestaña de la etapa activa en pantalla).
    """

    def __init__(self, contexto_vivo: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ayuda Contextual Dinámica — Red Sísmica del Austro")
        self.resize(860, 640)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(14, 14, 14, 14)
        layout_principal.setSpacing(10)

        # ---------------------------------------------------------------------
        # 1) Banner superior con la ruta jerárquica y el estado detectado en vivo
        # ---------------------------------------------------------------------
        marco_cabecera = QFrame(self)
        marco_cabecera.setStyleSheet(
            "QFrame { background-color: #eff6ff; border: 1px solid #93c5fd; "
            "border-radius: 6px; padding: 6px 10px; }"
        )
        layout_cabecera = QVBoxLayout(marco_cabecera)
        layout_cabecera.setContentsMargins(8, 6, 8, 6)
        layout_cabecera.setSpacing(3)

        lbl_ubicacion = QLabel(f"<b>Ubicación actual:</b>  {contexto_vivo.get('ruta_ubicacion', '')}")
        lbl_ubicacion.setFont(QFont("Segoe UI", 10))
        lbl_ubicacion.setStyleSheet("color: #1e3a8a; border: none;")
        layout_cabecera.addWidget(lbl_ubicacion)

        lbl_estado = QLabel(contexto_vivo.get('subtitulo_estado', ''))
        lbl_estado.setFont(QFont("Segoe UI", 9))
        lbl_estado.setWordWrap(True)
        lbl_estado.setStyleSheet("color: #0f4c81; border: none;")
        layout_cabecera.addWidget(lbl_estado)

        layout_principal.addWidget(marco_cabecera)

        # ---------------------------------------------------------------------
        # 2) Contenedor de pestañas locales del ámbito activo (QTabWidget)
        # ---------------------------------------------------------------------
        pestanas = contexto_vivo.get('pestanas', [])
        indice_activo = contexto_vivo.get('indice_activo', 0)

        if len(pestanas) == 1:
            visor_unico = QTextBrowser(self)
            visor_unico.setOpenExternalLinks(False)
            visor_unico.setHtml(ESTILO_HTML_AYUDA + pestanas[0][1])
            layout_principal.addWidget(visor_unico, 1)
        else:
            self.tab_widget = QTabWidget(self)
            self.tab_widget.setFont(QFont("Segoe UI", 9, QFont.Bold))
            self.tab_widget.setStyleSheet(
                "QTabBar::tab { padding: 7px 14px; } "
                "QTabBar::tab:selected { background-color: #dbeafe; color: #1e3a8a; }"
            )
            for idx_p, (titulo_tab, html_tab) in enumerate(pestanas):
                visor = QTextBrowser(self)
                visor.setOpenExternalLinks(False)
                visor.setHtml(ESTILO_HTML_AYUDA + html_tab)
                etiqueta_tab = f"● {titulo_tab} (Actual)" if idx_p == indice_activo else titulo_tab
                self.tab_widget.addTab(visor, etiqueta_tab)

            if 0 <= indice_activo < len(pestanas):
                self.tab_widget.setCurrentIndex(indice_activo)
            layout_principal.addWidget(self.tab_widget, 1)

        # ---------------------------------------------------------------------
        # 3) Pie con recordatorio de atajo F1 y botón Cerrar
        # ---------------------------------------------------------------------
        layout_inferior = QHBoxLayout()
        lbl_pie = QLabel(
            "<i>Esta ayuda cambia automáticamente según los botones, paneles y opciones activos en pantalla (Atajo: <b>F1</b>).</i>"
        )
        lbl_pie.setStyleSheet("color: #4b5563;")
        layout_inferior.addWidget(lbl_pie)
        layout_inferior.addStretch(1)

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setMinimumWidth(110)
        btn_cerrar.clicked.connect(self.accept)
        layout_inferior.addWidget(btn_cerrar)
        layout_principal.addLayout(layout_inferior)


def mostrar_dialogo_ayuda_contextual(ventana_principal):
    """
    Punto de entrada principal invocado por `VentanaPrincipal` (`programa_integrado.py`)
    al pulsar el botón `? Ayuda de esta pantalla`, el menú `Ayuda` o la tecla `F1`.
    Inspecciona en tiempo real el árbol de menús y los controles del subprograma activo
    y abre `DialogoAyudaContextual`.
    """
    contexto_vivo = construir_contexto_vivo(ventana_principal)
    dialogo = DialogoAyudaContextual(contexto_vivo, parent=ventana_principal)
    dialogo.exec_()
