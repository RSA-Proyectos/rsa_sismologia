# -*- coding: utf-8 -*-
"""
Subprograma de Reconstrucción de Eventos por Período (Menú Ingreso de Datos).

Recorre un rango de fechas dentro del directorio de trabajo (DIA) y, para cada día
donde existan AAAAMMDD_aux.csv, AAAAMMDD000000.csv y registros continuos en
mseed/registros/, reextrae los eventos (.mseed y .sis) usando las ventanas de tiempo
de AAAAMMDD_aux.csv pero respetando la clasificación definitiva y los tokens
EEEECBFFIISS de AAAAMMDD000000.csv.
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path


def extraer_hasta_directorio(ruta_completa, nombre_directorio):
    partes = Path(ruta_completa).parts
    if nombre_directorio in partes:
        indice = partes.index(nombre_directorio)
        ruta_recortada = Path(*partes[:indice + 1])
        return str(ruta_recortada) + '/'
    return ''


ruta_actual = os.path.dirname(__file__)
ruta_proyecto = extraer_hasta_directorio(ruta_actual, 'procesamiento')
ruta_librerias = os.path.abspath(os.path.join(ruta_proyecto, 'src', 'librerias'))
ruta_datos = os.path.abspath(os.path.join(ruta_proyecto, 'datos'))

if ruta_librerias not in sys.path:
    sys.path.insert(0, ruta_librerias)

from PyQt5 import uic
from PyQt5.QtCore import QDate, QThread, pyqtSignal
from PyQt5.QtWidgets import QMainWindow, QMessageBox

from metodos_gestion import parametros_estaciones
from rsa_io import lectura_archivo
from rsa_procesamiento import reconstruir_eventos_dia


class HiloReconstruccionPeriodo(QThread):
    """Hilo de trabajo para reconstruir eventos día a día sin bloquear la interfaz."""

    progreso_dia = pyqtSignal(int, int, str)
    progreso_evento = pyqtSignal(int, int, str)
    mensaje_bitacora = pyqtSignal(str)
    finalizado = pyqtSignal(dict)

    def __init__(
        self,
        directorio_trabajo,
        fecha_ini,
        fecha_fin,
        responsable,
        sobrescribir_existentes=True,
        solo_presentes_en_csv=True,
        reconstruir_sis=False,
        parent=None,
    ):
        super().__init__(parent)
        self.directorio_trabajo = str(directorio_trabajo).rstrip('/\\') + '/'
        self.fecha_ini = fecha_ini
        self.fecha_fin = fecha_fin
        self.responsable = responsable or 'RSA'
        self.sobrescribir_existentes = bool(sobrescribir_existentes)
        self.solo_presentes_en_csv = bool(solo_presentes_en_csv)
        self.reconstruir_sis = bool(reconstruir_sis)
        self._cancelado = False

    def solicitar_cancelacion(self):
        self._cancelado = True

    def esta_cancelado(self):
        return self._cancelado

    def run(self):
        total_dias = (self.fecha_fin - self.fecha_ini).days + 1
        resumen_global = {
            'total_dias': total_dias,
            'dias_reconstruidos': 0,
            'dias_omitidos': 0,
            'dias_error': 0,
            'eventos_reconstruidos': 0,
            'mseed_generados': 0,
            'sis_generados': 0,
            'ruido_omitidos': 0,
            'cancelado': False,
        }

        try:
            parametros = parametros_estaciones()
            estaciones_analogicas = lectura_archivo(os.path.join(ruta_datos, 'analogicas.csv')) or []
        except Exception as e_cfg:
            self.mensaje_bitacora.emit(f"[ERROR] No se pudieron cargar parámetros de estaciones: {e_cfg}")
            self.finalizado.emit(resumen_global)
            return

        fecha_actual = self.fecha_ini
        indice_dia = 0

        while fecha_actual <= self.fecha_fin:
            if self._cancelado:
                resumen_global['cancelado'] = True
                self.mensaje_bitacora.emit("⚠ Proceso cancelado por el usuario.")
                break

            indice_dia += 1
            fecha_str = fecha_actual.strftime('%Y-%m-%d')
            self.progreso_dia.emit(indice_dia, total_dias, fecha_str)

            archivo_dia = os.path.join(
                self.directorio_trabajo,
                fecha_actual.strftime('%Y%m%d000000'),
            )

            def _cb_evento(ev_act, ev_tot, nombre_ev):
                self.progreso_evento.emit(ev_act, ev_tot, nombre_ev)

            try:
                res_dia = reconstruir_eventos_dia(
                    archivo=archivo_dia,
                    responsable=self.responsable,
                    sobrescribir_existentes=self.sobrescribir_existentes,
                    solo_presentes_en_csv=self.solo_presentes_en_csv,
                    reconstruir_sis=self.reconstruir_sis,
                    parametros=parametros,
                    estaciones_analogicas=estaciones_analogicas,
                    progreso_callback=_cb_evento,
                    cancelar_callback=self.esta_cancelado,
                )

                estado = res_dia.get('estado', 'omitido')
                if estado == 'ok':
                    resumen_global['dias_reconstruidos'] += 1
                    resumen_global['eventos_reconstruidos'] += res_dia.get('eventos_reconstruidos', 0)
                    resumen_global['mseed_generados'] += res_dia.get('mseed_generados', 0)
                    resumen_global['sis_generados'] += res_dia.get('sis_generados', 0)
                    resumen_global['ruido_omitidos'] += res_dia.get('ruido_omitidos', 0)
                    self.mensaje_bitacora.emit(
                        f"✓ {fecha_str}: {res_dia['eventos_reconstruidos']} eventos "
                        f"({res_dia['mseed_generados']} .mseed, {res_dia['sis_generados']} .sis, "
                        f"{res_dia['ruido_omitidos']} ruido)"
                    )
                elif estado == 'cancelado':
                    resumen_global['cancelado'] = True
                    self.mensaje_bitacora.emit(f"⚠ {fecha_str}: cancelado por el usuario.")
                    break
                else:
                    resumen_global['dias_omitidos'] += 1
                    self.mensaje_bitacora.emit(f"  - {fecha_str}: omitido ({res_dia.get('motivo', '')})")

            except Exception as e_dia:
                resumen_global['dias_error'] += 1
                self.mensaje_bitacora.emit(f"❌ {fecha_str}: error inesperado -> {e_dia}")

            fecha_actual += timedelta(days=1)

        self.finalizado.emit(resumen_global)


class Reconstruccion_eventos(QMainWindow):
    """Ventana de reconstrucción masiva de eventos por período."""

    cerrado = pyqtSignal()

    def __init__(self, archivo, directorio_trabajo, responsable, horario, parent=None):
        super().__init__(parent)
        ruta_ui = os.path.abspath(os.path.join(ruta_proyecto, 'src', 'ui', 'reconstruccion_eventos.ui'))
        uic.loadUi(ruta_ui, self)

        self.archivo = archivo
        if directorio_trabajo and os.path.exists(directorio_trabajo):
            self.directorio_trabajo = str(directorio_trabajo).rstrip('/\\') + '/'
        elif os.path.exists('C:/DIA'):
            self.directorio_trabajo = 'C:/DIA/'
        else:
            self.directorio_trabajo = str(directorio_trabajo or 'C:/DIA/')
        self.responsable = responsable or 'RSA'
        self.horario = horario
        self.hilo_trabajo = None

        self.lbl_directorio_valor.setText(self.directorio_trabajo)

        hoy = QDate.currentDate()
        self.dateEdit_inicio.setDate(hoy.addDays(-30))
        self.dateEdit_fin.setDate(hoy)

        self.btn_reconstruir.clicked.connect(self.iniciar_reconstruccion)
        self.btn_cancelar.clicked.connect(self.cancelar_reconstruccion)
        self.btn_salir.clicked.connect(self.close)

    def _agregar_log(self, texto):
        self.txt_bitacora.appendPlainText(texto)

    def _establecer_estado_ejecucion(self, ejecutando):
        self.dateEdit_inicio.setEnabled(not ejecutando)
        self.dateEdit_fin.setEnabled(not ejecutando)
        self.chk_solo_en_csv.setEnabled(not ejecutando)
        self.chk_sobrescribir.setEnabled(not ejecutando)
        self.chk_reconstruir_sis.setEnabled(not ejecutando)
        self.btn_reconstruir.setEnabled(not ejecutando)
        self.btn_cancelar.setEnabled(ejecutando)
        self.btn_salir.setEnabled(not ejecutando)

    def iniciar_reconstruccion(self):
        f_ini = self.dateEdit_inicio.date().toPyDate()
        f_fin = self.dateEdit_fin.date().toPyDate()

        if f_ini > f_fin:
            QMessageBox.warning(
                self,
                "Rango de fechas inválido",
                "La fecha de INICIO no puede ser posterior a la fecha de FIN.",
            )
            return

        if not os.path.isdir(self.directorio_trabajo):
            QMessageBox.warning(
                self,
                "Directorio no disponible",
                f"El directorio de trabajo no existe:\n{self.directorio_trabajo}",
            )
            return

        total_dias = (f_fin - f_ini).days + 1
        self.txt_bitacora.clear()
        self._agregar_log(
            f"=== RECONSTRUCCIÓN DE EVENTOS POR PERÍODO ===\n"
            f"Directorio: {self.directorio_trabajo}\n"
            f"Período: {f_ini.strftime('%d/%m/%Y')} al {f_fin.strftime('%d/%m/%Y')} ({total_dias} días)\n"
            f"Solo presentes en AAAAMMDD000000.csv: {'Sí' if self.chk_solo_en_csv.isChecked() else 'No'}\n"
            f"Sobrescribir existentes: {'Sí' if self.chk_sobrescribir.isChecked() else 'No'}\n"
            f"Reconstruir archivos .sis: {'Sí' if self.chk_reconstruir_sis.isChecked() else 'No'}\n"
            f"---------------------------------------------"
        )

        self.barra_progreso_dias.setMaximum(total_dias)
        self.barra_progreso_dias.setValue(0)
        self.barra_progreso_eventos.setMaximum(1)
        self.barra_progreso_eventos.setValue(0)
        self.lbl_estado_actual.setText("Iniciando reconstrucción...")
        self._establecer_estado_ejecucion(True)

        self.hilo_trabajo = HiloReconstruccionPeriodo(
            directorio_trabajo=self.directorio_trabajo,
            fecha_ini=f_ini,
            fecha_fin=f_fin,
            responsable=self.responsable,
            sobrescribir_existentes=self.chk_sobrescribir.isChecked(),
            solo_presentes_en_csv=self.chk_solo_en_csv.isChecked(),
            reconstruir_sis=self.chk_reconstruir_sis.isChecked(),
            parent=self,
        )
        self.hilo_trabajo.progreso_dia.connect(self._actualizar_progreso_dia)
        self.hilo_trabajo.progreso_evento.connect(self._actualizar_progreso_evento)
        self.hilo_trabajo.mensaje_bitacora.connect(self._agregar_log)
        self.hilo_trabajo.finalizado.connect(self._al_finalizar_reconstruccion)
        self.hilo_trabajo.start()

    def _actualizar_progreso_dia(self, actual, total, fecha_str):
        self.barra_progreso_dias.setMaximum(max(1, total))
        self.barra_progreso_dias.setValue(actual)
        self.barra_progreso_eventos.setValue(0)
        self.lbl_estado_actual.setText(f"Procesando día {actual}/{total}: {fecha_str}")

    def _actualizar_progreso_evento(self, actual, total, nombre_ev):
        self.barra_progreso_eventos.setMaximum(max(1, total))
        self.barra_progreso_eventos.setValue(actual)
        self.lbl_estado_actual.setText(f"Reconstruyendo evento {actual}/{total}: {nombre_ev}")

    def cancelar_reconstruccion(self):
        if self.hilo_trabajo and self.hilo_trabajo.isRunning():
            self.hilo_trabajo.solicitar_cancelacion()
            self.btn_cancelar.setEnabled(False)
            self.lbl_estado_actual.setText("Cancelando al terminar el evento actual...")

    def _al_finalizar_reconstruccion(self, resumen):
        self._establecer_estado_ejecucion(False)
        estado_txt = "Cancelado por el usuario" if resumen.get('cancelado') else "Reconstrucción finalizada"
        self.lbl_estado_actual.setText(estado_txt)

        resumen_msg = (
            f"\n=== RESUMEN FINAL ({estado_txt}) ===\n"
            f"  • Días evaluados:       {resumen.get('total_dias', 0)}\n"
            f"  • Días reconstruidos:   {resumen.get('dias_reconstruidos', 0)}\n"
            f"  • Días omitidos:        {resumen.get('dias_omitidos', 0)}\n"
            f"  • Días con error:       {resumen.get('dias_error', 0)}\n"
            f"  • Eventos procesados:   {resumen.get('eventos_reconstruidos', 0)}\n"
            f"  • Archivos .mseed:      {resumen.get('mseed_generados', 0)}\n"
            f"  • Archivos .sis:        {resumen.get('sis_generados', 0)}\n"
            f"  • Eventos Ruido (sin extraer): {resumen.get('ruido_omitidos', 0)}"
        )
        self._agregar_log(resumen_msg)

        QMessageBox.information(
            self,
            "Reconstrucción de Eventos",
            f"{estado_txt}.\n\n"
            f"Días reconstruidos: {resumen.get('dias_reconstruidos', 0)} de {resumen.get('total_dias', 0)}\n"
            f"Eventos procesados: {resumen.get('eventos_reconstruidos', 0)}\n"
            f"Archivos .mseed generados: {resumen.get('mseed_generados', 0)}\n"
            f"Archivos .sis generados: {resumen.get('sis_generados', 0)}",
        )

    def limpiar_estado(self):
        if self.hilo_trabajo and self.hilo_trabajo.isRunning():
            self.hilo_trabajo.solicitar_cancelacion()
            self.hilo_trabajo.wait(5000)
        self.hilo_trabajo = None

    def closeEvent(self, event):
        self.limpiar_estado()
        self.cerrado.emit()
        event.accept()
