# ©️ nnnrodnoy, 2025 ладалалада
# 💬 @nnnrodnoy
# This file is part of Huekka
# 🌐 https://github.com/nnnrodnoy/Huekka/
# You can redistribute it and/or modify it under the terms of the MIT License
# 🔑 https://opensource.org/licenses/MIT
import logging
import re
from telethon import types
# ИСПРАВЛЕНИЕ: Заменяем markdown на html
from telethon.extensions import html 
from telethon.errors.rpcerrorlist import MessageNotModifiedError

logger = logging.getLogger("UserBot.Parser")

class CustomHtmlParser:
    """
    Чистый HTML парсер с поддержкой кастомных эмодзи
    
    Поддерживает: <a href="emoji/ID">Text</a> и <a href="spoiler">Text</a>
    """
    def __init__(self):
        pass

    def parse(self, text):
        # ИСПРАВЛЕНИЕ: Используем html.parse
        text, entities = html.parse(text)
        new_entities = []
        
        for entity in entities:
            if isinstance(entity, types.MessageEntityTextUrl):
                if entity.url == 'spoiler':
                    new_entities.append(types.MessageEntitySpoiler(
                        offset=entity.offset,
                        length=entity.length
                    ))
                elif entity.url.startswith('emoji/'):
                    try:
                        # Логика обработки emoji/ID остается такой же, она верна
                        doc_id = int(entity.url.split('/')[1])
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
                
        return text, new_entities

    def unparse(self, text, entities):
        converted_entities = []
        for entity in entities or []:
            if isinstance(entity, types.MessageEntityCustomEmoji):
                converted_entities.append(types.MessageEntityTextUrl(
                    offset=entity.offset,
                    length=entity.length,
                    url=f'emoji/{entity.document_id}'
                ))
            elif isinstance(entity, types.MessageEntitySpoiler):
                converted_entities.append(types.MessageEntityTextUrl(
                    offset=entity.offset,
                    length=entity.length,
                    url='spoiler'
                ))
            else:
                converted_entities.append(entity)
        
        # ИСПРАВЛЕНИЕ: Используем html.unparse
        return html.unparse(text, converted_entities)

# УДАЛЕНИЕ: Метод _convert_html_emoji_to_markdown больше не нужен

class EmojiHandler:
    """Обработчик премиум-эмодзи (логика остается неизменной)"""
    @staticmethod
    async def process_message(event):
        try:
            # Учитываем синтаксис HTML: <a href="emoji/..."
            if not event.text or event.text.startswith('.'):
                return
                
            if '](emoji/' not in event.text and '<a href="emoji/' not in event.text:
                return
                
            # Обратите внимание: event.edit() будет использовать парсер,
            # который вы передадите в client.send_message или client.edit_message.
            # Если парсер используется для команды, то он сработает здесь.
            await event.edit(event.text)
        except MessageNotModifiedError:
            pass
        except Exception as e:
            logger.error(f"Ошибка обработки эмодзи: {str(e)}", exc_info=True)

    @classmethod
    async def process_command_output(cls, text):
        return text
