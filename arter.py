# ©️ nnnrodnoy, 2025
# 💬 @nnnrodnoy
# This file is part of Huekka
# 🌐 https://github.com/nnnrodnoy/Huekka/
# You can redistribute it and/or modify it under the terms of the MIT License
# 🔑 https://opensource.org/licenses/MIT
import os
import re
import random
from pathlib import Path
from config import BotConfig

def convert_color(match):
    """Конвертирует цветные блоки в ANSI escape sequences"""
    hex_color = match.group(1).lower()
    text = match.group(2)
    
    # Заменяем все символы фона на пробелы
    for char in BotConfig.ARTER['background_chars']:
        text = text.replace(char, ' ')
    return f"\033[38;2;{int(hex_color[0:2], 16)};{int(hex_color[2:4], 16)};{int(hex_color[4:6], 16)}m{text}"

def print_random_art():
    """Выводит случайный ASCII арт из папки arts"""
    arts_dir = Path("arts")
    if not arts_dir.exists():
        return False
        
    # Получаем все txt файлы в папке arts
    art_files = list(arts_dir.glob("*.txt"))
    if not art_files:
        return False
        
    # Выбираем случайный файл
    art_file = random.choice(art_files)
    
    try:
        with open(art_file, 'r', encoding='utf-8') as f:
            for line in f:
                # Убираем символ перевода строки
                stripped_line = line.rstrip('\n')
                # Удаляем все теги, кроме цветовых
                stripped_line = re.sub(r'\[(?!color)[^]]*\]', '', stripped_line)
                stripped_line = re.sub(r'\[/color\]', '', stripped_line)
                
                # Обрабатываем цветовые блоки
                stripped_line = re.sub(
                    r'\[color=#([0-9a-f]{6})\](.*?)(?=\[color=|$)',
                    convert_color,
                    stripped_line,
                    flags=re.IGNORECASE
                )
                
                # Заменяем оставшиеся символы фона
                for char in BotConfig.ARTER['background_chars']:
                    stripped_line = stripped_line.replace(char, ' ')
                
                # Выводим строку арта
                print(stripped_line + "\033[0m")
        return True
    except Exception as e:
        print(f"Ошибка при обработке арта: {str(e)}")
        return False

def print_specific_art(art_name):
    """Выводит конкретный арт по имени файла"""
    art_path = Path("arts") / f"{art_name}.txt"
    if not art_path.exists():
        return False
        
    try:
        with open(art_path, 'r', encoding='utf-8') as f:
            for line in f:
                # Убираем символ перевода строки
                stripped_line = line.rstrip('\n')
                # Удаляем все теги, кроме цветовых
                stripped_line = re.sub(r'\[(?!color)[^]]*\]', '', stripped_line)
                stripped_line = re.sub(r'\[/color\]', '', stripped_line)
                
                # Обрабатываем цветовые блоки
                stripped_line = re.sub(
                    r'\[color=#([0-9a-f]{6})\](.*?)(?=\[color=|$)',
                    convert_color,
                    stripped_line,
                    flags=re.IGNORECASE
                )
                
                # Заменяем оставшиеся символы фона
                for char in BotConfig.ARTER['background_chars']:
                    stripped_line = stripped_line.replace(char, ' ')
                
                # Выводим строку арта
                print(stripped_line + "\033[0m")
        return True
    except Exception as e:
        print(f"Ошибка при обработке арта: {str(e)}")
        return False
