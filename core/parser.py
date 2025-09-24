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
    """HTML парсер с поддержкой кастомных эмодзи"""
    def __init__(self):
        pass

    def parse(self, text):
        if not text:
            return "", []

        # Сначала обрабатываем кастомные эмодзи в формате [текст](emoji/id)
        emoji_list = []
        
        # Паттерн для поиска кастомных эмодзи в формате [текст](emoji/id)
        emoji_pattern = re.compile(r'\[(.*?)\]\(emoji/(\d+)\)', re.DOTALL)
        
        # Заменяем эмодзи на временные плейсхолдеры
        def emoji_replacer(match):
            inner_text = match.group(1)
            doc_id = match.group(2)
            index = len(emoji_list)
            emoji_list.append((doc_id, inner_text))
            return f"%%EMOJI_{index}%%"

        text = emoji_pattern.sub(emoji_replacer, text)

        # Парсим HTML разметку (<b>, <i>, <u>, <code> и т.д.)
        text, entities = html.parse(text)
        
        if entities is None:
            entities = []

        # Восстанавливаем эмодзи из плейсхолдеров
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

        # Сортируем сущности по offset
        if entities:
            entities.sort(key=lambda e: e.offset)
        
        return text, entities

    def unparse(self, text, entities):
        if entities is None:
            entities = []
        if not text:
            return ""

        # Разделяем сущности на обычные HTML и кастомные эмодзи
        html_entities = []
        emoji_entities = []

        for entity in entities:
            if isinstance(entity, types.MessageEntityCustomEmoji):
                emoji_entities.append(entity)
            else:
                html_entities.append(entity)

        # Сначала обрабатываем HTML разметку
        text = html.unparse(text, html_entities or None)

        # Затем обрабатываем кастомные эмодзи (с конца, чтобы не сбивать offsets)
        emoji_entities.sort(key=lambda e: e.offset, reverse=True)
        
        for entity in emoji_entities:
            start = entity.offset
            end = start + entity.length
            inner_text = text[start:end]
            # Преобразуем обратно в формат [текст](emoji/id)
            tag = f'[{inner_text}](emoji/{entity.document_id})'
            text = text[:start] + tag + text[end:]

        return text

class EmojiHandler:
    """Обработчик премиум-эмодзи"""
    @staticmethod
    async def process_message(event):
        try:
            if not hasattr(event, 'text') or not event.text or event.text.startswith('.'):
                return
                
            # Проверяем наличие эмодзи в формате [текст](emoji/id)
            if '](emoji/' not in event.text:
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
