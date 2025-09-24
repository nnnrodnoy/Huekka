# ©️ nnnrodnoy, 2025
# 💬 @nnnrodnoy
# This file is part of Huekka
# 🌐 https://github.com/nnnrodnoy/Huekka/
# You can redistribute it and/or modify it under the terms of the MIT License
# 🔑 https://opensource.org/licenses/MIT
import logging
import re
from telethon import types
from telethon.extensions import html
from telethon.errors.rpcerrorlist import MessageNotModifiedError

logger = logging.getLogger("UserBot.Parser")

class CustomParseMode:
    """HTML парсер с поддержкой кастомных эмодзи и спойлеров"""
    def __init__(self):
        pass

    def parse(self, text):
        # Если текст пустой, возвращаем пустые значения
        if not text:
            return "", []
            
        # Списки для хранения данных о кастомных эмодзи и спойлерах
        emoji_list = []
        spoiler_list = []

        # Паттерны для поиска кастомных эмодзи и спойлеров
        emoji_pattern = re.compile(r'<emoji\s+document_id\s*=\s*["\']?(\d+)["\']?\s*>(.*?)</emoji>', re.DOTALL)
        spoiler_pattern = re.compile(r'<spoiler>(.*?)</spoiler>', re.DOTALL)

        # Заменяем эмодзи на плейсхолдеры
        def emoji_replacer(match):
            doc_id = match.group(1)
            inner_text = match.group(2)
            index = len(emoji_list)
            emoji_list.append((doc_id, inner_text))
            return f"%%EMOJI_{index}%%"

        text = emoji_pattern.sub(emoji_replacer, text)

        # Заменяем спойлеры на плейсхолдеры
        def spoiler_replacer(match):
            inner_text = match.group(1)
            index = len(spoiler_list)
            spoiler_list.append(inner_text)
            return f"%%SPOILER_{index}%%"

        text = spoiler_pattern.sub(spoiler_replacer, text)

        # Парсим HTML
        text, entities = html.parse(text)
        
        # Гарантируем, что entities является списком
        if entities is None:
            entities = []

        # Восстанавливаем эмодзи
        for index, (doc_id, inner_text) in enumerate(emoji_list):
            placeholder = f"%%EMOJI_{index}%%"
            if placeholder in text:
                start = text.find(placeholder)
                text = text.replace(placeholder, inner_text, 1)
                entity = types.MessageEntityCustomEmoji(
                    offset=start,
                    length=len(inner_text),
                    document_id=int(doc_id)
                )
                entities.append(entity)

        # Восстанавливаем спойлеры
        for index, inner_text in enumerate(spoiler_list):
            placeholder = f"%%SPOILER_{index}%%"
            if placeholder in text:
                start = text.find(placeholder)
                text = text.replace(placeholder, inner_text, 1)
                entity = types.MessageEntitySpoiler(
                    offset=start,
                    length=len(inner_text)
                )
                entities.append(entity)

        # Сортируем сущности по offset (только если есть сущности)
        if entities:
            entities.sort(key=lambda e: e.offset)

        return text, entities

    def unparse(self, text, entities):
        # Гарантируем, что entities является списком
        if entities is None:
            entities = []
            
        # Если текст пустой, возвращаем пустую строку
        if not text:
            return ""

        # Разделяем сущности на обычные и кастомные
        normal_entities = []
        custom_emoji_entities = []
        spoiler_entities = []

        for entity in entities:
            if isinstance(entity, types.MessageEntityCustomEmoji):
                custom_emoji_entities.append(entity)
            elif isinstance(entity, types.MessageEntitySpoiler):
                spoiler_entities.append(entity)
            else:
                normal_entities.append(entity)

        # Используем стандартный HTML unparse для обычных сущностей
        text = html.unparse(text, normal_entities or None)

        # Обрабатываем кастомные эмодзи и спойлеры с конца, чтобы не сбивать offsets
        custom_emoji_entities.sort(key=lambda e: e.offset, reverse=True)
        spoiler_entities.sort(key=lambda e: e.offset, reverse=True)

        for entity in custom_emoji_entities:
            start = entity.offset
            end = start + entity.length
            inner_text = text[start:end]
            tag = f'<emoji document_id="{entity.document_id}">{inner_text}</emoji>'
            text = text[:start] + tag + text[end:]

        for entity in spoiler_entities:
            start = entity.offset
            end = start + entity.length
            inner_text = text[start:end]
            tag = f'<spoiler>{inner_text}</spoiler>'
            text = text[:start] + tag + text[end:]

        return text

class EmojiHandler:
    """Обработчик премиум-эмодзи"""
    @staticmethod
    async def process_message(event):
        try:
            # Безопасная проверка текста сообщения
            if not hasattr(event, 'text') or not event.text or event.text.startswith('.'):
                return
                
            # Проверяем наличие эмодзи в тексте
            if '<emoji' not in event.text:
                return
                
            # Редактируем сообщение для активации эмодзи
            await event.edit(event.text)
        except MessageNotModifiedError:
            pass
        except Exception as e:
            logger.error(f"Ошибка обработки эмодзи: {str(e)}", exc_info=True)

    @classmethod
    async def process_command_output(cls, text):
        return text
