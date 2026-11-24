# ===============================================================================
# Replicador Oficial de la Suite 'RSA_Programacion' en el Escritorio
# ===============================================================================
param(
    [string]$RutaRepo = "C:\Proyectos\rsa_sismologia",
    [string]$RutaDesktop = [Environment]::GetFolderPath("Desktop")
)

$ErrorActionPreference = "Continue"

$CarpetaIconos = Join-Path $RutaRepo "iconos"
$Base = Join-Path $RutaDesktop "RSA_Programacion"

Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host "  CONFIGURANDO SUITE 'RSA_Programacion' EN EL ESCRITORIO" -ForegroundColor Cyan
Write-Host "===============================================================================" -ForegroundColor Cyan

# Asignar icono de directorio mediante desktop.ini referenciando SOLO C:\proyectos\rsa_sismologia\iconos\
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

    $Content = "[.ShellClassInfo]`r`nIconResource=$FullIconPath,0`r`nIconFile=$FullIconPath`r`nIconIndex=0`r`n[ViewState]`r`nMode=1`r`nVid={0057A0E0-350F-11CF-AE83-00AA00A3F253}`r`nFolderType=Generic`r`nLogicalViewMode=1`r`n"
    [System.IO.File]::WriteAllText($IniPath, $Content, [System.Text.Encoding]::Default)

    attrib +h +s "$IniPath"
    attrib +r "$Path"
    Write-Host "  [+] Icono carpeta: $(Split-Path $Path -Leaf) -> $IconFile" -ForegroundColor Green
}

$WshShell = New-Object -ComObject WScript.Shell
function Set-Shortcut {
    param(
        [string]$Folder,
        [string]$Name,
        [string]$TargetPath,
        [string]$Arguments = "",
        [string]$WorkDir = "",
        [string]$IconFile,
        [string]$Description = ""
    )
    if (-not (Test-Path $Folder)) {
        New-Item -ItemType Directory -Path $Folder -Force | Out-Null
    }
    $LnkPath = Join-Path $Folder "$Name.lnk"
    $IconPath = Join-Path $CarpetaIconos $IconFile

    $Shortcut = $WshShell.CreateShortcut($LnkPath)
    $Shortcut.TargetPath = $TargetPath
    if ($Arguments) { $Shortcut.Arguments = $Arguments }
    if ($WorkDir) { $Shortcut.WorkingDirectory = $WorkDir }
    if (Test-Path $IconPath) { $Shortcut.IconLocation = "$IconPath, 0" }
    if ($Description) { $Shortcut.Description = $Description }
    $Shortcut.Save()

    Write-Host "    - Acceso: $Name -> $IconFile" -ForegroundColor White
}

# Carpetas
$Dir1 = Join-Path $Base "1_Sismologia"
$Dir1_ModExt = Join-Path $Dir1 "Modulos_Externos"
$Dir2 = Join-Path $Base "2_NIDAQ"
$Dir3 = Join-Path $Base "3_Geotecnia"
$Dir4 = Join-Path $Base "4_Firmware_y_Workspace"
$Dir5 = Join-Path $Base "5_HYPO"

# Iconos de carpetas (apuntan exclusivamente al repositorio)
Set-FolderIcon "$Base" "dir_rsa_maestra.ico"
Set-FolderIcon "$Dir1" "dir_sismologia.ico"
Set-FolderIcon "$Dir1_ModExt" "dir_modulos.ico"
Set-FolderIcon "$Dir2" "dir_nidaq.ico"
Set-FolderIcon "$Dir3" "dir_geotecnia.ico"
Set-FolderIcon "$Dir4" "dir_firmware.ico"
Set-FolderIcon "$Dir5" "dir_hypo.ico"

# 1_Sismologia
Set-Shortcut $Dir1 "Programa Principal RSA" "$RutaRepo\procesamiento\Programa principal.bat" "" "$RutaRepo\procesamiento" "rsa_sismologia.ico" "Programa Principal RSA"

