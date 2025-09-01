# ©️ nnnrodnoy, 2025
# 💬 @nnnrodnoy
# This file is part of Huekka
# 🌐 https://github.com/nnnrodnoy/Huekka/
# You can redistribute it and/or modify it under the terms of the MIT License
# 🔑 https://opensource.org/licenses/MIT
import asyncio
import time
import logging
import re
from telethon import events
from telethon.errors import RPCError
from config import BotConfig

logger = logging.getLogger("UserBot.AutoCleaner")

class AutoCleaner:
    def __init__(self, bot, enabled=None, delay=None):
        self.bot = bot
        
        self.enabled = enabled if enabled is not None else BotConfig.AUTOCLEAN["enabled"]
        self.default_delay = delay if delay is not None else BotConfig.AUTOCLEAN["default_delay"]
        
        autoclean_config = BotConfig.AUTOCLEAN
        self.tracked_commands = autoclean_config["tracked_commands"]
        
        self.compiled_patterns = [
            re.compile(pattern.format(re.escape(bot.command_prefix)))
            for pattern in self.tracked_commands
        ]
        
        self.cleanup_task = None
        self.is_running = False
        
        @bot.client.on(events.NewMessage(outgoing=True))
        async def outgoing_handler(event):
            if self.enabled and (event.is_channel or event.is_group or event.is_private):
                await self.process_message(event)

    async def start(self):
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
        text = event.raw_text or ""
        for pattern in self.compiled_patterns:
            if pattern.match(text):
                logger.debug(f"Найдено сообщение для автоочистки: {text}")
                await self.schedule_cleanup(event)
                return

    async def schedule_cleanup(self, message):
        """Добавление сообщения в очередь на удаление"""
        try:
            success = self.bot.db.add_to_autoclean(
                message.chat_id, 
                message.id, 
                self.default_delay
            )
            
            if success:
                logger.info(f"Сообщение {message.id} в чате {message.chat_id} запланировано на удаление")
            else:
                logger.error(f"Ошибка планирования удаления сообщения {message.id}")
                
        except Exception as e:
            logger.error(f"Ошибка планирования удаления: {str(e)}")

    async def cleanup_loop(self):
        """Основной цикл автоочистки"""
        while self.is_running:
            try:
                if not self.bot.client.is_connected():
                    logger.debug("Бот отключен, пропускаем очистку")
                    await asyncio.sleep(10)
                    continue
                
                pending_messages = self.bot.db.get_pending_autoclean()
                
                if pending_messages:
                    logger.info(f"Найдено {len(pending_messages)} сообщений для удаления")
                
                for msg_id, chat_id, message_id, attempts in pending_messages:
                    try:
                        # Пытаемся получить entity для чата
                        try:
                            entity = await self.bot.client.get_input_entity(chat_id)
                        except Exception as e:
                            logger.warning(f"Не удалось получить entity для чата {chat_id}: {str(e)}")
                            self.bot.db.remove_from_autoclean(msg_id)
                            continue
                            
                        await self.bot.client.delete_messages(entity, message_id)
                        logger.info(f"Сообщение {message_id} в чате {chat_id} удалено")
                        
                        self.bot.db.remove_from_autoclean(msg_id)
                        
                    except RPCError as e:
                        # Обработка ошибки "Could not find the input entity"
                        if "Could not find the input entity" in str(e):
                            logger.warning(f"Чат {chat_id} недоступен, удаляем запись из очереди")
                            self.bot.db.remove_from_autoclean(msg_id)
                        else:
                            logger.warning(f"Ошибка RPC при удалении сообщения {message_id}: {str(e)}")
                            
                            new_attempts = attempts + 1
                            
                            if new_attempts >= 5:
                                logger.warning(f"Превышено максимальное количество попыток для сообщения {message_id}, удаляем из очереди")
                                self.bot.db.remove_from_autoclean(msg_id)
                            else:
                                new_delete_at = time.time() + 60
                                self.bot.db.update_autoclean_attempt(msg_id, new_attempts, new_delete_at)
                            
                    except Exception as e:
                        logger.error(f"Неизвестная ошибка при удалении сообщения {message_id}: {str(e)}")
                        self.bot.db.remove_from_autoclean(msg_id)
                    
            except Exception as e:
                logger.error(f"Ошибка в cleanup_loop: {str(e)}")
            
            await asyncio.sleep(15) 

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
