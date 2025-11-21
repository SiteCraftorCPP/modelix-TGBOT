@echo off
REM Автоматическая установка бота Modelix для Windows

echo 🤖 Установка телеграм-бота Modelix
echo ==================================
echo.

REM Перейти в директорию скрипта
cd /d "%~dp0"

REM Проверка Python
echo 1️⃣ Проверка Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден. Установите Python 3.7+
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Python найден: %PYTHON_VERSION%
echo.

REM Создание виртуального окружения
echo 2️⃣ Создание виртуального окружения...
if exist "venv\" (
    echo ⚠️  Виртуальное окружение уже существует, пропускаем...
) else (
    python -m venv venv
    echo ✅ Виртуальное окружение создано
)
echo.

REM Активация и установка зависимостей
echo 3️⃣ Установка зависимостей...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt
echo ✅ Зависимости установлены
echo.

REM Проверка конфигурации
echo 4️⃣ Проверка конфигурации...
findstr "YOUR_BOT_TOKEN_HERE" config.py >nul
if not errorlevel 1 (
    echo ⚠️  ВНИМАНИЕ: Не настроен BOT_TOKEN в config.py
    echo.
    set /p BOT_TOKEN="Введите токен бота (от @BotFather): "
    powershell -Command "(gc config.py) -replace 'YOUR_BOT_TOKEN_HERE', '%BOT_TOKEN%' | Out-File -encoding ASCII config.py"
    echo ✅ Токен сохранён
) else (
    echo ✅ Токен бота настроен
)

findstr "YOUR_CHANNEL_ID_HERE" config.py >nul
if not errorlevel 1 (
    echo ⚠️  ВНИМАНИЕ: Не настроен CHANNEL_ID в config.py
    echo.
    set /p CHANNEL_ID="Введите ID канала (например, -100XXXXXXXXX): "
    powershell -Command "(gc config.py) -replace 'YOUR_CHANNEL_ID_HERE', '%CHANNEL_ID%' | Out-File -encoding ASCII config.py"
    echo ✅ ID канала сохранён
) else (
    echo ✅ ID канала настроен
)
echo.

REM Тестирование
echo 5️⃣ Тестирование подключения...
python test_bot.py
if errorlevel 1 (
    echo.
    echo ❌ Тестирование не прошло
    echo Проверьте конфигурацию в config.py
    echo.
    pause
    exit /b 1
)

echo.
echo ==================================
echo 🎉 Установка завершена!
echo ==================================
echo.
echo Для запуска бота используйте:
echo   start_bot.bat
echo.
echo Для остановки:
echo   stop_bot.bat
echo.
echo Для запуска в фоне:
echo   start /B python bot.py
echo.
pause


