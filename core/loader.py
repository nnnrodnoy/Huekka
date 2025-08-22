import os
import sys
import importlib
import asyncio
import logging
import sqlite3
import difflib
from pathlib import Path
from telethon import events, types
from telethon.errors import MessageNotModifiedError
import traceback
import time
from config import BotConfig

logger = logging.getLogger("UserBot.Loader")

class LoaderModule:
    def __init__(self, bot):
        self.bot = bot
        
        # ID эмодзи из конфига
        self.loader_emoji_id = BotConfig.EMOJI_IDS["loader"]
        self.loaded_emoji_id = BotConfig.EMOJI_IDS["loaded"]
        self.command_emoji_id = BotConfig.EMOJI_IDS["command"]
        self.dev_emoji_id = BotConfig.EMOJI_IDS["dev"]
        self.info_emoji_id = BotConfig.EMOJI_IDS["info"]
        
        # Настройки из конфига
        self.min_animation_time = BotConfig.LOADER["min_animation_time"]
        self.delete_delay = BotConfig.LOADER["delete_delay"]
        
        bot.register_command(
            cmd="lm",
            handler=self.load_module,
            description="Загрузить модуль из файла",
            module_name="Loader"
        )
        
        bot.register_command(
            cmd="ulm",
            handler=self.unload_module,
            description="Выгрузить модуль",
            module_name="Loader"
        )
        
        bot.set_module_description("Loader", "Динамическая загрузка модулей")
        
        # Подключаемся к базе смайликов
        self.smile_db_path = Path("cash") / "smiles.db"
        self._init_smile_database()

    def get_module_info(self):
        return {
            "name": "Loader",
            "description": "Динамическая загрузка модулей",
            "developer": "@BotHuekka",
            "version": "1.0.0",
            "commands": [
                {
                    "command": "lm",
                    "description": "Загрузить модуль из файла"
                },
                {
                    "command": "ulm",
                    "description": "Выгрузить модуль"
                }
            ]
        }

    def _init_smile_database(self):
        """Инициализация базы смайлов (если не существует)"""
        os.makedirs("cash", exist_ok=True)
        conn = sqlite3.connect(self.smile_db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS smiles
                     (id INTEGER PRIMARY KEY, smile TEXT)''')
        if c.execute("SELECT COUNT(*) FROM smiles").fetchone()[0] == 0:
            for smile in BotConfig.DEFAULT_SMILES:
                c.execute("INSERT INTO smiles (smile) VALUES (?)", (smile,))
            conn.commit()
        conn.close()

    def get_random_smile(self):
        """Получение случайного смайла"""
        conn = sqlite3.connect(self.smile_db_path)
        smile = conn.cursor().execute(
            "SELECT smile FROM smiles ORDER BY RANDOM() LIMIT 1"
        ).fetchone()[0]
        conn.close()
        return smile

    async def get_user_info(self, event):
        """Получение информации о пользователе с кэшированием"""
        try:
            user = await event.get_sender()
            return {
                "premium": user.premium if hasattr(user, 'premium') else False,
                "username": user.username or f"id{user.id}"
            }
        except Exception as e:
            logger.error(f"Ошибка получения информации о пользователе: {str(e)}")
            return {"premium": False, "username": "unknown"}

    async def find_module_info(self, module_name):
        """
        Находит информацию о модуле по имени файла или имени регистрации
        Возвращает кортеж: (найденное имя модуля, информация)
        """
        normalized_query = module_name.lower().strip()
        
        # Прямое совпадение
        if module_name in self.bot.modules:
            return module_name, await self.get_module_info(module_name)
        
        # Поиск без учета регистра
        for name in self.bot.modules.keys():
            if name.lower() == normalized_query:
                return name, await self.get_module_info(name)
        
        # Поиск по имени файла без расширения
        file_name = normalized_query.replace('.py', '')
        for name in self.bot.modules.keys():
            if name.lower() == file_name:
                return name, await self.get_module_info(name)
        
        # Нечеткий поиск
        closest = difflib.get_close_matches(
            normalized_query,
            [name.lower() for name in self.bot.modules.keys()],
            n=1,
            cutoff=0.3
        )
        
        if closest:
            for name in self.bot.modules.keys():
                if name.lower() == closest[0]:
                    return name, await self.get_module_info(name)
        
        return None, None

    async def get_module_info(self, module_name):
        """Получение информации о модуле"""
        if module_name not in self.bot.modules:
            return None
            
        # Пытаемся получить информацию из самого модуля
        try:
            module = sys.modules.get(module_name)
            if module and hasattr(module, 'get_module_info'):
                return module.get_module_info()
        except Exception:
            pass
        
        # Формируем информацию по умолчанию
        commands = []
        for cmd, data in self.bot.modules[module_name].items():
            commands.append({
                "command": cmd,
                "description": data.get("description", "Без описания")
            })
        
        return {
            "name": module_name,
            "description": self.bot.module_descriptions.get(module_name, ""),
            "commands": commands,
            "is_stock": module_name in self.bot.core_modules,
            "version": "1.0.0",
            "developer": "@BotHuekka"
        }

    async def format_module_loaded_message(self, module_info, event):
        """Форматирование сообщения о загруженном модуле"""
        user_info = await self.get_user_info(event)
        is_premium = user_info["premium"]
        prefix = self.bot.command_prefix
        
        text = ""
        if is_premium:
            text += f"[🌘](emoji/{self.loaded_emoji_id}) "
        text += f"**{module_info['name']} загружен (v{module_info['version']})**\n"
        
        if module_info['description']:
            text += f"__{module_info['description']}__\n"
            
        text += f"__{self.get_random_smile()}__\n\n"
        
        for cmd in module_info['commands']:
            if is_premium:
                text += f"[▫️](emoji/{self.command_emoji_id}) "
            else:
                text += "▫️ "
                
            text += f"`{prefix}{cmd['command']}` - __{cmd['description']}__\n"
        
        text += "\n"
        if is_premium:
            text += f"[🫶](emoji/{self.dev_emoji_id}) "
        else:
            text += "🫶 "
        text += f"**Разработчик:** {module_info['developer']}"
        
        return text

    async def format_module_unloaded_message(self, module_name, event):
        """Форматирование сообщения об удалении модуля"""
        user_info = await self.get_user_info(event)
        is_premium = user_info["premium"]
        prefix = self.bot.command_prefix
        
        text = ""
        if is_premium:
            text += f"[▪️](emoji/{self.info_emoji_id})"
        else:
            text += "▪️"
        
        text += f"**Модуль {module_name} успешно удален.**\n"
        text += f"__(Используйте `{prefix}help` для просмотра модулей и команд.)__"
        
        return text

    async def animate_loading(self, event, message, is_premium):
        """Анимация загрузки/выгрузки с минимальным временем показа"""
        animation = ["/", "-", "\\", "|"]
        start_time = time.time()
        i = 0
        
        min_duration = self.min_animation_time
        
        try:
            while time.time() - start_time < min_duration:
                frame = animation[i % len(animation)]
                prefix = f"[⚙️](emoji/{self.loader_emoji_id}) " if is_premium else "⚙️ "
                await event.edit(f"{prefix}{message} {frame}")
                i += 1
                await asyncio.sleep(0.3)
        except MessageNotModifiedError:
            pass
        except Exception as e:
            logger.error(f"Ошибка анимации: {str(e)}")

    async def load_module(self, event):
        """Обработчик команды .lm"""
        if not event.is_reply:
            await event.edit("ℹ️ Ответьте на сообщение с файлом модуля!")
            return

        reply = await event.get_reply_message()
        if not reply.document or not reply.document.mime_type == "text/x-python":
            await event.edit("🚫 **Это не Python-файл!**")
            return

        user_info = await self.get_user_info(event)
        is_premium = user_info["premium"]

        # Получаем имя файла из атрибутов документа
        file_name = None
        for attr in reply.document.attributes:
            if isinstance(attr, types.DocumentAttributeFilename):
                file_name = attr.file_name
                break
        
        if not file_name:
            await event.edit("🚫 **Не удалось определить имя файла!**")
            return

        module_name = os.path.basename(file_name).replace(".py", "")
        
        anim_task = asyncio.create_task(
            self.animate_loading(event, f"Загружаю модуль `{module_name}`", is_premium)
        )

        # Временный путь для загрузки файла
        temp_dir = Path("temp_modules")
        temp_dir.mkdir(exist_ok=True)
        temp_file = temp_dir / file_name
        
        try:
            # Скачиваем файл во временную директорию
            module_file = await reply.download_media(file=str(temp_file))
            
            # Проверяем модуль на ошибки
            start_time = time.time()
            before_commands = set(self.bot.commands.keys())
            
            # Загружаем модуль для проверки
            spec = importlib.util.spec_from_file_location(module_name, module_file)
            module = importlib.util.module_from_spec(spec)
            
            # Выполняем модуль для проверки на ошибки
            spec.loader.exec_module(module)
            
            if not hasattr(module, 'setup'):
                raise Exception("В модуле отсутствует функция setup()")
            
            # Тестируем вызов setup
            test_bot = type('TestBot', (), {})()
            test_bot.commands = {}
            test_bot.modules = {}
            test_bot.module_descriptions = {}
            
            def mock_register_command(cmd, handler, description="", module_name="Test"):
                test_bot.commands[cmd] = {
                    "handler": handler,
                    "description": description,
                    "module": module_name
                }
            
            test_bot.register_command = mock_register_command
            test_bot.set_module_description = lambda name, desc: None
            
            # Вызываем setup на тестовом боте
            module.setup(test_bot)
            
            # Если дошли сюда, значит ошибок нет - перемещаем файл в папку modules
            final_path = Path("modules") / file_name
            os.rename(module_file, final_path)
            module_file = str(final_path)
            
            # Теперь загружаем модуль на реальном боте
            spec = importlib.util.spec_from_file_location(module_name, module_file)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            module.setup(self.bot)
                
            after_commands = set(self.bot.commands.keys())
            new_commands = after_commands - before_commands
            
            found_name, module_info = await self.find_module_info(module_name)
            
            elapsed = time.time() - start_time
            if elapsed < self.min_animation_time:
                await asyncio.sleep(self.min_animation_time - elapsed)
            
            if module_info:
                loaded_message = await self.format_module_loaded_message(module_info, event)
                await event.edit(loaded_message)
                logger.info(f"Модуль {found_name} загружен (команд: {len(new_commands)})")
            else:
                module_info = {
                    "name": module_name,
                    "description": "Описание недоступно",
                    "commands": [{
                        "command": cmd, 
                        "description": self.bot.commands[cmd].get("description", "Без описания")
                    } for cmd in new_commands],
                    "version": "1.0.0",
                    "developer": "@BotHuekka"
                }
                loaded_message = await self.format_module_loaded_message(module_info, event)
                await event.edit(loaded_message)
                
        except Exception as e:
            error_trace = traceback.format_exc()
            logger.error(f"Ошибка загрузки модуля: {str(e)}\n{error_trace}")
            
            # Удаляем временный файл, если он существует
            if 'module_file' in locals() and os.path.exists(module_file):
                try:
                    os.remove(module_file)
                except:
                    pass
                    
            # Удаляем файл из папки modules, если он там оказался
            modules_path = Path("modules") / file_name
            if modules_path.exists():
                try:
                    os.remove(modules_path)
                except:
                    pass
            
            await event.edit(
                f"🚫 **Ошибка загрузки модуля:** ```{str(e)}```\n"
                "ℹ️ **Проверьте логи для подробностей.**"
            )
        finally:
            # Очищаем временную директорию
            try:
                if temp_file.exists():
                    os.remove(temp_file)
            except:
                pass
                
            if not anim_task.done():
                anim_task.cancel()

    async def unload_module(self, event):
        """Обработчик команды .ulm"""
        prefix = self.bot.command_prefix
        
        args = event.text.split()
        if len(args) < 2:
            await event.edit(f"ℹ️ **Укажите название модуля:** `{prefix}ulm ModuleName`")
            return

        module_query = " ".join(args[1:]).strip()
        
        found_name, module_info = await self.find_module_info(module_query)
        
        if not found_name:
            await event.edit(f"🚫 **Модуль** `{module_query}` не найден!")
            return
            
        module_path = f"modules/{found_name}.py"
        
        if not os.path.exists(module_path):
            await event.edit(f"🚫 **Модуль** `{found_name}` не найден!")
            return

        user_info = await self.get_user_info(event)
        is_premium = user_info["premium"]

        anim_task = asyncio.create_task(
            self.animate_loading(event, f"Удаляю модуль `{found_name}`", is_premium)
        )

        try:
            start_time = time.time()
            
            commands_to_remove = [
                cmd for cmd, data in self.bot.commands.items() 
                if data.get("module") and data.get("module").lower() == found_name.lower()
            ]
            
            for cmd in commands_to_remove:
                del self.bot.commands[cmd]
            
            if found_name in sys.modules:
                del sys.modules[found_name]
            
            os.remove(module_path)
            
            if found_name in self.bot.modules:
                del self.bot.modules[found_name]
            
            if found_name in self.bot.module_descriptions:
                del self.bot.module_descriptions[found_name]
            
            elapsed = time.time() - start_time
            if elapsed < self.min_animation_time:
                await asyncio.sleep(self.min_animation_time - elapsed)
            
            unloaded_message = await self.format_module_unloaded_message(found_name, event)
            message = await event.edit(unloaded_message)
            
            await asyncio.sleep(self.delete_delay)
            await message.delete()
            
        except Exception as e:
            error_trace = traceback.format_exc()
            logger.error(f"Ошибка выгрузки модуля: {str(e)}\n{error_trace}")
            await event.edit(
                f"🚫 **Ошибка выгрузки модуля:** ```{str(e)}```\n"
                "ℹ️ **Проверьте логи для подробностей.**"
            )
        finally:
            if not anim_task.done():
                anim_task.cancel()

def get_module_info():
    return {
        "name": "Loader",
        "description": "Динамическая загрузка модулей",
        "developer": "@BotHuekka",
        "version": "1.0.0",
        "commands": [
            {
                "command": "lm",
                "description": "Загрузить модуль из файла"
            },
            {
                "command": "ulm",
                "description": "Выгрузить модуль"
            }
        ]
    }

def setup(bot):
    LoaderModule(bot)
