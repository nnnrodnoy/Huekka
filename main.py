# ©️ nnnrodnoy, 2025
# 💬 @nnnrodnoy
# This file is part of Huekka
# 🌐 https://github.com/nnnrodnoy/Huekka/
# You can redistribute it and/or modify it under the terms of the MIT License
# 🔑 https://opensource.org/licenses/MIT
import os
import sys
import re
import asyncio
import base64
import time
import hashlib
import json
import secrets
import shutil
import tempfile
import subprocess
import random
from pathlib import Path
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
from telethon.sessions import StringSession
from telethon import TelegramClient
from telethon.errors import (
    SessionPasswordNeededError,
    ApiIdInvalidError,
    PhoneNumberInvalidError,
    FloodWaitError,
    PhoneCodeInvalidError
)

class Colors:
    DARK_VIOLET = '\033[38;5;54m'
    LIGHT_BLUE = '\033[38;5;117m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

class Updater:
    def __init__(self):
        self.repo_url = "https://github.com/nnnrodnoy/Huekka"
        self.update_files = ['main.py', 'userbot.py', 'installer.sh', 'start_bot.sh', 'requirements.txt', 'config.py']
        self.update_dirs = ['core', 'asset', 'arts']
    
    def run_command(self, cmd, cwd=None):
        """Выполняет команду и возвращает результат"""
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)

    def check_update(self):
        """Проверяет наличие обновлений только для нужных файлов и папок"""
        # Создаем временную директорию
        temp_dir = tempfile.mkdtemp(prefix="huekka_update_")
        
        try:
            # Клонируем репозиторий
            success, stdout, stderr = self.run_command(f"git clone {self.repo_url} {temp_dir} --depth=1")
            if not success:
                shutil.rmtree(temp_dir, ignore_errors=True)
                return False
            
            # Проверяем изменения только в нужных файлах и папках
            has_changes = False
            
            # Проверяем файлы
            for file in self.update_files:
                repo_file = os.path.join(temp_dir, file)
                local_file = file
                
                if os.path.exists(repo_file):
                    if not os.path.exists(local_file):
                        has_changes = True
                        break
                    
                    # Сравниваем содержимое файлов
                    with open(repo_file, 'rb') as f1, open(local_file, 'rb') as f2:
                        if f1.read() != f2.read():
                            has_changes = True
                            break
            
            # Проверяем папки
            if not has_changes:
                for dir_name in self.update_dirs:
                    repo_dir = os.path.join(temp_dir, dir_name)
                    local_dir = dir_name
                    
                    if os.path.exists(repo_dir):
                        if not os.path.exists(local_dir):
                            has_changes = True
                            break
                        
                        # Рекурсивно проверяем файлы в папке
                        for root, dirs, files in os.walk(repo_dir):
                            for file in files:
                                rel_path = os.path.relpath(os.path.join(root, file), repo_dir)
                                repo_file_path = os.path.join(root, file)
                                local_file_path = os.path.join(local_dir, rel_path)
                                
                                if not os.path.exists(local_file_path):
                                    has_changes = True
                                    break
                                
                                with open(repo_file_path, 'rb') as f1, open(local_file_path, 'rb') as f2:
                                    if f1.read() != f2.read():
                                        has_changes = True
                                        break
                            
                            if has_changes:
                                break
                    
                    if has_changes:
                        break
            
            shutil.rmtree(temp_dir, ignore_errors=True)
            return has_changes
            
        except Exception as e:
            shutil.rmtree(temp_dir, ignore_errors=True)
            return False

    def perform_update(self):
        """Выполняет обновление только нужных файлов и папок"""
        # Создаем временную директорию
        temp_dir = tempfile.mkdtemp(prefix="huekka_update_")
        
        try:
            # Клонируем репозиторий
            success, stdout, stderr = self.run_command(f"git clone {self.repo_url} {temp_dir} --depth=1")
            if not success:
                shutil.rmtree(temp_dir, ignore_errors=True)
                return False
            
            # Удаляем старые файлы и папки
            for file in self.update_files:
                if os.path.exists(file):
                    os.remove(file)
            
            for dir_name in self.update_dirs:
                if os.path.exists(dir_name):
                    shutil.rmtree(dir_name)
            
            # Копируем новые файлы и папки
            for file in self.update_files:
                repo_file = os.path.join(temp_dir, file)
                if os.path.exists(repo_file):
                    shutil.copy2(repo_file, file)
            
            for dir_name in self.update_dirs:
                repo_dir = os.path.join(temp_dir, dir_name)
                if os.path.exists(repo_dir):
                    shutil.copytree(repo_dir, dir_name)
            
            # Очищаем временные файлы
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            # Удаляем временную папку репозитория, если она осталась
            if os.path.exists("Huekka"):
                shutil.rmtree("Huekka", ignore_errors=True)
            if os.path.exists(".git"):
                shutil.rmtree(".git", ignore_errors=True)
            
            return True
            
        except Exception as e:
            shutil.rmtree(temp_dir, ignore_errors=True)
            return False

