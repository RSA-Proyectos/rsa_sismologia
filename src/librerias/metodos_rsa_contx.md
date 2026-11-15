---
proyecto: rsa_sismologia
tipo: contexto_tecnico
archivo: src/librerias/metodos_rsa.py
temas: [procesamiento_sismologico, filtros_obspy, graficos_multicanal, carga_streams, miniseed]
generado: 2026-08-24
---

# `src/librerias/metodos_rsa.py` — Contexto Técnico para Agentes IA

> Librería central de procesamiento sismológico, renderizado gráfico multicanal con Matplotlib/ObsPy, filtrado Butterworth interactivo, carga y manipulación de streams MiniSEED continuos y por eventos.

**Ruta**: `src/librerias/metodos_rsa.py`  
**Lenguaje**: Python 3 (ObsPy, Matplotlib, NumPy)  
**Dependencias**: `obspy`, `matplotlib.figure.Figure`, `numpy`, `librerias.metodos_gestion`  
**Proceso**: Invocado por los subprogramas de extracción, marcado, fases y reportes sismológicos.

---

## 1. Arquitectura y Flujo de Procesamiento Sismológico

```mermaid
graph TD
    A[Streams MiniSEED: Registro Continuo o Eventos] --> B[cargar_dia / cargar_evento]
    B --> C[Aplicación de Filtros: filtro_evento con Butterworth pasa-banda]
    C --> D[Renderizado Gráfico: grafico_evento_int / imprimir_plt]
    D --> E[Visualizador Matplotlib en Canvas de Subprograma]
    
    E --> F[Interacción de Fases y Marcas de Tiempo]
    F --> G[Exportación de Señales a CSV o Formatos Externos]
```

---

## 2. Contratos de Datos y E/S

* **Formato de Filtros (`filtro_evento`)**:
  * Entrada: Stream de ObsPy y cadena de 6 caracteres `OOFFSS` (ej. `"040210"` para Orden 4, pasa-banda 2 Hz a 10 Hz; `"000000"` para omitir filtrado).
  * Salida: Stream filtrado con detrending y remoción de media aplicados.

* **Parámetros de `grafico_evento_int`**:
  * `visor`: Eje o figura de Matplotlib donde se realiza el trazado.
  * `stLeido`: Lista/Stream de trazas de sismogramas.
  * `t_inicio`, `t_final`: Ventana temporal UTC a graficar.
  * `estaciones_eventos`: Lista de índices de estaciones seleccionadas.
  * `hab_grafico`: Diccionario o lista con banderas `'1'`/`'0'` de habilitación visual.
  * `bandera_marcas`: Control de visualización de marcas de fases sismológicas.
  * `pagina`: Control de paginación para despliegues de múltiples canales.

---

## 3. Componentes y Métodos Clave

