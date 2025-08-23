import os
import sys
import asyncio
import logging
import json
import time
import sqlite3
import base64
import importlib.util
import re
import inspect
from pathlib import Path
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import hashlib
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.functions.channels import JoinChannelRequest
from core.parser import CustomParseMode, EmojiHandler
from core.log import setup_logging
from config import BotConfig
from core.autocleaner import AutoCleaner
from core.apilimiter import APILimiter
from core.system import SystemModule

logger = setup_logging()
logger = logging.getLogger("UserBot")

class Colors:
    LIGHT_BLUE = '\033[94m'
    ENDC = '\033[0m'

class SessionManager:
    @staticmethod
    def get_encryption_key():
        env_path = Path("session") / ".env"
        if not env_path.exists():
            raise Exception("Файл .env не найден в папке session")
        
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith("ENCRYPTION_KEY="):
                    return line.strip().split('=', 1)[1]
        
        raise Exception("Ключ шифрования не найден в .env")

    @staticmethod
    def encrypt_data(data: dict) -> str:
        key = SessionManager.get_encryption_key()
        salt = os.urandom(16)
        derived_key = hashlib.pbkdf2_hmac('sha256', key.encode(), salt, 100000, 32)
        
        cipher = AES.new(derived_key, AES.MODE_CBC, os.urandom(16))
        encrypted = cipher.encrypt(pad(json.dumps(data).encode(), AES.block_size))
        
        return base64.b64encode(salt + cipher.iv + encrypted).decode()

    @staticmethod
    def decrypt_data(encrypted_data: str) -> dict:
        key = SessionManager.get_encryption_key()
        data = base64.b64decode(encrypted_data)
        
        salt = data[:16]
        iv = data[16:32]
        encrypted = data[32:]
        
        derived_key = hashlib.pbkdf2_hmac('sha256', key.encode(), salt, 100000, 32)
        cipher = AES.new(derived_key, AES.MODE_CBC, iv)
        decrypted = unpad(cipher.decrypt(encrypted), AES.block_size)
        
        return json.loads(decrypted.decode())

