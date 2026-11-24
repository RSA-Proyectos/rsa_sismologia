# ===============================================================================
# Generador y Sincronizador de la Suite 'RSA_programacion' en el Escritorio
# ===============================================================================
param(
    [string]$RutaRepo = "C:\proyectos\rsa_sismologia",
    [string]$RutaDesktop = [Environment]::GetFolderPath("Desktop")
)

$ErrorActionPreference = "Continue"

$CarpetaIconos = Join-Path $RutaRepo "iconos"
$Base = Join-Path $RutaDesktop "RSA_programacion"

Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host "  CREANDO SUITE 'RSA_programacion' EN EL ESCRITORIO" -ForegroundColor Cyan
Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host "[*] Repositorio: $RutaRepo"
Write-Host "[*] Destino:     $Base"
Write-Host ""

# Funcion para asignar icono a carpeta via desktop.ini
function Set-FolderIcon {
    param(
        [string]$Path,
        [string]$IconFile
    )
    if (-not (Test-Path $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
    $FullIconPath = Join-Path $CarpetaIconos $IconFile
    if (-not (Test-Path $FullIconPath)) { return }

    $IniPath = Join-Path $Path "desktop.ini"
    if (Test-Path $IniPath) {
        attrib -h -s -r "$IniPath" 2>$null
    }

    $Content = "[.ShellClassInfo]`r`nIconResource=$FullIconPath,0`r`n[ViewState]`r`nMode=`r`nVid=`r`nFolderType=Generic`r`n"
    [System.IO.File]::WriteAllText($IniPath, $Content, [System.Text.Encoding]::Default)

    attrib +h +s "$IniPath"
    attrib +r "$Path"
    Write-Host "  [+] Icono de carpeta: $(Split-Path $Path -Leaf) -> $IconFile" -ForegroundColor Green
}

# Funcion para crear archivo .bat y su acceso directo .lnk con icono
$WshShell = New-Object -ComObject WScript.Shell
function Create-Launcher {
    param(
        [string]$Folder,
        [string]$Name,
        [string]$BatContent,
        [string]$IconFile,
        [string]$WorkDir,
        [string]$Description
    )
    if (-not (Test-Path $Folder)) {
        New-Item -ItemType Directory -Path $Folder -Force | Out-Null
    }

    $BatPath = Join-Path $Folder "$Name.bat"
    [System.IO.File]::WriteAllText($BatPath, $BatContent, [System.Text.Encoding]::Default)

    $LnkPath = Join-Path $Folder "$Name.lnk"
    $IconPath = Join-Path $CarpetaIconos $IconFile

    $Shortcut = $WshShell.CreateShortcut($LnkPath)
    $Shortcut.TargetPath = $BatPath
    $Shortcut.WorkingDirectory = $WorkDir
    if (Test-Path $IconPath) {
        $Shortcut.IconLocation = "$IconPath, 0"
    }
    $Shortcut.Description = $Description
    $Shortcut.Save()

    Write-Host "    - Creado lanzador: $Name (.lnk con $IconFile)" -ForegroundColor White
}

# Funcion para crear acceso directo de exploracion a una carpeta
function Create-FolderShortcut {
    param(
        [string]$DestFolder,
        [string]$Name,
        [string]$TargetFolder,
        [string]$IconFile,
        [string]$Description
    )
    $LnkPath = Join-Path $DestFolder "$Name.lnk"
    $IconPath = Join-Path $CarpetaIconos $IconFile

    $Shortcut = $WshShell.CreateShortcut($LnkPath)
    $Shortcut.TargetPath = "explorer.exe"
    $Shortcut.Arguments = "`"$TargetFolder`""
    $Shortcut.WorkingDirectory = $TargetFolder
    if (Test-Path $IconPath) {
        $Shortcut.IconLocation = "$IconPath, 0"
    }
    $Shortcut.Description = $Description
    $Shortcut.Save()

    Write-Host "    - Acceso a carpeta: $Name -> $(Split-Path $TargetFolder -Leaf)" -ForegroundColor Gray
}

# -------------------------------------------------------------------------------
# 1. Definicion y creacion de la jerarquia de carpetas con sus iconos
# -------------------------------------------------------------------------------
$Dir1 = Join-Path $Base "1_Sismologia"
$Dir1_ModExt = Join-Path $Dir1 "Modulos_externos"
$Dir2 = Join-Path $Base "2_NidaQ"
$Dir3 = Join-Path $Base "3_Geotecnia"
$Dir4 = Join-Path $Base "4_Firmware_y_Workspace"
$Dir5 = Join-Path $Base "5_HYPO"

Write-Host "--- 1. Configurando Iconos de Carpetas ---" -ForegroundColor Yellow
Set-FolderIcon $Base "dir_rsa_maestra.ico"
Set-FolderIcon $Dir1 "dir_sismologia.ico"
Set-FolderIcon $Dir1_ModExt "dir_modulos.ico"
Set-FolderIcon $Dir2 "dir_nidaq.ico"
Set-FolderIcon $Dir3 "dir_geotecnia.ico"
Set-FolderIcon $Dir4 "dir_firmware.ico"
Set-FolderIcon $Dir5 "dir_hypo.ico"

# -------------------------------------------------------------------------------
# 2. Contenido de '1_Sismologia'
# -------------------------------------------------------------------------------
Write-Host "`n--- 2. Generando lanzadores en '1_Sismologia' ---" -ForegroundColor Yellow

# Programa Principal
$BatProgPpal = @"
@echo off
title Programa Principal RSA - Sismologia
setlocal
call C:\entornos\venv_py309\Scripts\activate.bat
cd /d C:\proyectos\rsa_sismologia\procesamiento\src
python programa_integrado.py
if errorlevel 1 pause
endlocal
"@
Create-Launcher $Dir1 "Programa_Principal_RSA" $BatProgPpal "rsa_sismologia.ico" "$RutaRepo\procesamiento\src" "Programa Principal RSA Monitoreo y Sismologia"

# Procesamiento Integrado
$BatProcInt = @"
@echo off
title Procesamiento Integrado - Sismologia
setlocal
call C:\entornos\venv_py309\Scripts\activate.bat
cd /d C:\proyectos\rsa_sismologia\procesamiento\src\subprogramas
python procesamiento_integrado.py
if errorlevel 1 pause
endlocal
"@
Create-Launcher $Dir1 "Procesamiento_Integrado" $BatProcInt "modulos_externos.ico" "$RutaRepo\procesamiento\src\subprogramas" "Procesamiento sismologico, filtros, espectros y magnitudes"

# Marcar Fases
$BatFases = @"
@echo off
title Marcar Fases Sismicas - Sismologia
setlocal
call C:\entornos\venv_py309\Scripts\activate.bat
cd /d C:\proyectos\rsa_sismologia\procesamiento\src\subprogramas
python fases.py
if errorlevel 1 pause
endlocal
"@
Create-Launcher $Dir1 "Marcar_Fases_Sismicas" $BatFases "hypo.ico" "$RutaRepo\procesamiento\src\subprogramas" "Marcado de fases P y S con localizador FastHypo"

# Reporte Diario
$BatRepDiario = @"
@echo off
title Reporte Diario - Sismologia
setlocal
call C:\entornos\venv_py309\Scripts\activate.bat
cd /d C:\proyectos\rsa_sismologia\procesamiento\src\subprogramas
python reporte_diario.py
if errorlevel 1 pause
endlocal
"@
Create-Launcher $Dir1 "Reporte_Diario" $BatRepDiario "rsa_sismologia.ico" "$RutaRepo\procesamiento\src\subprogramas" "Generacion del boletin y reporte diario PDF"

# Reporte Periodo Acumulado
$BatRepAcum = @"
@echo off
title Reporte de Periodo Acumulado - Sismologia
setlocal
call C:\entornos\venv_py309\Scripts\activate.bat
cd /d C:\proyectos\rsa_sismologia\procesamiento\src\subprogramas
python reporte_acumulado.py
if errorlevel 1 pause
endlocal
"@
Create-Launcher $Dir1 "Reporte_Periodo_Acumulado" $BatRepAcum "rsa_sismologia.ico" "$RutaRepo\procesamiento\src\subprogramas" "Generacion de catalogo y reportes por rango de fechas"

# Extraer Integrado
$BatExtraer = @"
@echo off
title Extraer Trazas Integrado - Sismologia
setlocal
call C:\entornos\venv_py309\Scripts\activate.bat
cd /d C:\proyectos\rsa_sismologia\procesamiento\src\subprogramas
python extraer_integrado.py
if errorlevel 1 pause
endlocal
"@
Create-Launcher $Dir1 "Extraer_Integrado" $BatExtraer "rsa_sismologia.ico" "$RutaRepo\procesamiento\src\subprogramas" "Extraccion de trazas sismicas por ventana de tiempo"

# -------------------------------------------------------------------------------
# 3. Contenido de '1_Sismologia\Modulos_externos'
# -------------------------------------------------------------------------------
Write-Host "`n--- 3. Generando lanzadores en '1_Sismologia\Modulos_externos' ---" -ForegroundColor Yellow

# Consolidacion MiniSEED
$BatMseed = @"
@echo off
title Consolidacion de Acelerografos (MiniSEED)
setlocal
call C:\entornos\venv_py309\Scripts\activate.bat
cd /d "C:\proyectos\rsa_sismologia\procesamiento\modulos externos"
python consolidacion_mseed.py
if errorlevel 1 pause
endlocal
"@
Create-Launcher $Dir1_ModExt "Consolidacion_Acelerografos_mseed" $BatMseed "mseed.ico" "$RutaRepo\procesamiento\modulos externos" "Consolidacion e indexacion MiniSEED"

# Correccion EVT por Reseteo
$BatEvtReset = @"
@echo off
title Correccion de EVT por Reseteo
setlocal
call C:\entornos\venv_py309\Scripts\activate.bat
cd /d "C:\proyectos\rsa_sismologia\procesamiento\modulos externos"
python "Corrección de EVT por reseteo.py"
if errorlevel 1 pause
endlocal
"@
Create-Launcher $Dir1_ModExt "Correccion_EVT_por_Reseteo" $BatEvtReset "evt.ico" "$RutaRepo\procesamiento\modulos externos" "Correccion de fecha y hora en archivos EVT reseteados"

# Insercion de Estaciones EVT
$BatEvtInsert = @"
@echo off
title Insercion de Estaciones EVT
setlocal
call C:\entornos\venv_py309\Scripts\activate.bat
cd /d "C:\proyectos\rsa_sismologia\procesamiento\modulos externos"
python "Insercion de estaciones EVT.py"
if errorlevel 1 pause
endlocal
"@
Create-Launcher $Dir1_ModExt "Insercion_Estaciones_EVT" $BatEvtInsert "evt.ico" "$RutaRepo\procesamiento\modulos externos" "Insercion de cabeceras de estacion en archivos EVT"

# Caudales y Filtraciones
$BatCaudales = @"
@echo off
title Monitoreo de Caudales y Filtraciones
setlocal
call C:\entornos\venv_py309\Scripts\activate.bat
cd /d "C:\proyectos\rsa_sismologia\procesamiento\modulos externos"
python caudales_filtraciones.py
if errorlevel 1 pause
endlocal
"@
Create-Launcher $Dir1_ModExt "Caudales_y_Filtraciones" $BatCaudales "agua_caudales.ico" "$RutaRepo\procesamiento\modulos externos" "Monitoreo y analisis de caudales y filtraciones"

# Niveles de Embalses
$BatEmbalses = @"
@echo off
title Monitoreo de Niveles de Embalses
setlocal
call C:\entornos\venv_py309\Scripts\activate.bat
cd /d "C:\proyectos\rsa_sismologia\procesamiento\modulos externos"
python niveles_embalses.py
if errorlevel 1 pause
endlocal
"@
Create-Launcher $Dir1_ModExt "Niveles_de_Embalses" $BatEmbalses "embalses.ico" "$RutaRepo\procesamiento\modulos externos" "Monitoreo de niveles hidrometricos de embalses"

# Generar Shapefile GIS
$BatGis = @"
@echo off
title Generador de Shapefile GIS (Sismicidad)
setlocal
call C:\entornos\venv_py309\Scripts\activate.bat
cd /d "C:\proyectos\rsa_sismologia\procesamiento\modulos externos"
python generar_shape.py
if errorlevel 1 pause
endlocal
"@
Create-Launcher $Dir1_ModExt "Generar_Shapefile_GIS" $BatGis "gis_shape.ico" "$RutaRepo\procesamiento\modulos externos" "Generacion y exportacion de mapas vectoriales Shapefile"

# Arbol de Directorios
$BatArbol = @"
@echo off
title Generador de Arbol de Directorios DIA
setlocal
call C:\entornos\venv_py309\Scripts\activate.bat
cd /d "C:\proyectos\rsa_sismologia\procesamiento\modulos externos"
python arbol_directorios.py
if errorlevel 1 pause
endlocal
"@
Create-Launcher $Dir1_ModExt "Arbol_de_Directorios" $BatArbol "arbol_dir.ico" "$RutaRepo\procesamiento\modulos externos" "Estructurador y validador de carpetas DIA"

# -------------------------------------------------------------------------------
# 4. Contenido de '2_NidaQ'
# -------------------------------------------------------------------------------
Write-Host "`n--- 4. Generando lanzadores en '2_NidaQ' ---" -ForegroundColor Yellow

$BatNidaq = @"
@echo off
title Calibracion NIDAQ - Prensa 100 Toneladas
setlocal
call C:\entornos\estructuras\Scripts\activate.bat
cd /d C:\proyectos\rsa_sismologia\nidaq
python adquisicion_galgas_potenciometros.py
if errorlevel 1 pause
endlocal
"@
Create-Launcher $Dir2 "Calibracion_NIDAQ_Prensa_100Ton" $BatNidaq "nidaq.ico" "$RutaRepo\nidaq" "Banco de calibracion y adquisicion continua NI-USB-6210"

$BatNidaqTest = @"
@echo off
title Prueba Diagnostico NIDAQmx
setlocal
call C:\entornos\estructuras\Scripts\activate.bat
cd /d C:\proyectos\rsa_sismologia\nidaq
python "import nidaqmx.py"
if errorlevel 1 pause
endlocal
"@
Create-Launcher $Dir2 "Prueba_Diagnostico_NIDAQmx" $BatNidaqTest "nidaq.ico" "$RutaRepo\nidaq" "Prueba de comunicacion de hardware NI-DAQmx"

Create-FolderShortcut $Dir2 "Carpeta_Secuencias_Calibracion" "$RutaRepo\nidaq\secuencias_calibracion" "dir_nidaq.ico" "Carpeta de registros y secuencias de calibracion"

# -------------------------------------------------------------------------------
# 5. Contenido de '3_Geotecnia'
# -------------------------------------------------------------------------------
Write-Host "`n--- 5. Generando accesos en '3_Geotecnia' ---" -ForegroundColor Yellow

Create-FolderShortcut $Dir3 "Abrir_Carpeta_Geotecnia" "$RutaRepo\geotecnia" "geotecnia.ico" "Explorar archivos y modelos de geotecnia"

# -------------------------------------------------------------------------------
# 6. Contenido de '4_Firmware_y_Workspace'
# -------------------------------------------------------------------------------
Write-Host "`n--- 6. Generando lanzadores en '4_Firmware_y_Workspace' ---" -ForegroundColor Yellow

# VS Code Workspace
$BatCode = @"
@echo off
title Visual Studio Code - Proyecto RSA Sismologia
setlocal
cd /d C:\proyectos\rsa_sismologia
call code .
endlocal
"@
Create-Launcher $Dir4 "VSCode_Workspace_RSA" $BatCode "workspace_code.ico" "$RutaRepo" "Abrir proyecto RSA Sismologia en Visual Studio Code"

# Spyder IDE
$BatSpyder = @"
@echo off
title Spyder IDE - Entorno Sismologia py309
setlocal
call C:\entornos\venv_py309\Scripts\activate.bat
start "" "C:\entornos\venv_py309\Scripts\spyder.exe"
endlocal
"@
Create-Launcher $Dir4 "Spyder_IDE_py309" $BatSpyder "rsa_sismologia.ico" "$RutaRepo" "Lanzar Spyder IDE configurado en entorno py309"

Create-FolderShortcut $Dir4 "Firmware_ESP32" "$RutaRepo\esp_32" "firmware.ico" "Codigos fuentes y firmware para ESP32"
Create-FolderShortcut $Dir4 "Firmware_PICS" "$RutaRepo\PICS" "firmware.ico" "Codigos fuentes y firmware para PICs"
Create-FolderShortcut $Dir4 "Tarjeta_Digitalizadora" "$RutaRepo\tarjeta digitalizadora" "firmware.ico" "Planos y firmware de la tarjeta digitalizadora"

# -------------------------------------------------------------------------------
# 7. Contenido de '5_HYPO'
# -------------------------------------------------------------------------------
Write-Host "`n--- 7. Generando lanzadores en '5_HYPO' ---" -ForegroundColor Yellow

# FastHypo launcher (usa fases.py integrado con motor FastHypo Python)
$BatHypo = @"
@echo off
title Localizador FASTHYPO - Fases Sismicas
setlocal
call C:\entornos\venv_py309\Scripts\activate.bat
cd /d C:\proyectos\rsa_sismologia\procesamiento\src\subprogramas
python fases.py
if errorlevel 1 pause
endlocal
"@
Create-Launcher $Dir5 "Localizador_FASTHYPO" $BatHypo "hypo.ico" "$RutaRepo\procesamiento\src\subprogramas" "Localizador hipocentral FASTHYPO con mapa vectorial"

Create-FolderShortcut $Dir5 "Abrir_Carpeta_HYPO" "$RutaRepo\hypo" "dir_hypo.ico" "Archivos de configuracion, velocidades y modelos FastHypo"

# -------------------------------------------------------------------------------
# 8. Documento LEEME en la raiz de RSA_programacion
# -------------------------------------------------------------------------------
$LeemeContent = @"
===============================================================================
  SUITE RSA_PROGRAMACION - ESCRITORIO
===============================================================================
Estructura organizada de accesos directos y lanzadores para el proyecto RSA:

[1_Sismologia] (Icono: dir_sismologia.ico)
  - Programa_Principal_RSA.lnk (Icono: rsa_sismologia.ico)
  - Procesamiento_Integrado.lnk (Icono: modulos_externos.ico)
  - Marcar_Fases_Sismicas.lnk (Icono: hypo.ico)
  - Reporte_Diario.lnk (Icono: rsa_sismologia.ico)
  - Reporte_Periodo_Acumulado.lnk (Icono: rsa_sismologia.ico)
  - Extraer_Integrado.lnk (Icono: rsa_sismologia.ico)
  [Modulos_externos] (Icono: dir_modulos.ico)
    - Consolidacion_Acelerografos_mseed.lnk (Icono: mseed.ico)
    - Correccion_EVT_por_Reseteo.lnk (Icono: evt.ico)
    - Insercion_Estaciones_EVT.lnk (Icono: evt.ico)
    - Caudales_y_Filtraciones.lnk (Icono: agua_caudales.ico)
    - Niveles_de_Embalses.lnk (Icono: embalses.ico)
    - Generar_Shapefile_GIS.lnk (Icono: gis_shape.ico)
    - Arbol_de_Directorios.lnk (Icono: arbol_dir.ico)

[2_NidaQ] (Icono: dir_nidaq.ico)
  - Calibracion_NIDAQ_Prensa_100Ton.lnk (Icono: nidaq.ico - Python 3.13)
  - Prueba_Diagnostico_NIDAQmx.lnk (Icono: nidaq.ico)
  - Carpeta_Secuencias_Calibracion.lnk

[3_Geotecnia] (Icono: dir_geotecnia.ico)
  - Abrir_Carpeta_Geotecnia.lnk (Icono: geotecnia.ico)

[4_Firmware_y_Workspace] (Icono: dir_firmware.ico)
  - VSCode_Workspace_RSA.lnk (Icono: workspace_code.ico)
  - Spyder_IDE_py309.lnk (Icono: rsa_sismologia.ico)
  - Firmware_ESP32.lnk (Icono: firmware.ico)
  - Firmware_PICS.lnk (Icono: firmware.ico)
  - Tarjeta_Digitalizadora.lnk (Icono: firmware.ico)

[5_HYPO] (Icono: dir_hypo.ico)
  - Localizador_FASTHYPO.lnk (Icono: hypo.ico)
  - Abrir_Carpeta_HYPO.lnk (Icono: dir_hypo.ico)

===============================================================================
Para restaurar o actualizar esta suite en cualquier momento, ejecute:
  C:\proyectos\rsa_sismologia\configurar_iconos_y_accesos.bat
===============================================================================
"@
[System.IO.File]::WriteAllText((Join-Path $Base "LEEME.txt"), $LeemeContent, [System.Text.Encoding]::Default)

# -------------------------------------------------------------------------------
# 9. Refrescar explorador de Windows
# -------------------------------------------------------------------------------
Write-Host "`n[*] Refrescando explorador de Windows..." -ForegroundColor Cyan
try {
    Add-Type -TypeDefinition @"
    using System;
    using System.Runtime.InteropServices;
    public class ShellSuite {
        [DllImport("shell32.dll")]
        public static extern void SHChangeNotify(int wEventId, int uFlags, IntPtr dwItem1, IntPtr dwItem2);
    }
"@
    [ShellSuite]::SHChangeNotify(0x08000000, 0x0000, [IntPtr]::Zero, [IntPtr]::Zero)
} catch {
}

Write-Host "[OK] Suite 'RSA_programacion' creada y configurada con exito." -ForegroundColor Green
Write-Host "===============================================================================" -ForegroundColor Cyan
