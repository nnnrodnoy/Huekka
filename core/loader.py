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
from core.formatters import loader_format, msg

logger = logging.getLogger("UserBot.Loader")

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

MODULE_INFO = get_module_info()

class LoaderModule:
    def __init__(self, bot):
        self.bot = bot
        
        # Используем emoji ID из конфига
        self.loader_emoji_id = str(BotConfig.EMOJI_IDS["loader"])
        self.loaded_emoji_id = str(BotConfig.EMOJI_IDS["loaded"])
        self.command_emoji_id = str(BotConfig.EMOJI_IDS["command"])
        self.dev_emoji_id = str(BotConfig.EMOJI_IDS["dev"])
        self.info_emoji_id = str(BotConfig.EMOJI_IDS["info"])
        
        self.min_animation_time = BotConfig.LOADER["min_animation_time"]
        self.delete_delay = BotConfig.LOADER["delete_delay"]
        
        bot.register_command(
            cmd="lm",
            handler=self.load_module,
            description="Загрузить модуль из файла",
            module_name=MODULE_INFO["name"]
        )
        
        bot.register_command(
            cmd="ulm",
            handler=self.unload_module,
            description="Выгрузить модуль",
            module_name=MODULE_INFO["name"]
        )
        
        bot.set_module_description(MODULE_INFO["name"], MODULE_INFO["description"])
        
        # Сохраняем информацию о модуле в базу данных
        success = bot.db.set_module_info(
            MODULE_INFO["name"],
            MODULE_INFO["developer"],
            MODULE_INFO["version"],
            MODULE_INFO["description"],
            MODULE_INFO["commands"],
            True  # is_stock = True для core-модулей
        )
        
        if not success:
            logger.error("Не удалось сохранить информацию о модуле Loader в базу данных")

    def get_random_smile(self):
        """Возвращает случайный смайл из базы данных или конфигурации"""
        try:
            # Пытаемся получить из базы данных
            return self.bot.db.get_random_smile()
        except AttributeError:
            # Если база данных не доступна, используем конфиг
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

    def _camel_to_snake(self, name):
        """Преобразует CamelCase в snake_case"""
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()

    def _module_name_to_filename(self, module_name):
        """Преобразует имя модуля в предполагаемое имя файла"""
        variants = [
            module_name.lower() + '.py',
            self._camel_to_snake(module_name) + '.py',
            module_name + '.py'
        ]
        return variants

    async def find_module_info(self, module_name):
        normalized_query = module_name.lower().strip()
        
        if module_name in self.bot.modules:
            return module_name, await self.get_module_info(module_name)
        
        for name in self.bot.modules.keys():
            if name.lower() == normalized_query:
                return name, await self.get_module_info(name)
        
        closest = difflib.get_close_matches(
            normalized_query,
            [name.lower() for name in self.bot.modules.keys()],
            n=1,
            cutoff=0.6
        )
        
        if closest:
            for name in self.bot.modules.keys():
                if name.lower() == closest[0]:
                    return name, await self.get_module_info(name)
        
        return None, None

    def find_module_file(self, query):
        normalized_query = query.lower().strip().replace('.py', '')
        modules_dir = Path("modules").resolve()
        
        if not modules_dir.exists():
            logger.error(f"Директория модулей не найдена: {modules_dir}")
            return None

        files = [f for f in modules_dir.iterdir() if f.is_file() and f.suffix == '.py']
        
        for file in files:
            if file.stem.lower() == normalized_query:
                return file

        closest = difflib.get_close_matches(
            normalized_query,
            [f.stem.lower() for f in files],
            n=1,
            cutoff=0.7
        )
        
        if closest:
            for file in files:
                if file.stem.lower() == closest[0]:
                    return file
        
        snake_case_name = self._camel_to_snake(normalized_query)
        for file in files:
            if file.stem.lower() == snake_case_name:
                return file
        
        return None

    async def get_module_info(self, module_name):
        if module_name not in self.bot.modules:
            return None
            
        try:
            module = sys.modules.get(module_name)
            if module and hasattr(module, 'get_module_info'):
                info = module.get_module_info()
                return info
        except Exception:
            pass
        
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

    async def animate_loading_until_done(self, event, message, is_premium, coroutine):
        """Анимирует загрузку до завершения корутины"""
        animation = ["/", "-", "\\", "|"]
        i = 0
        
        anim_task = asyncio.create_task(self._run_animation(event, message, is_premium, animation))
        
        try:
            result = await coroutine
            return result
        finally:
            if not anim_task.done():
                anim_task.cancel()

    async def _run_animation(self, event, message, is_premium, animation):
        """Запускает анимацию"""
        i = 0
        try:
            while True:
                frame = animation[i % len(animation)]
                prefix = f"[⌛️](emoji/{self.loader_emoji_id}) " if is_premium else "⌛️ "
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
            
        async def install_deps():
            installed, errors = await self.bot.dependency_installer.install_dependencies(module_file)
            
            if errors:
                error_list = "\n".join([f"• {error}" for error in errors[:3]])
                raise Exception(f"Ошибки установки зависимостей:\n{error_list}")
            
            return True
            
        try:
            return await self.animate_loading_until_done(
                event, "Устанавливаю зависимости...", is_premium, install_deps()
            )
        except Exception as e:
            logger.error(f"Ошибка установки зависимостей: {str(e)}")
            await event.edit(f"[❌](emoji/5210952531676504517) {str(e)}")
            return False

    async def unload_existing_module(self, module_name):
        """Выгружает существующий модуль перед загрузкой новой версии"""
        if module_name not in self.bot.modules:
            logger.info(f"Модуль {module_name} не загружен, пропускаем выгрузку")
            return True
            
        if module_name in self.bot.core_modules:
            logger.warning(f"Попытка выгрузить системный модуль: {module_name}")
            return False
            
        logger.info(f"Выгружаем модуль {module_name}")
        
        # Удаляем команды модуля
        commands_to_remove = []
        for cmd, data in self.bot.commands.items():
            if data.get("module"):
                if data.get("module").lower() == module_name.lower():
                    commands_to_remove.append(cmd)
        
        logger.info(f"Найдены команды для удаления: {commands_to_remove}")
        
        for cmd in commands_to_remove:
            del self.bot.commands[cmd]
            logger.info(f"Команда {cmd} удалена")
        
        # Удаляем модуль из sys.modules
        if module_name in sys.modules:
            del sys.modules[module_name]
            logger.info(f"Модуль {module_name} удален из sys.modules")
        
        # Удаляем модуль из self.bot.modules
        if module_name in self.bot.modules:
            del self.bot.modules[module_name]
            logger.info(f"Модуль {module_name} удален из self.bot.modules")
        
        # Удаляем описание модуля
        if module_name in self.bot.module_descriptions:
            del self.bot.module_descriptions[module_name]
            logger.info(f"Описание модуля {module_name} удалено")
        
        # Удаляем информацию о модуле из базы данных
        self.bot.db.delete_module_info(module_name)
        logger.info(f"Информация о модуле {module_name} удалена из БД")
        
        logger.info(f"Модуль {module_name} выгружен перед загрузкой новой версии")
        return True

    async def load_module(self, event):
        if not event.is_reply:
            await event.edit("[ℹ️](emoji/5422439311196834318) **Ответьте на сообщение с файлом модуля!**")
            return

        reply = await event.get_reply_message()
        if not reply.document or not reply.document.mime_type == "text/x-python":
            await event.edit("[🚫](emoji/5240241223632954241) **Это не Python-файл!**")
            return

        user_info = await self.get_user_info(event)
        is_premium = user_info["premium"]

        file_name = None
        for attr in reply.document.attributes:
            if isinstance(attr, types.DocumentAttributeFilename):
                file_name = attr.file_name
                break
        
        if not file_name:
            await event.edit("[🚫](emoji/5240241223632954241) **Не удалось определить имя файла!**")
            return

        module_name = os.path.basename(file_name).replace(".py", "")
        
        # Проверяем, не является ли модуль системным
        if module_name in self.bot.core_modules:
            await event.edit("[🚫](emoji/5240241223632954241) **Нельзя перезаписать системный модуль!**")
            return

        # Показываем начальное сообщение о загрузке
        await event.edit(f"[⌛️](emoji/{self.loader_emoji_id}) **Загружаю** `{module_name}` **...**")
        
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
            
            # Выгружаем существующий модуль, если он есть
            await self.unload_existing_module(module_name)
            
            # Показываем сообщение о запуске
            await event.edit(f"[⌛️](emoji/{self.loader_emoji_id}) **Запускаю ...**")
            
            # Загружаем модуль с анимацией
            async def load_module_task():
                start_time = time.time()
                before_commands = set(self.bot.commands.keys())
                logger.info(f"Количество команд до загрузки: {len(before_commands)}")
                
                spec = importlib.util.spec_from_file_location(module_name, module_file)
                module = importlib.util.module_from_spec(spec)
                
                spec.loader.exec_module(module)
                
                if not hasattr(module, 'setup'):
                    raise Exception("В модуле отсутствует функция setup()")
                
                final_path = Path("modules") / file_name
                
                # Удаляем старый файл, если он существует
                if final_path.exists():
                    os.remove(final_path)
                
                os.rename(module_file, final_path)
                module_file_path = str(final_path)
                
                spec = importlib.util.spec_from_file_location(module_name, module_file_path)
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                
                module.setup(self.bot)
                    
                after_commands = set(self.bot.commands.keys())
                new_commands = after_commands - before_commands
                
                logger.info(f"Количество команд после загрузки: {len(after_commands)}")
                logger.info(f"Новые команды: {new_commands}")
                
                # Получаем информацию о модуле
                if hasattr(module, 'get_module_info'):
                    module_info = module.get_module_info()
                    # Сохраняем в БД
                    self.bot.db.set_module_info(
                        module_info['name'],
                        module_info['developer'],
                        module_info['version'],
                        module_info['description'],
                        module_info['commands'],
                        False  # is_stock = False для пользовательских модулей
                    )
                else:
                    module_info = {
                        "name": module_name,
                        "description": self.bot.module_descriptions.get(module_name, ""),
                        "commands": [{
                            "command": cmd, 
                            "description": self.bot.commands[cmd].get("description", "Без описания")
                        } for cmd in new_commands],
                        "version": "1.0.0",
                        "developer": "@BotHuekka"
                    }
                    # Сохраняем в БД
                    self.bot.db.set_module_info(
                        module_info['name'],
                        module_info['developer'],
                        module_info['version'],
                        module_info['description'],
                        module_info['commands'],
                        False  # is_stock = False для пользовательских модулей
                    )
                
                # Получаем актуальную информацию из БД
                found_name, module_info = await self.find_module_info(module_name)
                
                # Формируем сообщение о успешной загрузке
                if module_info:
                    loaded_message = loader_format.format_loaded_message(
                        module_info, is_premium, self.loaded_emoji_id, 
                        self.get_random_smile(), self.command_emoji_id, self.dev_emoji_id,
                        self.bot.command_prefix
                    )
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
                    loaded_message = loader_format.format_loaded_message(
                        module_info, is_premium, self.loaded_emoji_id, 
                        self.get_random_smile(), self.command_emoji_id, self.dev_emoji_id,
                        self.bot.command_prefix
                    )
                
                return loaded_message
            
            # Запускаем загрузку модуля с анимацией
            loaded_message = await self.animate_loading_until_done(
                event, "Запускаю ...", is_premium, load_module_task()
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
            
            error_msg = msg.error("Ошибка загрузки модуля", str(e))
            await event.edit(error_msg)
        finally:
            try:
                if temp_file.exists():
                    os.remove(temp_file)
            except:
                pass

    async def unload_module(self, event):
        prefix = self.bot.command_prefix
        
        args = event.text.split()
        if len(args) < 2:
            await event.edit(f"ℹ️ **Укажите название модуля:** `{prefix}ulm ModuleName`")
            return

        module_query = " ".join(args[1:]).strip()
        
        # Сначала ищем среди загруженных модулей
        found_name, module_info = await self.find_module_info(module_query)
        
        module_path = None
        if not found_name:
            found_file = self.find_module_file(module_query)
            if found_file:
                for loaded_name in self.bot.modules.keys():
                    if loaded_name.lower() == found_file.stem.lower():
                        found_name = loaded_name
                        module_info = await self.get_module_info(found_name)
                        break
                else:
                    found_name = found_file.stem

                module_path = found_file

        if not found_name:
            error_msg = msg.error(f"Модуль `{module_query}` не найден")
            await event.edit(error_msg)
            return

        if not module_path:
            possible_filenames = self._module_name_to_filename(found_name)
            modules_dir = Path("modules").resolve()
            
            for filename in possible_filenames:
                possible_path = modules_dir / filename
                if possible_path.exists():
                    module_path = possible_path
                    break
            else:
                module_path = self.find_module_file(found_name)

        if not module_path or not module_path.exists():
            error_msg = msg.error(f"Файл модуля `{found_name}` не найден")
            await event.edit(error_msg)
            return

        if found_name in self.bot.core_modules:
            error_msg = msg.error(f"Модуль `{found_name}` является системным и не может быть выгружен")
            await event.edit(error_msg)
            return

        user_info = await self.get_user_info(event)
        is_premium = user_info["premium"]

        # Показываем начальное сообщение об удалении
        await event.edit(f"[⌛️](emoji/{self.loader_emoji_id}) **Удаляю** `{found_name}` **...**")
        await asyncio.sleep(1)  # Небольшая пауза для визуального эффекта

        # Используем анимацию для выгрузки модуля
        async def unload_module_task():
            start_time = time.time()
            
            if found_name in self.bot.modules:
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
            
            # Удаляем информацию о модуле из базы данных
            self.bot.db.delete_module_info(found_name)
            
            elapsed = time.time() - start_time
            if elapsed < self.min_animation_time:
                await asyncio.sleep(self.min_animation_time - elapsed)
            
            # Используем форматтер для сообщения об удалении
            if is_premium:
                return f"[▪️](emoji/{self.info_emoji_id}) `{found_name}` __успешно удалён, используйте__ `{prefix}help` __для просмотра модулей и команд.__"
            else:
                return f"▪️ `{found_name}` __успешно удалён, используйте__ `{prefix}help` __для просмотра модулей и команд.__"

        try:
            # Показываем сообщение о запуске
            await event.edit(f"[⌛️](emoji/{self.loader_emoji_id}) **Запускаю ...**")
            
            # Запускаем выгрузку модуля с анимацией
            unloaded_message = await self.animate_loading_until_done(
                event, "**Запускаю ...**", is_premium, unload_module_task()
            )
            
            await event.edit(unloaded_message)
            
        except Exception as e:
            error_trace = traceback.format_exc()
            logger.error(f"Ошибка выгрузки модуля: {str(e)}\n{error_trace}")
            error_msg = msg.error("Ошибка выгрузки модуля", str(e))
            await event.edit(error_msg)

def setup(bot):
    LoaderModule(bot)
