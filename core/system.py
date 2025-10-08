# ©️ nnnrodnoy, 2025
# 💬 @nnnrodnoy
# This file is part of Huekka
# 🌐 https://github.com/nnnrodnoy/Huekka/
# You can redistribute it and/or modify it under the terms of the MIT License
# 🔑 https://opensource.org/licenses/MIT
import os
import sys
import time
import asyncio
import logging
import json
import re
from pathlib import Path
from telethon import events
from telethon.errors import MessageNotModifiedError
from config import BotConfig
from core.formatters import text, msg

logger = logging.getLogger("UserBot.System")

def get_module_info():
    return {
        "name": "System",
        "description": "Системные команды бота",
        "developer": "@BotHuekka",
        "version": "1.0.0",
        "commands": [
            {
                "command": "restart",
                "description": "Перезагрузить бота"
            }
        ]
    }

MODULE_INFO = get_module_info()

class SystemModule:
    def __init__(self, bot):
        self.bot = bot
        self.bot.start_time = time.time()
        
        self.restart_emoji_id = BotConfig.EMOJI_IDS["restart"]
        
        self.restart_file = Path("cash") / "restart_info.json"
        
        # Регистрируем команду из MODULE_INFO
        bot.register_command(
            cmd=MODULE_INFO["commands"][0]["command"],
            handler=self.cmd_restart,
            description=MODULE_INFO["commands"][0]["description"],
            module_name=MODULE_INFO["name"]
        )
        
        bot.set_module_description(MODULE_INFO["name"], MODULE_INFO["description"])
        
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

        @bot.client.on(events.NewMessage(outgoing=True, pattern=rf'^{re.escape(bot.command_prefix)}restart\b'))
        async def restart_handler(event):
            await self.cmd_restart(event)
            
        @bot.client.on(events.NewMessage(outgoing=True, pattern=rf'^{re.escape(bot.command_prefix)}reboot\b'))
        async def reboot_handler(event):
            await self.cmd_restart(event)
    
    async def send_restart_complete(self, restart_data):
        try:
            await asyncio.sleep(3)
            
            if restart_data["is_premium"]:
                text_msg = f"<emoji document_id={self.restart_emoji_id}>⚙️</emoji> <b>Huekka успешно перезагружен!</b>"
            else:
                text_msg = "⚙️ <b>Huekka успешно перезагрушен!</b>"
            
            msg_obj = await self.bot.client.edit_message(
                entity=restart_data["chat_id"],
                message=restart_data["message_id"],
                text=text_msg
            )
            
            await self.add_to_autoclean(msg_obj)
            
        except Exception as e:
            logger.error(f"Ошибка редактирования restart complete: {str(e)}")

    async def add_to_autoclean(self, message):
        try:
            if hasattr(self.bot, 'autocleaner') and self.bot.autocleaner.enabled:
                await self.bot.autocleaner.schedule_cleanup(message)
        except Exception as e:
            logger.error(f"Ошибка добавления в автоочистку: {str(e)}")

    async def is_premium_user(self, event):
        try:
            user = await event.get_sender()
            return user.premium if hasattr(user, 'premium') else False
        except Exception:
            return False

    async def cmd_restart(self, event):
        is_premium = await self.is_premium_user(event)
        
        try:
            restart_data = {
                "chat_id": event.chat_id,
                "message_id": event.id,
                "is_premium": is_premium
            }
            
            with open(self.restart_file, "w") as f:
                json.dump(restart_data, f)
            
            if is_premium:
                msg_obj = await event.edit(f"<emoji document_id={self.restart_emoji_id}>⚙️</emoji> <b>Перезагрузка Huekka...</b>")
            else:
                msg_obj = await event.edit("⚙️ <b>Перезагрузка Huekka...</b>")
            
            await self.add_to_autoclean(msg_obj)
            
            await asyncio.sleep(1)
            
            os.execl(sys.executable, sys.executable, "main.py")
            
        except Exception as e:
            error_msg = msg.error("Ошибка перезагрузки", str(e))
            error_obj = await event.edit(error_msg)
            await self.add_to_autoclean(error_obj)
            try:
                if self.restart_file.exists():
                    self.restart_file.unlink()
            except:
                pass

def setup(bot):
    SystemModule(bot)
