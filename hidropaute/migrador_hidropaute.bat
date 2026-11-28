@echo off
title Migrador Historico HIDROPAUTE / CELEC - RSA Sismologia
setlocal

set "PYTHON_EXE=C:\entornos\venv_py309\Scripts\python.exe"
if not exist "%PYTHON_EXE%" (
    set "PYTHON_EXE=C:\entornos\sismologia_py39_v2\Scripts\python.exe"
)

if not exist "%PYTHON_EXE%" (
    echo [ERROR] No se encontro el entorno Python 3.9 en C:\entornos\venv_py309.
    pause
    exit /b 1
)

"%PYTHON_EXE%" "%~dp0migrador_hidropaute.py"
if errorlevel 1 pause
endlocal
