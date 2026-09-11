@echo off
title Med-EHR Launcher
set SCRIPT_DIR=%~dp0

echo Starting Med-EHR servers...
echo.

start "Med-EHR Backend" /d "%SCRIPT_DIR%med_ehr_backend" cmd /k "python manage.py runserver"
start "Med-EHR Frontend" /d "%SCRIPT_DIR%med-ehr-frontend" cmd /k "npm start"

echo   Backend   : http://127.0.0.1:8000   (window: Med-EHR Backend)
echo   Frontend  : http://localhost:4200   (window: Med-EHR Frontend)
echo.
echo Opening the app in your browser...
timeout /t 3 >nul
start http://localhost:4200