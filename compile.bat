@echo off
py -3.12 -m venv .env
call .\.env\scripts\activate.bat
python.exe -m pip install --upgrade pip
pip install --upgrade gevent
pip install -r requirements.txt --upgrade
.\.env\Scripts\python.exe -m PyInstaller --noconfirm --onedir --windowed --icon ".\src\default-config\data\assets\app_icons\shelline\logo-nobg.ico" --add-data ".\src\default-config;default-config/" --hidden-import "pywin32" --hidden-import "cachetools" --collect-all "cachetools" --recursive-copy-metadata "cachetools" --collect-all "pywin32" --recursive-copy-metadata "pywin32" --add-data ".\.env\Lib\site-packages\stdlib_list;stdlib_list/" --add-data ".\.env\Lib\site-packages\win32;win32/" --add-data ".\.env\Lib\site-packages\win32com;win32com/" --add-data ".\.env\Lib\site-packages\win32comext;win32comext/" --add-data ".\.env\Lib\site-packages\win32ctypes;win32ctypes/" --collect-all "win32con" --collect-all "win32file" --hidden-import "win32con" --hidden-import "win32file" --hidden-import "PySide6.QtCore" --hidden-import "PySide6.QtGui" --collect-all "PySide6.QtCore" --collect-all "PySide6.QtGui" --recursive-copy-metadata "PySide6"  ".\src\main.py"
deactivate
rmdir /s /q .\.env
