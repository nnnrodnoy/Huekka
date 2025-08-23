import os
import sqlite3
import asyncio
import time
import logging
import re
from pathlib import Path
from telethon import events
from telethon.errors import RPCError
from config import BotConfig

logger = logging.getLogger("UserBot.AutoCleaner")

class AutoCleaner:
    def __init__(self, bot, enabled=None, delay=None):
        self.bot = bot
        self.db_path = Path("cash") / "autoclean.db"
        
        # Используем переданные настройки или загружаем из конфига
        self.enabled = enabled if enabled is not None else BotConfig.AUTOCLEAN["enabled"]
        self.default_delay = delay if delay is not None else BotConfig.AUTOCLEAN["default_delay"]
        
        # Загрузка настроек исключительно из конфига
        autoclean_config = BotConfig.AUTOCLEAN
        self.tracked_commands = autoclean_config["tracked_commands"]
        
        # Компилируем регулярные выражения
        self.compiled_patterns = [
            re.compile(pattern.format(re.escape(bot.command_prefix)))
            for pattern in self.tracked_commands
        ]
        
        self._init_db()
        self.cleanup_task = None
        self.is_running = False
        
        # Регистрация обработчика всех исходящих сообщений от бота
        @bot.client.on(events.NewMessage(outgoing=True))
        async def outgoing_handler(event):
            if self.enabled and (event.is_channel or event.is_group or event.is_private):
                await self.process_message(event)

    def _init_db(self):
        """Инициализация базы данных для автоочистки"""
        os.makedirs("cash", exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Создаем таблицу, если она не существует
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS autoclean_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    message_id INTEGER NOT NULL,
                    delete_at REAL NOT NULL,
                    attempts INTEGER DEFAULT 0
                )
            ''')
            
            # Проверяем наличие колонки attempts и добавляем ее, если отсутствует
            cursor.execute("PRAGMA table_info(autoclean_queue)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'attempts' not in columns:
                cursor.execute("ALTER TABLE autoclean_queue ADD COLUMN attempts INTEGER DEFAULT 0")
                logger.info("Добавлена колонка attempts в таблицу autoclean_queue")
            
            conn.commit()

    async def start(self):
        """Запуск задачи автоочистки"""
        if self.enabled and not self.is_running:
            self.is_running = True
            self.cleanup_task = asyncio.create_task(self.cleanup_loop())
            logger.info("Автоочистка запущена")

    async def stop(self):
        """Остановка задачи автоочистки"""
        if self.cleanup_task:
            self.is_running = False
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
            logger.info("Автоочистка остановлена")

    async def process_message(self, event):
        """Обработка исходящего сообщения бота"""
        # Проверяем, является ли сообщение результатом отслеживаемой команды
        text = event.raw_text or ""
        for pattern in self.compiled_patterns:
            if pattern.match(text):
                logger.debug(f"Найдено сообщение для автоочистки: {text}")
                await self.schedule_cleanup(event)
                return

    async def schedule_cleanup(self, message):
        """Добавление сообщения в очередь на удаление"""
        delete_at = time.time() + self.default_delay
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO autoclean_queue (chat_id, message_id, delete_at) VALUES (?, ?, ?)",
                    (message.chat_id, message.id, delete_at)
                )
                conn.commit()
            logger.info(f"Сообщение {message.id} в чате {message.chat_id} запланировано на удаление")
        except Exception as e:
            logger.error(f"Ошибка планирования удаления: {str(e)}")

    async def cleanup_loop(self):
        """Основной цикл автоочистки"""
        while self.is_running:
            try:
                # Проверяем, подключен ли бот
                if not self.bot.client.is_connected():
                    logger.debug("Бот отключен, пропускаем очистку")
                    await asyncio.sleep(10)
                    continue
                
                current_time = time.time()
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT id, chat_id, message_id, attempts FROM autoclean_queue WHERE delete_at <= ?",
                        (current_time,)
                    )
                    messages = cursor.fetchall()
                    
                    if messages:
                        logger.info(f"Найдено {len(messages)} сообщений для удаления")
                    
                    for msg_id, chat_id, message_id, attempts in messages:
                        try:
                            # Пытаемся удалить сообщение
                            await self.bot.client.delete_messages(chat_id, message_id)
                            logger.info(f"Сообщение {message_id} в чате {chat_id} удалено")
                            
                            # Удаляем запись из очереди
                            cursor.execute("DELETE FROM autoclean_queue WHERE id = ?", (msg_id,))
                            
                        except RPCError as e:
                            logger.warning(f"Ошибка RPC при удалении сообщения {message_id}: {str(e)}")
                            
                            # Увеличиваем счетчик попыток
                            new_attempts = attempts + 1
                            
                            if new_attempts >= 5:  # Максимум 5 попыток
                                logger.warning(f"Превышено максимальное количество попыток для сообщения {message_id}, удаляем из очереди")
                                cursor.execute("DELETE FROM autoclean_queue WHERE id = ?", (msg_id,))
                            else:
                                # Обновляем время удаления (через 1 минуту) и счетчик попыток
                                new_delete_at = time.time() + 60
                                cursor.execute(
                                    "UPDATE autoclean_queue SET delete_at = ?, attempts = ? WHERE id = ?",
                                    (new_delete_at, new_attempts, msg_id)
                                )
                                
                        except Exception as e:
                            logger.error(f"Неизвестная ошибка при удалении сообщения {message_id}: {str(e)}")
                            # Удаляем запись из очереди при неизвестной ошибке
                            cursor.execute("DELETE FROM autoclean_queue WHERE id = ?", (msg_id,))
                    
                    conn.commit()
                    
            except Exception as e:
                logger.error(f"Ошибка в cleanup_loop: {str(e)}")
            
            await asyncio.sleep(15)  # Проверяем каждые 15 секунд

    def update_settings(self, enabled=None, delay=None):
        """Обновление настроек автоклинера"""
        if enabled is not None:
            self.enabled = enabled
            if enabled and not self.is_running:
                asyncio.create_task(self.start())
            elif not enabled and self.is_running:
                asyncio.create_task(self.stop())
                
        if delay is not None:
            self.default_delay = delay
