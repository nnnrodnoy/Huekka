# database.py
import sqlite3
import os
import logging
from pathlib import Path
from typing import List, Tuple, Any, Optional, Dict, Union
import json
from datetime import datetime

logger = logging.getLogger("UserBot.Database")

class DatabaseManager:
    def __init__(self, db_folder: str = "cash"):
        self.db_folder = db_folder
        os.makedirs(db_folder, exist_ok=True)
        
        # Инициализация всех баз данных
        self._init_databases()
    
    def _init_databases(self):
        """Инициализация всех баз данных при запуске"""
        self.init_config_db()
        self.init_smiles_db()
        self.init_autoclean_db()
        self.init_quotes_db()
        self.init_modules_db()
    
    def get_db_path(self, db_name: str) -> str:
        """Получение полного пути к файлу базы данных"""
        return str(Path(self.db_folder) / db_name)
    
    def execute_query(self, db_name: str, query: str, params: tuple = (), 
                     fetchone: bool = False, fetchall: bool = False, commit: bool = False) -> Any:
        """
        Универсальный метод выполнения SQL-запросов
        
        Args:
            db_name: Имя файла базы данных
            query: SQL-запрос
            params: Параметры запроса
            fetchone: Вернуть одну запись
            fetchall: Вернуть все записи
            commit: Выполнить commit
        
        Returns:
            Результат запроса или None
        """
        db_path = self.get_db_path(db_name)
        result = None
        
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row  # Для доступа к колонкам по имени
            cursor = conn.cursor()
            
            cursor.execute(query, params)
            
            if fetchone:
                result = cursor.fetchone()
            elif fetchall:
                result = cursor.fetchall()
            
            if commit:
                conn.commit()
                
        except sqlite3.Error as e:
            logger.error(f"Ошибка выполнения запроса к {db_name}: {str(e)}")
            if 'conn' in locals():
                conn.rollback()
            raise e
        finally:
            if 'conn' in locals():
                conn.close()
        
        return result
    
    # ===== CONFIG DATABASE =====
    def init_config_db(self):
        """Инициализация базы данных конфигурации"""
        db_name = "config.db"
        
        queries = [
            '''CREATE TABLE IF NOT EXISTS global_config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at INTEGER DEFAULT (strftime('%s', 'now'))
            )''',
            
            '''CREATE TABLE IF NOT EXISTS user_settings (
                user_id INTEGER PRIMARY KEY,
                settings TEXT NOT NULL DEFAULT '{}',
                updated_at INTEGER DEFAULT (strftime('%s', 'now'))
            )''',
            
            '''CREATE TABLE IF NOT EXISTS module_settings (
                module_name TEXT PRIMARY KEY,
                settings TEXT NOT NULL DEFAULT '{}',
                updated_at INTEGER DEFAULT (strftime('%s', 'now'))
            )'''
        ]
        
        for query in queries:
            self.execute_query(db_name, query, commit=True)
        
        # Установка значений по умолчанию
        default_config = [
            ('command_prefix', '.'),
            ('autoclean_enabled', 'True'),
            ('autoclean_delay', '1800'),
            ('language', 'ru'),
            ('timezone', 'UTC+3')
        ]
        
        for key, value in default_config:
            self.execute_query(
                db_name,
                "INSERT OR IGNORE INTO global_config (key, value) VALUES (?, ?)",
                (key, value),
                commit=True
            )
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Получение значения из глобальной конфигурации"""
        result = self.execute_query(
            "config.db",
            "SELECT value FROM global_config WHERE key = ?",
            (key,),
            fetchone=True
        )
        
        return result[0] if result else default
    
    def set_config_value(self, key: str, value: Any) -> bool:
        """Установка значения в глобальной конфигурации"""
        try:
            self.execute_query(
                "config.db",
                "INSERT OR REPLACE INTO global_config (key, value) VALUES (?, ?)",
                (key, str(value)),
                commit=True
            )
            return True
        except Exception as e:
            logger.error(f"Ошибка установки конфига {key}: {str(e)}")
            return False
    
    def get_user_settings(self, user_id: int) -> Dict:
        """Получение настроек пользователя"""
        result = self.execute_query(
            "config.db",
            "SELECT settings FROM user_settings WHERE user_id = ?",
            (user_id,),
            fetchone=True
        )
        
        if result:
            return json.loads(result[0])
        return {}
    
    def set_user_settings(self, user_id: int, settings: Dict) -> bool:
        """Установка настроек пользователя"""
        try:
            self.execute_query(
                "config.db",
                "INSERT OR REPLACE INTO user_settings (user_id, settings) VALUES (?, ?)",
                (user_id, json.dumps(settings)),
                commit=True
            )
            return True
        except Exception as e:
            logger.error(f"Ошибка установки настроек пользователя {user_id}: {str(e)}")
            return False
    
    # ===== SMILES DATABASE =====
    def init_smiles_db(self):
        """Инициализация базы данных смайлов"""
        db_name = "smiles.db"
        
        query = '''CREATE TABLE IF NOT EXISTS smiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            smile TEXT NOT NULL UNIQUE,
            usage_count INTEGER DEFAULT 0,
            created_at INTEGER DEFAULT (strftime('%s', 'now'))
        )'''
        
        self.execute_query(db_name, query, commit=True)
        
        # Добавление смайлов по умолчанию, если таблица пуста
        count = self.execute_query(
            db_name,
            "SELECT COUNT(*) FROM smiles",
            fetchone=True
        )
        
        if count and count[0] == 0:
            default_smiles = [
                "╰(^∇^)╯", "(〜￣▽￣)〜", "٩(◕‿◕｡)۶", "ヾ(＾-＾)ノ", 
                "ʕ•́ᴥ•̀ʔっ", "(◠‿◠✿)", "(◕ω◕✿)", "(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧", 
                "♡(˃͈ દ ˂͈ ༶ )", "ヽ(♡‿♡)ノ"
            ]
            
            for smile in default_smiles:
                self.execute_query(
                    db_name,
                    "INSERT INTO smiles (smile) VALUES (?)",
                    (smile,),
                    commit=True
                )
    
    def get_random_smile(self) -> str:
        """Получение случайного смайла"""
        result = self.execute_query(
            "smiles.db",
            "SELECT smile FROM smiles ORDER BY RANDOM() LIMIT 1",
            fetchone=True
        )
        
        return result[0] if result else "☺️"
    
    def add_smile(self, smile: str) -> bool:
        """Добавление нового смайла"""
        try:
            self.execute_query(
                "smiles.db",
                "INSERT OR IGNORE INTO smiles (smile) VALUES (?)",
                (smile,),
                commit=True
            )
            return True
        except Exception as e:
            logger.error(f"Ошибка добавления смайла: {str(e)}")
            return False
    
    # ===== AUTOCLEAN DATABASE =====
    def init_autoclean_db(self):
        """Инициализация базы данных автоочистки"""
        db_name = "autoclean.db"
        
        query = '''CREATE TABLE IF NOT EXISTS autoclean_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            message_id INTEGER NOT NULL,
            delete_at REAL NOT NULL,
            attempts INTEGER DEFAULT 0,
            created_at INTEGER DEFAULT (strftime('%s', 'now'))
        )'''
        
        self.execute_query(db_name, query, commit=True)
    
    def add_to_autoclean(self, chat_id: int, message_id: int, delete_after: int) -> bool:
        """Добавление сообщения в очередь автоочистки"""
        delete_at = datetime.now().timestamp() + delete_after
        
        try:
            self.execute_query(
                "autoclean.db",
                "INSERT INTO autoclean_queue (chat_id, message_id, delete_at) VALUES (?, ?, ?)",
                (chat_id, message_id, delete_at),
                commit=True
            )
            return True
        except Exception as e:
            logger.error(f"Ошибка добавления в автоочистку: {str(e)}")
            return False
    
    def get_pending_autoclean(self) -> List[Tuple]:
        """Получение сообщений, готовых к удалению"""
        current_time = datetime.now().timestamp()
        
        results = self.execute_query(
            "autoclean.db",
            "SELECT id, chat_id, message_id, attempts FROM autoclean_queue WHERE delete_at <= ?",
            (current_time,),
            fetchall=True
        )
        
        return [(row[0], row[1], row[2], row[3]) for row in results] if results else []
    
    def remove_from_autoclean(self, record_id: int) -> bool:
        """Удаление записи из автоочистки"""
        try:
            self.execute_query(
                "autoclean.db",
                "DELETE FROM autoclean_queue WHERE id = ?",
                (record_id,),
                commit=True
            )
            return True
        except Exception as e:
            logger.error(f"Ошибка удаления из автоочистки: {str(e)}")
            return False
    
    def update_autoclean_attempt(self, record_id: int, attempts: int, new_delete_at: float) -> bool:
        """Обновление попытки автоочистки"""
        try:
            self.execute_query(
                "autoclean.db",
                "UPDATE autoclean_queue SET attempts = ?, delete_at = ? WHERE id = ?",
                (attempts, new_delete_at, record_id),
                commit=True
            )
            return True
        except Exception as e:
            logger.error(f"Ошибка обновления автоочистки: {str(e)}")
            return False
    
    # ===== QUOTES DATABASE =====
    def init_quotes_db(self):
        """Инициализация базы данных цитат"""
        db_name = "quotes.db"
        
        query = '''CREATE TABLE IF NOT EXISTS quotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            author_id INTEGER NOT NULL,
            author_name TEXT NOT NULL,
            date_added INTEGER NOT NULL,
            tags TEXT DEFAULT '',
            likes INTEGER DEFAULT 0,
            dislikes INTEGER DEFAULT 0
        )'''
        
        self.execute_query(db_name, query, commit=True)
    
    def add_quote(self, text: str, author_id: int, author_name: str) -> int:
        """Добавление новой цитаты"""
        try:
            result = self.execute_query(
                "quotes.db",
                "INSERT INTO quotes (text, author_id, author_name, date_added) VALUES (?, ?, ?, ?)",
                (text, author_id, author_name, int(datetime.now().timestamp())),
                commit=True
            )
            
            # Получаем ID добавленной цитаты
            quote_id = self.execute_query(
                "quotes.db",
                "SELECT last_insert_rowid()",
                fetchone=True
            )
            
            return quote_id[0] if quote_id else 0
        except Exception as e:
            logger.error(f"Ошибка добавления цитаты: {str(e)}")
            return 0
    
    def get_random_quote(self) -> Optional[sqlite3.Row]:
        """Получение случайной цитаты"""
        return self.execute_query(
            "quotes.db",
            "SELECT * FROM quotes ORDER BY RANDOM() LIMIT 1",
            fetchone=True
        )
    
    def get_quotes_by_author(self, author_id: int, limit: int = 10) -> List[sqlite3.Row]:
        """Получение цитат по автору"""
        return self.execute_query(
            "quotes.db",
            "SELECT * FROM quotes WHERE author_id = ? ORDER BY id DESC LIMIT ?",
            (author_id, limit),
            fetchall=True
        )
    
    def search_quotes(self, search_text: str, limit: int = 10) -> List[sqlite3.Row]:
        """Поиск цитат по тексту"""
        return self.execute_query(
            "quotes.db",
            "SELECT * FROM quotes WHERE text LIKE ? LIMIT ?",
            (f"%{search_text}%", limit),
            fetchall=True
        )
    
    def delete_quote(self, quote_id: int) -> bool:
        """Удаление цитаты по ID"""
        try:
            self.execute_query(
                "quotes.db",
                "DELETE FROM quotes WHERE id = ?",
                (quote_id,),
                commit=True
            )
            return True
        except Exception as e:
            logger.error(f"Ошибка удаления цитаты: {str(e)}")
            return False
    
    # ===== MODULES DATABASE =====
    def init_modules_db(self):
        """Инициализация базы данных модулей"""
        db_name = "modules.db"
        
        query = '''CREATE TABLE IF NOT EXISTS modules (
            name TEXT PRIMARY KEY,
            enabled INTEGER DEFAULT 1,
            settings TEXT DEFAULT '{}',
            last_loaded INTEGER,
            load_count INTEGER DEFAULT 0
        )'''
        
        self.execute_query(db_name, query, commit=True)
    
    def get_module_settings(self, module_name: str) -> Dict:
        """Получение настроек модуля"""
        result = self.execute_query(
            "modules.db",
            "SELECT settings FROM modules WHERE name = ?",
            (module_name,),
            fetchone=True
        )
        
        if result:
            return json.loads(result[0])
        return {}
    
    def set_module_settings(self, module_name: str, settings: Dict) -> bool:
        """Установка настроек модуля"""
        try:
            self.execute_query(
                "modules.db",
                '''INSERT OR REPLACE INTO modules (name, settings, last_loaded, load_count) 
                   VALUES (?, ?, COALESCE((SELECT last_loaded FROM modules WHERE name = ?), strftime('%s', 'now')), 
                   COALESCE((SELECT load_count FROM modules WHERE name = ?), 0) + 1)''',
                (module_name, json.dumps(settings), module_name, module_name),
                commit=True
            )
            return True
        except Exception as e:
            logger.error(f"Ошибка установки настроек модуля {module_name}: {str(e)}")
            return False
    
    def is_module_enabled(self, module_name: str) -> bool:
        """Проверка, включен ли модуль"""
        result = self.execute_query(
            "modules.db",
            "SELECT enabled FROM modules WHERE name = ?",
            (module_name,),
            fetchone=True
        )
        
        return bool(result[0]) if result else True
    
    def set_module_enabled(self, module_name: str, enabled: bool) -> bool:
        """Включение/выключение модуля"""
        try:
            self.execute_query(
                "modules.db",
                "INSERT OR REPLACE INTO modules (name, enabled) VALUES (?, ?)",
                (module_name, int(enabled)),
                commit=True
            )
            return True
        except Exception as e:
            logger.error(f"Ошибка изменения состояния модуля {module_name}: {str(e)}")
            return False

# Создаем глобальный экземпляр для использования в модулях
db_manager = DatabaseManager()

def setup(bot):
    """Функция setup для загрузки модуля"""
    # Мы не регистрируем команды, так как это сервисный модуль
    bot.db = db_manager
    logger.info("Database Manager инициализирован")
