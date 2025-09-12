# ©️ nnnrodnoy, 2025
# 💬 @nnnrodnoy
# This file is part of Huekka
# 🌐 https://github.com/nnnrodnoy/Huekka/
# You can redistribute it and/or modify it under the terms of the MIT License
# 🔑 https://opensource.org/licenses/MIT
import os
import logging
import asyncio
import random
import math
from pathlib import Path
from telethon import events
from telethon.errors import FloodWaitError, MessageNotModifiedError
from config import BotConfig
from core.formatters import text, msg

logger = logging.getLogger("UserBot.Love")

# Глобальные переменные для настроек
COLORS = ["🟥", "🟧", "🟨", "🟩", "🟦", "🟪"]
HEART_COLORS = ["❤️", "🧡", "💛", "💚", "💙", "💜", "🤎", "🖤", "🤍"]
EMPTY = "⬛️"
MAIN_COLOR = "🟥"
MAIN_HEART = "❤️"

def get_module_info():
    return {
        "name": "Love",
        "description": "Анимации сердца для выражения любви",
        "developer": "@BotHuekka",
        "version": "1.0.0",
        "commands": [
            {
                "command": "love1",
                "description": "Классическая анимация сердца"
            },
            {
                "command": "love2",
                "description": "Спиральная анимация сердца"
            },
            {
                "command": "love3",
                "description": "Анимация сердца из сердечек"
            },
            {
                "command": "love4",
                "description": "Спиральная анимация сердца из сердечек"
            }
        ]
    }

MODULE_INFO = get_module_info()

