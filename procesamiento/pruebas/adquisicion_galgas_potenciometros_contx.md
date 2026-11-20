---
proyecto: rsa_sismologia
tipo: contexto_tecnico
archivo: pruebas/adquisicion_galgas_potenciometros.py
temas: [calibracion_100_toneladas, sensor_presion, puente_wheatstone_8v, ina114ap, ni_usb_6210, fondo_escala_4_75_a_4_95v, osciloscopio_0_5s, multimetro_2_0s, grabacion_dual, secuencia_real_fs, secuencia_promedios_calibracion, escalabilidad_amplitud_tiempo, gestion_por_sesiones, trazabilidad_csv]
generado: 2026-11-19
---

# `pruebas/adquisicion_galgas_potenciometros.py` — Contexto Técnico para Agentes IA

> Software especializado de calibración y certificación para prensas hidráulicas y bancos de ensayo de hasta **$100\text{ Toneladas}$**. Instrumenta un sensor de presión basado en puente de Wheatstone ($8.0\text{ V}$) y preamplificador **INA114AP** con la tarjeta **National Instruments NI-USB-6210** (16 bits, `ai0` y `ai1` en modo DIFERENCIAL, `ai2+` en modo SINGLE-ENDED).
> 
> **Característica Clave Metrológica**: **Grabación Dual Simultánea**:
> 1. **Secuencia de Calibración (Promedios Integrados)**: Genera 1 muestra cada $0.5\text{ s}$ (osciloscopio) o $2.0\text{ s}$ (multímetro) para comparación limpia y cálculo de regresión con manómetro patrón.
> 2. **Secuencia Real en Bruto (Alta Velocidad a $F_s$)**: Graba **cada una de las muestras adquiridas por el ADC** (a $1000\text{ Hz}$ o $F_s$ configurada), preservando transitorios rápidos, armónicos de bombas/engranes, rizado de aceite y picos instantáneos para auditoría y certificación.

**Ruta**: `c:/proyectos/rsa_sismologia/pruebas/adquisicion_galgas_potenciometros.py`  
**Lanzador por lotes**: `c:/proyectos/rsa_sismologia/pruebas/lanzar_adquisicion_estructuras.bat`  
**Directorio Base de Ensayos**: `c:/proyectos/rsa_sismologia/pruebas/secuencias_calibracion/`  
**Estructura de Almacenamiento**: `secuencias_calibracion/sesion_YYYYMMDD_HHMMSS_<Etiqueta>/`  
**LOC**: ~2120 | **Lenguaje**: Python 3.13.11  
**Entorno de Ejecución**: `C:\entornos\estructuras`  
**Hardware Principal**: National Instruments **NI-USB-6210**  
**Dependencias**: `nidaqmx` (1.4.1), `PySide6` (6.10.2), `pyqtgraph` (0.14.0), `numpy` (2.4.3)  
**Ejecución**: Standalone GUI (`& "C:\entornos\estructuras\Scripts\python.exe" "pruebas/adquisicion_galgas_potenciometros.py"` o doble clic en `.bat`)  

---

## 1. Arquitectura de Grabación Dual Simultánea

Durante cualquier ensayo o secuencia iniciada, la aplicación genera dos flujos de datos y archivos CSV en paralelo:

```text
secuencias_calibracion/sesion_YYYYMMDD_HHMMSS_<Etiqueta>/
├── manifiesto_sesion.txt
├── ensayo_0_a_100_ton_001_YYYYMMDD_HHMMSS_calibracion_promedios_0.5s.csv
├── ensayo_0_a_100_ton_001_YYYYMMDD_HHMMSS_muestreo_real_fs1000Hz.csv
└── calibracion_patron_YYYYMMDD_HHMMSS.csv
```

