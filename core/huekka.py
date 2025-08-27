# ©️ nnnrodnoy, 2025
# 💬 @nnnrodnoy
# This file is part of Huekka
# 🌐 https://github.com/nnnrodnoy/Huekka/
# You can redistribute it and/or modify it under the terms of the MIT License
# 🔑 https://opensource.org/licenses/MIT
import os
import logging
from pathlib import Path
from telethon import events
from config import BotConfig

logger = logging.getLogger("UserBot.Huekka")

class HuekkaModule:
    def __init__(self, bot):
        self.bot = bot
        
        base_dir = Path(__file__).resolve().parent.parent
        
        self.image_path = base_dir / "asset" / "image" / "huekka.png"
        
        bot.register_command(
            cmd="huekka",
            handler=self.cmd_huekka,
            description="Показать информацию о боте",
            module_name="Huekka"
        )
        
        bot.set_module_description("Huekka", "Информация о боте Huekka")
        
        logger.info(f"Путь к изображению: {self.image_path}")
        logger.info(f"Изображение существует: {self.image_path.exists()}")

    async def cmd_huekka(self, event):
        """Обработчик команды .huekka"""
        try:
            if not self.image_path.exists():
                error_msg = f"🚫 Изображение не найдено по пути: {self.image_path}\n"
                error_msg += f"Текущая рабочая директория: {Path.cwd()}\n"
                error_msg += f"Абсолютный путь: {self.image_path.resolve()}\n"
                error_msg += f"Проверьте, что файл существует по указанному пути."
                await event.edit(error_msg)
                return
            
            message_text = (
                f"**[🌑](emoji/5370932688993656500) Huekka** - __Version__ __ {BotConfig.VERSION}__\n\n"
                f"**[ℹ️](emoji/5377520790868603876) GitHub**: __[Huekka]({BotConfig.GITHUB_URL})__\n"
                f"**[ℹ️](emoji/5377520790868603876) Channel**: __[Huekka](https://t.me/BotHuekka)__"
            )
            
            await event.delete() 
            await self.bot.client.send_file(
                event.chat_id,
                self.image_path,
                caption=message_text,
                reply_to=event.reply_to_msg_id
            )
            
        except Exception as e:
            error_msg = f"🚫 Ошибка при отправке информации: {str(e)}"
            await event.edit(error_msg)
            logger.error(f"Ошибка в команде .huekka: {str(e)}")

    def get_module_info(self):
        return {
            "name": "Huekka",
            "description": "Информация о боте Huekka",
            "developer": "@BotHuekka",
            "version": "1.0.0",
            "commands": [
                {
                    "command": "huekka",
                    "description": "Показать информацию о боте"
                }
            ]
        }

def get_module_info():
    return {
        "name": "Huekka",
        "description": "Информация о боте Huekka",
        "developer": "@BotHuekka",
        "version": "1.0.0",
        "commands": [
            {
                "command": "huekka",
                "description": "Показать информацию о боте"
            }
        ]
    }

def setup(bot):
    HuekkaModule(bot)
