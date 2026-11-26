@echo off
chcp 65001 >nul
title Instalador del Entorno RSA Sismologia (Python 3.9)
setlocal EnableDelayedExpansion

echo ===========================================================================
echo   INSTALADOR DE ENTORNO DE EJECUCION Y DESARROLLO - RSA SISMOLOGIA
echo ===========================================================================
echo.

set "DIR_SCRIPT=%~dp0"
set "VENV_DIR=C:\entornos\venv_py309"
set "REQ_FILE=%DIR_SCRIPT%requirements.txt"
set "REQ_DEV=%DIR_SCRIPT%requirements_dev.txt"

if not exist "%REQ_FILE%" (
    echo [ERROR] No se encontro "%REQ_FILE%".
    echo         Verifique que este ejecutando el instalador desde la carpeta procesamiento.
    pause
    exit /b 1
)

REM ---------------------------------------------------------------------------
REM 1) Localizar interprete de Python 3.9 en Windows
REM ---------------------------------------------------------------------------
set "PY39_CMD="

py -3.9 --version >nul 2>&1
if not errorlevel 1 (
    set "PY39_CMD=py -3.9"
)

if "%PY39_CMD%"=="" (
    if exist "C:\Python39\python.exe" (
        set "PY39_CMD=C:\Python39\python.exe"
    ) else if exist "%LOCALAPPDATA%\Programs\Python\Python39\python.exe" (
        set "PY39_CMD=%LOCALAPPDATA%\Programs\Python\Python39\python.exe"
    )
)

if "%PY39_CMD%"=="" (
    for /f "tokens=2 delims= " %%v in ('python --version 2^>nul') do (
        echo %%v | findstr /b "3.9." >nul
        if not errorlevel 1 (
            set "PY39_CMD=python"
        )
    )
)

if "%PY39_CMD%"=="" (
    echo [AVISO] No se encontro Python 3.9 instalado en esta computadora.
    echo.
    where winget >nul 2>&1
    if not errorlevel 1 (
        set /p "INST_PY=Desea instalar Python 3.9 automaticamente usando winget? [S/N]: "
        if /i "!INST_PY!"=="S" (
            echo Instalando Python 3.9...
            winget install -e --id Python.Python.3.9 --accept-source-agreements --accept-package-agreements
            if errorlevel 1 (
                echo [ERROR] No se pudo completar la instalacion con winget.
                echo Descargue Python 3.9.13 manualmente desde:
                echo   https://www.python.org/downloads/release/python-3913/
                echo Recuerde marcar "Add Python 3.9 to PATH" y vuelva a ejecutar este instalador.
                pause
                exit /b 1
            )
            echo.
            echo [OK] Python 3.9 instalado. Cierre esta ventana y vuelva a ejecutar instalar_entorno.bat
            echo      para refrescar las variables de entorno de Windows.
            pause
            exit /b 0
        )
    )
    echo Descargue e instale Python 3.9.13 (64-bit) desde:
    echo   https://www.python.org/downloads/release/python-3913/
    echo Luego vuelva a ejecutar este instalador.
    pause
    exit /b 1
)

echo [1/5] Python 3.9 detectado:
%PY39_CMD% --version
echo.

REM ---------------------------------------------------------------------------
REM 2) Crear o reutilizar entorno virtual C:\entornos\venv_py309
REM ---------------------------------------------------------------------------
if not exist "C:\entornos" mkdir "C:\entornos"

if exist "%VENV_DIR%\Scripts\python.exe" (
    echo [2/5] Ya existe un entorno en "%VENV_DIR%".
    echo       Se actualizaran las dependencias sobre el entorno existente.
) else (
    echo [2/5] Creando entorno virtual en "%VENV_DIR%"...
    %PY39_CMD% -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo [ERROR] No se pudo crear el entorno virtual en "%VENV_DIR%".
        pause
        exit /b 1
    )
)

set "VENV_PY=%VENV_DIR%\Scripts\python.exe"
echo.

REM ---------------------------------------------------------------------------
REM 3) Actualizar pip, setuptools y wheel
REM ---------------------------------------------------------------------------
echo [3/5] Actualizando pip, setuptools y wheel...
"%VENV_PY%" -m pip install --upgrade pip setuptools==58.0.4 wheel==0.45.1
if errorlevel 1 (
    echo [ERROR] Fallo la actualizacion de pip/setuptools/wheel.
    pause
    exit /b 1
)
echo.

REM ---------------------------------------------------------------------------
REM 4) Instalar librerias de ejecucion (requirements.txt)
REM ---------------------------------------------------------------------------
echo [4/5] Instalando librerias de ejecucion desde requirements.txt...
"%VENV_PY%" -m pip install -r "%REQ_FILE%"
if errorlevel 1 (
    echo.
    echo [ERROR] Ocurrio un fallo al instalar las dependencias de requirements.txt.
    echo         Verifique la conexion a Internet y revise el mensaje anterior.
    pause
    exit /b 1
)
echo.

REM ---------------------------------------------------------------------------
REM Opcional: Instalar entorno de desarrollo Spyder (requirements_dev.txt)
REM ---------------------------------------------------------------------------
if exist "%REQ_DEV%" (
    set /p "INST_DEV=Desea instalar tambien Spyder 5.4.3 (IDE de desarrollo)? [S/N]: "
    if /i "!INST_DEV!"=="S" (
        echo Instalando Spyder 5.4.3 desde requirements_dev.txt...
        "%VENV_PY%" -m pip install -r "%REQ_DEV%"
        if errorlevel 1 (
            echo [AVISO] Hubo un problema instalando Spyder, pero el entorno de ejecucion ya esta listo.
        ) else (
            echo [OK] Spyder 5.4.3 instalado correctamente.
        )
    )
)
echo.

REM ---------------------------------------------------------------------------
REM 5) Verificacion automatica de importaciones criticas
REM ---------------------------------------------------------------------------
echo [5/5] Verificando importacion de librerias criticas del sistema RSA...
"%VENV_PY%" -c "import PyQt5, obspy, numpy, scipy, matplotlib, pandas, reportlab, geopandas, shapely, shapefile, pyproj, openpyxl, PIL; print('OK - Todas las librerias criticas importaron correctamente.')"
if errorlevel 1 (
    echo [ERROR] Alguna libreria critica no pudo importarse. Revise los mensajes anteriores.
    pause
    exit /b 1
)

echo.
echo ===========================================================================
echo   INSTALACION COMPLETADA CON EXITO
echo ===========================================================================
echo   Entorno virtual : %VENV_DIR%
echo   Para iniciar    : ejecute "Programa principal.bat" en esta misma carpeta.
echo ===========================================================================
echo.

if exist "%DIR_SCRIPT%crear_accesos_escritorio.ps1" (
    set /p "CREAR_LNK=Desea crear los accesos directos en el Escritorio ahora? [S/N]: "
    if /i "!CREAR_LNK!"=="S" (
        powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%DIR_SCRIPT%crear_accesos_escritorio.ps1"
    )
)
echo.
pause
endlocal
