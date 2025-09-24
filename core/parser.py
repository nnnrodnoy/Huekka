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
    """HTML парсер, полностью совместимый с Markdown функционалом"""
    def __init__(self):
        pass

    def parse(self, text):
        if not text:
            return "", []

        # Сохраняем оригинальный текст для отладки
        original_text = text
        
        # Паттерны для Markdown-подобных элементов, которые нужно преобразовать в HTML
        # 1. Жирный текст: **текст** -> <b>текст</b>
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text, flags=re.DOTALL)
        
        # 2. Курсив: __текст__ -> <i>текст</i>
        text = re.sub(r'__(.*?)__', r'<i>\1</i>', text, flags=re.DOTALL)
        
        # 3. Подчеркивание: --текст-- -> <u>текст</u>  
        text = re.sub(r'--(.*?)--', r'<u>\1</u>', text, flags=re.DOTALL)
        
        # 4. Зачеркивание: ~~текст~~ -> <s>текст</s>
        text = re.sub(r'~~(.*?)~~', r'<s>\1</s>', text, flags=re.DOTALL)
        
        # 5. Моноширинный: `текст` -> <code>текст</code>
        text = re.sub(r'`(.*?)`', r'<code>\1</code>', text, flags=re.DOTALL)
        
        # 6. Преформатированный: ```текст``` -> <pre>текст</pre>
        text = re.sub(r'```(.*?)```', r'<pre>\1</pre>', text, flags=re.DOTALL)
        
        # 7. Ссылки: [текст](url) -> <a href="url">текст</a>
        text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', text, flags=re.DOTALL)

        # 8. Кастомные эмодзи: [текст](emoji/id) - оставляем как есть для последующей обработки
        # Сначала извлекаем все кастомные эмодзи
        emoji_list = []
        emoji_pattern = re.compile(r'\[(.*?)\]\(emoji/(\d+)\)', re.DOTALL)
        
        def emoji_replacer(match):
            inner_text = match.group(1)
            doc_id = match.group(2)
            index = len(emoji_list)
            emoji_list.append((doc_id, inner_text))
            return f"%%EMOJI_{index}%%"

        text = emoji_pattern.sub(emoji_replacer, text)

        # Парсим HTML
        try:
            text, entities = html.parse(text)
            if entities is None:
                entities = []
        except Exception as e:
            logger.error(f"Ошибка HTML парсинга: {e}")
            # Если парсинг не удался, возвращаем оригинальный текст
            return original_text, []

        # Восстанавливаем кастомные эмодзи
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

        # Сначала преобразуем HTML сущности обратно в текст с помощью стандартного unparse
        try:
            result = html.unparse(text, entities)
        except Exception as e:
            logger.error(f"Ошибка HTML unparse: {e}")
            return text

        # Теперь преобразуем HTML теги обратно в Markdown-подобный синтаксис
        # для совместимости с существующим кодом
        
        # 1. <b>текст</b> -> **текст**
        result = re.sub(r'<b>(.*?)</b>', r'**\1**', result, flags=re.DOTALL)
        
        # 2. <i>текст</i> -> __текст__
        result = re.sub(r'<i>(.*?)</i>', r'__\1__', result, flags=re.DOTALL)
        
        # 3. <u>текст</u> -> --текст--
        result = re.sub(r'<u>(.*?)</u>', r'--\1--', result, flags=re.DOTALL)
        
        # 4. <s>текст</s> -> ~~текст~~
        result = re.sub(r'<s>(.*?)</s>', r'~~\1~~', result, flags=re.DOTALL)
        
        # 5. <code>текст</code> -> `текст`
        result = re.sub(r'<code>(.*?)</code>', r'`\1`', result, flags=re.DOTALL)
        
        # 6. <pre>текст</pre> -> ```текст```
        result = re.sub(r'<pre>(.*?)</pre>', r'```\1```', result, flags=re.DOTALL)
        
        # 7. <a href="url">текст</a> -> [текст](url)
        result = re.sub(r'<a href="(.*?)">(.*?)</a>', r'[\2](\1)', result, flags=re.DOTALL)

        return result

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
