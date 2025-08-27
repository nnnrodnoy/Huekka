# ©️ nnnrodnoy, 2025
# 💬 @nnnrodnoy
# This file is part of Huekka
# 🌐 https://github.com/nnnrodnoy/Huekka/
# You can redistribute it and/or modify it under the terms of the MIT License
# 🔑 https://opensource.org/licenses/MIT
import os
import logging
import time
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
        
        bot.register_command(
            cmd="ping",
            handler=self.cmd_ping,
            description="Показать пинг бота",
            module_name="Huekka"
        )
        
        bot.set_module_description("Huekka", "Информация о боте Huekka")
        
        logger.info(f"Путь к изображению: {self.image_path}")
        logger.info(f"Изображение существует: {self.image_path.exists()}")

    async def cmd_huekka(self, event):
        """Обработчик команды .huekka"""
        try:
            if not self.image_path.exists():
                error_msg = f"[🚫](emoji/5240241223632954241) Изображение не найдено по пути: {self.image_path}\n"
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
            error_msg = f"[🚫](emoji/5240241223632954241) **Ошибка при отправке информации:** {str(e)}"
            await event.edit(error_msg)
            logger.error(f"**Ошибка в команде** '.huekka:' {str(e)}")

    async def cmd_ping(self, event):
        """Обработчик команды .ping"""
        # Вычисляем пинг на основе времени получения сообщения
        current_time = time.time()
        message_time = event.message.date.timestamp()
        ping_time = round((current_time - message_time) * 1000, 2)
        
        await event.edit(f"[▫️](emoji/5370932688993656500) сейчас пинг - {ping_time}ms")

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
                },
                {
                    "command": "ping",
                    "description": "Показать пинг бота"
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
            },
            {
                "command": "ping",
                "description": "Показать пинг бота"
            }
        ]
    }

def setup(bot):
    HuekkaModule(bot)
