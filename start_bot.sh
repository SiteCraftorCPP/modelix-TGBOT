#!/bin/bash
# Скрипт для запуска бота в фоне

# Перейти в директорию со скриптом
cd "$(dirname "$0")"

# Проверить наличие виртуального окружения
if [ ! -d "venv" ]; then
    echo "Создание виртуального окружения..."
    python3 -m venv venv
fi

# Активировать виртуальное окружение
source venv/bin/activate

# Установить зависимости
echo "Установка зависимостей..."
pip install -r requirements.txt

# Запустить бота в фоне
echo "Запуск бота..."
nohup python bot.py > bot.log 2>&1 &

# Получить PID
PID=$!
echo $PID > bot.pid

echo "Бот запущен с PID: $PID"
echo "Логи сохраняются в bot.log"
echo ""
echo "Для остановки используйте: kill $PID"
echo "Или: ./stop_bot.sh"


