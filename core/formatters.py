# ©️ nnnrodnoy, 2025
# 💬 @nnnrodnoy
# This file is part of Huekka
# 🌐 https://github.com/nnnrodnoy/Huekka/
# You can redistribute it and/or modify it under the terms of the MIT License
# 🔑 https://opensource.org/licenses/MIT
import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Union

logger = logging.getLogger("UserBot.Formatters")

class TextFormatters:
    """Универсальные текстовые форматтеры"""
    
    @staticmethod
    def progress_bar(percentage: int, length: int = 10, filled_char: str = "█", empty_char: str = "░") -> str:
        """Создает текстовый прогресс-бар"""
        filled = int(length * percentage / 100)
        empty = length - filled
        return f"[{filled_char * filled}{empty_char * empty}] {percentage}%"
    
    @staticmethod
    def format_table(headers: List[str], rows: List[List[str]], align: str = "left") -> str:
        """Создает текстовую таблицу"""
        if not rows:
            return "No data available"
            
        # Определяем ширину колонок
        col_widths = [len(str(header)) for header in headers]
        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(cell)))
        
        # Создаем таблицу
        separator = "+" + "+".join(["-" * (w + 2) for w in col_widths]) + "+"
        
        # Заголовок
        header_line = "|" + "|".join([
            f" {h:{'<' if align == 'left' else '>' if align == 'right' else '^'}{w}} " 
            for h, w in zip(headers, col_widths)
        ]) + "|"
        
        # Данные
        data_lines = []
        for row in rows:
            data_line = "|" + "|".join([
                f" {str(cell):{'<' if align == 'left' else '>' if align == 'right' else '^'}{w}} " 
                for cell, w in zip(row, col_widths)
            ]) + "|"
            data_lines.append(data_line)
        
        return "\n".join([separator, header_line, separator] + data_lines + [separator])
    
    @staticmethod
    def format_time(seconds: int) -> str:
        """Форматирует время в читаемый вид"""
        days, remainder = divmod(seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        parts = []
        if days: parts.append(f"{int(days)}д")
        if hours: parts.append(f"{int(hours)}ч")
        if minutes: parts.append(f"{int(minutes)}мин")
        if seconds or not parts: parts.append(f"{int(seconds)}сек")
        
        return " ".join(parts)
    
    @staticmethod
    def format_size(size_bytes: int) -> str:
        """Форматирует размер файла в читаемый вид"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
    
    @staticmethod
    def format_list(items: List[str], style: str = "bullet", start: int = 1) -> str:
        """Форматирует список элементов"""
        if style == "bullet":
            return "\n".join([f"• {item}" for item in items])
        elif style == "numbered":
            return "\n".join([f"{i}. {item}" for i, item in enumerate(items, start)])
        elif style == "dash":
            return "\n".join([f"- {item}" for item in items])
        return "\n".join(items)

class MessageFormatters:
    """Форматирование сообщений для различных ситуаций"""
    
    @staticmethod
    def error(message: str, details: str = "") -> str:
        """Форматирование сообщения об ошибке"""
        if details:
            return f"[🚫](emoji/5240241223632954241) **Ошибка:** {message}\n```{details}```"
        return f"[🚫](emoji/5240241223632954241) **Ошибка:** {message}"
    
    @staticmethod
    def warning(message: str) -> str:
        """Форматирование предупреждения"""
        return f"⚠️ **Внимание:** {message}"
    
    @staticmethod
    def success(message: str) -> str:
        """Форматирование успешного выполнения"""
        return f"[✅](emoji/5206607081334906820) **Успех:** {message}"
    
    @staticmethod
    def info(message: str) -> str:
        """Форматирование информационного сообщения"""
        return f"[ℹ️](emoji/5422439311196834318) **Информация:** {message}"
    
    @staticmethod
    def question(message: str) -> str:
        """Форматирование вопроса"""
        return f"[❓](emoji/5436113877181941026) **Вопрос:** {message}"
    
    @staticmethod
    def tip(message: str) -> str:
        """Форматирование подсказки"""
        return f"[💡](emoji/5422439311196834318) **Подсказка:** {message}"

class HelpFormatters:
    """Форматирование для help модуля"""
    
    @staticmethod
    def format_module_info(module_info, is_premium, total_emoji_id, random_smile, 
                          stock_emoji_id, custom_emoji_id, command_emoji_id, 
                          developer_emoji_id, prefix):
        """Форматирование информации о модуле (как в help.py)"""
        text = ""
        if is_premium:
            text += f"[🕒](emoji/{total_emoji_id}) "
        text += f"**{module_info['name']} (v{module_info['version']})**\n"
        text += f"__{module_info['description']}__\n"
        text += f"**"__{random_smile}**"__\n\n" 
                              
        for cmd in module_info['commands']:
            if is_premium:
                if module_info['is_stock']:
                    text += f"[▪️](emoji/{stock_emoji_id}) "
                else:
                    text += f"[▫️](emoji/{custom_emoji_id}) "
            else:
                text += "▪️ " if module_info['is_stock'] else "▫️ "
            
            text += f"`{prefix}{cmd['command']}` - __{cmd['description']}__\n"
        
        if is_premium:
            text += f"\n[🫶](emoji/{developer_emoji_id}) "
        else:
            text += "\n🫶 "
        text += f"**Разработчик:** {module_info['developer']}"
        
        return text

    @staticmethod
    def format_main_help(total_modules, is_premium, total_emoji_id, section_emoji_id,
                        stock_emoji_id, custom_emoji_id, stock_list, custom_list, prefix):
        """Форматирование главной справки (как в help.py)"""
        reply = ""
        
        if is_premium:
            reply += f"[🕒](emoji/{total_emoji_id}) "
        reply += f"**Доступно модулей:** {total_modules}\n"
        reply += f"__Используйте `{prefix}help <команда>` для информации о команде__\n"
        reply += f"__Или `{prefix}help <модуль>` для информации о модуле__\n\n"
        
        if is_premium:
            reply += f"[👁️](emoji/{section_emoji_id}) "
        reply += "**Стандартные модули:**\n"
        reply += "\n".join(stock_list) + "\n\n"
        
        if is_premium:
            reply += f"[👁️](emoji/{section_emoji_id}) "
        reply += "**Пользовательские модули:**\n"
        reply += "\n".join(custom_list)
        
        return reply

class LoaderFormatters:
    """Форматирование для loader модуля"""
    
    @staticmethod
    def format_loaded_message(module_info, is_premium, loaded_emoji_id, random_smile,
                             command_emoji_id, dev_emoji_id, prefix):
        """Форматирование сообщения о загруженном модуле (как в loader.py)"""
        text = ""
        if is_premium:
            text += f"[🌘](emoji/{loaded_emoji_id}) "
        text += f"**{module_info['name']} загружен (v{module_info['version']})**\n"
        
        if module_info['description']:
            text += f"__{module_info['description']}__\n"
            
        text += f"**"__{random_smile}**"__\n\n"
        
        for cmd in module_info['commands']:
            if is_premium:
                text += f"[▫️](emoji/{command_emoji_id}) "
            else:
                text += "▫️ "
                
            text += f"`{prefix}{cmd['command']}` - __{cmd['description']}__\n"
        
        text += "\n"
        if is_premium:
            text += f"[🫶](emoji/{dev_emoji_id}) "
        else:
            text += "🫶 "
        text += f"**Разработчик:** {module_info['developer']}"
        
        return text

    @staticmethod
    def format_unloaded_message(module_name, is_premium, info_emoji_id, prefix):
        """Форматирование сообщения об удалении модуля (как в loader.py)"""
        text = ""
        if is_premium:
            text += f"[▪️](emoji/{info_emoji_id})"
        else:
            text += "▪️"
        
        text += f"**Модуль {module_name} успешно удален.**\n"
        text += f"__(Используйте `{prefix}help` для просмотра модулей и команд.)__"
        
        return text

# Создаем экземпляры для удобного импорта
text = TextFormatters()
msg = MessageFormatters()
help_format = HelpFormatters()
loader_format = LoaderFormatters()
