# ©️ nnnrodnoy, 2025
# 💬 @nnnrodnoy
# This file is part of Huekka
# 🌐 https://github.com/nnnrodnoy/Huekka/
# You can redistribute it and/or modify it under the terms of the MIT License
# 🔑 https://opensource.org/licenses/MIT
import logging
import difflib
import os
import sys
from telethon import events
from config import BotConfig
from core.formatters import help_format, msg

logger = logging.getLogger("UserBot.Help")

def get_module_info():
    return {
        "name": "Help",
        "description": "Система помощи и информации о модулях",
        "developer": "@BotHuekka",
        "version": "1.0.0",
        "commands": [
            {
                "command": "help",
                "description": "Показать список команд"
            }
        ]
    }

MODULE_INFO = get_module_info()

class HelpModule:
    def __init__(self, bot):
        self.bot = bot
        
        self.total_emoji_id = BotConfig.EMOJI_IDS["total"]
        self.section_emoji_id = BotConfig.EMOJI_IDS["section"]
        self.developer_emoji_id = BotConfig.EMOJI_IDS["dev"]
        self.command_emoji_id = BotConfig.EMOJI_IDS["command"]
        
        bot.register_command(
            cmd=MODULE_INFO["commands"][0]["command"],
            handler=self.show_help,
            description=MODULE_INFO["commands"][0]["description"],
            module_name=MODULE_INFO["name"]
        )
    
    def get_random_smile(self):
        return self.bot.db.get_random_smile()

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
                        info['commands']
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
                    commands
                )
                
                return {
                    "name": module_name,
                    "description": description,
                    "commands": commands,
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
            commands
        )
        
        return {
            "name": module_name,
            "description": self.bot.module_descriptions.get(module_name, ""),
            "commands": commands,
            "version": "1.0.0",
            "developer": "@BotHuekka"
        }

    async def get_command_info(self, command_name):
        normalized_cmd = command_name.lstrip(self.bot.command_prefix).lower()
        
        for cmd, data in self.bot.commands.items():
            if cmd.lower() == normalized_cmd:
                return {
                    "command": cmd,
                    "description": data.get("description", "Без описания"),
                    "module": data.get("module", "Неизвестный модуль")
                }
        
        return None

    async def show_help(self, event):
        try:
            user = await event.get_sender()
            is_premium = user.premium if hasattr(user, 'premium') else False
        except Exception as e:
            logger.error(f"Ошибка проверки премиум-статуса: {str(e)}")
            is_premium = False
        
        prefix = self.bot.command_prefix
        args = event.text.split()
        
        if len(args) > 1:
            command_query = " ".join(args[1:]).strip()
            
            command_info = await self.get_command_info(command_query)
            
            if command_info:
                module_info = await self.get_module_info(command_info["module"])
                
                if not module_info:
                    text = ""
                    if is_premium:
                        text += f"<emoji document_id={self.command_emoji_id}>⚙️</emoji> "
                    text += f"<b>Информация о команде:</b> <code>{prefix}{command_info['command']}</code>\n\n"
                    text += f"<b>Описание:</b> {command_info['description']}\n"
                    text += f"<b>Модуль:</b> {command_info['module']}"
                    
                    await event.edit(text)
                    return
                
                text = help_format.format_module_info(
                    module_info, is_premium, self.total_emoji_id, self.get_random_smile(),
                    self.command_emoji_id, self.developer_emoji_id, prefix
                )
                
                await event.edit(text)
                return
            
            module_query = command_query
            normalized_query = module_query.lower()
            
            found_module = None
            for name in self.bot.modules.keys():
                if name.lower() == normalized_query:
                    found_module = name
                    break
            
            if not found_module:
                closest = difflib.get_close_matches(
                    normalized_query,
                    [name.lower() for name in self.bot.modules.keys()],
                    n=1,
                    cutoff=0.3
                )
                if closest:
                    for name in self.bot.modules.keys():
                        if name.lower() == closest[0]:
                            found_module = name
                            break
            
            if found_module:
                module_info = await self.get_module_info(found_module)
                
                if not module_info:
                    await event.edit(f"<emoji document_id=5240241223632954241>🚫</emoji> <b>Информация о модуле</b> <code>{found_module}</code> недоступна")
                    return
                
                text = help_format.format_module_info(
                    module_info, is_premium, self.total_emoji_id, self.get_random_smile(),
                    self.command_emoji_id, self.developer_emoji_id, prefix
                )
                
                await event.edit(text)
                return
            else:
                error_msg = msg.error(f"Команда или модуль <code>{command_query}</code> не найден")
                await event.edit(error_msg)
                return

        total_modules = len(self.bot.modules)
        
        # Получаем информацию о всех модулях из базы данных
        all_module_info = self.bot.db.get_all_module_info()
        
        modules_list = []
        for module_info in all_module_info:
            if module_info['name'] not in self.bot.modules:
                continue
                
            commands_list = [f'<code>{prefix}{cmd["command"]}</code>' for cmd in module_info['commands']]
            
            if is_premium:
                modules_list.append(f"<emoji document_id={self.command_emoji_id}>▪️</emoji> <b>{module_info['name']}</b>: ( {' | '.join(commands_list)} )")
            else:
                modules_list.append(f"▪️ <b>{module_info['name']}</b>: ( {' | '.join(commands_list)} )")
        
        # Исправленный вызов format_main_help с правильным количеством аргументов
        reply = help_format.format_main_help(
            total_modules, is_premium, self.total_emoji_id, self.section_emoji_id,
            self.command_emoji_id, modules_list, prefix
        )
        
        await event.edit(reply)

def setup(bot):
    bot.set_module_description(MODULE_INFO["name"], MODULE_INFO["description"])
    HelpModule(bot)
