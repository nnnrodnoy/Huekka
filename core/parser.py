import logging
import re
from telethon import types
from telethon.extensions import markdown
from telethon.errors.rpcerrorlist import MessageNotModifiedError

logger = logging.getLogger("UserBot.Parser")

class CustomParseMode:
    """Чистый Markdown парсер с поддержкой эмодзи"""
    def __init__(self):
        pass

    def parse(self, text):
        # Преобразуем HTML-эмодзи в Markdown-формат
        text = self._convert_html_emoji_to_markdown(text)
        
        # Парсим Markdown
        text, entities = markdown.parse(text)
        new_entities = []
        
        # Обрабатываем сущности
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
        
        return markdown.unparse(text, converted_entities)

    def _convert_html_emoji_to_markdown(self, text):
        """Конвертируем HTML-эмодзи в Markdown-формат"""
        return re.sub(
            r'<emoji\s+document_id\s*=\s*["\']?(\d+)["\']?\s*>(.*?)</emoji>',
            r'[\2](emoji/\1)',
            text,
            flags=re.DOTALL
        )

class EmojiHandler:
    """Обработчик премиум-эмодзи"""
    @staticmethod
    async def process_message(event):
        try:
            # Пропускаем команды и сообщения без текста
            if not event.text or event.text.startswith('.'):
                return
                
            # Проверяем наличие эмодзи в любом формате
            if '](emoji/' not in event.text and '<emoji' not in event.text:
                return
                
            # Редактируем сообщение для активации парсера
            await event.edit(event.text)
        except MessageNotModifiedError:
            # Игнорируем ошибку, если сообщение не изменилось
            pass
        except Exception as e:
            logger.error(f"Ошибка обработки эмодзи: {str(e)}", exc_info=True)

    @classmethod
    async def process_command_output(cls, text):
        return text