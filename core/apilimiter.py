# ©️ nnnrodnoy, 2025
# 💬 @nnnrodnoy
# This file is part of Huekka
# 🌐 https://github.com/nnnrodnoy/Huekka/
# You can redistribute it and/or modify it under the terms of the MIT License
# 🔑 https://opensource.org/licenses/MIT
import asyncio
import logging
import random
import time
from telethon.tl.tlobject import TLRequest
from config import BotConfig

logger = logging.getLogger("UserBot.APILimiter")

class APILimiter:
    def __init__(self, bot):
        self.bot = bot
        self._ratelimiter = []
        self._lock = asyncio.Lock()
        self._cooldown_event = None
        self._alert_sent = False
        
        # Настройки из конфига
        api_limiter_config = BotConfig.API_LIMITER
        self.time_sample = api_limiter_config["time_sample"]
        self.threshold = api_limiter_config["threshold"]
        self.local_floodwait = api_limiter_config["local_floodwait"]
        self.monitored_groups = api_limiter_config["monitored_groups"]
        self.forbidden_methods = api_limiter_config["forbidden_methods"]
        
        # Устанавливаем защиту
        self._install_protection()
        logger.info("API Limiter инициализирован")

    def _should_monitor(self, request):
        """Определяем, нужно ли мониторить этот запрос"""
        module_name = request.__class__.__module__.split('.')[-1]
        return module_name in self.monitored_groups

    def _is_forbidden(self, request):
        """Проверяет, запрещен ли этот запрос"""
        request_name = type(request).__name__
        return request_name in self.forbidden_methods

    def _install_protection(self):
        """Установка перехватчика API вызовов"""
        if hasattr(self.bot.client._call, "_api_limiter_installed"):
            logger.warning("API защита уже установлена")
            return

        old_call = self.bot.client._call

        async def new_call(
            sender,
            request: TLRequest,
            ordered: bool = False,
            flood_sleep_threshold: int = None,
        ):
            # Проверяем, не запрещен ли запрос
            if self._is_forbidden(request):
                logger.warning(f"Запрещенный запрос: {type(request).__name__}")
                raise Exception("This API method is forbidden by security policy")
            
            # Пропускаем запросы, которые не нужно мониторить
            if not self._should_monitor(request):
                return await old_call(sender, request, ordered, flood_sleep_threshold)

            # Добавляем случайную задержку (5-15 мс)
            delay = random.randint(5, 15) / 1000
            await asyncio.sleep(delay)

            # Если есть активный кулдаун - ждем его завершения
            if self._cooldown_event and not self._cooldown_event.is_set():
                logger.debug("Ожидание окончания кулдауна...")
                await self._cooldown_event.wait()

            async with self._lock:
                # Проверяем кулдаун еще раз внутри блокировки
                if self._cooldown_event and not self._cooldown_event.is_set():
                    return await old_call(sender, request, ordered, flood_sleep_threshold)

                # Получаем имя метода
                request_name = type(request).__name__
                current_time = time.perf_counter()
                
                # Добавляем запрос в историю
                self._ratelimiter.append((request_name, current_time))
                
                # Очищаем старые записи
                self._ratelimiter = [
                    (name, t) for name, t in self._ratelimiter 
                    if current_time - t < self.time_sample
                ]
                
                # **Проверяем превышение порога ЗА ВРЕМЯ**
                if len([t for name, t in self._ratelimiter if current_time - t < self.time_sample]) > self.threshold:
                    # Создаем событие кулдауна
                    if not self._cooldown_event:
                        self._cooldown_event = asyncio.Event()
                    
                    # Формируем сообщение об ошибке
                    error_msg = f"FloodError - wait {self.local_floodwait} seconds\nЗапросов: {len(self._ratelimiter)}/{self.threshold} за {self.time_sample} сек"
                    
                    # Логируем
                    if not self._alert_sent:
                        logger.warning(error_msg)
                        self._alert_sent = True
                    
                    # Запускаем сброс кулдауна
                    asyncio.create_task(self._reset_cooldown())
            
            return await old_call(sender, request, ordered, flood_sleep_threshold)

        # Сохраняем оригинальный метод и заменяем его
        self.bot.client._call = new_call
        self.bot.client._call._api_limiter_installed = True
        logger.info("✅ API protection installed")

    async def _reset_cooldown(self):
        """Сбрасывает флаги кулдауна после задержки"""
        await asyncio.sleep(self.local_floodwait)
        async with self._lock:
            self._ratelimiter = []
        if self._cooldown_event:
            self._cooldown_event.set()
            self._cooldown_event = None
            self._alert_sent = False
        logger.info("API cooldown finished")
