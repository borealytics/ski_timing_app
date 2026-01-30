@echo off
echo Installation des dependances...
pip install -r requirements.txt
pip install pyinstaller

echo.
echo Creation de l'executable...
pyinstaller --onefile --windowed --name "SkiTiming" --icon=icon.ico main.py 2>nul || pyinstaller --onefile --windowed --name "SkiTiming" main.py

echo.
echo Termine! L'executable se trouve dans: dist\SkiTiming.exe
pause
