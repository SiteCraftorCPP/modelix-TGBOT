#!/bin/bash
# Скрипт для остановки бота

# Перейти в директорию со скриптом
cd "$(dirname "$0")"

if [ -f "bot.pid" ]; then
    PID=$(cat bot.pid)
    echo "Остановка бота с PID: $PID"
    kill $PID
    rm bot.pid
    echo "Бот остановлен"
else
    echo "PID файл не найден. Ищем процесс..."
    PID=$(ps aux | grep '[b]ot.py' | awk '{print $2}')
    if [ ! -z "$PID" ]; then
        echo "Найден процесс с PID: $PID"
        kill $PID
        echo "Бот остановлен"
    else
        echo "Процесс бота не найден"
    fi
fi


