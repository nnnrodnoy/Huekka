# ©️ nnnrodnoy, 2025
# 💬 @nnnrodnoy
# This file is part of Huekka
# 🌐 https://github.com/nnnrodnoy/Huekka/
# You can redistribute it and/or modify it under the terms of the MIT License
# 🔑 https://opensource.org/licenses/MIT
import logging
import os
import re
from pathlib import Path
from telethon import events
from config import BotConfig

logger = logging.getLogger("UserBot.Configurator")

class ConfiguratorModule:
    def __init__(self, bot):
        self.bot = bot
        
        bot.register_command(
            cmd="config",
            handler=self.config_handler,
            description="Управление настройками бота",
            module_name="Configurator"
        )
        
        bot.set_module_description("Configurator", "Система управления настройками бота")

    def get_module_info(self):
        return {
            "name": "Configurator",
            "description": "Система управления настройками бота",
            "developer": "@BotHuekka",
            "version": "1.0.0",
            "commands": [
                {
                    "command": "config",
                    "description": "Управление настройками бота"
                }
            ]
        }

    async def config_handler(self, event):
        """Обработчик команды .config"""
        args = event.text.split()
        
        if len(args) < 2:
            await self.show_help(event)
            return
        
        subcommand = args[1].lower()
        
        if subcommand == "prefix" and len(args) > 2:
            await self.set_prefix(event, args[2])
        elif subcommand == "autoclean" and len(args) > 2:
            await self.set_autoclean(event, args[2].lower())
        elif subcommand == "autoclean_delay" and len(args) > 2:
            await self.set_autoclean_delay(event, args[2])
        elif subcommand == "autostart" and len(args) > 2:
            await self.set_autostart(event, args[2].lower())
        elif subcommand == "font" and len(args) > 2:
            await self.set_font(event, args[2].lower())
        elif subcommand == "font_enable" and len(args) > 2:
            await self.set_font_enable(event, args[2].lower())
        elif subcommand == "status":
            await self.show_status(event)
        else:
            await self.show_help(event)

    async def show_help(self, event):
        """Показать справку по команде config"""
        prefix = self.bot.command_prefix
        
        help_text = f"""
[⚙️](emoji/5370932688993656500) **Управление настройками бота**

**Использование:**
 [▪️](emoji/5251522431977291010)`{prefix}config prefix` `<новый префикс>` - __Изменить префикс команд__
 [▪️](emoji/5251522431977291010)`{prefix}config autoclean` `<on/off>` - __Включить/выключить автоклинер__
 [▪️](emoji/5251522431977291010)`{prefix}config autoclean_delay` <секунды>` - __Установить задержку автоклинера__
 [▪️](emoji/5251522431977291010)`{prefix}config autostart` `<on/off>` - __Включить/выключить автозапуск__
 [▪️](emoji/5251522431977291010)`{prefix}config font` `<название_шрифта>` - __Установить шрифт__
 [▪️](emoji/5251522431977291010)`{prefix}config font_enable` `<on/off>` - __Включить/выключить шрифты__
 [▪️](emoji/5251522431977291010)`{prefix}config status` - __Показать текущие настройки__

**Примеры:**
[▫️](emoji/5251481573953405172) `{prefix}config prefix !` - __Установить префикс "!"__
[▫️](emoji/5251481573953405172) `{prefix}config autoclean on` - __Включить автоклинер__
[▫️](emoji/5251481573953405172) `{prefix}config autoclean_delay 3600` - __Установить задержку 1 час__
[▫️](emoji/5251481573953405172) `{prefix}config autostart on` - __Включить автозапуск__
[▫️](emoji/5251481573953405172) `{prefix}config font шрифт1` - __Установить шрифт1__
[▫️](emoji/5251481573953405172) `{prefix}config font_enable on` - __Включить преобразование шрифтов__
"""
        await event.edit(help_text)

    async def set_prefix(self, event, new_prefix):
        """Установить новый префикс команд"""
        if not new_prefix or len(new_prefix) > 3:
            await event.edit("[❌](emoji/5210952531676504517) **Префикс должен быть от 1 до 3 символов!**")
            return
        
        if ' ' in new_prefix:
            await event.edit("[❌](emoji/5210952531676504517) **Префикс не может содержать пробелы!**")
            return
        
        success = self.bot.db.set_config_value('command_prefix', new_prefix)
        
        if success:
            self.bot.command_prefix = new_prefix
            await event.edit(f"[✅](emoji/5206607081334906820) **Префикс команд изменен на:** `{new_prefix}`")
        else:
            await event.edit("[❌](emoji/5210952531676504517) Ошибка при изменении префикса!")

    async def set_autoclean(self, event, state):
        """Включить/выключить автоклинер"""
        if state not in ['on', 'off']:
            await event.edit("[❌](emoji/5210952531676504517)**Используйте:** `on` **или** `off`")
            return
        
        enabled = state == 'on'
        
        success = self.bot.db.set_config_value('autoclean_enabled', str(enabled))
        
        if success:
            self.bot.autocleaner.update_settings(enabled=enabled)
            
            status = "включен" if enabled else "выключен"
            await event.edit(f"[✅](emoji/5206607081334906820) **Автоклинер** {status}!")
        else:
            await event.edit("[❌](emoji/5210952531676504517) **Ошибка при изменении настроек автоклинера!**")

    async def set_autoclean_delay(self, event, delay_str):
        """Установить задержку автоклинера"""
        try:
            delay = int(delay_str)
            
            if delay < 10:
                await event.edit("[❌](emoji/5210952531676504517) **Задержка должна быть не менее 10 секунд!**")
                return
            
            if delay > 86400:  # 24 часа
                await event.edit("[❌](emoji/5210952531676504517) **Задержка не может превышать 24 часа (86400 секунд)!**")
                return
            
            success = self.bot.db.set_config_value('autoclean_delay', str(delay))
            
            if success:
                self.bot.autocleaner.update_settings(delay=delay)
                
                if delay < 60:
                    time_str = f"{delay} секунд"
                elif delay < 3600:
                    minutes = delay // 60
                    time_str = f"{minutes} минут"
                else:
                    hours = delay // 3600
                    time_str = f"{hours} часов"
                
                await event.edit(f"[✅](emoji/5206607081334906820) **Задержка автоклинера установлена:** {time_str}")
            else:
                await event.edit("[❌](emoji/5210952531676504517) **Ошибка при установке задержки!**")
                
        except ValueError:
            await event.edit("[❌](emoji/5210952531676504517) **Задержка должна быть числом!**")

    async def set_autostart(self, event, state):
        """Включить/выключить автозапуск бота"""
        if state not in ['on', 'off']:
            await event.edit("[❌](emoji/5210952531676504517)** Используйте: `on` или `off`**")
            return
        
        enabled = state == 'on'
        
        bot_dir = os.getcwd()
        startup_cmd = f"cd {bot_dir} && python main.py\n"

        
        bashrc_path = Path.home() / ".bashrc"
        
        try:
            if enabled:
                with open(bashrc_path, 'a+') as f:
                    f.seek(0)
                    content = f.read()
                    if startup_cmd not in content:
                        f.write(f"\n# Автозапуск Huekka UserBot\n{startup_cmd}")
            else:
                if bashrc_path.exists():
                    with open(bashrc_path, 'r') as f:
                        lines = f.readlines()
                    
                    new_lines = []
                    skip_next = False
                    
                    for line in lines:
                        if skip_next:
                            skip_next = False
                            continue
                            
                        if "# Автозапуск Huekka UserBot" in line:
                            skip_next = True
                            continue
                            
                        if startup_cmd in line:
                            continue
                            
                        new_lines.append(line)
                    
                    with open(bashrc_path, 'w') as f:
                        f.writelines(new_lines)
            
            success = self.bot.db.set_config_value('autostart_enabled', str(enabled))
            
            if success:
                status = "включен" if enabled else "выключен"
                await event.edit(f"**[✅](emoji/5206607081334906820) Автозапуск** {status}!")
            else:
                await event.edit("[❌](emoji/5210952531676504517)** Ошибка при изменении настроек автозапуска!**")
                
        except Exception as e:
            logger.error(f"Ошибка изменения автозапуска: {str(e)}")
            await event.edit("[❌](emoji/5210952531676504517)** Ошибка при изменении настроек автозапуска!**")

    async def set_font(self, event, font_name):
        """Установить шрифт"""
        if not hasattr(self.bot, 'font_module'):
            await event.edit("**[❌](emoji/5210952531676504517) Модуль шрифтов не загружен!**")
            return
        
        if font_name not in self.bot.font_module.fonts:
            available_fonts = ", ".join(self.bot.font_module.fonts.keys())
            await event.edit(f"**[❌](emoji/5210952531676504517) Шрифт '{font_name}' не найден! Доступные шрифты:** {available_fonts}")
            return
        
        success = self.bot.db.set_config_value('current_font', font_name)
        
        if success:
            self.bot.font_module.current_font = font_name
            
            example = self.bot.font_module.apply_font("шрифт")
            await event.edit(f"**[✅](emoji/5206607081334906820) Шрифт изменен на:** {font_name}\nПример: {example}")
        else:
            await event.edit("**[❌](emoji/5210952531676504517) Ошибка при изменении шрифта!**")

    async def set_font_enable(self, event, state):
        """Включить/выключить шрифты"""
        if state not in ['on', 'off']:
            await event.edit("**[❌](emoji/5210952531676504517) Используйте:** `on` **или** `off`")
            return
        
        enabled = state == 'on'
        
        if not hasattr(self.bot, 'font_module'):
            await event.edit("[❌](emoji/5210952531676504517) Модуль шрифтов не загружен!")
            return
        
        success = self.bot.db.set_config_value('font_enabled', str(enabled))
        
        if success:
            self.bot.font_module.enabled = enabled
            status = "включены" if enabled else "выключены"
            await event.edit(f"[✅](emoji/5206607081334906820)** Шрифты** {status}!")
        else:
            await event.edit("[❌](emoji/5210952531676504517) **Ошибка при изменении настроек шрифтов!**")

    async def show_status(self, event):
        """Показать текущие настройки"""
        # Получаем настройки из базы данных
        prefix = self.bot.db.get_config_value('command_prefix', '.')
        autoclean_enabled = self.bot.db.get_config_value('autoclean_enabled', 'True').lower() == 'true'
        autoclean_delay = int(self.bot.db.get_config_value('autoclean_delay', '1800'))
        autostart_enabled = self.bot.db.get_config_value('autostart_enabled', 'False').lower() == 'true'
        
        font_enabled = False
        current_font = "Не установлен"
        
        if hasattr(self.bot, 'font_module'):
            font_enabled = self.bot.db.get_config_value('font_enabled', 'False').lower() == 'true'
            current_font = self.bot.db.get_config_value('current_font', 'шрифт1')
        
        if autoclean_delay < 60:
            delay_str = f"{autoclean_delay} секунд"
        elif autoclean_delay < 3600:
            minutes = autoclean_delay // 60
            delay_str = f"{minutes} минут"
        else:
            hours = autoclean_delay // 3600
            delay_str = f"{hours} часов"
        
        status_text = f"""
[⚙️](emoji/5370932688993656500) **Текущие настройки бота**

**Префикс команд:** `{prefix}`
[▪️](emoji/5251481573953405172)**Автоклинер:** {'[✅](emoji/5206607081334906820) Включен' if autoclean_enabled else '❌ Выключен'}
[▪️](emoji/5251481573953405172)**Задержка автоклинера:** {delay_str}
[▪️](emoji/5251481573953405172)**Автозапуск:** {'[✅](emoji/5206607081334906820) Включен' if autostart_enabled else '❌ Выключен'}
[▪️](emoji/5251481573953405172)**Шрифты:** {'[✅](emoji/5206607081334906820) Включены' if font_enabled else '❌ Выключены'}
[▪️](emoji/5251481573953405172)**Текущий шрифт:** {current_font if font_enabled else 'Не установлен'}

Используйте `{prefix}config help` для просмотра всех команд
"""
        await event.edit(status_text)

def get_module_info():
    return {
        "name": "Configurator",
        "description": "Система управления настройками бота",
        "developer": "@BotHuekka",
        "version": "1.0.0",
        "commands": [
            {
                "command": "config",
                "description": "Управление настройками бота"
            }
        ]
    }

def setup(bot):
    ConfiguratorModule(bot)
