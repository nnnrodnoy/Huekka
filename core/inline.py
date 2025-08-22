import os
import asyncio
from pathlib import Path
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from config import BotConfig

class InlineBot:
    def __init__(self, bot):
        self.bot = bot
        self.config_path = Path("session") / "inline_config.py"
        self.inline_client = None
        
        # Автоматически запускаем инлайн бота при инициализации
        if self.config_path.exists():
            asyncio.create_task(self.start_inline_bot())
        else:
            print("ℹ️ Инлайн бот не настроен. Будет создан автоматически.")

    async def start_inline_bot(self):
        """Запуск инлайн бота"""
        try:
            # Загружаем конфиг
            config = {}
            with open(self.config_path, 'r') as f:
                exec(f.read(), config)
            
            token = config.get('BOT_TOKEN')
            username = config.get('BOT_USERNAME')
            
            if not token:
                print("❌ Токен бота не найден в конфигурации")
                return
            
            # Создаем клиента для инлайн бота
            self.inline_client = TelegramClient(
                StringSession(),
                api_id=self.bot.api_id,
                api_hash=self.bot.api_hash
            )
            
            # Начинаем работу инлайн бота
            await self.inline_client.start(bot_token=token)
            
            # Регистрируем обработчики
            @self.inline_client.on(events.NewMessage(pattern='/start'))
            async def start_handler(event):
                await event.reply("✅ Инлайн бот успешно создан и работает!\n\nИспользуйте меня для инлайн-запросов!")
            
            print(f"✅ Инлайн бот @{username} запущен и готов к работе!")
            
            # Запускаем прослушивание сообщений в фоновом режиме
            asyncio.create_task(self.inline_client.run_until_disconnected())
            
        except Exception as e:
            print(f"❌ Ошибка запуска инлайн бота: {str(e)}")

def setup(bot):
    InlineBot(bot)
