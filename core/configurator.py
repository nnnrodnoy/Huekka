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
        elif subcommand == "status":
            await self.show_status(event)
        else:
            await self.show_help(event)

    async def show_help(self, event):
        """Показать справку по команде config"""
        prefix = self.bot.command_prefix
        
        help_text = f"""
<emoji document_id=5370932688993656500>⚙️</emoji> <b>Управление настройками бота</b>

<b>Использование:</b>
 <emoji document_id=5251522431977291010>▪️</emoji><code>{prefix}config prefix</code> <code>&lt;новый префикс&gt;</code> - <i>Изменить префикс команд</i>
 <emoji document_id=5251522431977291010>▪️</emoji><code>{prefix}config autoclean</code> <code>&lt;on/off&gt;</code> - <i>Включить/выключить автоклинер</i>
 <emoji document_id=5251522431977291010>▪️</emoji><code>{prefix}config autoclean_delay</code> <code>&lt;секунды&gt;</code> - <i>Установить задержку автоклинера</i>
 <emoji document_id=5251522431977291010>▪️</emoji><code>{prefix}config autostart</code> <code>&lt;on/off&gt;</code> - <i>Включить/выключить автозапуск</i>
 <emoji document_id=5251522431977291010>▪️</emoji><code>{prefix}config status</code> - <i>Показать текущие настройки</i>

<b>Примеры:</b>
<emoji document_id=5251481573953405172>▫️</emoji> <code>{prefix}config prefix !</code> - <i>Установить префикс "!"</i>
<emoji document_id=5251481573953405172>▫️</emoji> <code>{prefix}config autoclean on</code> - <i>Включить автоклинер</i>
<emoji document_id=5251481573953405172>▫️</emoji> <code>{prefix}config autoclean_delay 3600</code> - <i>Установить задержку 1 час</i>
<emoji document_id=5251481573953405172>▫️</emoji> <code>{prefix}config autostart on</code> - <i>Включить автозапуск</i>
"""
        await event.edit(help_text)

    async def set_prefix(self, event, new_prefix):
        """Установить новый префикс команд"""
        if not new_prefix or len(new_prefix) > 3:
            await event.edit("<emoji document_id=5210952531676504517>❌</emoji> <b>Префикс должен быть от 1 до 3 символов!</b>")
            return
        
        if ' ' in new_prefix:
            await event.edit("<emoji document_id=5210952531676504517>❌</emoji> <b>Префикс не может содержать пробелы!</b>")
            return
        
        success = self.bot.db.set_config_value('command_prefix', new_prefix)
        
        if success:
            self.bot.command_prefix = new_prefix
            await event.edit(f"<emoji document_id=5206607081334906820>✅</emoji> <b>Префикс команд изменен на:</b> <code>{new_prefix}</code>")
        else:
            await event.edit("<emoji document_id=5210952531676504517>❌</emoji> <b>Ошибка при изменении префикса!</b>")

    async def set_autoclean(self, event, state):
        """Включить/выключить автоклинер"""
        if state not in ['on', 'off']:
            await event.edit("<emoji document_id=5210952531676504517>❌</emoji> <b>Используйте:</b> <code>on</code> <b>или</b> <code>off</code>")
            return
        
        enabled = state == 'on'
        
        success = self.bot.db.set_config_value('autoclean_enabled', str(enabled))
        
        if success:
            self.bot.autocleaner.update_settings(enabled=enabled)
            
            status = "включен" if enabled else "выключен"
            await event.edit(f"<emoji document_id=5206607081334906820>✅</emoji> <b>Автоклинер</b> {status}!")
        else:
            await event.edit("<emoji document_id=5210952531676504517>❌</emoji> <b>Ошибка при изменении настроек автоклинера!</b>")

    async def set_autoclean_delay(self, event, delay_str):
        """Установить задержку автоклинера"""
        try:
            delay = int(delay_str)
            
            if delay < 10:
                await event.edit("<emoji document_id=5210952531676504517>❌</emoji> <b>Задержка должна быть не менее 10 секунд!</b>")
                return
            
            if delay > 86400:  # 24 часа
                await event.edit("<emoji document_id=5210952531676504517>❌</emoji> <b>Задержка не может превышать 24 часа (86400 секунд)!</b>")
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
                
                await event.edit(f"<emoji document_id=5206607081334906820>✅</emoji> <b>Задержка автоклинера установлена:</b> {time_str}")
            else:
                await event.edit("<emoji document_id=5210952531676504517>❌</emoji> <b>Ошибка при установке задержки!</b>")
                
        except ValueError:
            await event.edit("<emoji document_id=5210952531676504517>❌</emoji> <b>Задержка должна быть числом!</b>")

    async def set_autostart(self, event, state):
        """Включить/выключить автозапуск бота"""
        if state not in ['on', 'off']:
            await event.edit("<emoji document_id=5210952531676504517>❌</emoji> <b>Используйте:</b> <code>on</code> <b>или</b> <code>off</code>")
            return
        
        enabled = state == 'on'
        
        bot_dir = os.getcwd()
        startup_cmd = f"cd {bot_dir} && ./start_bot.sh\n"  # Изменено на запуск через скрипт

        
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
                await event.edit(f"<emoji document_id=5206607081334906820>✅</emoji> <b>Автозапуск</b> {status}!")
            else:
                await event.edit("<emoji document_id=5210952531676504517>❌</emoji> <b>Ошибка при изменении настроек автозапуска!</b>")
                
        except Exception as e:
            logger.error(f"Ошибка изменения автозапуска: {str(e)}")
            await event.edit("<emoji document_id=5210952531676504517>❌</emoji> <b>Ошибка при изменении настроек автозапуска!</b>")

    async def show_status(self, event):
        """Показать текущие настройки"""
        # Получаем настройки из базы данных
        prefix = self.bot.db.get_config_value('command_prefix', '.')
        autoclean_enabled = self.bot.db.get_config_value('autoclean_enabled', 'True').lower() == 'true'
        autoclean_delay = int(self.bot.db.get_config_value('autoclean_delay', '1800'))
        autostart_enabled = self.bot.db.get_config_value('autostart_enabled', 'False').lower() == 'true'
        
        if autoclean_delay < 60:
            delay_str = f"{autoclean_delay} секунд"
        elif autoclean_delay < 3600:
            minutes = autoclean_delay // 60
            delay_str = f"{minutes} минут"
        else:
            hours = autoclean_delay // 3600
            delay_str = f"{hours} часов"
        
        autoclean_status = "<emoji document_id=5206607081334906820>✅</emoji> Включен" if autoclean_enabled else "<emoji document_id=5210952531676504517>❌</emoji> Выключен"
        autostart_status = "<emoji document_id=5206607081334906820>✅</emoji> Включен" if autostart_enabled else "<emoji document_id=5210952531676504517>❌</emoji> Выключен"
        
        status_text = f"""
<emoji document_id=5370932688993656500>⚙️</emoji> <b>Текущие настройки бота</b>

<b>Префикс команд:</b> <code>{prefix}</code>
<emoji document_id=5251481573953405172>▪️</emoji> <b>Автоклинер:</b> {autoclean_status}
<emoji document_id=5251481573953405172>▪️</emoji> <b>Задержка автоклинера:</b> {delay_str}
<emoji document_id=5251481573953405172>▪️</emoji> <b>Автозапуск:</b> {autostart_status}

Используйте <code>{prefix}config help</code> для просмотра всех команд
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
