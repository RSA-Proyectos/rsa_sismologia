# `rsa_sismologia/hypo` — Reconstrucción en Python de Localizadores Hipocentrales (HYPO)

Proyecto de ingeniería inversa y reconstrucción limpia en **Python** de dos ejecutables legados de 32 bits (consola / DOS) para localización hipocentral, apoyado en **REA (Reverse Engineer Anything)** y las reglas de `rsa_sismologia`.

## Entorno de ejecución
* **Entorno virtual**: `C:\entornos\sismologia_py39_v2` *(Python 3.9, compatible con `procesamiento/`)*
* **Acceso rápido**: ejecutar `activar_entorno_hypo.bat` o abrir esta carpeta en VS Code.

## Estructura de carpetas
* `binarios_originales/` — Copias intactas (solo lectura) de los 2 ejecutables y archivos auxiliares.
* `analisis_rea/evidencias/` — Reportes estáticos, hashes, cabeceras, imports, strings y hallazgos de REA.
* `analisis_rea/notas/` — Especificación de formatos de entrada/salida y algoritmos descubiertos.
* `casos_prueba/entradas/` — Archivos reales de entrada (estaciones, fases, modelo de velocidades).
* `casos_prueba/salidas_originales/` — Salidas de referencia producidas por los ejecutables originales (*Golden Master*).
* `casos_prueba/salidas_reconstruidas/` — Salidas generadas por la versión en Python para comparación.
* `src/` — Código fuente reconstruido en Python (nomenclatura y documentación en español).
* `tests/` — Pruebas automáticas de equivalencia numérica (latitud, longitud, profundidad, RMS, GAP, ERH/ERZ).
* `docs/` — Documentación matemática, formatos y decisiones técnicas.

## Flujo de trabajo
1. Copiar los 2 ejecutables originales en `binarios_originales/`.
2. Copiar 2 o 3 casos reales en `casos_prueba/entradas/` y sus salidas originales en `casos_prueba/salidas_originales/`.
3. Ejecutar el diagnóstico estático inicial con REA sobre los binarios.
4. Reconstruir los módulos en `src/` y validar equivalencia numérica con `tests/`.