# Modulos_Externos
Set-Shortcut $Dir1_ModExt "Caudales y Filtraciones" "$RutaRepo\procesamiento\modulos externos\Caudales_Filtraciones.bat" "" "$RutaRepo\procesamiento\modulos externos" "agua_caudales.ico" "Caudales y Filtraciones"
Set-Shortcut $Dir1_ModExt "Niveles de Embalses" "$RutaRepo\procesamiento\modulos externos\Niveles_Embalses.bat" "" "$RutaRepo\procesamiento\modulos externos" "embalses.ico" "Niveles de Embalses"
Set-Shortcut $Dir1_ModExt "Consolidacion MSEED (Acelerografos)" "$RutaRepo\procesamiento\modulos externos\Consolidacion_MSEED.bat" "" "$RutaRepo\procesamiento\modulos externos" "mseed.ico" "Consolidacion MSEED"
Set-Shortcut $Dir1_ModExt "Arbol de Directorios" "$RutaRepo\procesamiento\modulos externos\Arbol_Directorios.bat" "" "$RutaRepo\procesamiento\modulos externos" "arbol_dir.ico" "Arbol de Directorios"
Set-Shortcut $Dir1_ModExt "Insercion de Estaciones EVT" "$RutaRepo\procesamiento\modulos externos\Insercion_Estaciones_EVT.bat" "" "$RutaRepo\procesamiento\modulos externos" "evt.ico" "Insercion de Estaciones EVT"
Set-Shortcut $Dir1_ModExt "Generar Shape" "$RutaRepo\procesamiento\modulos externos\Generar_Shape.bat" "" "$RutaRepo\procesamiento\modulos externos" "gis_shape.ico" "Generar Shapefile"
Set-Shortcut $Dir1_ModExt "Vigilante de Caudales" "$RutaRepo\procesamiento\modulos externos\Vigilante_Caudales.bat" "" "$RutaRepo\procesamiento\modulos externos" "agua_caudales.ico" "Vigilante de Caudales"
Set-Shortcut $Dir1_ModExt "Correccion EVT por Reseteo" "$RutaRepo\procesamiento\modulos externos\Correccion_EVT_Reseteo.bat" "" "$RutaRepo\procesamiento\modulos externos" "evt.ico" "Correccion EVT por Reseteo"

# 2_NIDAQ
Set-Shortcut $Dir2 "Adquisicion Galgas y Potenciometros" "$RutaRepo\nidaq\lanzar_adquisicion_estructuras.bat" "" "$RutaRepo\nidaq" "nidaq.ico" "Calibracion NIDAQ"

# 3_Geotecnia
Set-Shortcut $Dir3 "Entorno Geotecnia (Python 3.11)" "$RutaRepo\geotecnia\activar_entorno_geotecnia.bat" "" "$RutaRepo\geotecnia" "geotecnia.ico" "Entorno Geotecnia"
Set-Shortcut $Dir3 "Carpeta Geotecnia" "$RutaRepo\geotecnia" "" "" "dir_geotecnia.ico" "Carpeta Geotecnia"

# 4_Firmware_y_Workspace
Set-Shortcut $Dir4 "Abrir Espacio RSA (VS Code)" "$RutaRepo\rsa_sismologia.bat" "" "$RutaRepo" "workspace_code.ico" "VS Code Workspace"
Set-Shortcut $Dir4 "Carpeta ESP32" "$RutaRepo\esp_32" "" "" "dir_firmware.ico" "Carpeta ESP32"
Set-Shortcut $Dir4 "Carpeta PICS" "$RutaRepo\PICS" "" "" "dir_firmware.ico" "Carpeta PICS"
Set-Shortcut $Dir4 "Carpeta Tarjeta Digitalizadora" "$RutaRepo\tarjeta digitalizadora" "" "" "dir_firmware.ico" "Tarjeta Digitalizadora"

# 5_HYPO
Set-Shortcut $Dir5 "Binarios Originales HYPO" "$RutaRepo\hypo\binarios_originales" "" "" "dir_hypo.ico" "Binarios Originales HYPO"
Set-Shortcut $Dir5 "Carpeta HYPO" "$RutaRepo\hypo" "" "" "dir_hypo.ico" "Carpeta HYPO"
Set-Shortcut $Dir5 "Entorno Python HYPO" "$RutaRepo\hypo\activar_entorno_hypo.bat" "" "$RutaRepo\hypo" "hypo.ico" "Entorno Python HYPO"

# Refrescar Shell
try {
    Add-Type -TypeDefinition @"
    using System;
    using System.Runtime.InteropServices;
    public class ShellReplicatorFinal {
        [DllImport("shell32.dll")]
        public static extern void SHChangeNotify(int wEventId, int uFlags, IntPtr dwItem1, IntPtr dwItem2);
    }
"@
    [ShellReplicatorFinal]::SHChangeNotify(0x08000000, 0x0000, [IntPtr]::Zero, [IntPtr]::Zero)
} catch {}

Write-Host "`n[OK] Suite 'RSA_Programacion' configurada exitosamente." -ForegroundColor Green
