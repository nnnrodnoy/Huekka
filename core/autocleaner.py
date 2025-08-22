import os
import sqlite3
import asyncio
import time
import logging
import re
from pathlib import Path
from telethon import events
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
        self.task = asyncio.create_task(self.cleanup_task())
        
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
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS autoclean_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    message_id INTEGER NOT NULL,
                    delete_at REAL NOT NULL
                )
            ''')
            conn.commit()

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

    async def cleanup_task(self):
        """Фоновая задача для удаления сообщений"""
        while True:
            try:
                current_time = time.time()
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT id, chat_id, message_id FROM autoclean_queue WHERE delete_at <= ?",
                        (current_time,)
                    )
                    messages = cursor.fetchall()
                    
                    if messages:
                        logger.info(f"Найдено {len(messages)} сообщений для удаления")
                    
                    for msg_id, chat_id, message_id in messages:
                        try:
                            # Пытаемся удалить сообщение
                            await self.bot.client.delete_messages(chat_id, message_id)
                            logger.info(f"Сообщение {message_id} в чате {chat_id} удалено")
                        except Exception as e:
                            logger.warning(f"Не удалось удалить сообщение {message_id} в чате {chat_id}: {str(e)}")
                        
                        # Удаляем запись из очереди
                        cursor.execute("DELETE FROM autoclean_queue WHERE id = ?", (msg_id,))
                    
                    conn.commit()
            except Exception as e:
                logger.error(f"Ошибка в cleanup_task: {str(e)}")
                # В случае ошибки ждем перед следующей попыткой
                await asyncio.sleep(60)
            
            await asyncio.sleep(15)  # Проверяем каждые 15 секунд