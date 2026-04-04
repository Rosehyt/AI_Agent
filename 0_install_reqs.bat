@echo off
echo =======================================================
echo  Step 0: Installing Required Packages
echo =======================================================
call .venv\Scripts\activate.bat
pip install -r repo\requirements.txt
echo =======================================================
echo  Finished Installing! Press any key to close this window.
echo =======================================================
pause
