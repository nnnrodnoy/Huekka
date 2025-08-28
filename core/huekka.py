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
from telethon.tl.types import MessageEntityCustomEmoji
from telethon.errors import MessageNotModifiedError
from config import BotConfig
from core.formatters import text, msg

logger = logging.getLogger("UserBot.Huekka")

class HuekkaModule:
    def __init__(self, bot):
        self.bot = bot
        
        base_dir = Path(__file__).resolve().parent.parent
        
        self.image_path = base_dir / "asset" / "image" / "huekka.png"
        self.clock_emoji_id = BotConfig.EMOJI_IDS["clock"]
        
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
        
        bot.register_command(
            cmd="setamoji",
            handler=self.cmd_setamoji,
            description="Получить маркеры для премиум-эмодзи",
            module_name="Huekka"
        )
        
        bot.register_command(
            cmd="online",
            handler=self.cmd_online,
            description="Показать время работы бота",
            module_name="Huekka"
        )
        
        bot.set_module_description("Huekka", "Информация о боте Huekka и работа с эмодзи")
        
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
        current_time = time.time()
        message_time = event.message.date.timestamp()
        ping_time = round((current_time - message_time) * 1000, 2)
        
        await event.edit(f"[▫️](emoji/5370932688993656500) **сейчас пинг** - `{ping_time}ms`")

    async def cmd_setamoji(self, event):
        """Обработчик команды .setamoji - получение маркеров для премиум-эмодзи"""
        reply = await event.get_reply_message()
        if not reply:
            await event.edit("[❌](emoji/5210952531676504517) **Ответьте на сообщение с премиум-эмодзи!**")
            return
            
        if not reply.entities:
            await event.edit("[❌](emoji/5210952531676504517) **В сообщении нет премиум-эмодзи!**")
            return
            
        custom_emojis = []
        for entity in reply.entities:
            if isinstance(entity, MessageEntityCustomEmoji):
                emoji_char = reply.message[entity.offset:entity.offset + entity.length]
                custom_emojis.append((emoji_char, entity.document_id))
        
        if not custom_emojis:
            await event.edit("[❌](emoji/5210952531676504517) **В сообщении нет премиум-эмодзи!**")
            return
            
        result = "[▪️](emoji/5818774589714468177) **Premium-Amoji:**\n\n"
        
        for i, (emoji_char, doc_id) in enumerate(custom_emojis, 1):
            result += f"**1.** `MARKDOWN` - `[{emoji_char}](emoji/{doc_id})`\n\n"
            result += f"**2.** `HTML` - `<emoji document_id={doc_id}>{emoji_char}</emoji>`\n"
        
        await event.edit(result)

    async def is_premium_user(self, event):
        try:
            user = await event.get_sender()
            return user.premium if hasattr(user, 'premium') else False
        except Exception:
            return False

    async def add_to_autoclean(self, message):
        try:
            if hasattr(self.bot, 'autocleaner') and self.bot.autocleaner.enabled:
                await self.bot.autocleaner.schedule_cleanup(message)
        except Exception as e:
            logger.error(f"Ошибка добавления в автоочистку: {str(e)}")

    async def cmd_online(self, event):
        """Обработчик команды .online"""
        try:
            is_premium = await self.is_premium_user(event)
            uptime = text.format_time(time.time() - self.bot.start_time)
            
            if is_premium:
                msg_text = f"[🕒](emoji/{self.clock_emoji_id}) **Время работы:** `{uptime}`"
            else:
                msg_text = f"🕒 **Время работы:** `{uptime}`"
            
            msg_obj = await event.edit(msg_text)
            await self.add_to_autoclean(msg_obj)
        except MessageNotModifiedError:
            pass
        except Exception as e:
            logger.error(f"Ошибка в команде .online: {str(e)}")

    def get_module_info(self):
        return {
            "name": "Huekka",
            "description": "Информация о боте Huekka и работа с эмодзи",
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
                },
                {
                    "command": "setamoji",
                    "description": "Получить id premium-amoji"
                },
                {
                    "command": "online",
                    "description": "Показать время работы бота"
                }
            ]
        }

def get_module_info():
    return {
        "name": "Huekka",
        "description": "Huekka tools module ",
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
            },
            {
                "command": "setamoji",
                "description": "Получить id premium-amoji"
            },
            {
                "command": "online",
                "description": "Показать время работы бота"
            }
        ]
    }

def setup(bot):
    HuekkaModule(bot)
