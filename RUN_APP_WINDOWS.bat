@echo off
title EcoVision ST-04 (Backend FastAPI + Frontend React)
cd /d "%~dp0"

echo ========================================================
echo  EcoVision ST-04 - Station Industrielle de Tri Optique
echo  Backend FastAPI & Interface React 60 FPS
echo ========================================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [INFO] Environnement virtuel non detecte. Configuration en cours...
    call SETUP_WINDOWS.bat
    if errorlevel 1 (
        echo [ERREUR] Echec de la configuration de l'environnement Python.
        pause
        exit /b 1
    )
)

if not exist "frontend\dist\index.html" (
    echo [INFO] Construction de l'interface React en cours...
    cd frontend
    call npm run build
    cd ..
)

echo [INFO] Lancement de l'application EcoVision (Back + Front)...
echo [INFO] Ouverture automatique du navigateur sur http://localhost:8000
echo.

start http://localhost:8000

.venv\Scripts\python.exe -m uvicorn server:app --host 0.0.0.0 --port 8000

if errorlevel 1 (
    echo.
    echo [ERREUR] Le serveur s'est arrete avec une erreur.
    pause
)