class SessionManager:
    @staticmethod
    def generate_encryption_key():
        return secrets.token_urlsafe(32)

    @staticmethod
    def encrypt_data(data: dict, key: str) -> str:
        salt = get_random_bytes(16)
        derived_key = hashlib.pbkdf2_hmac('sha256', key.encode(), salt, 100000, 32)
        
        iv = get_random_bytes(16)
        cipher = AES.new(derived_key, AES.MODE_CBC, iv)
        encrypted = cipher.encrypt(pad(json.dumps(data).encode(), AES.block_size))
        
        return base64.b64encode(salt + iv + encrypted).decode()

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
        # Все возможные символы фона, которые нужно заменить на пробелы
        BACKGROUND_CHARS = {
            # Блоковые символы
            '▄', '▀', '▌', '▐', '■', '□', '▪', '▫', '▬', '▲', '▼', '◆', '●', '○',
            '◘', '◙', '◦', '◌', '◍', '◎', '◐', '◑', '◒', '◓', '◔', '◕', '◖', '◗',
            '◢', '◣', '◤', '◥', '◧', '◨', '◩', '◪', '◫', '◬', '◭', '◮', '◯',
            
            # Линейные символы
            '─', '━', '│', '┃', '┄', '┅', '┆', '┇', '┈', '┉', '┊', '┋', '┌', '┍',
            '┎', '┏', '┐', '┑', '┒', '┓', '└', '┕', '┖', '┗', '┘', '┙', '┚', '┛',
            '├', '┝', '┞', '┟', '┠', '┡', '┢', '┣', '┤', '┥', '┦', '┧', '┨', '┩',
            '┪', '┫', '┬', '┭', '┮', '┯', '┰', '┱', '┲', '┳', '┴', '┵', '┶', '┷',
            '┸', '┹', '┺', '┻', '┼', '┽', '┾', '┿', '╀', '╁', '╂', '╃', '╄', '╅',
            '╆', '╇', '╈', '╉', '╊', '╋', '╌', '╍', '╎', '╏', '═', '║', '╒', '╓',
            '╔', '╕', '╖', '╗', '╘', '╙', '╚', '╛', '╜', '╝', '╞', '╟', '╠', '╡',
            '╢', '╣', '╤', '╥', '╦', '╧', '╨', '╩', '╪', '╫', '╬', '¥',
            
            # Математические и технические символы
            '∩', '∪', '√', '∞', '≈', '≠', '≡', '≤', '≥', '⌠', '⌡', '∫', '∴', '∵',
            '∷', '∝', '∮', '∯', '∰', '∱', '∲', '∳', '∀', '∂', '∃', '∄', '∅', '∆',
            '∇', '∈', '∉', '∊', '∋', '∌', '∍', '∎', '∏', '∐', '∑', '−', '∓', '∔',
            '∕', '∖', '∗', '∘', '∙', '√', '∛', '∜', '∝', '∞', '∟', '∠', '∡', '∢',
            '∣', '∤', '∥', '∦', '∧', '∨', '∩', '∪', '∫', '∬', '∭', '∮', '∯', '∰',
            '∱', '∲', '∳', '∴', '∵', '∶', '∷', '∸', '∹', '∺', '∻', '∼', '∽', '∾',
            '∿', '≀', '≁', '≂', '≃', '≄', '≅', '≆', '≇', '≈', '≉', '≊', '≋', '≌',
            '≍', '≎', '≏', '≐', '≑', '≒', '≓', '≔', '≕', '≖', '≗', '≘', '≙', '≚',
            '≛', '≜', '≝', '≞', '≟', '≠', '≡', '≢', '≣', '≤', '≥', '≦', '≧', '≨',
            '≩', '≪', '≫', '≬', '≭', '≮', '≯', '≰', '≱', '≲', '≳', '≴', '≵', '≶',
            '≷', '≸', '≹', '≺', '≻', '≼', '≽', '≾', '≿', '⊀', '⊁', '⊂', '⊃', '⊄',
            '⊅', '⊆', '⊇', '⊈', '⊉', '⊊', '⊋', '⊌', '⊍', '⊎', '⊏', '⊐', '⊑', '⊒',
            '⊓', '⊔', '⊕', '⊖', '⊗', '⊘', '⊙', '⊚', '⊛', '⊜', '⊝', '⊞', '⊟', '⊠',
            '⊡', '⊢', '⊣', '⊤', '⊥', '⊦', '⊧', '⊨', '⊩', '⊪', '⊫', '⊬', '⊭', '⊮',
            '⊯', '⊰', '⊱', '⊲', '⊳', '⊴', '⊵', '⊶', '⊷', '⊸', '⊹', '⊺', '⊻', '⊼',
            '⊽', '⊾', '⊿', '⋀', '⋁', '⋂', '⋃', '⋄', '⋅', '⋆', '⋇', '⋈', '⋉', '⋊',
            '⋋', '⋌', '⋍', '⋎', '⋏', '⋐', '⋑', '⋒', '⋓', '⋔', '⋕', '⋖', '⋗', '⋘',
            '⋙', '⋚', '⋛', '⋜', '⋝', '⋞', '⋟', '⋠', '⋡', '⋢', '⋣', '⋤', '⋥', '⋦',
            '⋧', '⋨', '⋩', '⋪', '⋫', '⋬', '⋭', '⋮', '⋯', '⋰', '⋱', '⋲', '⋳', '⋴',
            '⋵', '⋶', '⋷', '⋸', '⋹', '⋺', '⋻', '⋼', '⋽', '⋾', '⋿',
            
            # Разные символы
            'µ', '¶', '§', '¬', '¤', '¦', '¨', '©', 'ª', '«', '®', '¯', '°', '±',
            '²', '³', '´', '·', '¸', '¹', 'º', '»', '¼', '½', '¾', '¿', 'À', 'Á',
            'Â', 'Ã', 'Ä', 'Å', 'Æ', 'Ç', 'È', 'É', 'Ê', 'Ë', 'Ì', 'Í', 'Î', 'Ï',
            'Ð', 'Ñ', 'Ò', 'Ó', 'Ô', 'Õ', 'Ö', '×', 'Ø', 'Ù', 'Ú', 'Û', 'Ü', 'Ý',
            'Þ', 'ß', 'à', 'á', 'â', 'ã', 'ä', 'å', 'æ', 'ç', 'è', 'é', 'ê', 'ë',
            'ì', 'í', 'î', 'ï', 'ð', 'ñ', 'ò', 'ó', 'ô', 'õ', 'ö', '÷', 'ø', 'ù',
            'ú', 'û', 'ü', 'ý', 'þ', 'ÿ', 'Ā', 'ā', 'Ă', 'ă', 'Ą', 'ą', 'Ć', 'ć',
            'Ĉ', 'ĉ', 'Ċ', 'ċ', 'Č', 'č', 'Ď', 'ď', 'Đ', 'đ', 'Ē', 'ē', 'Ĕ', 'ĕ',
            'Ė', 'ė', 'Ę', 'ę', 'Ě', 'ě', 'Ĝ', 'ĝ', 'Ğ', 'ğ', 'Ġ', 'ġ', 'Ģ', 'ģ',
            'Ĥ', 'ĥ', 'Ħ', 'ħ', 'Ĩ', 'ĩ', 'Ī', 'ī', 'Ĭ', 'ĭ', 'Į', 'į', 'İ', 'ı',
            'Ĳ', 'ĳ', 'Ĵ', 'ĵ', 'Ķ', 'Ķ', 'ķ', 'ĸ', 'Ĺ', 'ĺ', 'Ļ', 'ļ', 'Ľ', 'ľ',
            'Ŀ', 'ŀ', 'Ł', 'ł', 'Ń', 'ń', 'Ņ', 'ņ', 'Ň', 'ň', 'ŉ', 'Ŋ', 'ŋ', 'Ō',
            'ō', 'Ŏ', 'ŏ', 'Ő', 'ő', 'Œ', 'œ', 'Ŕ', 'ŕ', 'Ŗ', 'ŗ', 'Ř', 'ř', 'Ś',
            'ś', 'Ŝ', 'ŝ', 'Ş', 'ş', 'Š', 'š', 'Ţ', 'ţ', 'Ť', 'ť', 'Ŧ', 'ŧ', 'Ũ',
            'ũ', 'Ū', 'ū', 'Ŭ', 'ŭ', 'Ů', 'ů', 'Ű', 'ű', 'Ų', 'ų', 'Ŵ', 'ŵ', 'Ŷ',
            'ŷ', 'Ÿ', 'Ź', 'ź', 'Ż', 'ż', 'Ž', 'ž', 'ſ', 'ƀ', 'Ɓ', 'Ƃ', 'ƃ', 'Ƅ',
            'ƅ', 'Ɔ', 'Ƈ', 'ƈ', 'Ɖ', 'Ɗ', 'Ƌ', 'ƌ', 'ƍ', 'Ǝ', 'Ə', 'Ɛ', 'Ƒ', 'ƒ',
            'Ɠ', 'Ɣ', 'ƕ', 'Ɩ', 'Ɨ', 'Ƙ', 'ƙ', 'ƚ', 'ƛ', 'Ɯ', 'Ɲ', 'ƞ', 'Ɵ', 'Ơ',
            'ơ', 'Ƣ', 'ƣ', 'Ƥ', 'ƥ', 'Ʀ', 'Ƨ', 'ƨ', 'Ʃ', 'ƪ', 'ƫ', 'Ƭ', 'ƭ', 'Ʈ',
            'Ư', 'ư', 'Ʊ', 'Ʋ', 'Ƴ', 'ƴ', 'Ƶ', 'ƶ', 'Ʒ', 'Ƹ', 'ƹ', 'ƺ', 'ƻ', 'Ƽ',
            'ƽ', 'ƾ', 'ƿ', 'ǀ', 'ǁ', 'ǂ', 'ǃ', 'Ǆ', 'ǅ', 'ǆ', 'Ǉ', 'ǈ', 'ǉ', 'Ǌ',
            'ǋ', 'ǌ', 'Ǎ', 'ǎ', 'Ǐ', 'ǐ', 'Ǒ', 'ǒ', 'Ǔ', 'ǔ', 'Ǖ', 'ǖ', 'Ǘ', 'ǘ',
            'Ǚ', 'ǚ', 'Ǜ', 'ǜ', 'ǝ', 'Ǟ', 'ǟ', 'Ǡ', 'ǡ', 'Ǣ', 'ǣ', 'Ǥ', 'ǥ', 'Ǧ',
            'ǧ', 'Ǩ', 'ǩ', 'Ǫ', 'ǫ', 'Ǭ', 'ǭ', 'Ǯ', 'ǯ', 'ǰ', 'Ǳ', 'ǲ', 'ǳ', 'Ǵ',
            'ǵ', 'Ƕ', 'Ƿ', 'Ǹ', 'ǹ', 'Ǻ', 'ǻ', 'Ǽ', 'ǽ', 'Ǿ', 'ǿ', 'Ȁ', 'ȁ', 'Ȃ',
            'ȃ', 'Ȅ', 'ȅ', 'Ȇ', 'ȇ', 'Ȉ', 'ȉ', 'Ȋ', 'ȋ', 'Ȍ', 'ȍ', 'Ȏ', 'ȏ', 'Ȑ',
            'ȑ', 'Ȓ', 'ȓ', 'Ȕ', 'ȕ', 'Ȗ', 'ȗ', 'Ș', 'ș', 'Ț', 'ț', 'Ȝ', 'ȝ', 'Ȟ',
            'ȟ', 'Ƞ', 'ȡ', 'Ȣ', 'ȣ', 'Ȥ', 'ȥ', 'Ȧ', 'ȧ', 'Ȩ', 'ȩ', 'Ȫ', 'ȫ', 'Ȭ',
            'ȭ', 'Ȯ', 'ȯ', 'Ȱ', 'ȱ', 'Ȳ', 'ȳ', 'ȴ', 'ȵ', 'ȶ', 'ȷ', 'ȸ', 'ȹ', 'Ⱥ',
            'Ȼ', 'ȼ', 'Ƚ', 'Ⱦ', 'ȿ', 'ɀ', 'Ɂ', 'ɂ', 'Ƀ', 'Ʉ', 'Ʌ', 'Ɇ', 'ɇ', 'Ɉ',
            'ɉ', 'Ɋ', 'ɋ', 'Ɍ', 'ɍ', 'Ɏ', 'ɏ',
            
            # Греческие символы
            'α', 'β', 'γ', 'δ', 'ε', 'ζ', 'η', 'θ', 'ι', 'κ', 'λ', 'μ', 'ν', 'ξ',
            'ο', 'π', 'ρ', 'ς', 'σ', 'τ', 'υ', 'φ', 'χ', 'ψ', 'ω', 'Α', 'Β', 'Γ',
            'Δ', 'Ε', 'Ζ', 'Η', 'Θ', 'Ι', 'Κ', 'Λ', 'Μ', 'Ν', 'Ξ', 'Ο', 'Π', 'Ρ',
            'Σ', 'Τ', 'Υ', 'Φ', 'Χ', 'Ψ', 'Ω',
            
            # Дополнительные символы
            '⌐', '╧', '╙', '╫'  # Добавлены новые символы
        }
        
        def convert_color(match):
            hex_color = match.group(1).lower()
            text = match.group(2)
            
            # Заменяем все символы фона на пробелы
            for char in BACKGROUND_CHARS:
                text = text.replace(char, ' ')
            return f"\033[38;2;{int(hex_color[0:2], 16)};{int(hex_color[2:4], 16)};{int(hex_color[4:6], 16)}m{text}"
        
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
                for char in BACKGROUND_CHARS:
                    stripped_line = stripped_line.replace(char, ' ')
                
                # Выводим строку арта
                print(stripped_line + "\033[0m")
        return True
    except Exception as e:
        print(f"Ошибка при обработке арта: {str(e)}")
        return False

