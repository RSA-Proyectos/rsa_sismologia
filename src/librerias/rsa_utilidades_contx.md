---
proyecto: rsa_sismologia
tipo: contexto_tecnico
archivo: src/librerias/rsa_utilidades.py
temas: [utilidades_sismologicas, generacion_sis, resolucion_rutas, remuestreo_64hz, binarios_rsa]
generado: 2026-08-24
---

# `src/librerias/rsa_utilidades.py` — Contexto Técnico para Agentes IA

> Módulo transversal de utilidades sismológicas de bajo nivel: resolución heurística de rutas del repositorio `DIA`, conversión de series de tiempo a formato binario `.sis` (remuestreadas a 64 Hz para eventos de tipo `SISMO`), conversión binaria a MiniSEED y creación de estructuras de carpetas.

**Ruta**: `src/librerias/rsa_utilidades.py`  
**Lenguaje**: Python 3 (ObsPy, SciPy Signal, NumPy)  
**Dependencias**: `obspy`, `scipy.signal`, `numpy`, `pathlib.Path`, `re`  
**Proceso**: Invocado como soporte de bajo nivel por `extraer_integrado.py`, `rsa_procesamiento.py` y `metodos_gestion.py`.

---

## 1. Arquitectura y Flujo de Procesamiento

```mermaid
graph TD
    A[Cualquier ruta de archivo o subcarpeta bajo DIA] --> B[referencia_directorio_completa]
    B --> C{Extracción de Fecha YYYYMMDD}
    C -->|Por nombre de archivo| D[Regex 20\\d{6}]
    C -->|Por carpetas DIA/YYYY/YYYY_MM/YYYY_MM_DD| E[Desglose de partes de ruta]
    D --> F[Ruta Canónica .../DIA/AAAAMMDD000000]
    E --> F
    
    G[Evento tipo SISMO en extraccion] --> H[Lectura MiniSEED por estación analógica]
    H --> I[Remuestreo con scipy.signal.resample a 64 Hz]
    I --> J[Ajuste de muestras y ensamblaje con cabecera_sismo]
    J --> K[Generación de archivo binario AAAAMMDD_hhmmss.sis]
```

---

## 2. Contratos de Datos y E/S

* **Función `referencia_directorio_completa(archivo) -> str`**:
  * Entrada: Ruta arbitraria de archivo (ej. `C:/DIA/2026/2026_08/2026_08_24/mseed/registros/LABR_20260824.mseed`).
  * Salida: Ruta canónica sin extensión `C:/DIA/20260824000000`.

* **Generación de Archivo `.sis` (`extraccion`)**:
  * Solo se construye si `tipo_evento == "SISMO"`.
  * Busca la cabecera binaria en candidatos: `directorios['Directorio_trabajo']/cabecera_sismo`, `datos/cabecera_sismo`, `C:/DIA/cabecera_sismo`.
  * Remuestrea canales analógicos a 64 Hz con enteros de 32 bits (`int32`).

* **Función `obtener_datos_reporte(fecha_ini, fecha_fin, directorio_trabajo, mapa_="Ecuador", tipo_forzado=None)`**:
  * Resuelve el título descriptivo (`periodo_reporte`), la carpeta base unificada (`directorio_reporte`) y el prefijo de archivo (`archivo_reporte`) para reportes acumulados:
    * **Tipo `0` (Anual)**: `DIA/<AAAA>/reportes/<Región>/<AAAA>_*`
    * **Tipo `1` (Mensual)**: `DIA/<AAAA>/<AAAA_MM>/reporte/<Región>/<Mes> del <AAAA>_*`
    * **Tipo `2` (Semanal ISO)**: `DIA/<AAAA_fin>/reportes/semanal/semana<WW>/<Región>/Semana <WW>_*`
    * **Tipo `3` (Período / Rango de Fechas)**: `DIA/<AAAA_fin>/reportes/periodos/<AAAA_MM_DD_ini>_<AAAA_MM_DD_fin>/<Región>/<dd_mm_aaaa a dd_mm_aaaa>_*` (unificado para cualquier rango de fechas, sea dentro del mismo mes, entre meses o multianual).
  * Admite `tipo_forzado` (`0..3`) para respetar explícitamente el RadioButton seleccionado por el usuario en `reporte_acumulado.py`.

