@echo off
REM Freeze_versions?
py -3.13 -m pip install -r requirements.txt >nul
py -3.13 ./src/main.py
pause
