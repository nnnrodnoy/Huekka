# ©️ nnnrodnoy, 2025
# 💬 @nnnrodnoy
# This file is part of Huekka
# 🌐 https://github.com/nnnrodnoy/Huekka/
# You can redistribute it and/or modify it under the terms of the MIT License
# 🔑 https://opensource.org/licenses/MIT
import os
import sys
import importlib
import asyncio
import logging
import difflib
from pathlib import Path
from telethon import events, types
from telethon.errors import MessageNotModifiedError
import traceback
import time
import random
import re
from config import BotConfig
from core.formatters import loader_format

logger = logging.getLogger("UserBot.Loader")

def get_module_info():
    return {
        "name": "Loader",
        "description": "Динамическая загрузка и выгрузка модулей",
        "developer": "@BotHuekka",
        "version": "1.0.0",
        "commands": [
            {
                "command": "lm",
                "description": "Загрузить модуль из файла"
            },
            {
                "command": "ulm",
                "description": "Выгрузить модуль по имени"
            }
        ]
    }

MODULE_INFO = get_module_info()

class LoaderModule:
    def __init__(self, bot):
        self.bot = bot
        
        # Безопасное получение emoji ID с значениями по умолчанию
        self.loader_emoji_id = BotConfig.EMOJI_IDS.get("loader", "5370932688993656500")
        self.loaded_emoji_id = BotConfig.EMOJI_IDS.get("loaded", "5370932688993656500")
        self.command_emoji_id = BotConfig.EMOJI_IDS.get("command", "5370932688993656500")
        self.dev_emoji_id = BotConfig.EMOJI_IDS.get("dev", "5370932688993656500")
        self.info_emoji_id = BotConfig.EMOJI_IDS.get("info", "5422439311196834318")
        self.error_emoji_id = BotConfig.EMOJI_IDS.get("error", "5240241223632954241")
        self.unload_emoji_id = "5251522431977291010"  # Специальный emoji для удаления
        
        self.min_animation_time = BotConfig.LOADER.get("min_animation_time", 1.0)
        self.delete_delay = BotConfig.LOADER.get("delete_delay", 5.0)
        
        # Словарь для хранения соответствия имен модулей и файлов
        if not hasattr(bot, 'module_files'):
            bot.module_files = {}
        
        # Регистрация команд из MODULE_INFO
        for cmd_info in MODULE_INFO["commands"]:
            if cmd_info["command"] == "lm":
                bot.register_command(
                    cmd=cmd_info["command"],
                    handler=self.load_module,
                    description=cmd_info["description"],
                    module_name=MODULE_INFO["name"]
                )
            elif cmd_info["command"] == "ulm":
                bot.register_command(
                    cmd=cmd_info["command"],
                    handler=self.unload_module,
                    description=cmd_info["description"],
                    module_name=MODULE_INFO["name"]
                )
        
        bot.set_module_description(MODULE_INFO["name"], MODULE_INFO["description"])

    def get_random_smile(self):
        """Возвращает случайный смайл из конфигурации"""
        return random.choice(BotConfig.DEFAULT_SMILES)

    async def get_user_info(self, event):
        try:
            user = await event.get_sender()
            return {
                "premium": user.premium if hasattr(user, 'premium') else False,
                "username": user.username or f"id{user.id}"
            }
        except Exception as e:
            logger.error(f"Ошибка получения информации о пользователе: {str(e)}")
            return {"premium": False, "username": "unknown"}

    async def find_module_by_name(self, module_query):
        """Находит модуль по имени с учетом частичных совпадений"""
        normalized_query = module_query.lower().strip()
        
        # Сначала проверяем точное совпадение
        if normalized_query in [name.lower() for name in self.bot.modules.keys()]:
            for name in self.bot.modules.keys():
                if name.lower() == normalized_query:
                    return name
        
        # Ищем по частичному совпадению (70% сходство)
        closest = difflib.get_close_matches(
            normalized_query,
            [name.lower() for name in self.bot.modules.keys()],
            n=1,
            cutoff=0.7
        )
        
        if closest:
            for name in self.bot.modules.keys():
                if name.lower() == closest[0]:
                    return name
        
        return None

    async def find_module_info(self, module_name):
        normalized_query = module_name.lower().strip()
        
        # Сначала проверяем точное совпадение
        if module_name in self.bot.modules:
            return module_name, await self.get_module_info(module_name)
        
        # Ищем без учета регистра
        for name in self.bot.modules.keys():
            if name.lower() == normalized_query:
                return name, await self.get_module_info(name)
        
        # Ищем по частичному совпадению
        closest = difflib.get_close_matches(
            normalized_query,
            [name.lower() for name in self.bot.modules.keys()],
            n=1,
            cutoff=0.6  # Более низкий порог для частичного совпадения
        )
        
        if closest:
            for name in self.bot.modules.keys():
                if name.lower() == closest[0]:
                    return name, await self.get_module_info(name)
        
        return None, None

    async def get_module_info(self, module_name):
        # Сначала пытаемся получить информацию из базы данных
        db_info = self.bot.db.get_module_info(module_name)
        if db_info:
            return db_info
            
        # Fallback: если информации в БД нет, используем старую логику
        if module_name not in self.bot.modules:
            return None
            
        try:
            module = sys.modules.get(module_name)
            if module:
                # Пытаемся получить информацию через get_module_info
                if hasattr(module, 'get_module_info'):
                    info = module.get_module_info()
                    
                    # Сохраняем в базу данных для будущего использования
                    self.bot.db.set_module_info(
                        info['name'],
                        info['developer'],
                        info['version'],
                        info['description'],
                        info['commands'],
                        module_name in self.bot.core_modules
                    )
                    
                    return info
                
                # Если функции get_module_info нет, пытаемся получить информацию из переменных модуля
                developer = getattr(module, 'developer', None)
                if developer is None:
                    developer = '@BotHuekka'
                
                version = getattr(module, 'version', '1.0.0')
                description = getattr(module, 'description', self.bot.module_descriptions.get(module_name, ""))
                
                commands = []
                for cmd, data in self.bot.modules[module_name].items():
                    commands.append({
                        "command": cmd,
                        "description": data.get("description", "Без описания")
                    })
                
                # Сохраняем в базу данных для будущего использования
                self.bot.db.set_module_info(
                    module_name,
                    developer,
                    version,
                    description,
                    commands,
                    module_name in self.bot.core_modules
                )
                
                return {
                    "name": module_name,
                    "description": description,
                    "commands": commands,
                    "is_stock": module_name in self.bot.core_modules,
                    "version": version,
                    "developer": developer
                }
        except Exception:
            pass
        
        # Если не удалось получить информацию из модуля, создаем базовую информацию
        commands = []
        for cmd, data in self.bot.modules[module_name].items():
            commands.append({
                "command": cmd,
                "description": data.get("description", "Без описания")
            })
        
        # Сохраняем в базу данных для будущего использования
        self.bot.db.set_module_info(
            module_name,
            "@BotHuekka",
            "1.0.0",
            self.bot.module_descriptions.get(module_name, ""),
            commands,
            module_name in self.bot.core_modules
        )
        
        return {
            "name": module_name,
            "description": self.bot.module_descriptions.get(module_name, ""),
            "commands": commands,
            "is_stock": module_name in self.bot.core_modules,
            "version": "1.0.0",
            "developer": "@BotHuekka"
        }

    async def animate_loading_until_done(self, event, message, is_premium, coroutine):
        """Анимирует загрузку до завершения корутины"""
        animation = ["/", "-", "\\", "|"]
        i = 0
        
        # Запускаем анимацию
        anim_task = asyncio.create_task(self._run_animation(event, message, is_premium, animation))
        
        try:
            # Выполняем основную задачу
            result = await coroutine
            return result
        finally:
            # Останавливаем анимацию
            if not anim_task.done():
                anim_task.cancel()

    async def _run_animation(self, event, message, is_premium, animation):
        """Запускает анимацию"""
        i = 0
        try:
            while True:
                frame = animation[i % len(animation)]
                prefix = f"[⚙️](emoji/{self.loader_emoji_id}) " if is_premium else "⚙️ "
                await event.edit(f"{prefix}{message} {frame}")
                i += 1
                await asyncio.sleep(0.3)
        except MessageNotModifiedError:
            pass
        except Exception as e:
            logger.error(f"Ошибка анимации: {str(e)}")

    async def check_and_install_dependencies(self, module_file, event, is_premium):
        """Проверяет и устанавливает зависимости модуля"""
        if not hasattr(self.bot, 'dependency_installer'):
            return True
            
        # Используем анимацию для всего процесса установки зависимостей
        async def install_deps():
            installed, errors = await self.bot.dependency_installer.install_dependencies(module_file)
            
            if errors:
                error_list = "\n".join([f"• {error}" for error in errors[:3]])
                raise Exception(f"Ошибки установки зависимостей:\n{error_list}")
            
            return True
            
        try:
            return await self.animate_loading_until_done(
                event, "Установка зависимостей", is_premium, install_deps()
            )
        except Exception as e:
            logger.error(f"Ошибка установки зависимостей: {str(e)}")
            await event.edit(f"[❌](emoji/{self.error_emoji_id}) {str(e)}")
            return False

    async def unload_existing_module(self, module_name):
        """Выгружает существующий модуль с таким же именем"""
        if module_name in self.bot.modules:
            # Удаляем команды модуля
            commands_to_remove = [
                cmd for cmd, data in self.bot.commands.items() 
                if data.get("module") and data.get("module").lower() == module_name.lower()
            ]
            
            for cmd in commands_to_remove:
                del self.bot.commands[cmd]
            
            # Удаляем из sys.modules если есть
            if module_name in sys.modules:
                del sys.modules[module_name]
            
            # Удаляем из bot.modules если есть
            if module_name in self.bot.modules:
                del self.bot.modules[module_name]
            
            # Удаляем описание модуля если есть
            if module_name in self.bot.module_descriptions:
                del self.bot.module_descriptions[module_name]
            
            # Удаляем из module_files если есть
            if module_name in self.bot.module_files:
                del self.bot.module_files[module_name]
            
            # Удаляем информацию о модуле из базы данных
            self.bot.db.delete_module_info(module_name)
            
            logger.info(f"Модуль {module_name} выгружен перед загрузкой новой версии")

    async def unload_module(self, event):
        """Выгружает модуль по имени"""
        args = event.text.split(" ", 1)
        if len(args) < 2:
            await event.edit("❌ Укажите название модуля для выгрузки.")
            return

        module_query = args[1].strip()
        
        # Ищем модуль с учетом частичных совпадений
        found_module = await self.find_module_by_name(module_query)
        
        if not found_module:
            await event.edit(f"❌ Модуль `{module_query}` не найден.")
            return
            
        if found_module in self.bot.core_modules:
            await event.edit(f"❌ Модуль `{found_module}` является системным и не может быть выгружен.")
            return

        try:
            # Удаляем команды модуля
            commands_to_remove = []
            for cmd, data in self.bot.commands.items():
                if data.get("module") and data.get("module").lower() == found_module.lower():
                    commands_to_remove.append(cmd)
                    
            for cmd in commands_to_remove:
                del self.bot.commands[cmd]

            # Удаляем из sys.modules
            if found_module in sys.modules:
                del sys.modules[found_module]

            # Удаляем из bot.modules
            if found_module in self.bot.modules:
                del self.bot.modules[found_module]

            # Удаляем описание модуля
            if found_module in self.bot.module_descriptions:
                del self.bot.module_descriptions[found_module]

            # Удаляем информацию о файле модуля
            file_removed = False
            if found_module in self.bot.module_files:
                file_path = self.bot.module_files[found_module]
                if os.path.exists(file_path):
                    os.remove(file_path)
                    file_removed = True
                del self.bot.module_files[found_module]

            # Удаляем информацию о модуле из базы данных
            self.bot.db.delete_module_info(found_module)

            # Форматируем сообщение об успешном удалении
            user_info = await self.get_user_info(event)
            is_premium = user_info["premium"]
            
            if is_premium:
                success_msg = f"[▪️](emoji/{self.unload_emoji_id}) `{found_module}` __успешно удалён, используйте {self.bot.command_prefix}help для просмотра модулей и команд.__"
            else:
                success_msg = f"▪️ `{found_module}` __успешно удалён, используйте {self.bot.command_prefix}help для просмотра модулей и команд.__"
            
            if file_removed:
                success_msg += "\n📁 Файл модуля также был удалён."
                
            await event.edit(success_msg)

        except Exception as e:
            error_msg = f"❌ Ошибка при выгрузке модуля: {str(e)}"
            await event.edit(error_msg)
            logger.error(f"Ошибка выгрузки модуля {found_module}: {str(e)}")

    async def load_module(self, event):
        if not event.is_reply:
            await event.edit(f"[ℹ️](emoji/{self.info_emoji_id}) **Ответьте на сообщение с файлом модуля!**")
            return

        reply = await event.get_reply_message()
        if not reply.document or not reply.document.mime_type == "text/x-python":
            await event.edit(f"[🚫](emoji/{self.error_emoji_id}) **Это не Python-файл!**")
            return

        user_info = await self.get_user_info(event)
        is_premium = user_info["premium"]

        file_name = None
        for attr in reply.document.attributes:
            if isinstance(attr, types.DocumentAttributeFilename):
                file_name = attr.file_name
                break
        
        if not file_name:
            await event.edit(f"[🚫](emoji/{self.error_emoji_id}) **Не удалось определить имени файла!**")
            return

        module_name = os.path.basename(file_name).replace(".py", "")
        
        temp_dir = Path("temp_modules")
        temp_dir.mkdir(exist_ok=True)
        temp_file = temp_dir / file_name
        
        try:
            # Скачиваем файл
            module_file = await reply.download_media(file=str(temp_file))
            
            # Проверяем и устанавливаем зависимости
            deps_success = await self.check_and_install_dependencies(module_file, event, is_premium)
            if not deps_success:
                logger.warning(f"Не удалось установить зависимости для {module_name}")
                return
            
            # Проверяем, существует ли уже модуль с таким же именем
            final_path = Path("modules") / file_name
            if final_path.exists():
                # Выгружаем существующий модуль
                await self.unload_existing_module(module_name)
                # Удаляем старый файл
                os.remove(final_path)
                logger.info(f"Старая версия модуля {module_name} удалена")
            
            # Загружаем модуль с анимацией
            async def load_module_task():
                start_time = time.time()
                before_commands = set(self.bot.commands.keys())
                
                # Перемещаем файл в папку modules
                os.rename(module_file, final_path)
                module_file_path = str(final_path)
                
                # Загружаем модуль
                spec = importlib.util.spec_from_file_location(module_name, module_file_path)
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                
                if not hasattr(module, 'setup'):
                    raise Exception("В модуле отсутствует функция setup()")
                
                module.setup(self.bot)
                
                # Сохраняем информацию о файле модуля
                self.bot.module_files[module_name] = module_file_path
                    
                after_commands = set(self.bot.commands.keys())
                new_commands = after_commands - before_commands
                
                # Получаем информацию о модуле
                found_name, module_info = await self.find_module_info(module_name)
                
                # Если не удалось получить информацию через get_module_info, создаем базовую
                if not module_info:
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
                
                # ВАЖНОЕ ИСПРАВЛЕНИЕ: Удаляем старую запись в БД перед созданием новой
                # Это предотвращает накопление устаревших записей при обновлении модулей
                self.bot.db.delete_module_info(module_name)
                
                # Сохраняем информацию о модуле в базу данных
                self.bot.db.set_module_info(
                    module_info['name'],
                    module_info['developer'],
                    module_info['version'],
                    module_info['description'],
                    module_info['commands'],
                    False  # is_stock = False для загруженных модулей
                )
                
                # Формируем сообщение о успешной загрузке
                loaded_message = loader_format.format_loaded_message(
                    module_info, is_premium, self.loaded_emoji_id, 
                    self.get_random_smile(), self.command_emoji_id, self.dev_emoji_id,
                    self.bot.command_prefix
                )
                
                logger.info(f"Модуль {module_name} загружен (команд: {len(new_commands)})")
                return loaded_message
            
            # Запускаем загрузку модуля с анимацией
            loaded_message = await self.animate_loading_until_done(
                event, "Загрузка модуля", is_premium, load_module_task()
            )
            
            # Показываем результат
            await event.edit(loaded_message)
                
        except Exception as e:
            error_trace = traceback.format_exc()
            logger.error(f"Ошибка загрузки модуля: {str(e)}\n{error_trace}")
            
            if 'module_file' in locals() and os.path.exists(module_file):
                try:
                    os.remove(module_file)
                except:
                    pass
                    
            modules_path = Path("modules") / file_name
            if modules_path.exists():
                try:
                    os.remove(modules_path)
                except:
                    pass
            
            # Создаем сообщение об ошибке напрямую
            error_msg = f"[❌](emoji/{self.error_emoji_id}) **Ошибка загрузки модуля:** {str(e)}"
            await event.edit(error_msg)
        finally:
            try:
                if temp_file.exists():
                    os.remove(temp_file)
            except:
                pass

def setup(bot):
    LoaderModule(bot)
