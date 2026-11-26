# =============================================================================
# Creador y Verificador de Accesos Directos en el Escritorio - RSA Sismologia
# =============================================================================
# Verifica el entorno Python 3.9 en la nueva PC, valida librerias criticas y
# crea accesos directos portables en el Escritorio apuntando a la ruta real
# donde reside esta carpeta `procesamiento`.

$ErrorActionPreference = "Stop"

$DirProc = Split-Path -Parent $MyInvocation.MyCommand.Path
$DirRepo = Split-Path -Parent $DirProc
$DirIconos = Join-Path $DirRepo "iconos"
$Escritorio = [Environment]::GetFolderPath("Desktop")
$CarpetaAccesos = Join-Path $Escritorio "RSA Procesamiento"

Write-Host "===========================================================================" -ForegroundColor Cyan
Write-Host "  VERIFICACION DE ENTORNO Y CREACION DE ACCESOS DIRECTOS - RSA SISMOLOGIA" -ForegroundColor Cyan
Write-Host "===========================================================================" -ForegroundColor Cyan
Write-Host "Carpeta del sistema : $DirProc"
Write-Host "Escritorio detectado: $Escritorio"
Write-Host ""

# 1) Verificar entorno virtual Python 3.9 en la PC
$CandidatosVenv = @(
    "C:\entornos\venv_py309",
    "C:\entornos\sismologia_py39_v2"
)
$VenvDetectado = $null
$PythonExe = $null

foreach ($cand in $CandidatosVenv) {
    $py = Join-Path $cand "Scripts\python.exe"
    if (Test-Path $py) {
        $VenvDetectado = $cand
        $PythonExe = $py
        break
    }
}

if (-not $PythonExe) {
    Write-Host "[ERROR] No se encontro ningun entorno virtual Python 3.9 en:" -ForegroundColor Red
    foreach ($c in $CandidatosVenv) { Write-Host "        - $c" -ForegroundColor Red }
    Write-Host ""
    Write-Host "Ejecute primero 'instalar_entorno.bat' en esta misma carpeta." -ForegroundColor Yellow
    exit 1
}

Write-Host "[1/4] Entorno detectado: $VenvDetectado" -ForegroundColor Green
$PyVer = & $PythonExe --version 2>&1
Write-Host "      Version Python  : $PyVer"

# 2) Verificar importacion de librerias criticas
Write-Host "[2/4] Verificando librerias criticas..." -ForegroundColor Cyan
$TestCmd = "import PyQt5, obspy, numpy, scipy, matplotlib, pandas, reportlab, geopandas, shapely, shapefile, pyproj, openpyxl, PIL; print('OK')"
$ResTest = & $PythonExe -c $TestCmd 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Faltan librerias en el entorno actual:" -ForegroundColor Red
    Write-Host $ResTest -ForegroundColor Red
    Write-Host "Ejecute 'instalar_entorno.bat' para completar las dependencias." -ForegroundColor Yellow
    exit 1
}
Write-Host "      Librerias criticas: OK" -ForegroundColor Green

# 3) Verificar carpeta de datos operativa C:\DIA (solo aviso informativo)
if (Test-Path "C:\DIA") {
    Write-Host "[3/4] Carpeta operativa C:\DIA detectada." -ForegroundColor Green
} else {
    Write-Host "[3/4] Aviso: No se encontro C:\DIA en esta PC (podra elegir su carpeta DIA al iniciar el programa)." -ForegroundColor Yellow
}

# 4) Crear accesos directos en el Escritorio
Write-Host "[4/4] Creando accesos directos en el Escritorio..." -ForegroundColor Cyan
if (-not (Test-Path $CarpetaAccesos)) {
    New-Item -ItemType Directory -Path $CarpetaAccesos -Force | Out-Null
}

$WshShell = New-Object -ComObject WScript.Shell

function Crear-AccesoDirecto {
    param(
        [string]$RutaLnk,
        [string]$Destino,
        [string]$Argumentos = "",
        [string]$DirTrabajo = "",
        [string]$Descripcion = "",
        [string]$Icono = ""
    )
    $lnk = $WshShell.CreateShortcut($RutaLnk)
    $lnk.TargetPath = $Destino
    if ($Argumentos) { $lnk.Arguments = $Argumentos }
    if ($DirTrabajo) { $lnk.WorkingDirectory = $DirTrabajo }
    if ($Descripcion) { $lnk.Description = $Descripcion }
    if ($Icono -and (Test-Path $Icono)) { $lnk.IconLocation = "$Icono,0" }
    $lnk.Save()
    Write-Host "      + $RutaLnk" -ForegroundColor Gray
}

$IconoRSA = Join-Path $DirIconos "rsa_sismologia.ico"
$IconoDir = Join-Path $DirIconos "dir_sismologia.ico"
$BatPrincipal = Join-Path $DirProc "Programa principal.bat"
$BatInstalador = Join-Path $DirProc "instalar_entorno.bat"
$SpyderExe = Join-Path $VenvDetectado "Scripts\spyder.exe"

# Acceso directo principal en la raiz del Escritorio
Crear-AccesoDirecto `
    -RutaLnk (Join-Path $Escritorio "Programa Principal RSA.lnk") `
    -Destino $BatPrincipal `
    -DirTrabajo $DirProc `
    -Descripcion "Sistema Integrado de Procesamiento Sismologico - RSA" `
    -Icono $IconoRSA

# Accesos organizados dentro de Escritorio\RSA Procesamiento
Crear-AccesoDirecto `
    -RutaLnk (Join-Path $CarpetaAccesos "Programa Principal RSA.lnk") `
    -Destino $BatPrincipal `
    -DirTrabajo $DirProc `
    -Descripcion "Sistema Integrado de Procesamiento Sismologico - RSA" `
    -Icono $IconoRSA

Crear-AccesoDirecto `
    -RutaLnk (Join-Path $CarpetaAccesos "Instalar o Actualizar Entorno RSA.lnk") `
    -Destino $BatInstalador `
    -DirTrabajo $DirProc `
    -Descripcion "Instala o actualiza el entorno Python 3.9 y librerias del sistema RSA" `
    -Icono $IconoRSA

Crear-AccesoDirecto `
    -RutaLnk (Join-Path $CarpetaAccesos "Carpeta Procesamiento RSA.lnk") `
    -Destino $DirProc `
    -Descripcion "Abre la carpeta raiz del modulo procesamiento" `
    -Icono $IconoDir

# Acceso directo a Spyder solo si esta instalado en el entorno virtual
if (Test-Path $SpyderExe) {
    Crear-AccesoDirecto `
        -RutaLnk (Join-Path $CarpetaAccesos "Spyder (RSA Python 3.9).lnk") `
        -Destino $SpyderExe `
        -DirTrabajo (Join-Path $DirProc "src") `
        -Descripcion "IDE Spyder conectado al entorno Python 3.9 de RSA Sismologia" `
        -Icono $SpyderExe
    Write-Host "      (Spyder detectado en el entorno: acceso directo creado)" -ForegroundColor Green
} else {
    Write-Host "      (Spyder no instalado en el entorno: acceso directo omitido)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "===========================================================================" -ForegroundColor Green
Write-Host "  ACCESOS DIRECTOS CREADOS Y VERIFICADOS CORRECTAMENTE" -ForegroundColor Green
Write-Host "===========================================================================" -ForegroundColor Green
exit 0
