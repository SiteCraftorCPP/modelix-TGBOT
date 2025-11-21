"""
Django интеграция для отправки уведомлений через signals
Этот файл нужно подключить в Django приложение для мгновенной отправки уведомлений
"""
import asyncio
from django.db.models.signals import post_save
from django.dispatch import receiver
from telegram import Bot
from telegram.error import TelegramError
from datetime import datetime
import logging

# Импорт моделей Django
try:
    from main.models import CallRequest, PrintOrder
except ImportError:
    # Если запускается вне Django проекта
    CallRequest = None
    PrintOrder = None

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Класс для отправки уведомлений в Telegram"""
    
    _instance = None
    _bot = None
    _channel_id = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TelegramNotifier, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._bot is None:
            # Попытка импорта конфигурации
            try:
                # Попытка импорта из Django settings
                from django.conf import settings
                BOT_TOKEN = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
                CHANNEL_ID = getattr(settings, 'TELEGRAM_CHANNEL_ID', None)
                
                # Если не найдено в settings, пытаемся импортировать из config
                if not BOT_TOKEN or not CHANNEL_ID:
                    try:
                        from main.telegram_config import BOT_TOKEN, CHANNEL_ID
                    except ImportError:
                        import os
                        BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
                        CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')
            except Exception:
                # Fallback на переменные окружения
                import os
                BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
                CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')
            
            if not BOT_TOKEN or not CHANNEL_ID:
                raise ValueError(
                    "TELEGRAM_BOT_TOKEN и TELEGRAM_CHANNEL_ID должны быть настроены!\n"
                    "Используйте один из способов:\n"
                    "1. Переменные окружения\n"
                    "2. Django settings.py\n"
                    "3. Файл main/telegram_config.py"
                )
            
            self._bot = Bot(token=BOT_TOKEN)
            self._channel_id = CHANNEL_ID
    
    async def send_message_async(self, message: str):
        """Асинхронная отправка сообщения"""
        try:
            await self._bot.send_message(
                chat_id=self._channel_id,
                text=message,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
            logger.info(f"Уведомление отправлено в канал {self._channel_id}")
        except TelegramError as e:
            logger.error(f"Ошибка отправки уведомления: {e}")
    
    def send_message(self, message: str):
        """Синхронная обёртка для отправки сообщения"""
        try:
            # Создаём новый event loop если его нет
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Если loop уже запущен, создаём task
            if loop.is_running():
                asyncio.create_task(self.send_message_async(message))
            else:
                # Иначе запускаем синхронно
                loop.run_until_complete(self.send_message_async(message))
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления: {e}")


def format_call_request_message(instance):
    """Форматировать сообщение о заявке на звонок"""
    status = "✅ Обработано" if instance.is_processed else "🔔 Новая заявка"
    date_str = instance.created_at.strftime('%d.%m.%Y %H:%M')
    
    # Экранирование HTML символов
    name = str(instance.name).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    phone = str(instance.phone).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    message = f"""
<b>{status} - ЗВОНОК</b>

📞 <b>Заявка на звонок #{instance.id}</b>

👤 <b>Имя:</b> {name}
📱 <b>Телефон:</b> <code>{phone}</code>
🕐 <b>Дата:</b> {date_str}

<a href="https://3dmodelix.ru/admin/main/callrequest/{instance.id}/change/">Открыть в админке</a>
"""
    return message.strip()


def format_print_order_message(instance):
    """Форматировать сообщение о заявке на печать"""
    status = "✅ Обработано" if instance.is_processed else "🔔 Новая заявка"
    date_str = instance.created_at.strftime('%d.%m.%Y %H:%M')
    
    # Маппинг типов услуг
    service_types = {
        'other': 'Другое',
        'complex': 'Комплекс услуг',
        '3d_modeling': '3D моделирование',
        '3d_printing': '3D печать',
        '3d_scanning': '3D сканирование',
        'reverse_engineering': 'Реверс-инжиниринг',
        'engineering': 'Инжиниринг',
        'post_processing': 'Постобработка',
    }
    
    service_name = service_types.get(instance.service_type, instance.service_type)
    
    file_info = ""
    if instance.file:
        file_info = f"\n📎 <b>Файл:</b> Прикреплен"
    
    # Обработка пустого сообщения
    message_text = instance.message if instance.message else "Не указано"
    if str(message_text).strip() == '':
        message_text = "Не указано"
    
    # Экранирование HTML символов
    name = str(instance.name).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    phone = str(instance.phone).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    email = str(instance.email).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    message_text = str(message_text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    # Безопасное обрезание текста
    message_preview = message_text[:200] if len(message_text) > 200 else message_text
    ellipsis = '...' if len(message_text) > 200 else ''
    
    message = f"""
<b>{status} - ПЕЧАТЬ</b>

🖨️ <b>Заявка на печать #{instance.id}</b>

👤 <b>Имя:</b> {name}
📱 <b>Телефон:</b> <code>{phone}</code>
📧 <b>Email:</b> {email}
🛠️ <b>Услуга:</b> {service_name}
💬 <b>Сообщение:</b> {message_preview}{ellipsis}{file_info}
🕐 <b>Дата:</b> {date_str}

<a href="https://3dmodelix.ru/admin/main/printorder/{instance.id}/change/">Открыть в админке</a>
"""
    return message.strip()


# Signal handlers
if CallRequest is not None:
    @receiver(post_save, sender=CallRequest)
    def notify_new_call_request(sender, instance, created, **kwargs):
        """Отправить уведомление о новой заявке на звонок"""
        if created:  # Только для новых заявок
            try:
                message = format_call_request_message(instance)
                notifier = TelegramNotifier()
                notifier.send_message(message)
            except Exception as e:
                logger.error(f"Ошибка отправки уведомления о заявке на звонок: {e}")

if PrintOrder is not None:
    @receiver(post_save, sender=PrintOrder)
    def notify_new_print_order(sender, instance, created, **kwargs):
        """Отправить уведомление о новой заявке на печать"""
        if created:  # Только для новых заявок
            try:
                message = format_print_order_message(instance)
                notifier = TelegramNotifier()
                notifier.send_message(message)
            except Exception as e:
                logger.error(f"Ошибка отправки уведомления о заявке на печать: {e}")

