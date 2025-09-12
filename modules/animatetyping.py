import asyncio
import logging
from telethon import events
from telethon.tl.types import MessageEntityCustomEmoji
import os
import json
import re

logger = logging.getLogger("UserBot.Typing")

# Настройки пользователей
user_settings_file = "cash/typing_settings.json"

def load_settings():
    """Загружает настройки из файла"""
    if os.path.exists(user_settings_file):
        try:
            with open(user_settings_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Ошибка загрузки настроек: {e}")
    return {}

def save_settings(settings):
    """Сохраняет настройки в файл"""
    try:
        with open(user_settings_file, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка сохранения настроек: {e}")

user_settings = load_settings()
default_delay = 0.08
default_cursor = "▮"

def get_module_info():
    return {
        "name": "Typing",
        "description": "Анимации набора текста и эффекты печати",
        "developer": "@BotHuekka",
        "version": "1.0.0",
        "commands": [
            {
                "command": "п",
                "description": "Анимация печати текста (с поддержкой премиум эмодзи)"
            },
            {
                "command": "s",
                "description": "Сменить курсор"
            },
            {
                "command": "t",
                "description": "Изменить задержку печати"
            },
            {
                "command": "q",
                "description": "Сбросить настройки печати"
            },
            {
                "command": "а",
                "description": "Альтернативная анимация печати (жирный текст)"
            }
        ]
    }

MODULE_INFO = get_module_info()

async def extract_custom_emojis(text, entities):
    """Извлекает кастомные эмодзи из текста и сущностей"""
    custom_emojis = {}
    if entities:
        for entity in entities:
            if isinstance(entity, MessageEntityCustomEmoji):
                emoji_char = text[entity.offset:entity.offset + entity.length]
                custom_emojis[entity.offset] = (emoji_char, entity.document_id)
    return custom_emojis

async def type_animation(event):
    """Анимация печати текста с поддержкой премиум эмодзи"""
    try:
        # Получаем текст после команды
        command_prefix = event.text.split()[0]
        text = event.text[len(command_prefix):].strip()
        
        if not text:
            await event.edit("ℹ️ Введите текст после команды")
            return
        
        # Извлекаем кастомные эмодзи из исходного сообщения
        custom_emojis = await extract_custom_emojis(event.text, event.message.entities)
        
        user_id = str(event.sender_id)
        delay = user_settings.get(user_id, {}).get('delay', default_delay)
        cursor = user_settings.get(user_id, {}).get('cursor', default_cursor)
        
        msg = await event.edit(cursor)
        typed = ""
        
        # Создаем список позиций эмодзи для правильной анимации
        emoji_positions = {}
        command_len = len(command_prefix) + 1  # +1 для пробела после команды
        
        for offset, (emoji_char, doc_id) in custom_emojis.items():
            # Вычисляем позицию в тексте без префикса команды
            adjusted_offset = offset - command_len
            if adjusted_offset >= 0:
                emoji_positions[adjusted_offset] = (emoji_char, doc_id)
        
        # Анимация печати
        i = 0
        entities_list = []
        while i < len(text):
            # Проверяем, есть ли на этой позиции эмодзи
            if i in emoji_positions:
                emoji_char, doc_id = emoji_positions[i]
                typed += emoji_char
                
                # Добавляем сущность для эмодзи
                entities_list.append(MessageEntityCustomEmoji(
                    offset=len(typed) - len(emoji_char),
                    length=len(emoji_char),
                    document_id=doc_id
                ))
                
                # Пропускаем длину эмодзи
                i += len(emoji_char)
            else:
                typed += text[i]
                i += 1
            
            # Формируем сообщение с эмодзи
            message_with_emoji = typed + cursor
            
            await msg.edit(message_with_emoji, formatting_entities=entities_list)
            await asyncio.sleep(delay)
        
        # Финальное сообщение без курсора
        await msg.edit(typed, formatting_entities=entities_list)
    except Exception as e:
        logger.error(f"Ошибка анимации: {e}")
        await event.edit("⚠️ Ошибка при выполнении")

async def tp_animation(event):
    """Альтернативная анимация печати с жирным текстом"""
    try:
        input_str = event.text.split(maxsplit=1)[1].strip() if len(event.text.split()) > 1 else ""
        if not input_str:
            await event.edit("ℹ️ Введите текст после команды")
            return

        typing_symbol = "<"
        previous_text = ""
        await event.edit(f"**{typing_symbol}**", parse_mode='markdown')
        
        for character in input_str:
            previous_text += character
            typing_text = previous_text + typing_symbol
            await event.edit(f'**{typing_text}**', parse_mode='markdown')
            await asyncio.sleep(0.1)
        
        await event.edit(f'**{previous_text}**', parse_mode='markdown')
    except Exception as e:
        logger.error(f"Ошибка анимации: {e}")
        await event.edit("⚠️ Ошибка при выполнении")

async def change_cursor(event):
    """Сменить курсор"""
    try:
        new_cursor = event.text.split(maxsplit=1)[1].strip() if len(event.text.split()) > 1 else ""
        if not new_cursor:
            await event.edit("ℹ️ Укажите новый символ курсора")
            return

        user_id = str(event.sender_id)
        if user_id not in user_settings:
            user_settings[user_id] = {}
        user_settings[user_id]['cursor'] = new_cursor
        save_settings(user_settings)
        
        await event.edit(f"✅ Курсор изменен на: {new_cursor}")
    except Exception as e:
        logger.error(f"Ошибка смены курсора: {e}")
        await event.edit("⚠️ Ошибка при изменении курсора")

async def set_delay(event):
    """Изменить задержку"""
    try:
        delay_str = event.text.split(maxsplit=1)[1].strip() if len(event.text.split()) > 1 else ""
        if not delay_str:
            await event.edit("ℹ️ Укажите задержку (например 0.1)")
            return

        new_delay = float(delay_str)
        user_id = str(event.sender_id)
        
        if user_id not in user_settings:
            user_settings[user_id] = {}
        user_settings[user_id]['delay'] = new_delay
        save_settings(user_settings)
        
        await event.edit(f"✅ Задержка изменена на: {new_delay} сек")
    except ValueError:
        await event.edit("⚠️ Задержка должна быть числом (например 0.1)")
    except Exception as e:
        logger.error(f"Ошибка установки задержки: {e}")
        await event.edit("⚠️ Ошибка при изменении задержки")

async def reset_settings(event):
    """Сбросить настройки"""
    try:
        user_id = str(event.sender_id)
        if user_id in user_settings:
            del user_settings[user_id]
            save_settings(user_settings)
            await event.edit("✅ Настройки сброшены к стандартным")
        else:
            await event.edit("ℹ️ У вас нет сохраненных настроек")
    except Exception as e:
        logger.error(f"Ошибка сброса настроек: {e}")
        await event.edit("⚠️ Ошибка при сбросе настроек")

class TypingModule:
    def __init__(self, bot):
        self.bot = bot
        
        # Регистрируем все команды из MODULE_INFO
        for cmd_info in MODULE_INFO["commands"]:
            if cmd_info["command"] == "п":
                bot.register_command(
                    cmd=cmd_info["command"],
                    handler=type_animation,
                    description=cmd_info["description"],
                    module_name=MODULE_INFO["name"]
                )
            elif cmd_info["command"] == "s":
                bot.register_command(
                    cmd=cmd_info["command"],
                    handler=change_cursor,
                    description=cmd_info["description"],
                    module_name=MODULE_INFO["name"]
                )
            elif cmd_info["command"] == "t":
                bot.register_command(
                    cmd=cmd_info["command"],
                    handler=set_delay,
                    description=cmd_info["description"],
                    module_name=MODULE_INFO["name"]
                )
            elif cmd_info["command"] == "q":
                bot.register_command(
                    cmd=cmd_info["command"],
                    handler=reset_settings,
                    description=cmd_info["description"],
                    module_name=MODULE_INFO["name"]
                )
            elif cmd_info["command"] == "а":
                bot.register_command(
                    cmd=cmd_info["command"],
                    handler=tp_animation,
                    description=cmd_info["description"],
                    module_name=MODULE_INFO["name"]
                )
        
        bot.set_module_description(MODULE_INFO["name"], MODULE_INFO["description"])
        
        # Сохраняем информацию о модуле в базу данных
        success = bot.db.set_module_info(
            MODULE_INFO["name"],
            MODULE_INFO["developer"],
            MODULE_INFO["version"],
            MODULE_INFO["description"],
            MODULE_INFO["commands"],
            False  # is_stock = False для пользовательских модулей
        )
        
        if not success:
            logger.error("Не удалось сохранить информацию о модуле Typing в базу данных")

def setup(bot):
    TypingModule(bot)