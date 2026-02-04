@echo off
set APP_NAME=SistemaAtividades
set ICON_PATH=app\assets\icon.ico

echo Criando exe...
if exist "%ICON_PATH%" (
  pyinstaller --noconfirm --onefile --windowed --name "%APP_NAME%" ^
    --add-data "app\assets\style.qss;app\assets" ^
    --hidden-import PySide6.QtCharts ^
    --icon "%ICON_PATH%" app\main.py
) else (
  pyinstaller --noconfirm --onefile --windowed --name "%APP_NAME%" ^
    --add-data "app\assets\style.qss;app\assets" ^
    --hidden-import PySide6.QtCharts app\main.py
)
echo Finalizado. O exe esta em dist\%APP_NAME%.exe
