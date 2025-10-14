@echo off
py -3.12 -m venv .env
call .\.env\scripts\activate.bat
python.exe -m pip install --upgrade pip
pip install --upgrade gevent
pip install -r requirements.txt --upgrade
.\.env\Scripts\python.exe -m auto_py_to_exe -c ./pyautoinst-config.json
deactivate
rmdir /s /q .env
