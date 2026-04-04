@echo off
echo =======================================================
echo  Exporting Installed Packages to requirements.txt
echo =======================================================

:: Check if virtual environment exists
IF NOT EXIST .venv (
    echo [ERROR] Virtual environment (.venv) not found.
    echo Please run setup_env.bat first or manually activate the environment.
    pause
    exit /b 1
)

:: Activate the environment and export requirements
call .venv\Scripts\activate.bat
pip freeze > requirements.txt

echo.
echo [SUCCESS] Current packages have been successfully saved to requirements.txt!
echo Make sure to keep requirements.txt on your USB drive so it works on the other computer.
echo =======================================================
pause