def clear_screen():
    """Очистка экрана"""
    os.system('cls' if os.name == 'nt' else 'clear')

def show_welcome():
    """Очищает экран и показывает приветственное сообщение"""
    clear_screen()
    if not print_random_art():
        # Если не удалось показать случайный арт, показываем мишку
        art_path = Path("arts") / "mishka.txt"
        if art_path.exists():
            with open(art_path, 'r', encoding='utf-8') as f:
                for line in f:
                    print(line, end='')
    print(f"{Colors.DARK_VIOLET}{Colors.BOLD}Huekka is started!{Colors.ENDC}")

async def setup_session():
    # Создаем папку session, если её нет
    os.makedirs("session", exist_ok=True)
    
    show_welcome()

    print(f"{Colors.LIGHT_BLUE} 1. Go to {Colors.BOLD}https://my.telegram.org/apps{Colors.ENDC}{Colors.LIGHT_BLUE} and login.{Colors.ENDC}")
    print(f"{Colors.LIGHT_BLUE} 2. Click to {Colors.BOLD}API Development tools{Colors.ENDC}{Colors.LIGHT_BLUE}{Colors.ENDC}")
    print(f"{Colors.LIGHT_BLUE} 3. Create new application by entering the required details{Colors.ENDC}")
    print(f"{Colors.LIGHT_BLUE} 4. Copy {Colors.BOLD}API ID{Colors.ENDC}{Colors.LIGHT_BLUE} and {Colors.BOLD}API HASH{Colors.ENDC}{Colors.LIGHT_BLUE}\n{Colors.ENDC}")

    while True:
        api_id = input(f"{Colors.DARK_VIOLET}Enter API ID: {Colors.ENDC}").strip()
        if not api_id.isdigit() or len(api_id) < 5 or len(api_id) > 10:
            print(f"{Colors.RED}Invalid API ID! Must be 5-10 digit number{Colors.ENDC}")
            continue

        api_hash = input(f"{Colors.DARK_VIOLET}Enter API HASH: {Colors.ENDC}").strip()
        if not re.match(r'^[a-f0-9]{32}$', api_hash):
            print(f"{Colors.RED}Invalid API HASH! Must be 32-character hex string{Colors.ENDC}")
            continue

        phone = input(f"{Colors.DARK_VIOLET}Enter phone number: {Colors.ENDC}").strip()
        phone_clean = ''.join(filter(str.isdigit, phone))
        if len(phone_clean) < 10:
            print(f"{Colors.RED}Invalid phone number format!{Colors.ENDC}")
            continue

        break

    client = TelegramClient(StringSession(), int(api_id), api_hash)
    await client.connect()

    try:
        await client.send_code_request(phone_clean)
        print(f"\n{Colors.GREEN}Verification code sent to {phone_clean}{Colors.ENDC}")
    except FloodWaitError as e:
        print(f"\n{Colors.YELLOW}Flood limit exceeded. Wait {e.seconds} seconds{Colors.ENDC}")
        return
    except Exception as e:
        print(f"\n{Colors.RED}Error sending code: {str(e)}{Colors.ENDC}")
        return

    code_attempts = 0
    while code_attempts < 3:
        code = input(f"{Colors.DARK_VIOLET}Enter SMS code: {Colors.ENDC}").replace('-', '')

        try:
            await client.sign_in(phone_clean, code=code)
            break
        except SessionPasswordNeededError:
            password = input(f"{Colors.DARK_VIOLET}Enter 2FA password: {Colors.ENDC}")
            try:
                await client.sign_in(password=password)
                break
            except Exception as e:
                print(f"{Colors.RED}Auth error: {str(e)}{Colors.ENDC}")
                code_attempts = 3
        except PhoneCodeInvalidError:
            print(f"{Colors.RED}Invalid code. Try again{Colors.ENDC}")
            code_attempts += 1
        except Exception as e:
            print(f"{Colors.RED}Auth error: {str(e)}{Colors.ENDC}")
            code_attempts += 1

    if code_attempts >= 3:
        print(f"{Colors.RED}Too many failed attempts{Colors.ENDC}")
        return

    session_str = client.session.save()
    
    # Генерируем ключ шифрования
    encryption_key = SessionManager.generate_encryption_key()
    
    # Сохраняем ключ в .env в папке session
    with open(Path("session") / ".env", 'w') as f:
        f.write(f"ENCRYPTION_KEY={encryption_key}\n")
    
    # Шифруем данные сессии
    session_data = {
        'api_id': int(api_id),
        'api_hash': api_hash,
        'session_string': session_str
    }
    
    encrypted_session = SessionManager.encrypt_data(session_data, encryption_key)
    
    # Сохраняем зашифрованную сессию в папке session
    with open(Path("session") / "Huekka.session", 'w') as f:
        f.write(encrypted_session)

    # Запускаем бота
    show_welcome()
    os.execl(sys.executable, sys.executable, "userbot.py")

