@echo off
REM Script de compilation pour Windows

echo ===================================
echo Ski Timing Manager - Build Script
echo ===================================
echo.

REM Installer les dépendances
echo Installation des dependances...
pip install -r requirements.txt

echo.
echo Compilation pour Windows...
echo.

REM Compiler avec PyInstaller
pyinstaller --noconfirm --onefile --windowed ^
    --name=SkiTimingManager ^
    --add-data=".;." ^
    --hidden-import=pandas ^
    --hidden-import=openpyxl ^
    --collect-all pandas ^
    --collect-all openpyxl ^
    main.py

echo.
echo ===================================
echo Compilation terminee!
echo ===================================
echo.
echo L'executable se trouve dans: dist\SkiTimingManager.exe
echo.
echo Instructions:
echo - Copiez SkiTimingManager.exe ou vous voulez
echo - Double-cliquez pour lancer (pas d'installation requise)
echo.
pause
