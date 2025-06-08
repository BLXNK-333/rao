@echo off
setlocal enabledelayedexpansion

:: Проверка Python
where python >nul 2>nul
if errorlevel 1 (
    echo Python is not installed. Please install Python 3.8.20 or newer.
    pause
    exit /b 1
)

:: Проверка версии
for /f "tokens=2 delims== " %%A in ('python -c "import sys; print('version=' + sys.version.split()[0])"') do set VER=%%A
for /f "tokens=1-3 delims=." %%a in ("!VER!") do (
    set MAJ=%%a
    set MIN=%%b
    set PATCH=%%c
)

if !MAJ! LSS 3 (
    echo Python version too old.
    pause
    exit /b 1
)
if !MAJ! EQU 3 if !MIN! LSS 8 (
    echo Python version too old.
    pause
    exit /b 1
)

:: Создание виртуального окружения
if not exist .venv (
    python -m venv .venv
)

:: Установка зависимостей
call .venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt
deactivate

:: Копирование ярлыка на рабочий стол
powershell -ExecutionPolicy Bypass -File create_shortcut.ps1
echo Установка завершена.
pause
