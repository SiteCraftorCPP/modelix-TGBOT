"""
Пример конфигурации телеграм-бота для уведомлений Modelix
Скопируйте этот файл в config.py и заполните своими данными
"""
import os

# Токен бота от @BotFather
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')

# ID канала для уведомлений (можно получить через @userinfobot)
# Формат: -100XXXXXXXXX для приватных каналов или @channel_name для публичных
CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID', 'YOUR_CHANNEL_ID_HERE')

# Путь к базе данных Django на VPS
DJANGO_DB_PATH = '/var/www/modelix/db.sqlite3'

# Интервал проверки новых заявок (в секундах)
CHECK_INTERVAL = 30

# URL сайта для ссылок в сообщениях
SITE_URL = 'https://3dmodelix.ru'

# Админ панель URL
ADMIN_URL = f'{SITE_URL}/admin'
