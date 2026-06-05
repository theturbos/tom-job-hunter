@echo off
chcp 65001 >nul 2>&1
cd /d "C:\Users\TurboS\.tom-job-hunter"
if exist ".venv\Scripts\activate.bat" call ".venv\Scripts\activate.bat"
python bot.py
pause
