@echo off
title Programa Principal RSA - Sismologia
setlocal

set "PYTHON_EXE="
if exist "C:\entornos\sismologia_py39_v2\Scripts\python.exe" (
    set "PYTHON_EXE=C:\entornos\sismologia_py39_v2\Scripts\python.exe"
) else if exist "C:\entornos\venv_py309\Scripts\python.exe" (
    set "PYTHON_EXE=C:\entornos\venv_py309\Scripts\python.exe"
)

if "%PYTHON_EXE%"=="" (
    echo [ERROR] No se encontro el interprete de Python en venv_py309 ni sismologia_py39_v2.
    pause
    exit /b 1
)

cd /d "%~dp0src"
"%PYTHON_EXE%" programa_integrado.py

if errorlevel 1 pause
endlocal
