@echo off
echo =======================================================
echo  Step 2: Evaluating Agents (Task A vs Tasks B-E)
echo =======================================================
call .venv\Scripts\activate.bat
cd repo
python evaluator.py
echo =======================================================
echo  Finished Evaluation! Press any key to close this window.
echo =======================================================
pause
