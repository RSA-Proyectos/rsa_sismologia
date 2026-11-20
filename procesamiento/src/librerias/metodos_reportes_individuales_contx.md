---
proyecto: rsa_sismologia
tipo: contexto_tecnico
archivo: src/librerias/metodos_reportes_individuales.py
temas: [reportes_individuales, sismo_individual, acelerograma, pyqt5, gis]
generado: 2026-11-14
---

# `src/librerias/metodos_reportes_individuales.py` — Contexto Técnico para Agentes IA

> Módulo puente de interfaz gráfica para la generación de reportes PDF individuales por evento: filtra el evento seleccionado en el catálogo, despliega la vista previa cartográfica GIS (`catalogo_gis`), solicita confirmación al operador mediante `QMessageBox` y delega la emisión del PDF a `impresion_reporte_sismo` o al diálogo `Subventana_aceleraciones`.

**Ruta**: `src/librerias/metodos_reportes_individuales.py`  
**LOC**: 102 | **Lenguaje**: Python 3 (PyQt5)  
**Dependencias**: `PyQt5.QtWidgets.QMessageBox`, `librerias.metodos_gis_rsa.catalogo_gis`, `librerias.rsa_pdf_reportes.impresion_reporte_sismo`, `librerias.ventana_aceleraciones.Subventana_aceleraciones`  
**Proceso**: Invocado desde `src/subprogramas/reporte_diario.py` y `src/subprogramas/procesamiento_integrado.py` (`reportar_()`).

---

## 1. Arquitectura y Flujo de Interacción

```mermaid
flowchart TD
    A[Subprograma: reporte_diario / procesamiento_integrado] --> B[generar_reporte_sismo]
    B --> C[Filtrar catalogo donde registro[18] == evento_escogido[0][1]]
    C --> D{¿Existe en catálogo?}
    D -->|No| E[QMessageBox: No hay información del evento en el catálogo]
    D -->|Sí| F[catalogo_gis: Mostrar mapa Matplotlib de vista previa]
    F --> G{QMessageBox: ¿Generar el reporte del evento?}
    G -->|Sí| H[impresion_reporte_sismo con bandera_periodo=0, mapa_escogido=1]
    H --> I[QMessageBox: Reporte generado]
    G -->|No| J[QMessageBox: Reporte no generado]

    A --> K[generar_reporte_acelerograma]
    K --> L{¿Tipo es Evento_local o CONTROL?}
    L -->|Sí| M[Construir tupla sintética mensaje con origen RSA]
    L -->|No| N[Tomar fila de catalogo_escogido]
    M --> O[Subventana_aceleraciones.exec_]
    N --> O
```

---

## 2. Componentes y Funciones Clave

| Función | Firma | Descripción |
|---|---|---|
| `_filtrar_catalogo_evento` | `(catalogo, nombre_evento)` | Filtra las filas del catálogo asociadas a `nombre_evento` y garantiza que la solución `RSA` ocupe siempre el índice `0` (o `[]` si el evento solo tiene solución de otra red), seguida de las soluciones de redes externas (`IGEPN`, `USGS`, `Otras redes`). |
| `generar_reporte_sismo` | `(catalogo, evento_escogido, canales, tr_canal, archivo_rep, directorio_trabajo)` | Filtra las filas del catálogo asociadas al archivo `.sis` del evento mediante `_filtrar_catalogo_evento`, muestra el mapa `catalogo_gis`, pide confirmación y ejecuta `impresion_reporte_sismo` con `mapa_escogido=0` y `banderas={'mostrar_cobertura_red': False, 'mostrar_intentos_proc': False}` (boletín externo para investigadores y medios, sin estaciones ni zonas de cobertura). |
| `generar_reporte_acelerograma` | `(eventos, indice, catalogo, evento_escogido, archivo_escogido)` | Abre el diálogo modal `Subventana_aceleraciones` para seleccionar estaciones acelerográficas y generar sus reportes individuales; evalúa primero si es `Evento_local` o `CONTROL` (construyendo una tupla sintética compatible con nombres de 12 y 14 dígitos) y para sismos regulares usa `_filtrar_catalogo_evento`. |

---

## 3. Riesgos Específicos y Checklist de Estabilidad

1. **Firma de `generar_reporte_sismo` (6 parámetros)**:
   * `generar_reporte_sismo` requiere `directorio_trabajo` como sexto argumento para pasarlo a `impresion_reporte_sismo`. Cualquier llamador (como `reportar_()` en `procesamiento_integrado.py` o `reporte_diario.py`) debe suministrar los 6 argumentos.
2. **Eventos `FF` o `FC` Vinculados a Otras Redes**:
   * Tanto `generar_reporte_sismo` como `generar_reporte_acelerograma` soportan eventos clasificados como `FF` o `FC` siempre que estén vinculados en `catalogo` a una red externa (`IGEPN`, `USGS`, `Otras redes`), recibiendo la estructura `[[], fila_otra_red]` desde `_filtrar_catalogo_evento`. Si no están vinculados, muestran un aviso explícito indicando que un evento `FF`/`FC` requiere vincularse a un evento de Otras Redes.