async def check_and_update():
    """Проверяет и устанавливает обновления автоматически"""
    updater = Updater()
    
    # Проверяем обновления
    has_update = updater.check_update()
    
    if has_update:
        # Выполняем обновление
        success = updater.perform_update()
        
        if success:
            print(f"{Colors.GREEN} Update installed! Restarting...{Colors.ENDC}")
            # Перезапускаем процесс
            os.execl(sys.executable, sys.executable, "main.py")
        else:
            print(f"{Colors.RED}❌ Update failed!{Colors.ENDC}")
    
    # Если обновлений нет или обновление не удалось, продолжаем запуск

if __name__ == "__main__":
    session_path = Path("session") / "Huekka.session"
    env_path = Path("session") / ".env"

    # Проверяем, существуют ли файлы сессии
    session_exists = session_path.exists()
    env_exists = env_path.exists()
    
    if not session_exists or not env_exists:
        show_welcome()
        
        if session_exists and not env_exists:
            print(f"{Colors.YELLOW}⚠️ Found session file but no encryption key!{Colors.ENDC}")
            print(f"{Colors.YELLOW}This might cause issues. Do you want to:{Colors.ENDC}")
            print(f"{Colors.LIGHT_BLUE}1. Create new session (recommended){Colors.ENDC}")
            print(f"{Colors.LIGHT_BLUE}2. Try to continue anyway{Colors.ENDC}")
            
            choice = input(f"{Colors.DARK_VIOLET}Enter your choice (1/2): {Colors.ENDC}").strip()
            if choice == "1":
                # Удаляем старую сессию и создаем новую
                session_path.unlink()
                asyncio.run(setup_session())
            else:
                # Пытаемся продолжить без ключа шифрования
                print(f"{Colors.YELLOW}⚠️ Continuing without encryption key...{Colors.ENDC}")
                time.sleep(1)
                # Проверяем и устанавливаем обновления
                asyncio.run(check_and_update())
                # Показываем приветственное сообщение
                show_welcome()
                # Запускаем бота
                os.execl(sys.executable, sys.executable, "userbot.py")
        else:
            asyncio.run(setup_session())
    else:
        # Проверяем и устанавливаем обновления
        asyncio.run(check_and_update())
        # Показываем приветственное сообщение
        show_welcome()
        # Запускаем бота
        os.execl(sys.executable, sys.executable, "userbot.py")
