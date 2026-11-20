# ADR-008: Integración Nativa de FASTHYPO en Python (`rsa_fasthypo.py`), Mapa del Ecuador y Persistencia Exclusiva `.fas`

- **Estado**: Aceptado y verificado en producción local
- **Fecha**: 2026-11-20
- **Ámbito**: `procesamiento/src/librerias/rsa_fasthypo.py`, `procesamiento/src/subprogramas/fases.py`, `procesamiento/datos/fasthypo/`, `hypo/`

## Contexto
1. El flujo histórico de localización hipocentral dependía de ejecutables DOS de 16 bits (`CONVERT1.EXE`, `FAST.EXE`, `FPONG.EXE`) y un módulo VB5 (`Iaspei.frm`), obligando a usar máquina virtual y carpetas intermedias definidas en `responsables.csv`.
2. En `FAST.EXE` la convergencia dependía de la profundidad semilla (`60`, `49.9`, `33`, `14.9 km`), por lo que el operador debía probar manualmente múltiples corridas o recurrir a `FPONG.EXE` (menos preciso).
3. En `fases.py`, se generaban archivos `<evento>.json` redundantes dentro de `dia/` que ningún otro módulo consumía, contaminando la estructura histórica de `DIA\`.
4. En el entorno oficial `C:\entornos\sismologia_py39_v2`, `reportlab 4.4.1` carecía del extra `rl-renderPM`, provocando fallo al exportar gráficos vectoriales de señales a PDF.

## Decisión
1. **Motor FASTHYPO unificado en Python (`procesamiento/src/librerias/rsa_fasthypo.py`)**:
   - Se implementa el motor estratificado 1D con inversión amortiguada tipo Levenberg-Marquardt + covarianza SVD, cálculo de `Md` con `Mag2000.txt` y exportación fiel de `.rsa`, `.L`, `.S`, `.P` y `Phase*` (manteniendo `crustal model` e historial para compatibilidad total con `lectura_rsa()`).
   - Se ofrece corrida **multi-profundidad** (`60 / 49.9 / 33 / 14.9 km`) con tabla comparativa para que el sismólogo escoja la solución óptima, tabla de 14 columnas de la última iteración con resaltado semafórico de `P-res` y `S-res`, y **mapa vectorial interactivo del Ecuador** (`ECU provincias.shp`) con opción de ventana emergente sincronizada.
2. **Guardado directo en `fastHypo/` del día**:
   - `fases.py` invoca `archivos_fast(..., usuario='', modo_minuto_fast='auto')` y fija la carpeta destino a `self.directorios['Directorio_fastHypo']`, eliminando la redirección a carpetas de máquina virtual.
3. **Persistencia exclusiva en `.fas` en `fases.py`**:
   - Se elimina la creación/escritura de `<evento>.json` en `dia/`, conservando únicamente el `.fas` binario canónico (con lectura pasiva de respaldo si existiera un `.json` antiguo).
4. **Mejoras operativas en `fases.py` y entorno**:
   - Semáforo de colores en `combo_sis` idéntico a `procesamiento_integrado.py` (Verde `#009600`, Rojo `#C80000`, Negro `#000000`).
   - Ocultamiento de `..dia\` y botones `Tipo: FC` / `Tipo: FF` para reclasificación directa en el CSV del día.
   - Limpieza completa de `_zoom_info` / `drag_zoom` en `VentanaGrafico` al completar zoom o volver con doble clic derecho, y opción `"Ninguno"` en `Tipo P`, `Pol P` y `Pol S`.
   - Instalación de `rl-renderPM 4.0.3` en `C:\entornos\sismologia_py39_v2`.

## Consecuencias
- **Positivas**: Cero dependencia de DOS/máquina virtual para localizar eventos; selección informada entre profundidades semilla con visualización inmediata en el mapa del Ecuador; estructura `DIA\` limpia sin `.json` innecesarios; reportes PDF operativos.
- **Riesgos mitigados**: Compatibilidad preservada con `lectura_rsa()`, `procesamiento_integrado.py` y formatos históricos `.fas`/`.rsa`/`.L`/`.S`/`.P`/`Phase*`.
