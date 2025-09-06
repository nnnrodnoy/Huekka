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
import inspect
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
        self.unload_emoji_id = "5251522431977291010"
        
        self.min_animation_time = BotConfig.LOADER.get("min_animation_time", 1.0)
        self.delete_delay = BotConfig.LOADER.get("delete_delay", 5.0)
        
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
        
        # Ищем по частичному совпадению
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

    async def extract_module_name_from_file(self, file_path):
        """Извлекает имя модуля из файла"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Ищем определение модуля
            module_pattern = r'def get_module_info\(\):.*?return\s*{.*?"name":\s*"([^"]+)"'
            match = re.search(module_pattern, content, re.DOTALL)
            if match:
                return match.group(1)
            
            # Альтернативный поиск имени модуля
            name_pattern = r'MODULE_NAME\s*=\s*["\']([^"\']+)["\']'
            match = re.search(name_pattern, content)
            if match:
                return match.group(1)
                
        except Exception as e:
            logger.error(f"Ошибка извлечения имени модуля: {str(e)}")
        
        # Если не нашли в коде, используем имя файла
        return Path(file_path).stem

    async def unload_existing_module(self, module_name):
        """Выгружает существующий модуль"""
        if module_name in self.bot.modules:
            # Удаляем команды модуля
            commands_to_remove = [
                cmd for cmd, data in self.bot.commands.items() 
                if data.get("module") and data.get("module").lower() == module_name.lower()
            ]
            
            for cmd in commands_to_remove:
                del self.bot.commands[cmd]
            
            # Удаляем из sys.modules
            if module_name in sys.modules:
                del sys.modules[module_name]
            
            # Удаляем из bot.modules
            if module_name in self.bot.modules:
                del self.bot.modules[module_name]
            
            # Удаляем описание модуля
            if module_name in self.bot.module_descriptions:
                del self.bot.module_descriptions[module_name]
            
            logger.info(f"Модуль {module_name} выгружен")

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
                event, "Установка зависимостей", is_premium, install_deps()
            )
        except Exception as e:
            logger.error(f"Ошибка установки зависимостей: {str(e)}")
            await event.edit(f"[❌](emoji/{self.error_emoji_id}) {str(e)}")
            return False

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
                prefix = f"[⚙️](emoji/{self.loader_emoji_id}) " if is_premium else "⚙️ "
                await event.edit(f"{prefix}{message} {frame}")
                i += 1
                await asyncio.sleep(0.3)
        except MessageNotModifiedError:
            pass
        except Exception as e:
            logger.error(f"Ошибка анимации: {str(e)}")

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

        temp_dir = Path("temp_modules")
        temp_dir.mkdir(exist_ok=True)
        temp_file = temp_dir / file_name
        
        try:
            # Скачиваем файл
            module_file = await reply.download_media(file=str(temp_file))
            
            # Извлекаем имя модуля из файла
            module_name = await self.extract_module_name_from_file(module_file)
            
            # Проверяем и устанавливаем зависимости
            deps_success = await self.check_and_install_dependencies(module_file, event, is_premium)
            if not deps_success:
                return
            
            # Проверяем, существует ли уже модуль с таким именем
            final_path = Path("modules") / file_name
            existing_module = await self.find_module_by_name(module_name)
            
            if existing_module:
                # Выгружаем существующий модуль
                await self.unload_existing_module(existing_module)
                
                # Удаляем старый файл
                old_file = Path("modules") / f"{existing_module}.py"
                if old_file.exists():
                    os.remove(old_file)
                    logger.info(f"Старый файл модуля {existing_module} удален")
                
                # Удаляем информацию из БД
                self.bot.db.delete_module_info(existing_module)
                logger.info(f"Информация о модуле {existing_module} удалена из БД")
            
            # Перемещаем файл в папку modules
            os.rename(module_file, final_path)
            
            # Сохраняем базовую информацию о модуле в БД
            self.bot.db.set_module_info(
                module_name,
                "@BotHuekka",
                "1.0.0",
                "Описание будет доступно после перезагрузки",
                [],
                False
            )
            
            # Показываем сообщение об успехе
            if is_premium:
                success_msg = f"[✅](emoji/{self.loaded_emoji_id}) **Модуль {module_name} успешно загружен!**\n\n__Перезагружаю бота...__"
            else:
                success_msg = f"✅ **Модуль {module_name} успешно загружен!**\n\n__Перезагружаю бота...__"
            
            await event.edit(success_msg)
            
            # Перезагружаем бота
            await asyncio.sleep(2)
            await self.bot.restart()
                
        except Exception as e:
            error_trace = traceback.format_exc()
            logger.error(f"Ошибка загрузки модуля: {str(e)}\n{error_trace}")
            
            error_msg = f"[❌](emoji/{self.error_emoji_id}) **Ошибка загрузки модуля:** {str(e)}"
            await event.edit(error_msg)
        finally:
            # Очищаем временные файлы
            try:
                if temp_file.exists():
                    os.remove(temp_file)
            except:
                pass

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
            # Выгружаем модуль из памяти
            await self.unload_existing_module(found_module)
            
            # Удаляем файл модуля
            module_file = Path("modules") / f"{found_module}.py"
            if module_file.exists():
                os.remove(module_file)
            
            # Удаляем информацию из БД
            self.bot.db.delete_module_info(found_module)
            
            # Показываем сообщение об успехе
            user_info = await self.get_user_info(event)
            is_premium = user_info["premium"]
            
            if is_premium:
                success_msg = f"[✅](emoji/{self.unload_emoji_id}) **Модуль {found_module} успешно удален!**\n\n__Перезагружаю бота...__"
            else:
                success_msg = f"✅ **Модуль {found_module} успешно удален!**\n\n__Перезагружаю бота...__"
            
            await event.edit(success_msg)
            
            # Перезагружаем бота
            await asyncio.sleep(2)
            await self.bot.restart()

        except Exception as e:
            error_msg = f"❌ Ошибка при выгрузке модуля: {str(e)}"
            await event.edit(error_msg)
            logger.error(f"Ошибка выгрузки модуля {found_module}: {str(e)}")

def setup(bot):
    LoaderModule(bot)
