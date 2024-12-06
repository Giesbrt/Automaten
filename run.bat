@echo off
echo Installing/Checking Packages ...
REM Freeze_versions?
py -3.13 -m pip install -r requirements.txt >nul
cd src
py -3.13 ./main.py
pause
