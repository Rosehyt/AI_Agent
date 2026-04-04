@echo off
echo =======================================================
echo  Assignment 3: Portable Virtual Environment Setup
echo =======================================================

if exist .venv goto SkipVenv
echo [INFO] Creating new virtual environment...
python -m venv .venv
:SkipVenv
echo [INFO] Virtual environment ready.

:: Activate the environment
echo [INFO] Activating virtual environment...
call .venv\Scripts\activate.bat

:: Upgrade pip
echo [INFO] Upgrading pip...
python -m pip install --upgrade pip

REM Install requirements if they exist
if not exist requirements.txt goto SkipReq
echo [INFO] Installing packages from requirements.txt...
pip install -r requirements.txt
:SkipReq

echo.
echo =======================================================
echo  Setup Complete! The environment is now activated.
echo  To keep working in this window, just start typing.
echo =======================================================
cmd /k
