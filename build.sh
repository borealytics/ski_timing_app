#!/bin/bash
# Script de compilation pour créer les exécutables

echo "==================================="
echo "Ski Timing Manager - Build Script"
echo "==================================="

# Installer les dépendances si nécessaire
echo ""
echo "Installation des dépendances..."
pip install -r requirements.txt

# Déterminer la plateforme
if [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="macOS"
    OUTPUT_DIR="dist_macos"
    APP_NAME="SkiTimingManager.app"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    PLATFORM="Windows"
    OUTPUT_DIR="dist_windows"
    APP_NAME="SkiTimingManager.exe"
else
    echo "Plateforme non supportée: $OSTYPE"
    exit 1
fi

echo ""
echo "Compilation pour: $PLATFORM"
echo ""

# Compiler avec PyInstaller
pyinstaller --noconfirm --onefile --windowed \
    --name="SkiTimingManager" \
    --add-data=".:." \
    --hidden-import=pandas \
    --hidden-import=openpyxl \
    --collect-all pandas \
    --collect-all openpyxl \
    main.py

echo ""
echo "==================================="
echo "Compilation terminée!"
echo "==================================="
echo ""
echo "L'exécutable se trouve dans: dist/$APP_NAME"
echo ""
echo "Instructions:"
if [[ "$PLATFORM" == "macOS" ]]; then
    echo "- Copiez SkiTimingManager.app dans /Applications ou où vous voulez"
    echo "- Double-cliquez pour lancer (pas d'installation requise)"
else
    echo "- Copiez SkiTimingManager.exe où vous voulez"
    echo "- Double-cliquez pour lancer (pas d'installation requise)"
fi
echo ""
