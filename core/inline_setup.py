import os
import re
import asyncio
import random
import string
from pathlib import Path
from telethon import events
from telethon.errors import FloodWaitError
from config import BotConfig

class InlineSetup:
    def __init__(self, bot):
        self.bot = bot
        self.creation_in_progress = False
        self.expected_name = "Huekka-inline-bot"
        self.config_path = Path("session") / "inline_config.py"
        
        # Автоматически запускаем создание бота при инициализации, если нужно
        if not self.config_path.exists():
            asyncio.create_task(self.auto_create_bot())

    async def auto_create_bot(self):
        """Автоматическое создание бота при запуске"""
        if self.creation_in_progress:
            return
            
        self.creation_in_progress = True
        
        try:
            # Ждем немного перед началом, чтобы бот успел полностью запуститься
            await asyncio.sleep(10)
            
            # Получаем нашу сущность для отправки сообщений себе
            me = await self.bot.client.get_me()
            
            # Отправляем уведомление о начале создания бота
            await self.bot.client.send_message(me.id, "🔄 Автоматически создаю инлайн бота...")
            
            # Создаем бота
            success = await self.create_bot_process()
            
            if success:
                await self.bot.client.send_message(me.id, "✅ Инлайн бот успешно создан и настроен!")
            else:
                await self.bot.client.send_message(me.id, "❌ Не удалось создать инлайн бота. Используйте команду .create_inline_bot для ручного создания.")
                
        except Exception as e:
            me = await self.bot.client.get_me()
            await self.bot.client.send_message(me.id, f"❌ Ошибка при автоматическом создании инлайн бота: {str(e)}")
        finally:
            self.creation_in_progress = False

    async def create_bot_process(self):
        """Процесс создания бота"""
        try:
            # Получаем entity BotFather
            botfather = await self.bot.client.get_entity('BotFather')
            
            # Шаг 1: /start
            await self.bot.client.send_message(botfather, '/start')
            await asyncio.sleep(2)
            
            # Шаг 2: /newbot
            await self.bot.client.send_message(botfather, '/newbot')
            await asyncio.sleep(2)
            
            # Получаем последние сообщения от BotFather
            messages = await self.bot.client.get_messages(botfather, limit=10)
            
            # Обрабатываем ответы BotFather
            for msg in messages:
                text = msg.text.lower()
                
                # Шаг 3: Отправляем имя бота
                if "how are we going to call it" in text or "выберите имя для вашего бота" in text:
                    await self.bot.client.send_message(botfather, self.expected_name)
                    await asyncio.sleep(2)
                    continue
                
                # Шаг 4: Отправляем username
                if "choose a username for your bot" in text or "придумайте юзернейм для вашего бота" in text:
                    username = self.generate_username()
                    await self.bot.client.send_message(botfather, username)
                    await asyncio.sleep(2)
                    continue
                
                # Шаг 5: Обрабатываем занятый username
                if "sorry" in text or "это имя пользователя уже занято" in text:
                    username = self.generate_username()
                    await self.bot.client.send_message(botfather, username)
                    await asyncio.sleep(2)
                    continue
                
                # Шаг 6: Извлекаем токен при успешном создании
                if "done" in text or "готово" in text:
                    token = self.extract_token(msg.text)
                    bot_username = self.extract_bot_username(msg.text)
                    
                    if token and bot_username:
                        await self.save_bot_config(token, bot_username)
                        
                        # Отправляем /start новому боту
                        await asyncio.sleep(2)
                        await self.bot.client.send_message(bot_username, '/start')
                        
                        # Очищаем сообщения
                        await self.cleanup_messages(botfather)
                        return True
            
            return False
                
        except FloodWaitError as e:
            await asyncio.sleep(e.seconds)
            return await self.create_bot_process()
        except Exception as e:
            print(f"Ошибка при создании бота: {str(e)}")
            return False

    def generate_username(self):
        """Генерация случайного username"""
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        return f"huekka_inline_bot_{random_suffix}_bot"

    def extract_token(self, text):
        """Извлечение токена из текста"""
        token_pattern = r'(\d+:[a-zA-Z0-9_-]+)'
        match = re.search(token_pattern, text)
        return match.group(1) if match else None

    def extract_bot_username(self, text):
        """Извлечение username бота из текста"""
        username_pattern = r't\.me/(\w+)'
        match = re.search(username_pattern, text)
        return match.group(1) if match else None

    async def save_bot_config(self, token, username):
        """Сохранение конфигурации бота"""
        os.makedirs("session", exist_ok=True)
        with open(self.config_path, 'w') as f:
            f.write(f"BOT_TOKEN = '{token}'\n")
            f.write(f"BOT_USERNAME = '{username}'\n")
        
    async def cleanup_messages(self, botfather):
        """Очистка сообщений связанных с созданием бота"""
        try:
            # Получаем все сообщения из диалога с BotFather
            messages = await self.bot.client.get_messages(botfather, limit=20)
            
            # Удаляем сообщения связанные с созданием бота
            for message in messages:
                try:
                    if message.sender_id == (await self.bot.client.get_me()).id:
                        await message.delete()
                        await asyncio.sleep(0.5)
                except:
                    pass
        except Exception as e:
            print(f"Ошибка при очистке сообщений: {str(e)}")

def setup(bot):
    InlineSetup(bot)
