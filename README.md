# Telegram-бот уведомлений Modelix

Автоматические уведомления о заявках с сайта 3dmodelix.ru в Telegram-канал.

## Быстрый старт

1. **Создать бота через @BotFather**
2. **Создать канал и добавить бота как админа**
3. **Настроить config.py:**
   ```bash
   cp config.example.py config.py
   # Отредактировать config.py - вставить токен и ID канала
   ```
4. **Установить и запустить:**
   ```bash
   pip install python-telegram-bot==13.15
   python test_bot.py  # Тест
   python bot.py       # Запуск
   ```

## Файлы

- `bot.py` - основной код бота
- `config.py` - настройки (создать из config.example.py)
- `test_bot.py` - тестирование
- `django_integration.py` - интеграция с Django signals

## Деплой на VPS

```bash
git clone https://github.com/SiteCraftorCPP/modelix-TGBOT.git
cd modelix-TGBOT
cp config.example.py config.py
# Настроить config.py
pip install -r requirements.txt
python test_bot.py
python bot.py
```
