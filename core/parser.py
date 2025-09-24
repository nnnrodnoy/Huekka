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
    """Чистый HTML парсер с поддержкой кастомных эмодзи и спойлеров"""
    def __init__(self):
        pass

    def parse(self, text):
        if not text:
            return "", []

        # 1. Заменяем кастомные теги <spoiler>текст</spoiler> на Markdown-подобный TextUrl
        # Это нужно, чтобы Telethon не пытался их парсить как обычный HTML, а
        # затем мы преобразуем TextUrl в MessageEntitySpoiler
        text = re.sub(
            r'<spoiler>(.*?)</spoiler>',
            r'[\1](spoiler)',
            text,
            flags=re.DOTALL
        )
        
        # 2. Парсим текст. html.parse обработает ВСЕ:
        #    - HTML теги (<b>, <i>, <u>) в Telethon сущности.
        #    - Кастомные эмодзи вида [текст](emoji/id) в MessageEntityTextUrl.
        #    - Кастомные спойлеры вида [текст](spoiler) в MessageEntityTextUrl.
        text, entities = html.parse(text)
        
        if entities is None:
            entities = []

        # 3. Преобразуем MessageEntityTextUrl обратно в MessageEntityCustomEmoji и MessageEntitySpoiler
        new_entities = []
        for entity in entities:
            if isinstance(entity, types.MessageEntityTextUrl):
                url = entity.url.lower()
                
                if url == 'spoiler':
                    # Преобразование в MessageEntitySpoiler
                    new_entities.append(types.MessageEntitySpoiler(
                        offset=entity.offset,
                        length=entity.length
                    ))
                elif url.startswith('emoji/'):
                    try:
                        doc_id = int(url.split('/')[1])
                        # Преобразование в MessageEntityCustomEmoji
                        new_entities.append(types.MessageEntityCustomEmoji(
                            offset=entity.offset,
                            length=entity.length,
                            document_id=doc_id
                        ))
                    except (ValueError, IndexError):
                        logger.warning(f"Невалидный ID эмодзи: {entity.url}")
                        new_entities.append(entity)
                else:
                    new_entities.append(entity)
            else:
                new_entities.append(entity)

        # Сортируем сущности по offset
        new_entities.sort(key=lambda e: e.offset)
        
        return text, new_entities

    def unparse(self, text, entities):
        if entities is None:
            entities = []
        if not text:
            return ""

        # Создаем временные TextUrl сущности из CustomEmoji/Spoiler
        converted_entities = []
        for entity in entities:
            if isinstance(entity, types.MessageEntityCustomEmoji):
                converted_entities.append(types.MessageEntityTextUrl(
                    offset=entity.offset,
                    length=entity.length,
                    url=f'emoji/{entity.document_id}' # Сохраняем Markdown-подобный формат
                ))
            elif isinstance(entity, types.MessageEntitySpoiler):
                converted_entities.append(types.MessageEntityTextUrl(
                    offset=entity.offset,
                    length=entity.length,
                    url='spoiler' # Сохраняем Markdown-подобный формат
                ))
            else:
                converted_entities.append(entity)
        
        # Используем html.unparse. Он преобразует:
        # 1. Обычные сущности в HTML теги (<b>, <i>).
        # 2. Временные TextUrl (эмодзи/спойлеры) в Markdown-подобный синтаксис ([текст](url)).
        # Возвращаемый текст будет в HTML, но эмодзи и спойлеры будут в Markdown-подобном формате.
        return html.unparse(text, converted_entities)

class EmojiHandler:
    """Обработчик премиум-эмодзи. Вызывает edit() для активации."""
    @staticmethod
    async def process_message(event):
        try:
            if not hasattr(event, 'text') or not event.text or event.text.startswith('.'):
                return
                
            # Проверяем наличие Markdown-подобного формата эмодзи
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