| Función | Firma | Descripción |
|---|---|---|
| `grafico_evento_int` | `(visor, stLeido, t_inicio, t_final, estaciones_eventos, hab_grafico, bandera_marcas, pagina)` | Dibuja en Matplotlib las trazas sismológicas multicanal normalizadas con etiquetas y tiempos. |
| `filtro_evento` | `(stream, filtro_str)` | Aplica filtro Butterworth pasa-banda (desempaquetando `OOFFSS`) usando ObsPy. |
| `cargar_evento` | `(parametro, eventos_reporte, catalogo, eventos, ...)` | Carga y recorta trazas MiniSEED correspondientes a un evento específico del catálogo, soportando nombres de 12 y 14 dígitos e índices numéricos o de texto en `eventos_reporte`. |
| `cargar_dia` | `(directorios)` | Carga consolidada de los eventos, catálogo (`_cat.csv`), resumen (`_rep.csv`, `_res.csv`, `_resp.csv`) y XML del día, preservando e insertando los registros de otras redes (`Id[-2:] != '00'`) inmediatamente debajo de su evento `.sis` asociado. |
| `insertar_evento_otras_redes` | `(catalogo, indice_catalogo, eventos_reporte, ...)` | Parsea boletines de `IGEPN`, `USGS` u `Otras redes`, asigna `latitud` en la columna `7` y `longitud` en la columna `8`, calcula epicentro con `ubicacion(latitud, longitud)` y actualiza `catalogo` y `eventos_reporte` sin duplicados. |
| `consultar_sismos_igepn_web` / `consultar_sismos_usgs_api` | `(...)` | Consultan en línea la tabla HTML de Últimos Sismos del IGEPN (`portal/sismos/index2.html`) y el servicio FDSN GeoJSON de la USGS (`earthquake.usgs.gov/fdsnws/event/1/query`) devolviendo registros normalizados. |
| `buscar_evento_otra_red_en_linea` | `(nombre_sis, catalogo, red_nombre, tolerancia_seg=60)` | Busca en línea un evento particular de la RSA (priorizando la hora origen en `catalogo` o la marca del `.sis` para eventos `FF`/`FC`) dentro de `±60 s` y retorna el texto preformateado y el tipo de magnitud. |
| `sincronizar_otras_redes_dia` | `(directorios, catalogo, eventos_reporte, eventos, tolerancia_seg=60)` | Cruza de forma automática y transparente todos los eventos `SISMO`, `FF` y `FC` del día contra IGEPN y USGS (`Δt ≤ 60 s`), integrando las coincidencias en `catalogo` y `eventos_reporte` sin intervención del usuario. |
| `imprimir_plt` | `(...)` | Genera y guarda representaciones gráficas vectoriales y rasterizadas para informes PDF. |
| `guardar_seniales_csv`| `(...)` | Exporta las series temporales de un evento sismológico a archivos CSV. |
| `recolectar_evt` / `extraer_kinemetrics_evt` | `(...)` | Manejo y extracción de datos en formato Kinemetrics EVT hacia MiniSEED. |

---

## 4. Decisiones de Diseño y Algoritmos

1. **Normalización y Trazado Robusto**:
   * `grafico_evento_int` ajusta los offsets verticales de cada canal dinámicamente según la amplitud máxima local, evitando traslapes destructivos entre trazas continuas.
   * Los títulos por estación (`fontsize=8, pad=2`), etiquetas de marcas temporales (`labelsize=7, pad=1`) y márgenes (`subplots_adjust`) están calibrados para mantener legibilidad en pantallas pequeñas sin solapamiento entre los 6 subgráficos apilados.
2. **Filtrado Eficiente de Señales**:
   * Previo al filtrado pasa-banda, se ejecuta `detrend("demean")` y `detrend("linear")` para estabilizar la línea base de los sismogramas y mitigar efectos de borde en la convolución.
3. **Mapeo Seguro de Tiempos UTC y Carga Silenciosa (`cargar_dia`)**:
   * Uso sistemático de `obspy.UTCDateTime` para operaciones aritméticas sobre fechas y marcas sismológicas.
   * `cargar_dia` evalúa los eventos `SISMO` sin desplegar ventanas emergentes (`QMessageBox`) bloqueantes por cada evento pendiente (`No procesado`), delegando la indicación de estado al sistema de colores del módulo de procesamiento.

---

## 5. Riesgos Técnicos y Deuda Técnica

* **Uso de Memoria en Carga Masiva de Streams**:
  * `cargar_dia` carga archivos MiniSEED de 24h a memoria. Es indispensable procesar copias y liberar referencias cuando se procesan lotes extensos.
* **Manejo de Gaps y Muestreo No Homogéneo**:
  * Si un stream contiene discontinuidades (*gaps*), debe ser consolidado o fusionado antes de pasar a filtrado.

---

## 6. Checklist de Verificación y Regresión

- [x] `grafico_evento_int` recibe `t_inicio` y `t_final` explícitos sin colapsar en eventos vacíos.
- [x] `filtro_evento` parsea correctamente cadenas de 6 dígitos sin arrojar excepción con `"000000"`.
- [x] Trazado multicanal respeta la bandera de visibilidad `hab_grafico`.
- [x] Compatibilidad verificada con `Extraer_evento`, `Marcar_evento` y `Procesamiento_evento`.
