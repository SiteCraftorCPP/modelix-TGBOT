"""
Тестовый скрипт для проверки работоспособности бота
"""
import asyncio
from datetime import datetime
from telegram.error import TelegramError

from config import BOT_TOKEN, CHANNEL_ID
from telegram_client import create_telegram_bot, resolve_proxy_url


async def test_bot():
    """Тестирование подключения к боту и каналу"""
    print("Начинаем тестирование бота...")
    print(f"Токен бота: {BOT_TOKEN[:10]}...{BOT_TOKEN[-10:]}")
    print(f"ID канала: {CHANNEL_ID}")
    if resolve_proxy_url():
        print("Прокси: да (TELEGRAM_PROXY_URL / TELEGRAM_PROXY)")
    else:
        print("Прокси: нет")

    try:
        bot = create_telegram_bot(BOT_TOKEN)

        print("\n1. Проверка токена бота...")
        bot_info = await bot.get_me()
        print(f"OK Бот подключен: @{bot_info.username} ({bot_info.first_name})")

        print("\n2. Проверка доступа к каналу...")
        test_message = """
<b>🧪 Тестовое сообщение</b>

Это тестовое уведомление от бота Modelix.
Если вы видите это сообщение, значит бот настроен правильно! ✅

<i>Время теста: {time}</i>
""".format(time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        message = await bot.send_message(
            chat_id=CHANNEL_ID,
            text=test_message,
            parse_mode='HTML'
        )

        print(f"OK Сообщение успешно отправлено в канал (ID сообщения: {message.message_id})")

        print("\n3. Проверка доступа к базе данных...")
        import sqlite3
        import os
        from config import DJANGO_DB_PATH

        if not os.path.exists(DJANGO_DB_PATH):
            print(f"ERROR База данных не найдена: {DJANGO_DB_PATH}")
            return False

        conn = sqlite3.connect(DJANGO_DB_PATH)
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT COUNT(*) FROM main_callrequest")
            call_count = cursor.fetchone()[0]
            print(f"OK Найдено заявок на звонок: {call_count}")
        except sqlite3.OperationalError as e:
            print(f"WARNING Таблица main_callrequest не найдена: {e}")

        try:
            cursor.execute("SELECT COUNT(*) FROM main_printorder")
            print_count = cursor.fetchone()[0]
            print(f"OK Найдено заявок на печать: {print_count}")
        except sqlite3.OperationalError as e:
            print(f"WARNING Таблица main_printorder не найдена: {e}")

        conn.close()

        print("\n" + "="*50)
        print("SUCCESS Все проверки пройдены успешно!")
        print("READY Бот готов к работе!")
        print("="*50)

        return True

    except TelegramError as e:
        print(f"\nERROR Ошибка Telegram API: {e}")
        if "Unauthorized" in str(e):
            print("TIP Проверьте правильность токена бота в config.py")
        elif "Chat not found" in str(e):
            print("TIP Проверьте:")
            print("   - Правильность ID канала")
            print("   - Что бот добавлен в канал как администратор")
        return False

    except Exception as e:
        print(f"\nERROR Ошибка: {e}")
        return False


if __name__ == '__main__':
    asyncio.run(test_bot())
