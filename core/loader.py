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
from config import BotConfig
from core.formatters import loader_format, msg

logger = logging.getLogger("UserBot.Loader")

class LoaderModule:
    def __init__(self, bot):
        self.bot = bot
        
        self.loader_emoji_id = BotConfig.EMOJI_IDS["loader"]
        self.loaded_emoji_id = BotConfig.EMOJI_IDS["loaded"]
        self.command_emoji_id = BotConfig.EMOJI_IDS["command"]
        self.dev_emoji_id = BotConfig.EMOJI_IDS["dev"]
        self.info_emoji_id = BotConfig.EMOJI_IDS["info"]
        
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

    async def find_module_info(self, module_name):
        normalized_query = module_name.lower().strip()
        
        if module_name in self.bot.modules:
            return module_name, await self.get_module_info(module_name)
        
        for name in self.bot.modules.keys():
            if name.lower() == normalized_query:
                return name, await self.get_module_info(name)
        
        file_name = normalized_query.replace('.py', '')
        for name in self.bot.modules.keys():
            if name.lower() == file_name:
                return name, await self.get_module_info(name)
        
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

    def find_module_file(self, query):
        normalized_query = query.lower().strip().replace('.py', '')
        modules_dir = Path("modules")
        
        if not modules_dir.exists():
            return None

        files = [f for f in modules_dir.iterdir() if f.is_file() and f.suffix == '.py']
        file_names = [f.stem for f in files]

        for name in file_names:
            if name.lower() == normalized_query:
                return name

        closest = difflib.get_close_matches(
            normalized_query,
            [name.lower() for name in file_names],
            n=1,
            cutoff=0.3
        )
        
        if closest:
            return closest[0]
        
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
            await event.edit(f"[❌](emoji/5210952531676504517) {str(e)}")
            return False

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
            
            # Загружаем модуль с анимацией
            async def load_module_task():
                start_time = time.time()
                before_commands = set(self.bot.commands.keys())
                
                spec = importlib.util.spec_from_file_location(module_name, module_file)
                module = importlib.util.module_from_spec(spec)
                
                spec.loader.exec_module(module)
                
                if not hasattr(module, 'setup'):
                    raise Exception("В модуле отсутствует функция setup()")
                
                final_path = Path("modules") / file_name
                os.rename(module_file, final_path)
                module_file_path = str(final_path)
                
                spec = importlib.util.spec_from_file_location(module_name, module_file_path)
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                
                module.setup(self.bot)
                    
                after_commands = set(self.bot.commands.keys())
                new_commands = after_commands - before_commands
                
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
            
            error_msg = msg.error("Ошибка загрузки модуля", str(e))
            await event.edit(error_msg)
        finally:
            try:
                if temp_file.exists():
                    os.remove(temp_file)
            except:
                pass

    async def unload_module(self, event):
        logger.info("Начало выгрузки модуля...")
        prefix = self.bot.command_prefix
        
        args = event.text.split()
        if len(args) < 2:
            await event.edit(f"ℹ️ **Укажите название модуля:** `{prefix}ulm ModuleName`")
            return

        module_query = " ".join(args[1:]).strip()
        logger.info(f"Поиск модуля для выгрузки: {module_query}")
        
        # Сначала ищем среди загруженных модулей
        found_name, module_info = await self.find_module_info(module_query)
        logger.info(f"Результат поиска модуля: {found_name}, {module_info}")
        
        # Если не нашли, ищем файл модуля
        if not found_name:
            found_name = self.find_module_file(module_query)
            logger.info(f"Поиск файла модуля: {found_name}")
        
        if not found_name:
            error_msg = msg.error(f"Модуль `{module_query}` не найден")
            await event.edit(error_msg)
            return

        module_path = f"modules/{found_name}.py"
        logger.info(f"Путь к модулю: {module_path}")
        
        if not os.path.exists(module_path):
            error_msg = msg.error(f"Модуль `{found_name}` не найден")
            await event.edit(error_msg)
            return

        user_info = await self.get_user_info(event)
        is_premium = user_info["premium"]

        # Используем анимацию для выгрузки модуля
        async def unload_module_task():
            logger.info("Начало задачи выгрузки модуля...")
            start_time = time.time()
            
            # Удаляем команды только если модуль загружен
            if found_name in self.bot.modules:
                logger.info(f"Модуль найден в bot.modules: {found_name}")
                commands_to_remove = [
                    cmd for cmd, data in self.bot.commands.items() 
                    if data.get("module") and data.get("module").lower() == found_name.lower()
                ]
                logger.info(f"Команды для удаления: {commands_to_remove}")
                
                for cmd in commands_to_remove:
                    logger.info(f"Удаление команды: {cmd}")
                    del self.bot.commands[cmd]
            else:
                logger.info(f"Модуль не найден в bot.modules: {found_name}")
            
            # Удаляем из sys.modules если есть
            if found_name in sys.modules:
                logger.info(f"Удаление модуля из sys.modules: {found_name}")
                try:
                    del sys.modules[found_name]
                    logger.info(f"Модуль успешно удален из sys.modules: {found_name}")
                except Exception as e:
                    logger.error(f"Ошибка при удалении модуля из sys.modules: {str(e)}")
            else:
                logger.info(f"Модуль не найден в sys.modules: {found_name}")
            
            # Удаляем файл
            try:
                os.remove(module_path)
                logger.info(f"Файл модуля успешно удален: {module_path}")
            except Exception as e:
                logger.error(f"Ошибка при удалении файла модуля: {str(e)}")
            
            # Удаляем из bot.modules если есть
            if found_name in self.bot.modules:
                logger.info(f"Удаление модуля из bot.modules: {found_name}")
                del self.bot.modules[found_name]
                logger.info(f"Модуль успешно удален из bot.modules: {found_name}")
            else:
                logger.info(f"Модуль не найден в bot.modules: {found_name}")
            
            # Удаляем описание модуля если есть
            if found_name in self.bot.module_descriptions:
                logger.info(f"Удаление описания модуля: {found_name}")
                del self.bot.module_descriptions[found_name]
                logger.info(f"Описание модуля успешно удалено: {found_name}")
            else:
                logger.info(f"Описание модуля не найдено: {found_name}")
            
            elapsed = time.time() - start_time
            if elapsed < self.min_animation_time:
                await asyncio.sleep(self.min_animation_time - elapsed)
            
            logger.info("Задача выгрузки модуля завершена.")
            return loader_format.format_unloaded_message(
                found_name, is_premium, self.info_emoji_id, self.bot.command_prefix
            )

        try:
            # Запускаем выгрузку модуля с анимацией
            unloaded_message = await self.animate_loading_until_done(
                event, f"Удаляю модуль `{found_name}`", is_premium, unload_module_task()
            )
            
            message = await event.edit(unloaded_message)
            
            await asyncio.sleep(self.delete_delay)
            await message.delete()
            
        except Exception as e:
            error_trace = traceback.format_exc()
            logger.error(f"Ошибка выгрузки модуля: {str(e)}\n{error_trace}")
            error_msg = msg.error("Ошибка выгрузки модуля", str(e))
            await event.edit(error_msg)

def setup(bot):
    LoaderModule(bot)
