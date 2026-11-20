# `rsa_sismologia/nidaq` — Adquisición de Datos con Hardware National Instruments (NI-DAQmx)

Proyecto independiente dedicado a software de adquisición, instrumentación y calibración con tarjetas **National Instruments** (actualmente **NI-USB-6210** y futuros proyectos NI-DAQ).

## Entorno de ejecución
* **Entorno virtual**: `C:\entornos\estructuras` (Python 3.13)
* **Dependencias principales**: `nidaqmx`, `PySide6`, `pyqtgraph`, `numpy`

## Contenido principal
* `adquisicion_galgas_potenciometros.py` — Software de calibración de sensor de presión (Puente de Wheatstone 8 V + INA114AP + NI-USB-6210).
* `lanzar_adquisicion_estructuras.bat` — Lanzador por lotes (doble clic para ejecutar con `C:\entornos\estructuras`).
* `import nidaqmx.py` — Pruebas base de lectura multicanal NI-DAQmx.
* `secuencias_calibracion/` — Sesiones y archivos CSV generados.