class UserBot:
    def __init__(self):
        self.client = None
        self.api_id = None
        self.api_hash = None
        self.modules = {}
        self.commands = {}
        self.cache_dir = "cash"
        self.module_descriptions = {}
        self.core_modules = BotConfig.CORE_MODULES
        self.post_restart_actions = []
        self.last_loaded_module = None
        self.config = BotConfig
        self.owner_id = None
        self.start_time = time.time()
        
        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs("modules", exist_ok=True)
        self._init_client()
        
        self.command_prefix = self._load_prefix_from_db()
        
        # Загружаем настройки автоклинера из базы данных
        autoclean_enabled = self.get_config_value('autoclean_enabled', 
                                                 str(BotConfig.AUTOCLEAN["enabled"])).lower() == 'true'
        autoclean_delay = int(self.get_config_value('autoclean_delay', 
                                                  BotConfig.AUTOCLEAN["default_delay"]))
        
        self.autocleaner = AutoCleaner(self, enabled=autoclean_enabled, delay=autoclean_delay)
        self.apilimiter = APILimiter(self)
        self.system_module = SystemModule(self)
    
    def _load_prefix_from_db(self):
        db_path = Path("cash") / "config.db"
        if not db_path.exists():
            # Если базы нет, создаем ее с значением по умолчанию
            os.makedirs("cash", exist_ok=True)
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS global_config (
                         key TEXT PRIMARY KEY,
                         value TEXT)''')
            c.execute("INSERT OR IGNORE INTO global_config (key, value) VALUES ('command_prefix', ?)",
                     (self.config.COMMAND_PREFIX,))
            conn.commit()
            conn.close()
            return self.config.COMMAND_PREFIX
        
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("SELECT value FROM global_config WHERE key='command_prefix'")
            result = c.fetchone()
            conn.close()
            
            return result[0] if result else self.config.COMMAND_PREFIX
        except Exception as e:
            logger.error(f"Ошибка загрузки префикса: {str(e)}")
            return self.config.COMMAND_PREFIX
    
    def get_config_value(self, key, default=None):
        db_path = Path("cash") / "config.db"
        if not db_path.exists():
            return default
        
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("SELECT value FROM global_config WHERE key=?", (key,))
            result = c.fetchone()
            conn.close()
            
            return result[0] if result else default
        except Exception as e:
            logger.error(f"Ошибка загрузки настройки {key}: {str(e)}")
            return default

    def set_config_in_db(self, key, value):
        db_path = Path("cash") / "config.db"
        os.makedirs("cash", exist_ok=True)
        
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS global_config (
                     key TEXT PRIMARY KEY,
                     value TEXT)''')
        c.execute("INSERT OR REPLACE INTO global_config (key, value) VALUES (?, ?)", (key, value))
        conn.commit()
        conn.close()

    def _init_client(self):
        session_path = Path("session") / "Huekka.session"
        if not session_path.exists():
            raise Exception("Файл сессии не найден в папке session")
        
        with open(session_path, 'r') as f:
            encrypted_data = f.read().strip()
        
        try:
            session_data = SessionManager.decrypt_data(encrypted_data)
            self.api_id = session_data['api_id']
            self.api_hash = session_data['api_hash']
            session_str = session_data['session_string']
        except Exception as e:
            logger.error(f"Ошибка дешифровки сессии: {str(e)}")
            raise
        
        self.client = TelegramClient(
            StringSession(session_str),
            self.api_id,
            self.api_hash
        )
        
        self.client.parse_mode = CustomParseMode()
    
    async def start(self):
        await self.client.connect()
        
        if not await self.client.is_user_authorized():
            logger.error("Ошибка авторизации! Проверьте файл сессии")
            return
        
        me = await self.client.get_me()
        self.owner_id = me.id
        logger.info(f"ID владельца бота: {self.owner_id}")
        
        # Автоматическая подписка на канал @BotHuekka
        try:
            channel = await self.client.get_entity('t.me/BotHuekka')
            await self.client(JoinChannelRequest(channel))
            logger.info("Успешно подписался на канал @BotHuekka")
        except Exception as e:
            logger.error(f"Ошибка при подписке на канал @BotHuekka: {str(e)}")
        
        print(f"\n{Colors.LIGHT_BLUE}[+] Welcome Huekka userbot !{Colors.ENDC}")
        print(f"{Colors.LIGHT_BLUE}[+] Usage {self.command_prefix}help to view commands{Colors.ENDC}")
        print(f"{Colors.LIGHT_BLUE}[+] Subscribe to @BotHuekka telegram{Colors.ENDC}")
        print(f"{Colors.LIGHT_BLUE}[+] Use '.sitting' to change the bot settings{Colors.ENDC}\n")
        
        @self.client.on(events.NewMessage(outgoing=True))
        async def command_handler(event):
            prefix = re.escape(self.command_prefix)
            pattern = r'^{}(\w+)(?:\s+([\s\S]*))?$'.format(prefix)
            
            match = re.match(pattern, event.text)
            if match:
                cmd = match.group(1).lower()
                args = match.group(2) or ""
                
                if cmd in self.commands:
                    try:
                        event.text = f"{self.command_prefix}{cmd} {args}"
                        await self.commands[cmd]["handler"](event)
                    except Exception as e:
                        logger.error(f"Ошибка в команде {self.command_prefix}{cmd}: {str(e)}")
                        await event.edit(f"⚠️ Ошибка: {str(e)}")
        
        @self.client.on(events.NewMessage(outgoing=True))
        async def message_handler(event):
            await EmojiHandler.process_message(event)
        
        await self.load_modules()
        
        for action in self.post_restart_actions:
            try:
                await action()
            except Exception as e:
                logger.error(f"Ошибка выполнения post-restart action: {str(e)}")
        self.post_restart_actions = []
        
        if self.last_loaded_module:
            module_name, chat_id, reply_to = self.last_loaded_module
            try:
                if "help" in self.commands:
                    event = events.NewMessage.Event(
                        message=events.Message(
                            id=0,
                            peer=await self.client.get_input_entity(chat_id),
                            text=f"{self.command_prefix}help {module_name}",
                            reply_to=reply_to
                        )
                    )
                    await self.commands["help"]["handler"](event)
            except Exception as e:
                logger.error(f"Ошибка при показе справки: {str(e)}")
            finally:
                self.last_loaded_module = None
        
        await self.client.run_until_disconnected()

    async def load_modules(self):
        # Сначала загружаем core-модули
        core_modules_dir = "core"
        protected_names = ["typing", "sys", "os", "json", "asyncio", "logging", "importlib", "telethon", "config"]
        
        # Загрузка core-модулей
        for file in os.listdir(core_modules_dir):
            if file.endswith(".py") and file != "__init__.py":
                module_name = file[:-3]
                
                # Пропускаем updater.py, так как он не является модулем
                if module_name == "updater":
                    continue
                
                if module_name in protected_names:
                    logger.error(f"Пропуск core-модуля с защищенным именем: {file}")
                    continue
                    
                try:
                    module_path = os.path.join(core_modules_dir, file)
                    
                    spec = importlib.util.spec_from_file_location(module_name, module_path)
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = module
                    spec.loader.exec_module(module)
                    
                    if hasattr(module, 'setup'):
                        before = len(self.commands)
                        setup_func = module.setup
                        
                        # Проверяем, является ли функция асинхронной
                        if inspect.iscoroutinefunction(setup_func):
                            await setup_func(self)
                        else:
                            setup_func(self)
                            
                        after = len(self.commands)
                        
                        logger.debug(f"Core-модуль {module_name} загружен (команд: {after - before})")
                except Exception as e:
                    error_msg = f"Ошибка загрузки core-модуля {file}: {str(e)}"
                    logger.error(error_msg)
        
        # Затем загружаем пользовательские модули из папки modules
        modules_dir = "modules"
        
        for file in os.listdir(modules_dir):
            if file.endswith(".py") and file != "__init__.py":
                module_name = file[:-3]
                
                if module_name in protected_names:
                    logger.error(f"Пропуск модуля с защищенным именем: {file}")
                    continue
                    
                try:
                    module_path = os.path.join(modules_dir, file)
                    
                    spec = importlib.util.spec_from_file_location(module_name, module_path)
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = module
                    spec.loader.exec_module(module)
                    
                    if hasattr(module, 'setup'):
                        before = len(self.commands)
                        setup_func = module.setup
                        
                        # Проверяем, является ли функция асинхронной
                        if inspect.iscoroutinefunction(setup_func):
                            await setup_func(self)
                        else:
                            setup_func(self)
                            
                        after = len(self.commands)
                        
                        logger.debug(f"Модуль {module_name} загружен (команд: {after - before})")
                except Exception as e:
                    error_msg = f"Ошибка загрузки модуля {file}: {str(e)}"
                    logger.error(error_msg)

    def register_command(self, cmd, handler, description="", module_name="System"):
        self.commands[cmd] = {
            "handler": handler,
            "description": description,
            "module": module_name
        }
        
        if module_name not in self.modules:
            self.modules[module_name] = {}
        
        self.modules[module_name][cmd] = {
            "description": description
        }
    
    def set_module_description(self, module_name, description):
        self.module_descriptions[module_name] = description
    
    def add_post_restart_action(self, action):
        self.post_restart_actions.append(action)
    
    async def restart(self):
        logger.info("Перезагрузка бота...")
        os.execl(sys.executable, sys.executable, *sys.argv)
    
    async def stop(self):
        if self.client and self.client.is_connected():
            await self.client.disconnect()

async def main():
    bot = UserBot()
    try:
        await bot.start()
    except Exception as e:
        logger.error(f"Критическая ошибка: {str(e)}")
    finally:
        await bot.stop()

if __name__ == "__main__":
    asyncio.run(main())
