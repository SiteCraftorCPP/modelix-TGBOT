"""
Телеграм-бот для отправки уведомлений о заказах Modelix
"""
import asyncio
import sqlite3
import json
import os
import time
from datetime import datetime
from telegram.error import TelegramError
import logging

from config import BOT_TOKEN, CHANNEL_ID, DJANGO_DB_PATH
from telegram_client import create_telegram_bot, resolve_proxy_url

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class ModelixNotificationBot:
    """Бот для отправки уведомлений о заявках"""
    
    def __init__(self):
        if resolve_proxy_url():
            logger.info("Telegram API через прокси (TELEGRAM_PROXY_URL / TELEGRAM_PROXY)")
        self.bot = create_telegram_bot(BOT_TOKEN)
        self.channel_id = CHANNEL_ID
        self.db_path = DJANGO_DB_PATH
        # Абсолютный путь к файлу состояния
        self.state_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bot_state.json')
        self.last_call_request_id = 0
        self.last_print_order_id = 0
        # Кэш для предотвращения дублирования
        self.recent_calls = []  # [(name, phone, timestamp), ...]
        
    def get_db_connection(self):
        """Получить соединение с БД Django"""
        return sqlite3.connect(self.db_path)
    
    async def send_notification(self, message: str, file_path=None):
        """Отправить уведомление в канал, с опциональным файлом"""
        try:
            if file_path and os.path.exists(file_path):
                # Отправляем файл БЕЗ СЖАТИЯ через send_document
                try:
                    with open(file_path, 'rb') as file:
                        await self.bot.send_document(
                            chat_id=self.channel_id,
                            document=file,
                            caption=message,
                            parse_mode='HTML'
                        )
                    logger.info(f"Уведомление с файлом отправлено в канал {self.channel_id}: {file_path}")
                except Exception as file_error:
                    logger.error(f"Ошибка отправки файла {file_path}: {file_error}")
                    # Отправляем только текст если файл не отправился
                    await self.bot.send_message(
                        chat_id=self.channel_id,
                        text=message,
                        parse_mode='HTML',
                        disable_web_page_preview=True
                    )
                    logger.info(f"Уведомление отправлено без файла в канал {self.channel_id}")
            else:
                # Отправляем только текст
                await self.bot.send_message(
                    chat_id=self.channel_id,
                    text=message,
                    parse_mode='HTML',
                    disable_web_page_preview=True
                )
                logger.info(f"Уведомление отправлено в канал {self.channel_id}")
        except TelegramError as e:
            logger.error(f"Ошибка отправки уведомления: {e}")
        except Exception as e:
            logger.error(f"Неожиданная ошибка отправки уведомления: {e}")
    
    def format_call_request(self, request_data):
        """Форматировать сообщение о заявке на звонок"""
        req_id, name, phone, created_at, is_processed = request_data
        
        status = "✅ Обработано" if is_processed else "🔔 Новая заявка"
        
        # Парсим дату
        try:
            dt = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S.%f')
        except ValueError:
            try:
                dt = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                # Если не удалось распарсить, используем текущее время
                dt = datetime.now()
        
        date_str = dt.strftime('%d.%m.%Y %H:%M')
        
        # Экранирование HTML символов в имени
        name = str(name).replace('<', '&lt;').replace('>', '&gt;').replace('&', '&amp;')
        phone = str(phone).replace('<', '&lt;').replace('>', '&gt;').replace('&', '&amp;')
        
        message = f"""
<b>{status} - ЗВОНОК</b>

👤 <b>Имя:</b> {name}
📱 <b>Телефон:</b> <code>{phone}</code>
"""
        return message.strip()
    
    def format_print_order(self, order_data):
        """Форматировать сообщение о заявке на печать"""
        order_id, name, phone, email, service_type, message_text, file_path, created_at, is_processed = order_data
        
        status = "✅ Обработано" if is_processed else "🔔 Новая заявка"
        
        # Парсим дату
        try:
            dt = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S.%f')
        except ValueError:
            try:
                dt = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                # Если не удалось распарсить, используем текущее время
                dt = datetime.now()
        
        date_str = dt.strftime('%d.%m.%Y %H:%M')
        
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
        
        service_name = service_types.get(service_type, service_type)
        
        # Обработка пустого сообщения
        if not message_text or str(message_text).strip() == '':
            message_text = "Не указано"
        
        # Экранирование HTML символов
        name = str(name).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        phone = str(phone).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        email = str(email).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        message_text = str(message_text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        # Безопасное обрезание текста
        message_preview = message_text[:200] if len(message_text) > 200 else message_text
        ellipsis = '...' if len(message_text) > 200 else ''
        
        message = f"""
<b>🔔 Заявка c данными</b>

👤 <b>Имя:</b> {name}
📱 <b>Телефон:</b> <code>{phone}</code>
📧 <b>Email:</b> {email}
🛠️ <b>Услуга:</b> {service_name}
💬 <b>Сообщение:</b> {message_preview}{ellipsis}
"""
        return message.strip()
    
    def is_duplicate_call(self, name, phone):
        """Проверить, не дублируется ли заявка на звонок (создана вместе с печатью)"""
        current_time = time.time()
        # Очищаем старые записи (старше 2 минут)
        self.recent_calls = [(n, p, t) for n, p, t in self.recent_calls if current_time - t < 120]
        
        # Проверяем есть ли такая же заявка в последние 2 минуты
        for cached_name, cached_phone, timestamp in self.recent_calls:
            if cached_name == name and cached_phone == phone:
                logger.info(f"Найден дубль заявки на звонок: {name} {phone} (создана {current_time - timestamp:.1f} сек назад)")
                return True
        
        # Добавляем в кэш
        self.recent_calls.append((name, phone, current_time))
        return False
    
    async def check_new_call_requests(self):
        """Проверить новые заявки на звонок"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Получаем новые заявки
            cursor.execute(
                """
                SELECT id, name, phone, created_at, is_processed
                FROM main_callrequest
                WHERE id > ?
                ORDER BY id ASC
                """,
                (self.last_call_request_id,)
            )
            
            new_requests = cursor.fetchall()
            
            for request in new_requests:
                request_id = request[0]
                name = str(request[1])
                phone = str(request[2])
                
                logger.info(f"Обрабатываем новую заявку на звонок ID={request_id}")
                
                # Проверяем на дубль (создана вместе с заявкой на печать)
                if self.is_duplicate_call(name, phone):
                    logger.info(f"Пропускаем дубль заявки на звонок ID={request_id}")
                else:
                    message = self.format_call_request(request)
                    await self.send_notification(message)
                
                self.last_call_request_id = request_id
                self.save_state()  # Сохраняем состояние после каждой заявки
                logger.info(f"Обновлен last_call_request_id до {self.last_call_request_id}")
            
            conn.close()
            
            if new_requests:
                logger.info(f"Обработано {len(new_requests)} новых заявок на звонок")
                
        except Exception as e:
            logger.error(f"Ошибка при проверке заявок на звонок: {e}")
    
    async def check_new_print_orders(self):
        """Проверить новые заявки на печать"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Получаем новые заявки
            cursor.execute(
                """
                SELECT id, name, phone, email, service_type, message, file, created_at, is_processed
                FROM main_printorder
                WHERE id > ?
                ORDER BY id ASC
                """,
                (self.last_print_order_id,)
            )
            
            new_orders = cursor.fetchall()
            
            for order in new_orders:
                order_id = order[0]
                name = str(order[1])
                phone = str(order[2])
                file_path = order[6]  # Путь к файлу из БД
                
                logger.info(f"Обрабатываем новую заявку на печать ID={order_id}, file_path из БД: {file_path}")
                
                # Добавляем в кэш чтобы избежать дублей звонков
                current_time = time.time()
                self.recent_calls.append((name, phone, current_time))
                logger.info(f"Добавлен в кэш: {name} {phone}")
                
                message = self.format_print_order(order)
                
                # Отправляем уведомление с текстом
                await self.send_notification(message, file_path=None)
                
                # Получаем ВСЕ файлы для этой заявки из разных возможных таблиц
                all_files = []
                
                # Пробуем разные варианты названий таблиц
                possible_table_names = [
                    'main_printorderfile',
                    'main_printorder_file', 
                    'main_orderfile',
                    'main_file',
                    'main_printorderfiles'
                ]
                
                for table_name in possible_table_names:
                    try:
                        # Пробуем разные варианты названий полей
                        possible_queries = [
                            f"SELECT file FROM {table_name} WHERE print_order_id = ?",
                            f"SELECT file FROM {table_name} WHERE order_id = ?",
                            f"SELECT file_path FROM {table_name} WHERE print_order_id = ?",
                            f"SELECT file_path FROM {table_name} WHERE order_id = ?",
                            f"SELECT file FROM {table_name} WHERE printorder_id = ?",
                        ]
                        
                        for query in possible_queries:
                            try:
                                cursor.execute(query, (order_id,))
                                file_records = cursor.fetchall()
                                if file_records:
                                    logger.info(f"Найдена таблица {table_name} с запросом {query}, файлов: {len(file_records)}")
                                    for file_record in file_records:
                                        if file_record[0]:
                                            all_files.append(str(file_record[0]).strip())
                                    break
                            except:
                                continue
                        
                        if all_files:
                            break
                    except:
                        continue
                
                # Если не нашли в связанных таблицах, пробуем поле file из main_printorder
                if not all_files and file_path and str(file_path).strip():
                    all_files.append(str(file_path).strip())
                    logger.info(f"Используем файл из поля file: {file_path}")
                
                # Отправляем ВСЕ файлы отдельными сообщениями
                django_project_path = os.path.dirname(self.db_path)  # /var/www/modelix
                files_sent = 0
                
                for file_path_str in all_files:
                    if not file_path_str:
                        continue
                    
                    # Пробуем несколько вариантов путей
                    possible_paths = [
                        os.path.join(django_project_path, 'media', file_path_str),
                        os.path.join(django_project_path, file_path_str),
                        file_path_str
                    ]
                    
                    full_file_path = None
                    for path in possible_paths:
                        if os.path.exists(path):
                            full_file_path = path
                            break
                    
                    if full_file_path:
                        try:
                            with open(full_file_path, 'rb') as file:
                                await self.bot.send_document(
                                    chat_id=self.channel_id,
                                    document=file,
                                    parse_mode='HTML'
                                )
                            logger.info(f"Файл отправлен: {full_file_path}")
                            files_sent += 1
                        except Exception as file_error:
                            logger.error(f"Ошибка отправки файла {full_file_path}: {file_error}")
                    else:
                        logger.warning(f"Файл не найден: {file_path_str}")
                
                if files_sent > 0:
                    logger.info(f"Отправлено файлов: {files_sent} из {len(all_files)}")
                elif all_files:
                    logger.warning(f"Файлы найдены в БД но не отправлены: {all_files}")
                
                self.last_print_order_id = order_id
                self.save_state()  # Сохраняем состояние после каждой заявки
                logger.info(f"Обновлен last_print_order_id до {self.last_print_order_id}")
            
            conn.close()
            
            if new_orders:
                logger.info(f"Обработано {len(new_orders)} новых заявок на печать")
                
        except Exception as e:
            logger.error(f"Ошибка при проверке заявок на печать: {e}")
    
    def load_state(self):
        """Загрузить состояние из файла"""
        try:
            logger.info(f"Проверяем файл состояния: {self.state_file}")
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.last_call_request_id = state.get('last_call_request_id', 0)
                    self.last_print_order_id = state.get('last_print_order_id', 0)
                    logger.info(f"Состояние загружено из {self.state_file}: звонки ID={self.last_call_request_id}, печать ID={self.last_print_order_id}")
            else:
                logger.info(f"Файл состояния не найден по пути {self.state_file}, начинаем с текущих максимальных ID")
                self.initialize_from_db()
        except Exception as e:
            logger.error(f"Ошибка загрузки состояния из {self.state_file}: {e}")
            self.initialize_from_db()
    
    def save_state(self):
        """Сохранить состояние в файл"""
        try:
            state = {
                'last_call_request_id': self.last_call_request_id,
                'last_print_order_id': self.last_print_order_id
            }
            with open(self.state_file, 'w') as f:
                json.dump(state, f)
            logger.info(f"Состояние сохранено в {self.state_file}: звонки={self.last_call_request_id}, печать={self.last_print_order_id}")
        except Exception as e:
            logger.error(f"Ошибка сохранения состояния в {self.state_file}: {e}")
    
    def initialize_from_db(self):
        """Инициализация из БД (только при первом запуске)"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Получить последний ID заявки на звонок
            cursor.execute("SELECT MAX(id) FROM main_callrequest")
            result = cursor.fetchone()
            self.last_call_request_id = result[0] if result[0] else 0
            
            # Получить последний ID заявки на печать
            cursor.execute("SELECT MAX(id) FROM main_printorder")
            result = cursor.fetchone()
            self.last_print_order_id = result[0] if result[0] else 0
            
            conn.close()
            
            # Сохранить состояние
            self.save_state()
            
            logger.info(f"Инициализация из БД: звонки ID={self.last_call_request_id}, печать ID={self.last_print_order_id}")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации из БД: {e}")
            raise
    
    async def initialize(self):
        """Инициализация бота"""
        try:
            # Загружаем состояние из файла
            self.load_state()
            
            logger.info("Бот будет отслеживать только НОВЫЕ заявки после последней обработанной")
            
            # Отправить уведомление о запуске
            await self.send_notification("<b>Бот уведомлений Modelix запущен</b>\n\n"
                                        "Отслеживание новых заявок активировано.")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации: {e}")
            raise
    
    async def run(self, interval=30):
        """Запустить бота с указанным интервалом проверки (в секундах)"""
        logger.info(f"Запуск бота с интервалом проверки {interval} секунд")
        
        await self.initialize()
        
        while True:
            try:
                # Сначала проверяем печать, потом звонки (чтобы избежать дублей)
                await self.check_new_print_orders()
                await self.check_new_call_requests()
                await asyncio.sleep(interval)
            except KeyboardInterrupt:
                logger.info("Остановка бота...")
                await self.send_notification("🛑 <b>Бот уведомлений Modelix остановлен</b>")
                break
            except Exception as e:
                logger.error(f"Ошибка в основном цикле: {e}")
                await asyncio.sleep(interval)


async def main():
    """Главная функция"""
    bot = ModelixNotificationBot()
    await bot.run(interval=30)


if __name__ == '__main__':
    asyncio.run(main())

