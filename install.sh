#!/bin/bash
# Автоматическая установка бота Modelix для Linux

echo "🤖 Установка телеграм-бота Modelix"
echo "=================================="
echo ""

# Перейти в директорию скрипта
cd "$(dirname "$0")"

# Проверка Python
echo "1️⃣ Проверка Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 не найден. Установите Python 3.7+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d ' ' -f 2)
echo "✅ Python найден: $PYTHON_VERSION"
echo ""

# Создание виртуального окружения
echo "2️⃣ Создание виртуального окружения..."
if [ -d "venv" ]; then
    echo "⚠️  Виртуальное окружение уже существует, пропускаем..."
else
    python3 -m venv venv
    echo "✅ Виртуальное окружение создано"
fi
echo ""

# Активация и установка зависимостей
echo "3️⃣ Установка зависимостей..."
source venv/bin/activate
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt
echo "✅ Зависимости установлены"
echo ""

# Проверка конфигурации
echo "4️⃣ Проверка конфигурации..."
if grep -q "YOUR_BOT_TOKEN_HERE" config.py; then
    echo "⚠️  ВНИМАНИЕ: Не настроен BOT_TOKEN в config.py"
    echo ""
    read -p "Введите токен бота (от @BotFather): " BOT_TOKEN
    sed -i "s/YOUR_BOT_TOKEN_HERE/$BOT_TOKEN/" config.py
    echo "✅ Токен сохранён"
else
    echo "✅ Токен бота настроен"
fi

if grep -q "YOUR_CHANNEL_ID_HERE" config.py; then
    echo "⚠️  ВНИМАНИЕ: Не настроен CHANNEL_ID в config.py"
    echo ""
    read -p "Введите ID канала (например, -100XXXXXXXXX): " CHANNEL_ID
    sed -i "s/YOUR_CHANNEL_ID_HERE/$CHANNEL_ID/" config.py
    echo "✅ ID канала сохранён"
else
    echo "✅ ID канала настроен"
fi
echo ""

# Тестирование
echo "5️⃣ Тестирование подключения..."
python3 test_bot.py
TEST_RESULT=$?
echo ""

if [ $TEST_RESULT -eq 0 ]; then
    echo "✅ Все проверки пройдены!"
    echo ""
    echo "=================================="
    echo "🎉 Установка завершена!"
    echo "=================================="
    echo ""
    echo "Для запуска бота используйте:"
    echo "  ./start_bot.sh"
    echo ""
    echo "Для остановки:"
    echo "  ./stop_bot.sh"
    echo ""
    echo "Для установки как сервис (автозапуск):"
    echo "  sudo cp modelix-bot.service /etc/systemd/system/"
    echo "  sudo nano /etc/systemd/system/modelix-bot.service  # настроить пути"
    echo "  sudo systemctl enable modelix-bot"
    echo "  sudo systemctl start modelix-bot"
    echo ""
else
    echo "❌ Тестирование не прошло"
    echo "Проверьте конфигурацию в config.py"
    echo ""
    exit 1
fi