### A. Secuencia 1: Calibración por Promedios de Bloque
* **Tasa de Registro**: 1 fila cada $T_{\text{ventana}}$ ($0.5\text{ s}$ en osciloscopio, $2.0\text{ s}$ en multímetro).
* **Propósito**: Señal filtrada mediante integración boxcar (filtro sinc natural) libre de rizado de motor y pulsaciones mecánicas para certificación y ajuste de curva contra manómetro patrón.
* **Columnas**:
  * `Tiempo_s` (tiempo transcurrido del ensayo).
  * `Voltaje_ai0_DIFF_V` (promedio del bloque con tara descontada).
  * `Carga_Calculada_Ton` (tonelaje calculado según referencia fijada).
  * `Tension_Puente_ai0_mV` (tensión de entrada del puente $V_{in} = V_{out} / G$).
  * `Sensibilidad_ai0_mV_V` ($mV/V$ con respecto a $V_{exc} = 8.0\text{ V}$).
  * `ai1_DIFF_V`, `ai2_RSE_V`, etc. (promedios de canales activos).
  * `Ruido_Vpp_mV`, `Desv_Estandar_mV` (estadísticas internas del bloque).

### B. Secuencia 2: Muestreo Real en Bruto a Frecuencia de Tarjeta ($F_s$)
* **Tasa de Registro**: Muestra por muestra a la frecuencia exacta del reloj de hardware ($F_s$, por defecto $1000\text{ Hz} \implies 1000\text{ filas/s}$).
* **Propósito**: Trazabilidad física absoluta. Almacena el perfil dinámico de la prensa: armónicos de bomba hidráulica, variaciones de presión por pistones, transitorios de válvulas de alivio y el escalón real de 0 a 100 Toneladas.
* **Columnas**:
  * `Indice_Muestra` (contador acumulativo de muestras de hardware: 0, 1, 2, ...).
  * `Tiempo_Hardware_s` (timestamp temporal exacto $t_i = t_{\text{bloque}} + i \cdot \frac{1}{F_s}$).
  * `Voltaje_ai0_DIFF_V` (voltaje instantáneo adquirido por el convertidor A/D).
  * `Carga_Instantanea_Ton` (tonelaje instantáneo punto a punto).
  * `ai1_DIFF_V`, `ai2_RSE_V`, etc. (voltajes instantáneos de los demás canales).

---

## 2. Metodología de Calibración de 100 Toneladas

1. **Ajuste de Fondo de Escala ($100\text{ Toneladas} \rightarrow 4.75\text{ V}$ a $4.95\text{ V}$)**:
   * Carga nominal en prensa a $100\text{ Toneladas}$.
   * Se ajusta $R_G$ del INA114AP hasta que el semáforo visual se coloque en **VERDE** ($4.75\text{ V} \le V \le 4.95\text{ V}$).
   * Se ingresa el valor medido de $R_G$ colocada ($\Omega$) y se pulsa `📌 Fijar Referencia de Fondo de Escala (100 Ton)`.
2. **Ensayo de Calibración en Osciloscopio ($0 \rightarrow 100\text{ Toneladas}$)**:
   * Con la prensa en cero (tara aplicada), se presiona `▶ Iniciar Ensayo (0 a 100 Ton)`.
   * Se genera la grabación dual: archivo de promedios ($0.5\text{ s}$) y archivo en bruto ($1000\text{ Hz}$).
   * El osciloscopio en tiempo real permite graficar en Toneladas o Voltios y escalar libremente en Amplitud (Auto Y, Presets, Manual) y Tiempo (Global o Ventana Deslizante).
3. **Modo Multímetro & Cotejo con Manómetro Patrón**:
   * Promedios estables de $2.0\text{ s}$ para lectura humana cómoda.
   * Registro de pares patrón ($P_{\text{patrón}}$ vs $V_{\text{medido}}$), regresión lineal $P = m \cdot V + b$, cálculo de $R^2$ y guardado con un clic en la carpeta de la sesión.

---

## 3. Configuración de Hardware NI-USB-6210

* **`ai0`**: **DIFERENCIAL (`TerminalConfiguration.DIFF`)** — Sensor de Presión con INA114AP (Pines AI 0 / AI 8).
* **`ai1`**: **DIFERENCIAL (`TerminalConfiguration.DIFF`)** — Galga / Puente Auxiliar (Pines AI 1 / AI 9).
* **`ai2` a `ai7`**: **SINGLE-ENDED (`TerminalConfiguration.RSE`)** — Entradas referenciadas a AI GND.
