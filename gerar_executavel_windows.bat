@echo off
cd /d "%~dp0"
python -m pip install -r requirements.txt
if errorlevel 1 goto :erro
python -m pip install "pyinstaller>=6,<7"
if errorlevel 1 goto :erro
python -m PyInstaller --noconfirm --clean --windowed --onedir --name PAT_BEP_Desktop app.py
if errorlevel 1 goto :erro
echo.
echo Executable created at dist\PAT_BEP_Desktop\PAT_BEP_Desktop.exe
pause
exit /b 0
:erro
echo Dependency installation or executable build failed.
pause
exit /b 1
