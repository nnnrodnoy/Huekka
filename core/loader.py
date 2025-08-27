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

    async def animate_loading(self, event, message, is_premium):
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

    async def check_and_install_dependencies(self, module_file, event, is_premium):
        """Проверяет и устанавливает зависимости модуля"""
        prefix = f"[⚙️](emoji/{self.loader_emoji_id}) " if is_premium else "⚙️ "
        check_msg = await event.edit(f"{prefix}Проверяю зависимости /")
        
        if hasattr(self.bot, 'dependency_installer'):
            installed, errors = await self.bot.dependency_installer.install_dependencies(module_file)
            
            if errors:
                error_list = "\n".join([f"• {error}" for error in errors[:3]])
                error_msg = f"❌ **Ошибки установки зависимостей:**\n{error_list}"
                await check_msg.edit(error_msg)
                return False
            elif installed:
                installed_list = "\n".join([f"• {pkg}" for pkg in installed])
                success_msg = f"✅ **Установлены зависимости:**\n{installed_list}"
                await check_msg.edit(success_msg)
                await asyncio.sleep(2)
                return True
            else:
                await check_msg.edit("✅ **Зависимости не требуются**")
                await asyncio.sleep(1)
                return True
        else:
            await check_msg.edit("⚠️ **Установщик зависимостей не доступен**")
            await asyncio.sleep(1)
            return True

    async def load_module(self, event):
        if not event.is_reply:
            await event.edit("ℹ️ Ответьте на сообщение с файлом модуля!")
            return

        reply = await event.get_reply_message()
        if not reply.document or not reply.document.mime_type == "text/x-python":
            await event.edit("🚫 **Это не Python-файл!**")
            return

        user_info = await self.get_user_info(event)
        is_premium = user_info["premium"]

        file_name = None
        for attr in reply.document.attributes:
            if isinstance(attr, types.DocumentAttributeFilename):
                file_name = attr.file_name
                break
        
        if not file_name:
            await event.edit("🚫 **Не удалось определить имя файла!**")
            return

        module_name = os.path.basename(file_name).replace(".py", "")
        
        temp_dir = Path("temp_modules")
        temp_dir.mkdir(exist_ok=True)
        temp_file = temp_dir / file_name
        
        try:
            module_file = await reply.download_media(file=str(temp_file))
            
            # Проверяем и устанавливаем зависимости
            deps_success = await self.check_and_install_dependencies(module_file, event, is_premium)
            if not deps_success:
                logger.warning(f"Не удалось установить зависимости для {module_name}")
                return
            
            # Загружаем модуль
            anim_task = asyncio.create_task(
                self.animate_loading(event, f"Загружаю модуль `{module_name}`", is_premium)
            )

            start_time = time.time()
            before_commands = set(self.bot.commands.keys())
            
            spec = importlib.util.spec_from_file_location(module_name, module_file)
            module = importlib.util.module_from_spec(spec)
            
            spec.loader.exec_module(module)
            
            if not hasattr(module, 'setup'):
                raise Exception("В модуле отсутствует функция setup()")
            
            final_path = Path("modules") / file_name
            os.rename(module_file, final_path)
            module_file = str(final_path)
            
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
                loaded_message = loader_format.format_loaded_message(
                    module_info, is_premium, self.loaded_emoji_id, 
                    self.get_random_smile(), self.command_emoji_id, self.dev_emoji_id,
                    self.bot.command_prefix
                )
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
                loaded_message = loader_format.format_loaded_message(
                    module_info, is_premium, self.loaded_emoji_id, 
                    self.get_random_smile(), self.command_emoji_id, self.dev_emoji_id,
                    self.bot.command_prefix
                )
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
                
            if 'anim_task' in locals() and not anim_task.done():
                anim_task.cancel()

    # Остальной код без изменений...

def setup(bot):
    LoaderModule(bot)
