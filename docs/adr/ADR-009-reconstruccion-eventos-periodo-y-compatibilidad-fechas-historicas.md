---
proyecto: rsa_sismologia
tipo: adr
id: ADR-009
fecha: 2026-11-25
estado: Aceptado
---

# ADR-009: Compatibilidad Histórica 2/4 Dígitos, Portada Unificada en Reporte por Estaciones y Reconstrucción de Eventos por Período

## Contexto

Durante la operación sobre el archivo histórico completo en `C:\DIA` (2020–2026) se identificaron cuatro problemas estructurales:
1. **Pérdida silenciosa de eventos anteriores a 2025 en Reporte por Estaciones**: los catálogos consolidados 1995–2024 guardan el nombre del evento con 2 dígitos de año (`230318_171259.sis`), mientras que en disco el CSV diario y sus filas usan 4 dígitos (`20230318000000.csv` y `20230318_171259.sis`). `obtener_directorios()` construía `230318000000.csv` (inexistente) y la comparación de IDs fallaba.
2. **Ruido en selección de directorio de trabajo**: `config_local_pc.json` y el checkbox de recordatorio interferían con el flujo directo del botón `\DIA\` en `Inicio_proceso`.
3. **Portada descuadrada en `imprimir_reporte_especial_estaciones`**: se pasaba `'tipo_institucional': 'OFICIAL'` (string evaluado como `True`) y `formato(..., 1, lienzo)`, provocando un layout institucional incorrecto.
4. **Necesidad de reconstrucción masiva por período sin perder reclasificaciones**: al incorporar registros continuos de estaciones digitales, `extraer_dia()` operaba solo por día y sobrescribía las reclasificaciones de `AAAAMMDD000000.csv` con la clasificación inicial de `AAAAMMDD_aux.csv`.

## Decisión

1. **Resolución contra disco en `metodos_gestion.obtener_directorios()`**: verificar existencia real de prefijos de 4 dígitos (`YYYYMMDD`) y 2 dígitos (`YYMMDD`) para los archivos diarios (`archivo_csv`, `archivo_cat`, `archivo_rep`, `archivo_xml`, `archivo_res`, `archivo_auxiliar`, etc.) y normalizar IDs de evento a 14 dígitos al cruzar catálogos con matrices diarias.
2. **Asignación directa del directorio `\DIA\`**: eliminar `chk_recordar_pc` y la interferencia de `config_local_pc.json` en `inicio.py` y `reporte_acumulado.py`, propagando directamente la ruta seleccionada por el usuario.
3. **Portada estándar en `imprimir_reporte_especial_estaciones()`**: derivar banderas con `derivar_banderas_desde_modo(MODO_OFICIAL_DETALLADO, ...)` y usar el mismo algoritmo de portada (`formato`, `mapa`, `dibujo_sismos_`, `caja_simbologia`) que `imprimir_reporte_general()`.
4. **Reconstrucción de eventos por período (`reconstruir_eventos_dia` + `Reconstruccion_eventos`)**: nuevo subprograma en el menú `Ingreso de Datos` ejecutado en `QThread`, con respaldo previo de clasificaciones y tokens `EEEECBFFIISS` de `AAAAMMDD000000.csv`, generación de `.sis` opcional (desactivada por defecto), y aplicación de la misma protección de clasificaciones en `extraer_dia()`.
5. **Exclusión de accesos directos locales en Git**: añadir `*.lnk`, `*.bat` y `desktop.ini` en `.gitignore`.

## Consecuencias

* **Positivas**: recuperación completa del histórico 2020–2024 en reportes por estaciones (verificado con 19 eventos ≥ 0.98 cm/s² en 2023 incluyendo Balao), portada consistente con los demás reportes oficiales, reconstrucción rápida de períodos largos sin pérdida de clasificaciones y repositorio libre de accesos directos dependientes de cada PC.
* **Consideraciones**: la generación de `.sis` en reconstrucción por período requiere marcar explícitamente la casilla correspondiente cuando se requiera soporte para estaciones analógicas.
