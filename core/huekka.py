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

def get_module_info():
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
                "description": "Получить маркеры для премиум-эмодзи"
            },
            {
                "command": "online",
                "description": "Показать время работы бота"
            }
        ]
    }

MODULE_INFO = get_module_info()

class HuekkaModule:
    def __init__(self, bot):
        self.bot = bot
        
        base_dir = Path(__file__).resolve().parent.parent
        
        self.image_path = base_dir / "asset" / "image" / "huekka.jpg"
        self.clock_emoji_id = BotConfig.EMOJI_IDS["clock"]
        
        # Регистрируем все команды из MODULE_INFO
        for cmd_info in MODULE_INFO["commands"]:
            if cmd_info["command"] == "huekka":
                bot.register_command(
                    cmd=cmd_info["command"],
                    handler=self.cmd_huekka,
                    description=cmd_info["description"],
                    module_name=MODULE_INFO["name"]
                )
            elif cmd_info["command"] == "ping":
                bot.register_command(
                    cmd=cmd_info["command"],
                    handler=self.cmd_ping,
                    description=cmd_info["description"],
                    module_name=MODULE_INFO["name"]
                )
            elif cmd_info["command"] == "setamoji":
                bot.register_command(
                    cmd=cmd_info["command"],
                    handler=self.cmd_setamoji,
                    description=cmd_info["description"],
                    module_name=MODULE_INFO["name"]
                )
            elif cmd_info["command"] == "online":
                bot.register_command(
                    cmd=cmd_info["command"],
                    handler=self.cmd_online,
                    description=cmd_info["description"],
                    module_name=MODULE_INFO["name"]
                )
        
        bot.set_module_description(MODULE_INFO["name"], MODULE_INFO["description"])
        
        logger.info(f"Путь к изображению: {self.image_path}")
        logger.info(f"Изображение существует: {self.image_path.exists()}")

    async def cmd_huekka(self, event):
        """Обработчик команды .huekka"""
        try:
            if not self.image_path.exists():
                error_msg = f"<emoji document_id=5240241223632954241>🚫</emoji> <b>Изображение не найдено по пути:</b> <code>{self.image_path}</code>\n"
                error_msg += f"<b>Текущая рабочая директория:</b> <code>{Path.cwd()}</code>\n"
                error_msg += f"<b>Абсолютный путь:</b> <code>{self.image_path.resolve()}</code>\n"
                error_msg += f"<b>Проверьте, что файл существует по указанному пути.</b>"
                await event.edit(error_msg)
                return
            
            message_text = (
                f"<emoji document_id=5370932688993656500>🌑</emoji> <b>Huekka</b> - <i>Version</i> <i>{BotConfig.VERSION}</i>\n\n"
                f"<emoji document_id=5377520790868603876>ℹ️</emoji> <b>GitHub</b>: <i><a href='{BotConfig.GITHUB_URL}'>Huekka</a></i>\n"
                f"<emoji document_id=5377520790868603876>ℹ️</emoji> <b>Channel</b>: <i><a href='https://t.me/BotHuekka'>Huekka</a></i>"
            )
            
            await event.delete() 
            await self.bot.client.send_file(
                event.chat_id,
                self.image_path,
                caption=message_text,
                reply_to=event.reply_to_msg_id
            )
            
        except Exception as e:
            error_msg = f"<emoji document_id=5240241223632954241>🚫</emoji> <b>Ошибка при отправке информации:</b> {str(e)}"
            await event.edit(error_msg)
            logger.error(f"<b>Ошибка в команде</b> '.huekka:' {str(e)}")

    async def cmd_ping(self, event):
        """Обработчик команды .ping"""
        current_time = time.time()
        message_time = event.message.date.timestamp()
        ping_time = round((current_time - message_time) * 1000, 2)
        
        await event.edit(f"<emoji document_id=5370932688993656500>▫️</emoji> <b>сейчас пинг</b> - <code>{ping_time}ms</code>")

    async def cmd_setamoji(self, event):
        """Обработчик команды .setamoji - получение маркеров для премиум-эмодзи"""
        reply = await event.get_reply_message()
        if not reply:
            await event.edit("<emoji document_id=5210952531676504517>❌</emoji> <b>Ответьте на сообщение с премиум-эмодзи!</b>")
            return
            
        if not reply.entities:
            await event.edit("<emoji document_id=5210952531676504517>❌</emoji> <b>В сообщении нет премиум-эмодзи!</b>")
            return
            
        custom_emojis = []
        for entity in reply.entities:
            if isinstance(entity, MessageEntityCustomEmoji):
                emoji_char = reply.message[entity.offset:entity.offset + entity.length]
                custom_emojis.append((emoji_char, entity.document_id))
        
        if not custom_emojis:
            await event.edit("<emoji document_id=5210952531676504517>❌</emoji> <b>В сообщении нет премиум-эмодзи!</b>")
            return
            
        result = "<emoji document_id=5818774589714468177>▪️</emoji> <b>Premium-Amoji:</b>\n\n"
        
        for i, (emoji_char, doc_id) in enumerate(custom_emojis, 1):
            result += f"<b>1.</b> <code>MARKDOWN</code> - <code>[{emoji_char}](emoji/{doc_id})</code>\n\n"
            result += f"<b>2.</b> <code>HTML</code> - <code>&lt;emoji document_id={doc_id}&gt;{emoji_char}&lt;/emoji&gt;</code>\n"
        
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
                msg_text = f"<emoji document_id={self.clock_emoji_id}>🕒</emoji> <b>Время работы:</b> <code>{uptime}</code>"
            else:
                msg_text = f"🕒 <b>Время работы:</b> <code>{uptime}</code>"
            
            msg_obj = await event.edit(msg_text)
            await self.add_to_autoclean(msg_obj)
        except MessageNotModifiedError:
            pass
        except Exception as e:
            logger.error(f"Ошибка в команде .online: {str(e)}")

def setup(bot):
    HuekkaModule(bot)
