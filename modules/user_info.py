# ©️ nnnrodnoy, 2025
# 💬 @nnnrodnoy
# This file is part of Huekka
# 🌐 https://github.com/nnnrodnoy/Huekka/
# You can redistribute it and/or modify it under the terms of the MIT License
# 🔑 https://opensource.org/licenses/MIT
import logging
import time
from datetime import datetime
from telethon import events
from telethon.tl import functions, types
from telethon.errors import FloodWaitError, MessageNotModifiedError
from config import BotConfig
from core.formatters import text, msg

logger = logging.getLogger("UserBot.UserInfo")

def get_module_info():
    return {
        "name": "UserInfo",
        "description": "Получение информации о пользователях, чатах и каналах",
        "developer": "BotHuekka",
        "version": "2.1.0",
        "commands": [
            {
                "command": "userinfo",
                "description": "Получить информацию о пользователе, чате или канале"
            }
        ]
    }

MODULE_INFO = get_module_info()

class UserInfoModule:
    def __init__(self, bot):
        self.bot = bot
        
        bot.register_command(
            cmd=MODULE_INFO["commands"][0]["command"],
            handler=self.cmd_userinfo,
            description=MODULE_INFO["commands"][0]["description"],
            module_name=MODULE_INFO["name"]
        )
        
        bot.set_module_description(MODULE_INFO["name"], MODULE_INFO["description"])

    async def add_to_autoclean(self, message):
        try:
            if hasattr(self.bot, 'autocleaner') and self.bot.autocleaner.enabled:
                await self.bot.autocleaner.schedule_cleanup(message)
        except Exception as e:
            logger.error(f"Ошибка добавления в автоочистку: {str(e)}")

    async def resolve_entity(self, event, entity_ref):
        """Resolve entity from message text or reply"""
        try:
            if entity_ref:
                try:
                    return await self.bot.client.get_input_entity(entity_ref)
                except ValueError:
                    return await self.bot.client.get_input_entity(int(entity_ref))
            elif event.reply_to_msg_id:
                reply_msg = await event.get_reply_message()
                # Исправление: получаем InputEntity из sender_id
                return await self.bot.client.get_input_entity(reply_msg.sender_id)
            else:
                # Если нет аргументов и нет реплая, получаем информацию о текущем чате/пользователе
                return await event.get_input_chat()
        except Exception as e:
            logger.error(f"Ошибка разрешения entity: {str(e)}")
            return None

    async def get_common_chats_count(self, user_id):
        """Get count of common chats with user"""
        try:
            common_chats = await self.bot.client(functions.messages.GetCommonChatsRequest(
                user_id=await self.bot.client.get_input_entity(user_id),
                max_id=0,
                limit=100
            ))
            return len(common_chats.chats)
        except Exception as e:
            logger.error(f"Ошибка получения общих чатов: {str(e)}")
            return 0

    def format_last_seen(self, status):
        """Format last seen status"""
        if isinstance(status, types.UserStatusOnline):
            return "В сети"
        elif isinstance(status, types.UserStatusOffline):
            return datetime.fromtimestamp(status.was_online).strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(status, types.UserStatusRecently):
            return "Недавно"
        elif isinstance(status, types.UserStatusLastWeek):
            return "На прошлой неделе"
        elif isinstance(status, types.UserStatusLastMonth):
            return "В прошлом месяце"
        elif isinstance(status, types.UserStatusEmpty):
            return "Скрыт"
        return "Неизвестно"

    def format_date(self, date_obj):
        """Format date object safely"""
        try:
            if isinstance(date_obj, int):
                # Если это timestamp
                return datetime.fromtimestamp(date_obj).strftime('%Y-%m-%d %H:%M:%S')
            elif hasattr(date_obj, 'strftime'):
                # Если это объект datetime
                return date_obj.strftime('%Y-%m-%d %H:%M:%S')
            else:
                return "Неизвестно"
        except (ValueError, TypeError, OSError):
            return "Неизвестно"

    async def cmd_userinfo(self, event):
        """Обработчик команды .userinfo"""
        try:
            await event.edit("⏳ **Получение информации...**")
            
            args = event.text.split()
            entity_ref = args[1] if len(args) > 1 else None
            
            entity = await self.resolve_entity(event, entity_ref)
            if not entity:
                await event.edit("Не удалось найти сущность")
                return

            # For users
            if isinstance(entity, (types.InputPeerUser, types.InputPeerSelf)):
                try:
                    user = await self.bot.client.get_entity(entity)
                    full_user = await self.bot.client(functions.users.GetFullUserRequest(id=entity))
                    
                    # Check if it's a bot
                    if hasattr(user, 'bot') and user.bot:
                        # Bot info
                        common_chats = await self.get_common_chats_count(user.id)
                        about = getattr(full_user.full_user, 'about', 'Отсутствует') if hasattr(full_user, 'full_user') else "Отсутствует"
                        
                        bot_info = (
                            f"🤖 **Информация о боте**\n\n"
                            f"**🆔 ID:** `{user.id}`\n"
                            f"**👤 Имя:** `{user.first_name or 'Отсутствует'}`\n"
                            f"**🔹 Username:** @{user.username if hasattr(user, 'username') and user.username else 'Отсутствует'}\n"
                            f"**👥 Общие чаты:** `{common_chats}`\n"
                            f"**📝 Описание:** {about}"
                        )
                        
                        msg_obj = await event.edit(bot_info)
                        await self.add_to_autoclean(msg_obj)
                        return
                    
                    # Regular user info
                    common_chats = await self.get_common_chats_count(user.id)
                    last_seen = self.format_last_seen(user.status) if hasattr(user, 'status') else "Неизвестно"
                    
                    # Get attached channel if exists
                    personal_channel = "Отсутствует"
                    if hasattr(full_user, 'full_user') and hasattr(full_user.full_user, 'personal_channel_id') and full_user.full_user.personal_channel_id:
                        try:
                            channel = await self.bot.client.get_entity(full_user.full_user.personal_channel_id)
                            personal_channel = f"📢 @{channel.username}" if hasattr(channel, 'username') and channel.username else f"📢 ID: {channel.id}"
                        except:
                            personal_channel = f"📢 ID: {full_user.full_user.personal_channel_id}"

                    about = getattr(full_user.full_user, 'about', 'Отсутствует') if hasattr(full_user, 'full_user') else "Отсутствует"
                    
                    user_info = (
                        f"👤 **Информация о пользователе**\n\n"
                        f"**🆔 ID:** `{user.id}`\n"
                        f"**👤 Имя:** `{user.first_name or 'Отсутствует'}`\n"
                        f"**👤 Фамилия:** `{user.last_name or 'Отсутствует'}`\n"
                        f"**🔹 Username:** @{user.username if hasattr(user, 'username') and user.username else 'Отсутствует'}\n"
                        f"**📝 Био:** {about}\n"
                        f"**📢 Прикрепленный канал:** {personal_channel}\n"
                        f"**👥 Общие чаты:** `{common_chats}`\n"
                        f"**🕒 Последний визит:** `{last_seen}`\n"
                        f"**⭐ Премиум:** `{'Да' if hasattr(user, 'premium') and user.premium else 'Нет'}`\n"
                        f"**✅ Верифицирован:** `{'Да' if hasattr(user, 'verified') and user.verified else 'Нет'}`"
                    )
                    
                    msg_obj = await event.edit(user_info)
                    await self.add_to_autoclean(msg_obj)
                    
                except Exception as e:
                    logger.error(f"Ошибка получения информации о пользователе: {str(e)}")
                    await event.edit("Ошибка получения информации о пользователе")

            # For chats
            elif isinstance(entity, types.InputPeerChat):
                try:
                    chat = await self.bot.client.get_entity(entity)
                    full_chat = await self.bot.client(functions.messages.GetFullChatRequest(chat.id))
                    about = getattr(full_chat.full_chat, 'about', 'Отсутствует')
                    participants_count = getattr(full_chat.full_chat, 'participants_count', 'N/A')
                    
                    # Безопасное форматирование даты
                    creation_date = "Неизвестно"
                    if hasattr(chat, 'date'):
                        creation_date = self.format_date(chat.date)
                    
                    chat_info = (
                        f"👥 **Информация о чате**\n\n"
                        f"**🆔 ID:** `{chat.id}`\n"
                        f"**📛 Название:** `{chat.title}`\n"
                        f"**👥 Участников:** `{participants_count}`\n"
                        f"**📝 Описание:** {about}\n"
                        f"**📅 Дата создания:** `{creation_date}`"
                    )
                    
                    msg_obj = await event.edit(chat_info)
                    await self.add_to_autoclean(msg_obj)
                    
                except Exception as e:
                    logger.error(f"Ошибка получения информации о чате: {str(e)}")
                    await event.edit("Ошибка получения информации о чате")

            # For channels
            elif isinstance(entity, types.InputPeerChannel):
                try:
                    channel = await self.bot.client.get_entity(entity)
                    full_channel = await self.bot.client(functions.channels.GetFullChannelRequest(entity))
                    
                    about = getattr(full_channel.full_chat, 'about', 'Отсутствует')
                    participants_count = getattr(full_channel.full_chat, 'participants_count', 'N/A')
                    
                    # Безопасное форматирование даты
                    creation_date = "Неизвестно"
                    if hasattr(channel, 'date'):
                        creation_date = self.format_date(channel.date)
                    
                    channel_info = (
                        f"📢 **Информация о канале**\n\n"
                        f"**🆔 ID:** `{channel.id}`\n"
                        f"**📛 Название:** `{channel.title}`\n"
                        f"**🔹 Username:** @{channel.username if hasattr(channel, 'username') and channel.username else 'Отсутствует'}\n"
                        f"**👥 Подписчиков:** `{participants_count}`\n"
                        f"**📝 Описание:** {about}\n"
                        f"**📅 Дата создания:** `{creation_date}`"
                    )
                    
                    msg_obj = await event.edit(channel_info)
                    await self.add_to_autoclean(msg_obj)
                    
                except Exception as e:
                    logger.error(f"Ошибка получения информации о канале: {str(e)}")
                    await event.edit("Ошибка получения информации о канале")
            
            else:
                await event.edit("Данный тип сущности не поддерживается")

        except Exception as e:
            logger.error(f"Ошибка в команде .userinfo: {str(e)}")
            await event.edit(f"Ошибка: {str(e)}")

def setup(bot):
    UserInfoModule(bot)
