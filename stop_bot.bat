@echo off
REM Скрипт для остановки бота на Windows

echo Остановка бота...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq bot.py"

echo Бот остановлен
pause


