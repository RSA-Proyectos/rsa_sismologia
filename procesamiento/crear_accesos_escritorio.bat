@echo off
chcp 65001 >nul
title Crear Accesos Directos en Escritorio - RSA Sismologia
setlocal

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0crear_accesos_escritorio.ps1"
if errorlevel 1 (
    echo.
    echo [AVISO] La verificacion detecto un problema en el entorno.
    pause
    exit /b 1
)

echo.
pause
endlocal
