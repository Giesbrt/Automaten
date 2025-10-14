@echo off
echo Installing/Checking Packages ...
REM Freeze_versions?
py -3.12 -m pip install -r requirements.txt >nul
cd src
py -3.12 ./main.py
cd ..
pause
