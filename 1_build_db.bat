@echo off
echo =======================================================
echo  Step 1: Building Vector Database (ChromaDB)
echo =======================================================
call .venv\Scripts\activate.bat
cd repo
python build_rag.py
echo =======================================================
echo  Finished Building! Press any key to close this window.
echo =======================================================
pause
