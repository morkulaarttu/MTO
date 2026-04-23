@echo off
title MTO - Builder
color 0A

echo ============================================
echo   MTO (Mp3ToOgg) - Builder
echo ============================================
echo.

echo [1/3] Installing needed libraries ...
py -3.12 -m pip install customtkinter pystray pillow nuitka --quiet

echo [2/3] Building EXE with Nuitka (5-15 minutes)...
py -3.12 -m nuitka ^
    --onefile ^
    --windows-console-mode=disable ^
    --windows-icon-from-ico=logo.ico ^
    --output-filename=MTO.exe ^
    --output-dir=dist ^
    --enable-plugin=tk-inter ^
    --nofollow-import-to=tkinter.test ^
    --assume-yes-for-downloads ^
    app.py

if %errorlevel% neq 0 (
    echo ERROR: Build failed.
    pause
    exit /b 1
)

echo [3/3] Compressing ZIP...
powershell -Command "Compress-Archive -Path 'dist\MTO.exe' -DestinationPath 'dist\MTO.zip' -Force"

echo.
echo Ready! File: dist\MTO.zip
echo.
pause
