@echo off
REM Build a Windows executable installer for Vex using PyInstaller.
REM Run this from the repository root: scripts\build_installer.bat

python -m pip install --upgrade pyinstaller
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%

REM Clean previous build artifacts
rd /s /q dist 2>nul
rd /s /q build 2>nul
del /q spec\* 2>nul

set ICON_ARG=
if exist assets\vex.ico set ICON_ARG=--icon assets\vex.ico

pyinstaller --onefile --name vex.exe %ICON_ARG% \
    --add-data "examples;examples" \
    --add-data "README.md;README.md" \
    --add-data "LICENSE;LICENSE" \
    src\cli.py

necho Installer build complete.
echo Generated executable is in dist\vex.exe
