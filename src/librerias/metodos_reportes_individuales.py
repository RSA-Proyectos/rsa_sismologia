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
# Insertar la ruta al inicio del sys.path
if ruta_librerias not in sys.path:
    sys.path.insert(0, ruta_librerias)


from metodos_gis_rsa import catalogo_gis
from rsa_pdf_reportes import impresion_reporte_sismo
from PyQt5.QtWidgets import QMessageBox
from ventana_aceleraciones import Subventana_aceleraciones
def _filtrar_catalogo_evento(catalogo, nombre_evento):
    """
    Extrae y ordena los registros del catálogo asociados a 'nombre_evento'
    garantizando que la solución de la RSA ocupe siempre la posición 0 (o []
    si el evento solo cuenta con solución de otra red como IGEPN/USGS), seguida
    de las soluciones de redes externas.
    """
    nombre_limpio = str(nombre_evento).strip()
    filas_evento = [
        registro for registro in catalogo
        if registro and len(registro) > 18 and registro[0] != 'Id' and str(registro[18]).strip() == nombre_limpio
    ]
    if not filas_evento:
        return []

    filas_rsa = [f for f in filas_evento if str(f[17]).strip() in ('RSA', 'No procesado') or str(f[0]).endswith('00')]
    filas_ext = [f for f in filas_evento if f not in filas_rsa]

    if filas_rsa:
        return [filas_rsa[0]] + filas_ext
    return [[]] + filas_ext


def generar_reporte_sismo(catalogo, evento_escogido, canales, tr_canal, archivo_rep, directorio_trabajo):
    """
    Genera un reporte de sismo basado en un evento escogido del catálogo.

    Args:
        catalogo (list): Lista con los registros del catálogo del período.
        evento_escogido (list): Lista con el evento seleccionado.
        canales (list): Lista de canales asociados al evento.
        tr_canal (list): Datos relacionados con los canales.
        archivo_rep (str): Nombre del archivo del reporte.
        directorio_trabajo (str): Directorio raíz de trabajo (..\\DIA\\).
    """
    if not evento_escogido or not evento_escogido[0]:
        QMessageBox.information(None, "Aviso", "No hay un evento seleccionado para reportar.")
        return

    tipo_ev_sel = str(evento_escogido[0][2]).strip() if len(evento_escogido[0]) > 2 else ""
    if tipo_ev_sel in ("Ruido", "CONTROL"):
        QMessageBox.information(
            None,
            "Aviso",
            f"Los eventos clasificados como '{tipo_ev_sel}' no generan reportes.",
        )
        return

    catalogo_escogido = _filtrar_catalogo_evento(catalogo, evento_escogido[0][1])

    if not catalogo_escogido:
        tipo_ev = str(evento_escogido[0][2]).strip() if len(evento_escogido[0]) > 2 else ""
        if tipo_ev in ("FF", "FC"):
            QMessageBox.information(
                None,
                "Aviso",
                f"El evento está marcado como {tipo_ev} y debe estar vinculado a un evento de Otras Redes (IGEPN / USGS) para generar un reporte.",
            )
        else:
            QMessageBox.information(None, "Aviso", "No hay información del evento en el catálogo")
        return

    # Llama a la función que despliega la vista previa cartográfica GIS
    catalogo_gis(catalogo_escogido)

    # Crear una ventana de confirmación para generar el reporte
    message_box = QMessageBox()
    message_box.setIcon(QMessageBox.Question)
    message_box.setWindowTitle("Reporte")
    message_box.setText("¿Generar el reporte del evento?")
    message_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    
    result = message_box.exec_()

    if result == QMessageBox.Yes:
        # Reporte individual externo (investigadores y prensa): sin estaciones,
        # sin polígonos de cobertura de red y sin historial interno de intentos (_proc.csv)
        banderas_externas = {
            'mostrar_cobertura_red': False,
            'mostrar_intentos_proc': False,
        }
        impresion_reporte_sismo(
            archivo_rep,
            catalogo_escogido,
            canales,
            tr_canal,
            0,
            directorio_trabajo,
            0,
            banderas=banderas_externas,
        )
        QMessageBox.information(None, "Aviso", "Reporte generado\n" + archivo_rep)
    else:
        QMessageBox.information(None, "Aviso", "Reporte no generado")
    return


def generar_reporte_acelerograma(eventos, indice, catalogo, evento_escogido, archivo_escogido):
    """
    Abre el selector de estaciones acelerográficas y genera los reportes
    individuales de acelerogramas para el evento escogido.
    """
    if not eventos or indice >= len(eventos) or not evento_escogido or not evento_escogido[0]:
        QMessageBox.information(None, "Aviso", "No hay un evento válido seleccionado.")
        return

    tipo_ev_acel = str(eventos[indice][2]).strip() if len(eventos[indice]) > 2 else ""
    if tipo_ev_acel in ("Ruido", "CONTROL"):
        QMessageBox.information(
            None,
            "Aviso",
            f"Los eventos clasificados como '{tipo_ev_acel}' no generan reportes acelerográficos.",
        )
        return

    if tipo_ev_acel == 'Evento_local':
        stem_limpio = Path(str(eventos[indice][1]).strip()).stem.replace('_', '')
        if len(stem_limpio) == 12:
            fecha = "20" + stem_limpio
        else:
            fecha = stem_limpio[:14]
        mensaje = (
            fecha,
            int(fecha[:4]),
            int(fecha[4:6]),
            int(fecha[6:8]),
            int(fecha[8:10]),
            int(fecha[10:12]),
            int(fecha[12:14]),
            0, 0, "", "", "", "", "", "", "", "", "RSA", "", "Evento Local"
        )
        Subventana_aceleraciones(archivo_escogido, mensaje, eventos[indice]).exec_()
        return

    catalogo_escogido = _filtrar_catalogo_evento(catalogo, evento_escogido[0][1])

    if not catalogo_escogido:
        tipo_ev = str(evento_escogido[0][2]).strip() if len(evento_escogido[0]) > 2 else ""
        if tipo_ev in ("FF", "FC"):
            QMessageBox.information(
                None,
                "Aviso",
                f"El evento está marcado como {tipo_ev} y debe estar vinculado a un evento de Otras Redes (IGEPN / USGS) para generar un reporte.",
            )
        else:
            QMessageBox.information(None, "Aviso", "No hay información del evento en el catálogo")
        return

    catalogo_data = catalogo_escogido[0] if catalogo_escogido[0] else catalogo_escogido[1]
    Subventana_aceleraciones(archivo_escogido, catalogo_data, eventos[indice]).exec_()
