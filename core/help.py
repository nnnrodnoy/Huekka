import logging
import difflib
import os
import sys
from telethon import events
from config import BotConfig

logger = logging.getLogger("UserBot.Help")

class HelpModule:
    def __init__(self, bot):
        self.bot = bot
        self.stock_modules = BotConfig.STOCK_MODULES
        
        self.total_emoji_id = BotConfig.EMOJI_IDS["total"]
        self.section_emoji_id = BotConfig.EMOJI_IDS["section"]
        self.stock_emoji_id = BotConfig.EMOJI_IDS["stock"]
        self.custom_emoji_id = BotConfig.EMOJI_IDS["custom"]
        self.developer_emoji_id = BotConfig.EMOJI_IDS["dev"]
        self.command_emoji_id = BotConfig.EMOJI_IDS["command"]
        
        bot.register_command(
            cmd="help",
            handler=self.show_help,
            description="Показать список команд",
            module_name="Help"
        )
    
    def get_module_info(self):
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
    
    def get_random_smile(self):
        """Получение случайного смайла через DatabaseManager"""
        return self.bot.db.get_random_smile()

    async def get_module_info(self, module_name):
        if module_name not in self.bot.modules:
            return None
            
        try:
            module = sys.modules.get(module_name)
            if module and hasattr(module, 'get_module_info'):
                info = module.get_module_info()
                
                # Добавляем информацию из базы данных
                db_info = self.bot.db.get_module_settings(module_name)
                if db_info and "load_count" in db_info:
                    info["load_count"] = db_info.get("load_count", 0)
                    info["last_loaded"] = db_info.get("last_loaded", 0)
                
                return info
        except Exception:
            pass
        
        # Формируем информацию по умолчанию
        commands = []
        for cmd, data in self.bot.modules[module_name].items():
            commands.append({
                "command": cmd,
                "description": data.get("description", "Без описания")
            })
        
        # Добавляем информацию из базы данных
        db_info = self.bot.db.get_module_settings(module_name)
        load_count = db_info.get("load_count", 1) if db_info else 1
        last_loaded = db_info.get("last_loaded", 0) if db_info else 0
        
        return {
            "name": module_name,
            "description": self.bot.module_descriptions.get(module_name, ""),
            "commands": commands,
            "is_stock": module_name in self.stock_modules,
            "version": "1.0.0",
            "developer": "@BotHuekka",
            "load_count": load_count,
            "last_loaded": last_loaded
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
                        text += f"[⚙️](emoji/{self.command_emoji_id}) "
                    text += f"**Информация о команде:** `{prefix}{command_info['command']}`\n\n"
                    text += f"**Описание:** {command_info['description']}\n"
                    text += f"**Модуль:** {command_info['module']}"
                    
                    await event.edit(text)
                    return
                
                text = ""
                if is_premium:
                    text += f"[🕒](emoji/{self.total_emoji_id}) "
                text += f"**{module_info['name']} (v{module_info['version']})**\n"
                text += f"__{self.get_random_smile()}__\n\n"
                
                text += f"{module_info['description']}\n\n"
                
                # Добавляем статистику загрузок, если доступна
                if "load_count" in module_info:
                    text += f"**Загружено раз:** {module_info['load_count']}\n\n"
                
                found = False
                for cmd in module_info['commands']:
                    if cmd['command'] == command_info['command']:
                        if is_premium:
                            text += f"[▪️](emoji/{self.stock_emoji_id}) "
                        else:
                            text += "▪️"
                            
                        text += f"`{prefix}{cmd['command']}` - __{cmd['description']}__\n"
                        found = True
                        break
                
                if not found:
                    text += f"ℹ▪️ `{prefix}{command_info['command']}` - __{command_info['description']}__\n"
                
                if is_premium:
                    text += f"\n[🫶](emoji/{self.developer_emoji_id}) "
                else:
                    text += "\n🫶 "
                text += f"**Разработчик:** {module_info['developer']}"
                
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
                    await event.edit(f"🚫 Информация о модуле `{found_module}` недоступна")
                    return
                
                text = ""
                if is_premium:
                    text += f"[🕒](emoji/{self.total_emoji_id}) "
                text += f"**{module_info['name']} (v{module_info['version']})**\n"
                text += f"__{self.get_random_smile()}__\n\n"
                
                text += f"{module_info['description']}\n\n"
                
                # Добавляем статистику загрузок, если доступна
                if "load_count" in module_info:
                    text += f"**Загружено раз:** {module_info['load_count']}\n\n"
                
                for cmd in module_info['commands']:
                    if is_premium:
                        if module_info['is_stock']:
                            text += f"[▪️](emoji/{self.stock_emoji_id}) "
                        else:
                            text += f"[▫️](emoji/{self.custom_emoji_id}) "
                    else:
                        text += "▪️ " if module_info['is_stock'] else "▫️ "
                    
                    text += f"`{prefix}{cmd['command']}` - __{cmd['description']}__\n"
                
                if is_premium:
                    text += f"\n[🫶](emoji/{self.developer_emoji_id}) "
                else:
                    text += "\n🫶 "
                text += f"**Разработчик:** {module_info['developer']}"
                
                await event.edit(text)
                return
            else:
                await event.edit(f"🚫 Команда или модуль `{command_query}` не найден")
                return

        total_modules = len(self.bot.modules)
        reply = ""
        
        if is_premium:
            reply += f"[🕒](emoji/{self.total_emoji_id}) "
        reply += f"**Доступно модулей:** {total_modules}\n"
        reply += f"__Используйте `{prefix}help <команда>` для информации о команде__\n"
        reply += f"__Или `{prefix}help <модуль>` для информации о модуле__\n\n"
        
        if is_premium:
            reply += f"[👁️](emoji/{self.section_emoji_id}) "
        reply += "**Стандартные модули:**\n"
        
        stock_list = []
        for module_name in self.stock_modules:
            if module_name not in self.bot.modules:
                continue
                
            module_info = await self.get_module_info(module_name)
            if not module_info:
                continue
                
            commands_list = [f'`{prefix}{cmd["command"]}`' for cmd in module_info['commands']]
            
            if is_premium:
                stock_list.append(f"[▪️](emoji/{self.stock_emoji_id}) **{module_name}**: ( {' | '.join(commands_list)} )")
            else:
                stock_list.append(f"▪️ **{module_name}**: ( {' | '.join(commands_list)} )")
        
        reply += "\n".join(stock_list) + "\n\n"
        
        if is_premium:
            reply += f"[👁️](emoji/{self.section_emoji_id}) "
        reply += "**Пользовательские модули:**\n"
        
        custom_list = []
        for module_name in self.bot.modules.keys():
            if module_name in self.stock_modules:
                continue
                
            module_info = await self.get_module_info(module_name)
            if not module_info:
                continue
                
            commands_list = [f'`{prefix}{cmd["command"]}`' for cmd in module_info['commands']]
            
            if is_premium:
                custom_list.append(f"[▫️](emoji/{self.custom_emoji_id}) **{module_name}**: ( {' | '.join(commands_list)} )")
            else:
                custom_list.append(f"▫️ **{module_name}**: ( {' | '.join(commands_list)} )")
        
        reply += "\n".join(custom_list)
        
        await event.edit(reply)

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

def setup(bot):
    bot.set_module_description("Help", "Система помощи и информации о модулях")
    HelpModule(bot)
