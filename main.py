# ©️ nnnrodnoy, 2025
# 💬 @nnnrodnoy 1111111111
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

class GitHubUpdater:
    def __init__(self):
        self.repo_url = "https://github.com/nnnrodnoy/Huekka"
        self.update_files = ['main.py', 'userbot.py', 'installer.sh', 'start_bot.sh', 'requirements.txt', 'config.py', 'arter.py']
        self.update_dirs = ['core', 'asset', 'arts']
        self.last_update_file = Path("data") / "last_update.txt"
        self.last_update_file.parent.mkdir(exist_ok=True)
    
    async def get_latest_commit_info(self):
        """Получает информацию о последнем коммите из репозитория"""
        try:
            # Альтернативный способ получения информации о репозитории
            result = subprocess.run([
                'git', 'ls-remote', '--heads', self.repo_url
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                # Получаем хэш последнего коммита
                lines = result.stdout.strip().split('\n')
                if lines and lines[0]:
                    latest_commit_hash = lines[0].split()[0]
                    return latest_commit_hash
        except Exception as e:
            logger.error(f"Ошибка получения информации о коммите: {str(e)}")
        
        return None
    
    async def get_local_last_update(self):
        """Получает дату последнего обновления из файла"""
        if self.last_update_file.exists():
            try:
                with open(self.last_update_file, 'r') as f:
                    content = f.read().strip()
                    if content:
                        return content
            except:
                pass
        return ""
    
    async def set_local_last_update(self, commit_hash):
        """Устанавливает хэш коммита как дату последнего обновления"""
        try:
            with open(self.last_update_file, 'w') as f:
                f.write(commit_hash)
            return True
        except Exception as e:
            logger.error(f"Ошибка записи даты обновления: {str(e)}")
            return False
    
    async def check_for_updates(self):
        """Проверяет наличие обновлений"""
        try:
            # Получаем хэш последнего коммита
            latest_commit = await self.get_latest_commit_info()
            if not latest_commit:
                return False
            
            # Получаем хэш последнего локального обновления
            local_commit = await self.get_local_last_update()
            
            # Если коммиты разные, есть обновление
            return latest_commit != local_commit
            
        except Exception as e:
            logger.error(f"Ошибка проверки обновлений: {str(e)}")
            return False
    
    def _get_file_hash(self, file_path):
        """Вычисляет хэш файла для сравнения"""
        if not file_path.exists():
            return None
        
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            while True:
                data = f.read(65536)  # 64kb chunks
                if not data:
                    break
                hasher.update(data)
        return hasher.hexdigest()
    
    def _print_update_status(self, message):
        """Красивый вывод статуса обновления"""
        print(f"{Colors.GREEN_BOLD}[Huekka Update]{Colors.ENDC} {message}")
    
    async def perform_update(self):
        """Выполняет обновление только измененных файлов"""
        temp_dir = tempfile.mkdtemp(prefix="huekka_update_")
        updated_files = 0
        
        try:
            # Получаем хэш последнего коммита перед обновлением
            latest_commit = await self.get_latest_commit_info()
            if not latest_commit:
                return False
            
            # Скачиваем архив с репозиторием
            zip_url = f"{self.repo_url}/archive/refs/heads/main.zip"
            zip_path = Path(temp_dir) / "huekka.zip"
            
            response = requests.get(zip_url, timeout=60)
            if response.status_code != 200:
                return False
            
            with open(zip_path, 'wb') as f:
                f.write(response.content)
            
            # Распаковываем архив
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            extracted_dir = Path(temp_dir) / "Huekka-main"
            
            # Обновляем файлы только если они изменились
            for file in self.update_files:
                repo_file = extracted_dir / file
                local_file = Path(file)
                
                if repo_file.exists():
                    # Создаем директорию, если её нет
                    local_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Проверяем, изменился ли файл
                    repo_hash = self._get_file_hash(repo_file)
                    local_hash = self._get_file_hash(local_file)
                    
                    if repo_hash != local_hash:
                        # Копируем файл только если он изменился
                        shutil.copy2(repo_file, local_file)
                        self._print_update_status(f"Updated: {file}")
                        updated_files += 1
                    else:
                        logger.info(f"File unchanged: {file}")
            
            # Обновляем папки с проверкой изменений
            for dir_name in self.update_dirs:
                repo_dir = extracted_dir / dir_name
                local_dir = Path(dir_name)
                
                if repo_dir.exists():
                    # Рекурсивно обходим все файлы в директории
                    for root, _, files in os.walk(repo_dir):
                        for file in files:
                            repo_file_path = Path(root) / file
                            relative_path = repo_file_path.relative_to(repo_dir)
                            local_file_path = local_dir / relative_path
                            
                            # Проверяем, изменился ли файл
                            repo_hash = self._get_file_hash(repo_file_path)
                            local_hash = self._get_file_hash(local_file_path)
                            
                            if repo_hash != local_hash:
                                # Создаем директорию, если её нет
                                local_file_path.parent.mkdir(parents=True, exist_ok=True)
                                
                                # Копируем файл только если он изменился
                                shutil.copy2(repo_file_path, local_file_path)
                                self._print_update_status(f"Updated: {local_file_path}")
                                updated_files += 1
                            else:
                                logger.info(f"File unchanged: {local_file_path}")
            
            if updated_files > 0:
                # Сохраняем хэш коммита как дату последнего обновления
                await self.set_local_last_update(latest_commit)
                self._print_update_status(f"Updated {updated_files} files")
                return True
            else:
                self._print_update_status("No files need updating")
                return False
            
        except Exception as e:
            logger.error(f"Ошибка выполнения обновления: {str(e)}")
            return False
        finally:
            # Очищаем временные файлы
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    async def auto_update(self):
        """Автоматическая проверка и установка обновлений"""
        try:
            self._print_update_status("Checking for updates...")
            has_update = await self.check_for_updates()
            
            if has_update:
                self._print_update_status("Updates found, installing...")
                success = await self.perform_update()
                
                if success:
                    self._print_update_status("Update successfully installed")
                    return True
                else:
                    self._print_update_status("Error installing update")
            else:
                self._print_update_status("No updates available")
            
            return False
            
        except Exception as e:
            logger.error(f"Ошибка автоматического обновления: {str(e)}")
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

async def check_and_update():
    """Проверяет и устанавливает обновления автоматически"""
    updater = GitHubUpdater()
    
    try:
        # Проверяем и устанавливаем обновления
        needs_restart = await updater.auto_update()
        return needs_restart
    except Exception as e:
        logger.error(f"Ошибка при проверке обновлений: {str(e)}")
        return False

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
