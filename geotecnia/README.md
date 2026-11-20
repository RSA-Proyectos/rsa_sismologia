# `rsa_sismologia/geotecnia` — Geotecnia Basada en Vibraciones y Geoeléctrica 3D

Proyecto independiente para análisis geotécnico y geofísico aplicado:
* **Vibraciones / Ondas Superficiales (soporte Geopsy)**: `hvsrpy`, `swprocess`, `swprepost`, `disba`, `obspy`.
* **Geoeléctrica 2D / 3D (arreglos no colineales)**: `SimPEG`, `ResIPy`.
* **Visualización 3D e Interfaz**: `pyvista`, `PySide6`, `pyqtgraph`, `matplotlib`, `numpy`, `scipy`, `pandas`, `openpyxl`.

## Entorno de ejecución
* **Entorno virtual**: `C:\entornos\geotecnia` (Python 3.11)
* **Acceso rápido**: ejecutar `activar_entorno_geotecnia.bat` o abrir esta carpeta en VS Code (el intérprete ya está configurado en `.vscode/settings.json`).

## Estructura
* `src/` — Scripts y aplicaciones principales.
* `ejemplos/` — Pruebas y simulaciones 3D (sondeos no colineales, HVSR, MASW, ERT).
* `datos/` — Registros de campo y modelos.
* `docs/` — Documentación técnica y notas de campaña.