class LoveModule:
    def __init__(self, bot):
        self.bot = bot
        
        # Регистрация команд через MODULE_INFO
        for cmd_info in MODULE_INFO["commands"]:
            cmd = cmd_info["command"]
            handler = getattr(self, f"cmd_{cmd}")
            bot.register_command(
                cmd=cmd,
                handler=handler,
                description=cmd_info["description"],
                module_name=MODULE_INFO["name"]
            )
        
        bot.set_module_description(MODULE_INFO["name"], MODULE_INFO["description"])

    async def is_premium_user(self, event):
        try:
            user = await event.get_sender()
            return user.premium if hasattr(user, 'premium') else False
        except Exception:
            return False

    async def add_to_autoclean(self, message):
        try:
            if hasattr(self.bot, 'autocleaner') and self.bot.autocleaner.enabled:
                await self.bot.autocleaner.schedule_cleanup(message)
        except Exception as e:
            logger.error(f"Ошибка добавления в автоочистку: {str(e)}")

    async def safe_edit(self, message, new_text, is_html=False):
        """Безопасное редактирование сообщения с обработкой ошибок"""
        try:
            if is_html:
                await message.edit(new_text, parse_mode='html')
            else:
                await message.edit(new_text)
            return True
        except FloodWaitError as e:
            logger.warning(f"Ожидание FloodWait: {e.seconds} сек.")
            await asyncio.sleep(e.seconds + 2)
            return await self.safe_edit(message, new_text, is_html)
        except MessageNotModifiedError:
            logger.debug("Сообщение не изменено")
            return True
        except Exception as e:
            logger.error(f"Ошибка редактирования: {str(e)}")
            return False

    async def classic_animation(self, event):
        """Анимация классического сердца"""
        try:
            # Начальное сообщение
            msg = await event.edit("<b>Я ТЕБЯ ЛЮБЛЮ!...❤️</b>", parse_mode='html')
            await asyncio.sleep(0.7)

            # Этапы построения сердца
            heart_stages = [
                [
                    EMPTY * 9,
                    EMPTY * 2 + MAIN_COLOR * 2 + EMPTY + MAIN_COLOR * 2 + EMPTY * 2,
                    EMPTY * 9
                ],
                [
                    EMPTY * 9,
                    EMPTY * 2 + MAIN_COLOR * 2 + EMPTY + MAIN_COLOR * 2 + EMPTY * 2,
                    EMPTY + MAIN_COLOR * 7 + EMPTY,
                    EMPTY + MAIN_COLOR * 7 + EMPTY,
                    EMPTY * 9
                ],
                [
                    EMPTY * 9,
                    EMPTY * 2 + MAIN_COLOR * 2 + EMPTY + MAIN_COLOR * 2 + EMPTY * 2,
                    EMPTY + MAIN_COLOR * 7 + EMPTY,
                    EMPTY + MAIN_COLOR * 7 + EMPTY,
                    EMPTY + MAIN_COLOR * 7 + EMPTY,
                    EMPTY * 2 + MAIN_COLOR * 5 + EMPTY * 2,
                    EMPTY * 9
                ],
                [
                    EMPTY * 9,
                    EMPTY * 2 + MAIN_COLOR * 2 + EMPTY + MAIN_COLOR * 2 + EMPTY * 2,
                    EMPTY + MAIN_COLOR * 7 + EMPTY,
                    EMPTY + MAIN_COLOR * 7 + EMPTY,
                    EMPTY + MAIN_COLOR * 7 + EMPTY,
                    EMPTY * 2 + MAIN_COLOR * 5 + EMPTY * 2,
                    EMPTY * 3 + MAIN_COLOR * 3 + EMPTY * 3,
                    EMPTY * 4 + MAIN_COLOR + EMPTY * 4,
                    EMPTY * 9
                ]
            ]

            # Постепенное построение сердца
            for stage in heart_stages:
                await self.safe_edit(msg, "<pre>" + "\n".join(stage) + "</pre>", True)
                await asyncio.sleep(0.4)

            # Смена цветов сердца
            for color in COLORS:
                colored_heart = [
                    EMPTY * 9,
                    EMPTY * 2 + color * 2 + EMPTY + color * 2 + EMPTY * 2,
                    EMPTY + color * 7 + EMPTY,
                    EMPTY + color * 7 + EMPTY,
                    EMPTY + color * 7 + EMPTY,
                    EMPTY * 2 + color * 5 + EMPTY * 2,
                    EMPTY * 3 + color * 3 + EMPTY * 3,
                    EMPTY * 4 + color + EMPTY * 4,
                    EMPTY * 9
                ]
                await self.safe_edit(msg, "<pre>" + "\n".join(colored_heart) + "</pre>", True)
                await asyncio.sleep(0.6)

            # Уменьшение сердца
            for i in range(8, 0, -1):
                heart = (MAIN_COLOR * i + "\n") * i
                await self.safe_edit(msg, f"<pre>{heart}</pre>", True)
                await asyncio.sleep(0.3)

            # Финальный текст
            final_text = "I LOVE YOU! ❤️"
            for i in range(1, len(final_text) + 1):
                await self.safe_edit(msg, f"<b>{final_text[:i]}</b>", True)
                await asyncio.sleep(0.2)

        except Exception as e:
            logger.error(f"Ошибка в classic_animation: {str(e)}")
            await event.respond(f"⚠️ Ошибка: {str(e)}")

    async def spiral_animation(self, event):
        """Спиральная анимация сердца"""
        try:
            # Начальное сообщение
            msg = await event.edit("<b>Я ТЕБЯ ОБОЖАЮ!...❤️</b>", parse_mode='html')
            await asyncio.sleep(0.7)

            # Базовое сердце
            base = [
                [EMPTY] * 9,
                [EMPTY] * 2 + ["❤️"] * 2 + [EMPTY] + ["❤️"] * 2 + [EMPTY] * 2,
                [EMPTY] + ["❤️"] * 7 + [EMPTY],
                [EMPTY] + ["❤️"] * 7 + [EMPTY],
                [EMPTY] + ["❤️"] * 7 + [EMPTY],
                [EMPTY] * 2 + ["❤️"] * 5 + [EMPTY] * 2,
                [EMPTY] * 3 + ["❤️"] * 3 + [EMPTY] * 3,
                [EMPTY] * 4 + ["❤️"] + [EMPTY] * 4,
                [EMPTY] * 9
            ]

            # Собираем все точки сердца
            points = []
            for i in range(len(base)):
                for j in range(len(base[i])):
                    if base[i][j] == "❤️":
                        points.append((i, j))

            # Сортируем точки для спирального эффекта
            center = (4, 4)
            points.sort(key=lambda p: math.atan2(p[0] - center[0], p[1] - center[1]))

            # Постепенное заполнение
            current_heart = [[EMPTY for _ in range(9)] for _ in range(9)]
            for i, (x, y) in enumerate(points):
                current_heart[x][y] = random.choice(COLORS)
                if i % 2 == 0:
                    spiral_msg = "<pre>" + "\n".join("".join(line) for line in current_heart) + "</pre>"
                    await self.safe_edit(msg, spiral_msg, True)
                    await asyncio.sleep(0.25)

            # Вращение цветов
            for _ in range(8):
                for x, y in points:
                    current_heart[x][y] = random.choice(COLORS)
                
                rotate_msg = "<pre>" + "\n".join("".join(line) for line in current_heart) + "</pre>"
                await self.safe_edit(msg, rotate_msg, True)
                await asyncio.sleep(0.7)

            # Постепенное удаление
            num_points = len(points)
            for i in range(num_points):
                index = num_points - 1 - i
                x, y = points[index]
                current_heart[x][y] = EMPTY

                if i % 3 == 0:
                    remove_msg = "<pre>" + "\n".join("".join(line) for line in current_heart) + "</pre>"
                    await self.safe_edit(msg, remove_msg, True)
                    await asyncio.sleep(0.15)

            # Финальный текст
            text_stages = ["❤️", "I❤️", "I L❤️", "I LO❤️", "I LOV❤️", "I LOVE❤️", 
                          "I LOVE Y❤️", "I LOVE YO❤️", "I LOVE YOU❤️", "I LOVE YOU!❤️", "I LOVE YOU! ❤️"]
            for text in text_stages:
                await self.safe_edit(msg, f"<b>{text}</b>", True)
                await asyncio.sleep(0.4)

        except Exception as e:
            logger.error(f"Ошибка в spiral_animation: {str(e)}")
            await event.respond(f"⚠️ Ошибка: {str(e)}")

    async def classic_animation_hearts(self, event):
        """Анимация сердца из сердечек"""
        try:
            # Начальное сообщение
            msg = await event.edit("<b>Я ТЕБЯ ЛЮБЛЮ!...❤️</b>", parse_mode='html')
            await asyncio.sleep(0.7)

            # Этапы построения сердца
            heart_stages = [
                [
                    EMPTY * 9,
                    EMPTY * 2 + MAIN_HEART * 2 + EMPTY + MAIN_HEART * 2 + EMPTY * 2,
                    EMPTY * 9
                ],
                [
                    EMPTY * 9,
                    EMPTY * 2 + MAIN_HEART * 2 + EMPTY + MAIN_HEART * 2 + EMPTY * 2,
                    EMPTY + MAIN_HEART * 7 + EMPTY,
                    EMPTY + MAIN_HEART * 7 + EMPTY,
                    EMPTY * 9
                ],
                [
                    EMPTY * 9,
                    EMPTY * 2 + MAIN_HEART * 2 + EMPTY + MAIN_HEART * 2 + EMPTY * 2,
                    EMPTY + MAIN_HEART * 7 + EMPTY,
                    EMPTY + MAIN_HEART * 7 + EMPTY,
                    EMPTY + MAIN_HEART * 7 + EMPTY,
                    EMPTY * 2 + MAIN_HEART * 5 + EMPTY * 2,
                    EMPTY * 9
                ],
                [
                    EMPTY * 9,
                    EMPTY * 2 + MAIN_HEART * 2 + EMPTY + MAIN_HEART * 2 + EMPTY * 2,
                    EMPTY + MAIN_HEART * 7 + EMPTY,
                    EMPTY + MAIN_HEART * 7 + EMPTY,
                    EMPTY + MAIN_HEART * 7 + EMPTY,
                    EMPTY * 2 + MAIN_HEART * 5 + EMPTY * 2,
                    EMPTY * 3 + MAIN_HEART * 3 + EMPTY * 3,
                    EMPTY * 4 + MAIN_HEART + EMPTY * 4,
                    EMPTY * 9
                ]
            ]

            # Постепенное построение сердца
            for stage in heart_stages:
                await self.safe_edit(msg, "<pre>" + "\n".join(stage) + "</pre>", True)
                await asyncio.sleep(0.4)

            # Смена цветов сердечек
            for _ in range(2):
                for color in random.sample(HEART_COLORS, len(HEART_COLORS)):
                    colored_heart = [
                        EMPTY * 9,
                        EMPTY * 2 + color * 2 + EMPTY + color * 2 + EMPTY * 2,
                        EMPTY + color * 7 + EMPTY,
                        EMPTY + color * 7 + EMPTY,
                        EMPTY + color * 7 + EMPTY,
                        EMPTY * 2 + color * 5 + EMPTY * 2,
                        EMPTY * 3 + color * 3 + EMPTY * 3,
                        EMPTY * 4 + color + EMPTY * 4,
                        EMPTY * 9
                    ]
                    await self.safe_edit(msg, "<pre>" + "\n".join(colored_heart) + "</pre>", True)
                    await asyncio.sleep(0.5)

            # Уменьшение сердца
            for i in range(8, 0, -1):
                heart = (MAIN_HEART * i + "\n") * i
                await self.safe_edit(msg, f"<pre>{heart}</pre>", True)
                await asyncio.sleep(0.3)

            # Финальный текст
            final_text = "I LOVE YOU! ❤️"
            for i in range(1, len(final_text) + 1):
                await self.safe_edit(msg, f"<b>{final_text[:i]}</b>", True)
                await asyncio.sleep(0.2)

        except Exception as e:
            logger.error(f"Ошибка в classic_animation_hearts: {str(e)}")
            await event.respond(f"⚠️ Ошибка: {str(e)}")

    async def spiral_animation_hearts(self, event):
        """Спиральная анимация сердца из сердечек"""
        try:
            # Начальное сообщение
            msg = await event.edit("<b>Я ТЕБЯ ОБОЖАЮ!...❤️</b>", parse_mode='html')
            await asyncio.sleep(0.7)

            # Базовое сердце
            base = [
                [EMPTY] * 9,
                [EMPTY] * 2 + ["❤️"] * 2 + [EMPTY] + ["❤️"] * 2 + [EMPTY] * 2,
                [EMPTY] + ["❤️"] * 7 + [EMPTY],
                [EMPTY] + ["❤️"] * 7 + [EMPTY],
                [EMPTY] + ["❤️"] * 7 + [EMPTY],
                [EMPTY] * 2 + ["❤️"] * 5 + [EMPTY] * 2,
                [EMPTY] * 3 + ["❤️"] * 3 + [EMPTY] * 3,
                [EMPTY] * 4 + ["❤️"] + [EMPTY] * 4,
                [EMPTY] * 9
            ]

            # Собираем все точки сердца
            points = []
            for i in range(len(base)):
                for j in range(len(base[i])):
                    if base[i][j] == "❤️":
                        points.append((i, j))

            # Сортируем точки для спирального эффекта
            center = (4, 4)
            points.sort(key=lambda p: math.atan2(p[0] - center[0], p[1] - center[1]))

            # Постепенное заполнение
            current_heart = [[EMPTY for _ in range(9)] for _ in range(9)]
            for i, (x, y) in enumerate(points):
                current_heart[x][y] = random.choice(HEART_COLORS)
                if i % 2 == 0:
                    spiral_msg = "<pre>" + "\n".join("".join(line) for line in current_heart) + "</pre>"
                    await self.safe_edit(msg, spiral_msg, True)
                    await asyncio.sleep(0.25)

            # Вращение сердечек
            for _ in range(8):
                for x, y in points:
                    current_heart[x][y] = random.choice(HEART_COLORS)
                
                rotate_msg = "<pre>" + "\n".join("".join(line) for line in current_heart) + "</pre>"
                await self.safe_edit(msg, rotate_msg, True)
                await asyncio.sleep(0.7)

            # Постепенное удаление
            num_points = len(points)
            for i in range(num_points):
                index = num_points - 1 - i
                x, y = points[index]
                current_heart[x][y] = EMPTY

                if i % 3 == 0:
                    remove_msg = "<pre>" + "\n".join("".join(line) for line in current_heart) + "</pre>"
                    await self.safe_edit(msg, remove_msg, True)
                    await asyncio.sleep(0.15)

            # Финальный текст
            text_stages = ["❤️", "I❤️", "I L❤️", "I LO❤️", "I LOV❤️", "I LOVE❤️", 
                          "I LOVE Y❤️", "I LOVE YO❤️", "I LOVE YOU❤️", "I LOVE YOU! ❤️"]
            for text in text_stages:
                await self.safe_edit(msg, f"<b>{text}</b>", True)
                await asyncio.sleep(0.4)

        except Exception as e:
            logger.error(f"Ошибка в spiral_animation_hearts: {str(e)}")
            await event.respond(f"⚠️ Ошибка: {str(e)}")

    async def cmd_love1(self, event):
        """Обработчик команды .love1"""
        await self.classic_animation(event)

    async def cmd_love2(self, event):
        """Обработчик команды .love2"""
        await self.spiral_animation(event)

    async def cmd_love3(self, event):
        """Обработчик команды .love3"""
        await self.classic_animation_hearts(event)

    async def cmd_love4(self, event):
        """Обработчик команды .love4"""
        await self.spiral_animation_hearts(event)

def setup(bot):
    LoveModule(bot)