---

## 3. Componentes y Métodos Clave

| Función | Firma | Descripción |
|---|---|---|
| `referencia_directorio_completa` | `(archivo) -> str` | Resuelve la ruta canónica `DIA/AAAAMMDD000000` extrayendo la fecha por regex o desglose jerárquico. |
| `extraccion` | `(t_ini, t_fin, canales, tipo_evento, directorios, parametros, ...)` | Recorta trazas sísmicas, genera MiniSEED de eventos y emite `.sis` binario para sismos. |
| `binario_a_mseed` | `(ruta_binario, ruta_salida, ...)` | Convierte registros binarios directos a archivos MiniSEED con metadatos de traza. |
| `ubicacion` | `(latitud, longitud) -> str` | Calcula la distancia y referencia geográfica respecto al catálogo `datos/poblaciones.csv`. |
| `obtener_datos_reporte` | `(fecha_ini, fecha_fin, directorio_trabajo, mapa_="Ecuador", tipo_forzado=None)` | Unifica las rutas de guardado para reportes anuales (`0`), mensuales (`1`), semanales (`2`) y por rango de fechas (`3`). Reconoce automáticamente unidades completas cuando `tipo_forzado=None`. |
| `generar_directorios_unidades_basicas` | `(fecha_ini, fecha_fin, directorio_trabajo, verificar_existencia=False, detallar=False, nivel_maximo="ANIO")` | Descompone jerárquicamente cualquier rango `[fecha_ini, fecha_fin]` en unidades básicas (`días -> semanas -> meses -> años -> meses -> semanas -> días`), verificando opcionalmente la existencia de `<prefijo>_cat.csv` en disco con *fallback* automático al nivel inferior. |
| `consolidar_archivos_periodo_ecuador` | `(fecha_ini, fecha_fin, directorio_trabajo, tipo_forzado=None, nivel_maximo="DIA")` | Reconstruye y escribe en `Ecuador` todos los archivos consolidados de un período (`_cat.csv`, `_rep.csv`, `_res.csv`, `_rep_total.csv`, `.xml` y CSVs SIG) sin generar PDFs. |
| `actualizar_periodos_emitidos_desde_fecha` | `(fecha_referencia, directorio_trabajo)` | Propaga automáticamente en cascada (`Semana ISO -> Mes -> Año`) cualquier modificación de un día hacia los períodos cuyos archivos `_cat.csv` ya hayan sido emitidos en `Ecuador`. |

---

## 4. Decisiones de Diseño y Algoritmos

1. **Resolución Heurística y Robusta de Fechas**:
   * `referencia_directorio_completa` implementa búsqueda múltiple: primero inspecciona el stem del archivo buscando patrones `20\d{6}`, luego itera de forma inversa por las carpetas secundarias, asegurando compatibilidad con estructuras planas o anidadas.
2. **Localización de `cabecera_sismo`**:
   * Búsqueda en cascada en directorios de trabajo, datos del proyecto y raíz `C:/DIA` para garantizar la generación del binario `.sis` en cualquier estación de trabajo.
3. **Copia Segura de Streams**:
   * Antes de mutar componentes o ejecutar `detrend`, se genera `stcanal = stcanal.copy()` previniendo corrupción de trazas en memoria compartida.

---

## 5. Riesgos Técnicos y Deuda Técnica

* **Índices de Canales Analógicos Fuera de Rango**:
  * Se aplica guarda `min(max(0, componente), len(stcanal) - 1)` para evitar excepciones `IndexError` si una estación tiene menos canales de los esperados.

---

## 6. Checklist de Verificación y Regresión

- [x] `referencia_directorio_completa` resuelve correctamente nombres de archivo con guiones o prefijos.
- [x] Generación de `.sis` solo ocurre para tipo `SISMO` y omite eventos de ruido o calibración.
- [x] Remuestreo a 64 Hz produce tamaño exacto de muestras con padding en caso de discrepancias mínimas.
