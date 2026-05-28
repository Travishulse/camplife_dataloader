@echo off
echo ==============================================
echo Building Camplife DataLoader Executable...
echo ==============================================

REM Ensure all dependencies are installed
.venv\Scripts\python.exe -m pip install pyinstaller
.venv\Scripts\python.exe -m pip install -r requirements.txt

REM Clean previous build artifacts to avoid stale files
if exist "dist\Camplife DataLoader" (
    echo Cleaning previous dist...
    rmdir /s /q "dist\Camplife DataLoader"
)
if exist "build\Camplife DataLoader" (
    echo Cleaning previous build...
    rmdir /s /q "build\Camplife DataLoader"
)

REM Build using the spec file (handles hidden imports like openpyxl)
.venv\Scripts\pyinstaller.exe --noconfirm "Camplife DataLoader.spec"

echo ==============================================
echo Build Complete!
echo Executable is in: dist\Camplife DataLoader\
echo Run: dist\Camplife DataLoader\Camplife DataLoader.exe
echo NOTE: You must distribute the entire 'Camplife DataLoader' folder, not just the .exe
echo ==============================================
pause
