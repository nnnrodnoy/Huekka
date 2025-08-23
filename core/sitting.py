import os
import sqlite3
from telethon import events, Button
from config import BotConfig

def setup(bot):
    @bot.register_command("sitting", "Настройки бота", module_name="Settings")
    async def sitting_handler(event):
        # Создаем интерактивное меню настроек
        buttons = [
            [Button.inline("1. Автоочистка", b"autoclean_settings")],
            [Button.inline("2. Автозапуск", b"autostart_settings")],
            [Button.inline("3. Префикс команд", b"prefix_settings")],
            [Button.inline("❌ Закрыть", b"close_settings")]
        ]
        
        message = "⚙️ **Huekka Settings**\n\n"
        message += "Выберите настройку для изменения:\n\n"
        
        # Получаем текущие настройки
        prefix = bot.command_prefix
        autoclean_enabled = bot.get_config_value('autoclean_enabled', 
                                               str(BotConfig.AUTOCLEAN["enabled"])).lower() == 'true'
        autoclean_delay = int(bot.get_config_value('autoclean_delay', 
                                                BotConfig.AUTOCLEAN["default_delay"]))
        
        # Проверяем автозапуск
        autostart_enabled = False
        if os.path.exists(os.path.expanduser("~/.bashrc")):
            with open(os.path.expanduser("~/.bashrc"), "r") as f:
                autostart_enabled = "python main.py" in f.read()
        
        message += f"📝 Префикс: `{prefix}`\n"
        message += f"🧹 Автоочистка: {'ВКЛ' if autoclean_enabled else 'ВЫКЛ'} ({autoclean_delay} сек)\n"
        message += f"🚀 Автозапуск: {'ВКЛ' if autostart_enabled else 'ВЫКЛ'}\n\n"
        message += "Выберите опцию ниже:"
        
        await event.reply(message, buttons=buttons)
    
    # Обработчик callback-кнопок
    @bot.client.on(events.CallbackQuery)
    async def settings_callback_handler(event):
        if event.data == b"close_settings":
            await event.delete()
            return
        
        # Получаем текущие настройки
        prefix = bot.command_prefix
        autoclean_enabled = bot.get_config_value('autoclean_enabled', 
                                               str(BotConfig.AUTOCLEAN["enabled"])).lower() == 'true'
        autoclean_delay = int(bot.get_config_value('autoclean_delay', 
                                                BotConfig.AUTOCLEAN["default_delay"]))
        
        # Проверяем автозапуск
        autostart_enabled = False
        if os.path.exists(os.path.expanduser("~/.bashrc")):
            with open(os.path.expanduser("~/.bashrc"), "r") as f:
                autostart_enabled = "python main.py" in f.read()
        
        if event.data == b"autoclean_settings":
            buttons = [
                [Button.inline(f"{'✅' if autoclean_enabled else '☑️'} Включить", b"autoclean_enable"),
                 Button.inline(f"{'✅' if not autoclean_enabled else '☑️'} Выключить", b"autoclean_disable")],
                [Button.inline("⏱ Изменить время", b"autoclean_time")],
                [Button.inline("🔙 Назад", b"back_to_main")]
            ]
            
            message = "🧹 **Настройки автоочистки**\n\n"
            message += f"Текущий статус: {'ВКЛ' if autoclean_enabled else 'ВЫКЛ'}\n"
            message += f"Текущее время: {autoclean_delay} секунд\n\n"
            message += "Выберите действие:"
            
            await event.edit(message, buttons=buttons)
        
        elif event.data == b"autostart_settings":
            buttons = [
                [Button.inline(f"{'✅' if autostart_enabled else '☑️'} Включить", b"autostart_enable"),
                 Button.inline(f"{'✅' if not autostart_enabled else '☑️'} Выключить", b"autostart_disable")],
                [Button.inline("🔙 Назад", b"back_to_main")]
            ]
            
            message = "🚀 **Настройки автозапуска**\n\n"
            message += f"Текущий статус: {'ВКЛ' if autostart_enabled else 'ВЫКЛ'}\n\n"
            message += "Выберите действие:"
            
            await event.edit(message, buttons=buttons)
        
        elif event.data == b"prefix_settings":
            buttons = [
                [Button.inline("✏️ Изменить префикс", b"change_prefix")],
                [Button.inline("🔙 Назад", b"back_to_main")]
            ]
            
            message = "📝 **Настройки префикса**\n\n"
            message += f"Текущий префикс: `{prefix}`\n\n"
            message += "Выберите действие:"
            
            await event.edit(message, buttons=buttons)
        
        elif event.data == b"back_to_main":
            buttons = [
                [Button.inline("1. Автоочистка", b"autoclean_settings")],
                [Button.inline("2. Автозапуск", b"autostart_settings")],
                [Button.inline("3. Префикс команд", b"prefix_settings")],
                [Button.inline("❌ Закрыть", b"close_settings")]
            ]
            
            message = "⚙️ **Huekka Settings**\n\n"
            message += "Выберите настройку для изменения:\n\n"
            message += f"📝 Префикс: `{prefix}`\n"
            message += f"🧹 Автоочистка: {'ВКЛ' if autoclean_enabled else 'ВЫКЛ'} ({autoclean_delay} сек)\n"
            message += f"🚀 Автозапуск: {'ВКЛ' if autostart_enabled else 'ВЫКЛ'}\n\n"
            message += "Выберите опцию ниже:"
            
            await event.edit(message, buttons=buttons)
        
        elif event.data == b"autoclean_enable":
            bot.set_config_in_db("autoclean_enabled", "True")
            bot.autocleaner.enabled = True
            await event.answer("✅ Автоочистка включена!")
            
            # Обновляем меню
            buttons = [
                [Button.inline("✅ Включить", b"autoclean_enable"),
                 Button.inline("☑️ Выключить", b"autoclean_disable")],
                [Button.inline("⏱ Изменить время", b"autoclean_time")],
                [Button.inline("🔙 Назад", b"back_to_main")]
            ]
            
            message = "🧹 **Настройки автоочистки**\n\n"
            message += "Текущий статус: ВКЛ\n"
            message += f"Текущее время: {autoclean_delay} секунд\n\n"
            message += "Выберите действие:"
            
            await event.edit(message, buttons=buttons)
        
        elif event.data == b"autoclean_disable":
            bot.set_config_in_db("autoclean_enabled", "False")
            bot.autocleaner.enabled = False
            await event.answer("✅ Автоочистка выключена!")
            
            # Обновляем меню
            buttons = [
                [Button.inline("☑️ Включить", b"autoclean_enable"),
                 Button.inline("✅ Выключить", b"autoclean_disable")],
                [Button.inline("⏱ Изменить время", b"autoclean_time")],
                [Button.inline("🔙 Назад", b"back_to_main")]
            ]
            
            message = "🧹 **Настройки автоочистки**\n\n"
            message += "Текущий статус: ВЫКЛ\n"
            message += f"Текущее время: {autoclean_delay} секунд\n\n"
            message += "Выберите действие:"
            
            await event.edit(message, buttons=buttons)
        
        elif event.data == b"autoclean_time":
            # Переходим в режим ввода времени
            await event.delete()
            async with bot.client.conversation(event.chat_id) as conv:
                await conv.send_message("⏱ Введите новое время автоочистки в секундах:")
                response = await conv.get_response()
                
                try:
                    new_time = int(response.text.strip())
                    if new_time < 10:
                        await conv.send_message("❌ Время должно быть не менее 10 секунд!")
                    else:
                        bot.set_config_in_db("autoclean_delay", str(new_time))
                        bot.autocleaner.delay = new_time
                        await conv.send_message(f"✅ Время автоочистки установлено на {new_time} секунд!")
                except ValueError:
                    await conv.send_message("❌ Пожалуйста, введите корректное число!")
        
        elif event.data == b"autostart_enable":
            # Включаем автозапуск
            if not os.path.exists(os.path.expanduser("~/.bashrc")):
                open(os.path.expanduser("~/.bashrc"), "w").close()
            
            with open(os.path.expanduser("~/.bashrc"), "a") as f:
                f.write(f"\ncd {os.getcwd()} && python main.py\n")
            
            await event.answer("✅ Автозапуск включен!")
            
            # Обновляем меню
            buttons = [
                [Button.inline("✅ Включить", b"autostart_enable"),
                 Button.inline("☑️ Выключить", b"autostart_disable")],
                [Button.inline("🔙 Назад", b"back_to_main")]
            ]
            
            message = "🚀 **Настройки автозапуска**\n\n"
            message += "Текущий статус: ВКЛ\n\n"
            message += "Выберите действие:"
            
            await event.edit(message, buttons=buttons)
        
        elif event.data == b"autostart_disable":
            # Выключаем автозапуск
            if os.path.exists(os.path.expanduser("~/.bashrc")):
                with open(os.path.expanduser("~/.bashrc"), "r") as f:
                    lines = f.readlines()
                
                with open(os.path.expanduser("~/.bashrc"), "w") as f:
                    for line in lines:
                        if "python main.py" not in line:
                            f.write(line)
            
            await event.answer("✅ Автозапуск выключен!")
            
            # Обновляем меню
            buttons = [
                [Button.inline("☑️ Включить", b"autostart_enable"),
                 Button.inline("✅ Выключить", b"autostart_disable")],
                [Button.inline("🔙 Назад", b"back_to_main")]
            ]
            
            message = "🚀 **Настройки автозапуска**\n\n"
            message += "Текущий статус: ВЫКЛ\n\n"
            message += "Выберите действие:"
            
            await event.edit(message, buttons=buttons)
        
        elif event.data == b"change_prefix":
            # Переходим в режим ввода префикса
            await event.delete()
            async with bot.client.conversation(event.chat_id) as conv:
                await conv.send_message("✏️ Введите новый префикс команд:")
                response = await conv.get_response()
                
                new_prefix = response.text.strip()
                if len(new_prefix) == 0:
                    await conv.send_message("❌ Префикс не может быть пустым!")
                else:
                    bot.set_config_in_db("command_prefix", new_prefix)
                    bot.command_prefix = new_prefix
                    await conv.send_message(f"✅ Префикс изменен на `{new_prefix}`!")
