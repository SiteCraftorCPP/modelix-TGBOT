@echo off
REM Скрипт для запуска бота на Windows

echo Переход в директорию бота...
cd /d "%~dp0"

echo Проверка виртуального окружения...
if not exist "venv\" (
    echo Создание виртуального окружения...
    python -m venv venv
)

echo Активация виртуального окружения...
call venv\Scripts\activate.bat

echo Установка зависимостей...
pip install -r requirements.txt

echo Запуск бота...
start /B python bot.py > bot.log 2>&1

echo Бот запущен!
echo Логи сохраняются в bot.log
echo.
echo Для остановки используйте stop_bot.bat или нажмите Ctrl+C
pause


