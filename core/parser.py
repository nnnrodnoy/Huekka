# ©️ nnnrodnoy, 2025
# 💬 @nnnrodnoy
# This file is part of Huekka
# 🌐 https://github.com/nnnrodnoy/Huekka/
# You can redistribute it and/or modify it under the terms of the MIT License
# 🔑 https://opensource.org/licenses/MIT
import logging
import re
from telethon import types
from telethon.extensions import markdown
from telethon.errors.rpcerrorlist import MessageNotModifiedError

logger = logging.getLogger("UserBot.Parser")

class CustomParseMode:
    """Чистый Markdown парсер с поддержкой эмодзи и цитирования"""
    def __init__(self):
        pass

    def parse(self, text):
        # Обрабатываем цитирование перед другими преобразованиями
        text = self._convert_quotes_to_html(text)
        text = self._convert_html_emoji_to_markdown(text)
        
        text, entities = markdown.parse(text)
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
                        doc_id = int(entity.url.split('/')[1])
                        new_entities.append(types.MessageEntityCustomEmoji(
                            offset=entity.offset,
                            length=entity.length,
                            document_id=doc_id
                        ))
                    except (ValueError, IndexError):
                        logger.warning(f"Невалидный ID эмодзи: {entity.url}")
                        new_entities.append(entity)
                elif entity.url == 'quote':
                    # Создаем кастомную сущность для цитирования
                    new_entities.append(types.MessageEntityBlockquote(
                        offset=entity.offset,
                        length=entity.length
                    ))
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
            elif isinstance(entity, types.MessageEntityBlockquote):
                converted_entities.append(types.MessageEntityTextUrl(
                    offset=entity.offset,
                    length=entity.length,
                    url='quote'
                ))
            else:
                converted_entities.append(entity)
        
        return markdown.unparse(text, converted_entities)

    def _convert_html_emoji_to_markdown(self, text):
        """Конвертируем HTML-эмодзи в Markdown-формат"""
        return re.sub(
            r'<emoji\s+document_id\s*=\s*["\']?(\d+)["\']?\s*>(.*?)</emoji>',
            r'[\2](emoji/\1)',
            text,
            flags=re.DOTALL
        )

    def _convert_quotes_to_html(self, text):
        """Конвертируем символы цитирования в HTML-формат"""
        # Обрабатываем многострочные цитаты
        lines = text.split('\n')
        in_quote = False
        result_lines = []
        
        for line in lines:
            if line.startswith('> '):
                if not in_quote:
                    result_lines.append('<blockquote>')
                    in_quote = True
                result_lines.append(line[2:])
            else:
                if in_quote:
                    result_lines.append('</blockquote>')
                    in_quote = False
                result_lines.append(line)
        
        if in_quote:
            result_lines.append('</blockquote>')
        
        return '\n'.join(result_lines)

class EmojiHandler:
    """Обработчик премиум-эмодзи и цитирования"""
    @staticmethod
    async def process_message(event):
        try:
            if not event.text or event.text.startswith('.'):
                return
                
            if '](emoji/' not in event.text and '<emoji' not in event.text and '> ' not in event.text:
                return
                
            await event.edit(event.text)
        except MessageNotModifiedError:
            pass
        except Exception as e:
            logger.error(f"Ошибка обработки эмодзи: {str(e)}", exc_info=True)

    @classmethod
    async def process_command_output(cls, text):
        return text
