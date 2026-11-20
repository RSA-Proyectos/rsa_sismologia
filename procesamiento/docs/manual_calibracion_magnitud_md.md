# Manual de Usuario — Calibración de Magnitud de Duración ($M_d$) y Generación de `Mag2000.txt`

> **Ubicación en el sistema**: Menú **`Configuración → Calibración de Magnitud (Md — Mag2000.txt)`** en `programa_integrado.py` (disponible en Estado A, antes de inicializar un día).

---

## 1. Fundamento Sismológico

El sistema de localización **FASTHYPO / RSA** estima la magnitud de duración ($M_d$) de cada estación mediante la relación empírica de **Lee, Bennett y Meagher (1972)** (estandarizada por **IASPEI / NMSOP-2** e implementada en `Iaspei.frm` y `hypo/src/fasthypo.py`):

$$M_d = b_1 + c_1 \cdot \log_{10}(\tau) + c_2 \cdot \Delta$$

Donde:
* **$\tau$ (`Coda_s`)**: duración de la coda en segundos, medida siempre con el mismo criterio operativo de inicio y fin de señal.
* **$\Delta$ (`Dist_km`)**: distancia epicentral en kilómetros.
* **$b_1$**: constante de nivel base (absorbe sensibilidad instrumental y efecto de sitio).
* **$c_1$**: pendiente de crecimiento con la duración de coda (siempre positiva; normalmente entre `0.9` y `2.5`).
* **$c_2$**: corrección por atenuación con la distancia (pequeña y $\ge 0$, típicamente entre `0.0001` y `0.0035`).

Cada estación tiene su propia fila en **`Mag2000.txt`**:
```text
LABR 2.131382 0.975177 0.001410
CHAI 2.455171 0.924346 0.000099
```
Si una estación tiene `0.000000 0.000000 0.000000`, el sistema reportará `NMG` (sin magnitud) aunque se marque la coda.

---

## 2. Qué es un "Evento Bien Caracterizado"

Para que la regresión produzca coeficientes confiables y estables, conviene usar **al menos 20 a 50 sismos por estación** que cumplan:

1. **Referencia confiable de magnitud ($M_{\text{ref}}$)**:
   * **Prioridad 1 — USGS**: ideal para eventos regionales moderados ($M \ge 3.5$), con escalas globales consistentes ($M_w$, $m_b$).
   * **Prioridad 2 — IGEPN**: excelente para sismicidad nacional y regional del Ecuador ($M_L$, $M_{Lv}$).
   * **Prioridad 3 — RSA (Transferencia)**: útil para **calibrar estaciones nuevas** usando sismos locales bien registrados simultáneamente en una estación patrón ya calibrada (como `LABR`).
2. **Buena localización**: `RMS ≤ 0.35 s` y al menos `3` estaciones (preferiblemente $\ge 4$).
3. **Coda limpia**: sin superposición de otro sismo ni ruido antrópico (`5 s ≤ Coda ≤ 600 s`).
4. **Cobertura**: incluir tanto sismos pequeños como medianos y a distintas distancias (`1 km ≤ Dist ≤ 400 km`).

---

## 3. Procedimiento Paso a Paso

### Paso 1 — Recolectar el dataset (Pestaña 1)
1. Verifique el **Directorio `..\DIA\`** (se precarga desde `config_local_pc.json`).
2. Defina el rango de fechas (**Desde / Hasta**).
3. Elija la **Prioridad de Referencia** (recomendado: **`USGS > IGEPN > RSA`** o **`Solo USGS e IGEPN`**).
4. Ajuste los filtros de calidad (`RMS máx`, `Mín. Estaciones`, rango de Coda, Distancia y Magnitud).
5. Pulse **`🔍 Escanear Eventos en ..\DIA\`**.
   * El módulo cruza automáticamente los catálogos `*_cat.csv` (con los eventos cargados de USGS/IGEPN/RSA) con los archivos `.rsa` en `fastHypo/` para extraer `Dist_km` y `Coda_s` de cada estación.
   * También puede **importar un CSV externo** (`📂 Importar Dataset CSV`) o **exportar** el dataset recolectado (`💾 Exportar Dataset CSV`) para revisarlo en Excel.
6. Revise la tabla y **desmarque** cualquier lectura dudosa o atípica en la columna `Incluir`.

### Paso 2 — Calcular los coeficientes (Pestaña 2)
1. Deje activadas las opciones recomendadas:
   * **`Filtrar atípicos (|r| > 2σ)`**: descarta automáticamente hasta 2 rondas de outliers.
   * **`Restringir c₂ ≥ 0`**: evita pendientes de distancia físicamente negativas cuando el rango de distancias es estrecho.
   * *(Opcional)* **`Fijar c₂ = 0`**: útil para estaciones muy locales con poca variación de distancia.
2. Pulse **`📐 Calcular Coeficientes`**.
3. Revise el semáforo de calidad por estación:
   * **🟢 Óptimo**: $N \ge N_{\min}$, $R^2 \ge 0.75$, $\sigma \le 0.30$ y $c_1 > 0$.
   * **🟠 Aceptable**: $R^2 \ge 0.50$, $\sigma \le 0.45$ y $c_1 > 0$.
   * **🔴 Revisar ajuste / Pocas muestras**: recolecte más eventos o desmarque atípicos.

### Paso 3 — Inspeccionar las gráficas (Pestaña 3)
1. Seleccione cada estación en el desplegable superior.
2. Verifique:
   * **Gráfica izquierda ($M_d$ vs $M_{\text{ref}}$)**: los puntos (coloreados por fuente USGS/IGEPN/RSA) deben alinearse cerca de la recta `1:1` y dentro de la banda `±0.3`. Las `×` indican atípicos descartados.
   * **Gráfica derecha (Residuales vs Distancia)**: los residuales deben distribuirse alrededor de `0.0` sin tendencia inclinada con la distancia.

### Paso 4 — Generar `Mag2000.txt` y respaldos (Pestaña 2)
1. Si desea conservar intactas las estaciones que ya tenía configuradas y no fueron recalibradas en esta corrida, seleccione su **`Mag2000.txt` previo** en *Plantilla Mag2000.txt previa*.
2. Pulse **`💾 Generar Mag2000.txt, CSVs y Reporte Técnico...`** y seleccione la carpeta destino.
3. El módulo genera automáticamente:
   * **`Mag2000.txt`** (creando primero `Mag2000_respaldo_AAAAMMDD_HHMMSS.txt` si ya existía).
   * **`coeficientes_md_AAAAMMDD_HHMMSS.csv`** (resumen estadístico completo por estación).
   * **`dataset_calibracion_md_AAAAMMDD_HHMMSS.csv`** (todas las lecturas y fuentes usadas).
   * **`reporte_calibracion_md_AAAAMMDD_HHMMSS.txt`** (bitácora auditable de parámetros y resultados).
