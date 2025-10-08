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

class CustomHtmlParser:
    """Чистый HTML парсер с поддержкой кастомных эмодзи и спойлеров"""
    
    def __init__(self):
        pass

    def parse(self, text):
        """Парсинг HTML текста в текст и сущности"""
        # Сначала преобразуем все специальные маркеры в HTML формат
        text = self._convert_emoji_markers_to_html(text)
        
        # Используем стандартный HTML парсер Telethon
        text, entities = html.parse(text)
        new_entities = []
        
        for entity in entities:
            if isinstance(entity, types.MessageEntityTextUrl):
                if entity.url == 'spoiler':
                    # Преобразуем <a href="spoiler">Text</a> в сущность спойлера
                    new_entities.append(types.MessageEntitySpoiler(
                        offset=entity.offset,
                        length=entity.length
                    ))
                elif entity.url.startswith('emoji/'):
                    try:
                        # Преобразуем <a href="emoji/ID">Text</a> в сущность кастомного эмодзи
                        emoji_id = int(entity.url.split('/')[1])
                        new_entities.append(types.MessageEntityCustomEmoji(
                            offset=entity.offset,
                            length=entity.length,
                            document_id=emoji_id
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
        """Обратное преобразование сущностей в HTML"""
        converted_entities = []
        for entity in entities or []:
            if isinstance(entity, types.MessageEntityCustomEmoji):
                # Преобразуем кастомные эмодзи обратно в HTML ссылки
                converted_entities.append(types.MessageEntityTextUrl(
                    offset=entity.offset,
                    length=entity.length,
                    url=f'emoji/{entity.document_id}'
                ))
            elif isinstance(entity, types.MessageEntitySpoiler):
                # Преобразуем спойлеры обратно в HTML ссылки
                converted_entities.append(types.MessageEntityTextUrl(
                    offset=entity.offset,
                    length=entity.length,
                    url='spoiler'
                ))
            else:
                converted_entities.append(entity)
        
        return html.unparse(text, converted_entities)

    def _convert_emoji_markers_to_html(self, text):
        """Преобразует специальные маркеры эмодзи в HTML формат"""
        # Преобразуем <emoji document_id=5370932688993656500>🌕</emoji> в <a href="emoji/5370932688993656500">🌕</a>
        text = re.sub(
            r'<emoji\s+document_id\s*=\s*["\']?(\d+)["\']?\s*>(.*?)</emoji>',
            r'<a href="emoji/\1">\2</a>',
            text,
            flags=re.DOTALL
        )
        return text

class EmojiHandler:
    """Обработчик премиум-эмодзи для HTML"""
    
    @staticmethod
    async def process_message(event):
        """Обработка всех исходящих сообщений с автоматическим преобразованием маркеров эмодзи"""
        try:
            if not event.text:
                return
                
            # Пропускаем команды (начинающиеся с префикса)
            if event.text.startswith('.'):
                return
                
            # Проверяем наличие специальных маркеров эмодзи
            if '<emoji document_id=' in event.text:
                # Преобразуем маркеры в HTML формат
                new_text = EmojiHandler.convert_emoji_markers(event.text)
                
                # Если текст изменился, редактируем сообщение
                if new_text != event.text:
                    await event.edit(new_text)
                    
        except MessageNotModifiedError:
            pass
        except Exception as e:
            logger.error(f"Ошибка обработки эмодзи: {str(e)}", exc_info=True)

    @staticmethod
    def convert_emoji_markers(text):
        """Конвертирует маркеры эмодзи в HTML формат"""
        # Используем тот же метод, что и в парсере
        parser = CustomHtmlParser()
        return parser._convert_emoji_markers_to_html(text)

    @classmethod
    async def process_command_output(cls, text):
        """Обработка вывода команд для HTML формата"""
        # Конвертируем специальные маркеры в HTML
        text = cls.convert_emoji_markers(text)
        return text

# Для обратной совместимости с существующим кодом
CustomParseMode = CustomHtmlParser
