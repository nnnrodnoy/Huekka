import os
import sys
import time
import asyncio
import logging
import json
import re
from pathlib import Path
from telethon import events
from config import BotConfig

logger = logging.getLogger("UserBot.System")

class SystemModule:
    def __init__(self, bot):
        self.bot = bot
        self.bot.start_time = time.time()
        
        # ID эмодзи из конфига
        self.restart_emoji_id = BotConfig.EMOJI_IDS["restart"]
        self.clock_emoji_id = BotConfig.EMOJI_IDS["clock"]
        
        # Путь к файлу с информацией о перезагрузке
        self.restart_file = Path("cash") / "restart_info.json"
        
        # Проверяем, нужно ли отправить сообщение о завершении перезагрузки
        if self.restart_file.exists():
            try:
                with open(self.restart_file, "r") as f:
                    restart_data = json.load(f)
                
                asyncio.create_task(self.send_restart_complete(restart_data))
            except Exception as e:
                logger.error(f"Ошибка обработки restart_info: {str(e)}")
            finally:
                try:
                    self.restart_file.unlink()
                except:
                    pass

        # Регистрируем обработчики команд напрямую, без модульной системы
        @bot.client.on(events.NewMessage(outgoing=True, pattern=rf'^{re.escape(bot.command_prefix)}restart\b'))
        async def restart_handler(event):
            await self.cmd_restart(event)
            
        @bot.client.on(events.NewMessage(outgoing=True, pattern=rf'^{re.escape(bot.command_prefix)}reboot\b'))
        async def reboot_handler(event):
            await self.cmd_restart(event)
            
        @bot.client.on(events.NewMessage(outgoing=True, pattern=rf'^{re.escape(bot.command_prefix)}online\b'))
        async def online_handler(event):
            await self.cmd_online(event)
            
        @bot.client.on(events.NewMessage(outgoing=True, pattern=rf'^{re.escape(bot.command_prefix)}uptime\b'))
        async def uptime_handler(event):
            await self.cmd_online(event)
    
    async def send_restart_complete(self, restart_data):
        """Редактирует сообщение о завершении перезагрузки"""
        try:
            # Ждем пока бот полностью инициализируется
            await asyncio.sleep(3)
            
            # Формируем сообщение
            if restart_data["is_premium"]:
                text = f"[⚙️](emoji/{self.restart_emoji_id}) **Huekka успешно перезагружен!**"
            else:
                text = "⚙️ **Huekka успешно перезагружен!**"
            
            # Редактируем исходное сообщение
            msg = await self.bot.client.edit_message(
                entity=restart_data["chat_id"],
                message=restart_data["message_id"],
                text=text
            )
            
            # Добавляем сообщение в автоочистку
            await self.add_to_autoclean(msg)
            
        except Exception as e:
            logger.error(f"Ошибка редактирования restart complete: {str(e)}")

    async def add_to_autoclean(self, message):
        """Добавляет сообщение в автоочистку"""
        try:
            if hasattr(self.bot, 'autocleaner') and self.bot.autocleaner.enabled:
                # Используем встроенный автоочиститель
                await self.bot.autocleaner.schedule_cleanup(message)
        except Exception as e:
            logger.error(f"Ошибка добавления в автоочистку: {str(e)}")

    async def is_premium_user(self, event):
        try:
            user = await event.get_sender()
            return user.premium if hasattr(user, 'premium') else False
        except Exception:
            return False

    async def format_time(self, seconds):
        """Форматирование времени в читаемый вид"""
        days, remainder = divmod(seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(days)}д {int(hours)}ч {int(minutes)}мин {int(seconds)}сек"

    async def cmd_restart(self, event):
        """Обработчик команды .restart"""
        is_premium = await self.is_premium_user(event)
        
        try:
            # Сохраняем информацию для отправки после перезагрузки
            restart_data = {
                "chat_id": event.chat_id,
                "message_id": event.id,
                "is_premium": is_premium
            }
            
            # Сохраняем в файл в папке cash
            with open(self.restart_file, "w") as f:
                json.dump(restart_data, f)
            
            # Сообщение о начале перезагрузки
            if is_premium:
                msg = await event.edit(f"[⚙️](emoji/{self.restart_emoji_id}) **Перезагрузка Huekka...**")
            else:
                msg = await event.edit("⚙️ **Перезагрузка Huekka...**")
            
            # Добавляем в автоочистку
            await self.add_to_autoclean(msg)
            
            # Даем время на сохранение файла
            await asyncio.sleep(1)
            
            # Перезапуск процесса
            os.execl(sys.executable, sys.executable, "main.py")
            
        except Exception as e:
            error_msg = await event.edit(f"🚫 **Ошибка перезагрузки:** `{str(e)}`")
            await self.add_to_autoclean(error_msg)
            # Удаляем файл в случае ошибки
            try:
                if self.restart_file.exists():
                    self.restart_file.unlink()
            except:
                pass

    async def cmd_online(self, event):
        """Обработчик команды .online"""
        is_premium = await self.is_premium_user(event)
        uptime = await self.format_time(time.time() - self.bot.start_time)
        
        if is_premium:
            msg = await event.edit(f"[🕒](emoji/{self.clock_emoji_id}) **Время работы:** `{uptime}`")
        else:
            msg = await event.edit(f"🕒 **Время работы:** `{uptime}`")
        
        await self.add_to_autoclean(msg)