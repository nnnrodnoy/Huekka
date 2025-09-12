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
import logging
import requests
import zipfile
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

# Импортируем функции для работы с артами
from arter import print_random_art, print_specific_art

# Импортируем обновленную систему обновлений
from updater import check_and_update

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("Huekka.Main")

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
    GREEN_BOLD = '\033[1;92m'  # Жирный зеленый цвет

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

def clear_screen():
    """Очистка экрана"""
    os.system('cls' if os.name == 'nt' else 'clear')

def show_welcome():
    """Очищает экран и показывает приветственное сообщение"""
    clear_screen()
    if not print_random_art():
        # Если не удалось показать случайный арт, показываем мишку
        if not print_specific_art("mishka"):
            # Если даже мишки нет, просто выводим текст
            print(f"{Colors.DARK_VIOLET}{Colors.BOLD}Huekka UserBot{Colors.ENDC}")
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
                needs_restart = asyncio.run(check_and_update())
                if needs_restart:
                    print(f"{Colors.GREEN}✅ Update installed! Restarting...{Colors.ENDC}")
                    os.execl(sys.executable, sys.executable, "main.py")
                # Показываем приветственное сообщение
                show_welcome()
                # Запускаем бота
                os.execl(sys.executable, sys.executable, "userbot.py")
        else:
            asyncio.run(setup_session())
    else:
        # Проверяем и устанавливаем обновления
        needs_restart = asyncio.run(check_and_update())
        if needs_restart:
            print(f"{Colors.GREEN}✅ Update installed! Restarting...{Colors.ENDC}")
            os.execl(sys.executable, sys.executable, "main.py")
        # Показываем приветственное сообщение
        show_welcome()
        # Запускаем бота
        os.execl(sys.executable, sys.executable, "userbot.py")
