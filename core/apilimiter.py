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
from collections import deque
from telethon.tl.tlobject import TLRequest
from config import BotConfig

logger = logging.getLogger("UserBot.APILimiter")

class APILimiter:
    def __init__(self, bot):
        self.bot = bot
        
        # Для ограничения скорости (Rate Limiting)
        self._rate_requests = deque()
        self._rate_lock = asyncio.Lock()
        self._rate_cooldown = None
        
        # Для общего ограничения (Burst Limiting)
        self._burst_requests = deque()
        self._burst_lock = asyncio.Lock()
        self._burst_cooldown = None
        
        # Настройки из конфига
        api_limiter_config = BotConfig.API_LIMITER
        self.rate_time_sample = api_limiter_config["rate_time_sample"]
        self.rate_threshold = api_limiter_config["rate_threshold"]
        self.rate_cooldown_duration = api_limiter_config["rate_cooldown_duration"]
        
        self.burst_max_requests = api_limiter_config["burst_max_requests"]
        self.burst_cooldown_duration = api_limiter_config["burst_cooldown_duration"]
        
        self.monitored_groups = api_limiter_config["monitored_groups"]
        self.forbidden_methods = api_limiter_config["forbidden_methods"]
        
        # Устанавливаем защиту
        self._install_protection()
        logger.info("API Limiter инициализирован с двумя типами ограничений")

    def _should_monitor(self, request):
        """Определяем, нужно ли мониторить этот запрос"""
        module_name = request.__class__.__module__.split('.')[-1]
        return module_name in self.monitored_groups

    def _is_forbidden(self, request):
        """Проверяет, запрещен ли этот запрос"""
        request_name = type(request).__name__
        return request_name in self.forbidden_methods

    async def _check_rate_limit(self, request_name):
        """Проверяет ограничение скорости"""
        async with self._rate_lock:
            current_time = time.perf_counter()
            
            # Удаляем старые запросы
            while self._rate_requests and current_time - self._rate_requests[0] > self.rate_time_sample:
                self._rate_requests.popleft()
            
            # Добавляем текущий запрос
            self._rate_requests.append(current_time)
            
            # Проверяем превышение лимита
            if len(self._rate_requests) > self.rate_threshold:
                if not self._rate_cooldown:
                    self._rate_cooldown = asyncio.Event()
                    error_msg = (f"RateLimitExceeded - wait {self.rate_cooldown_duration} seconds\n"
                               f"Запросов: {len(self._rate_requests)}/{self.rate_threshold} "
                               f"за {self.rate_time_sample} сек")
                    logger.warning(error_msg)
                    
                    # Запускаем сброс кулдауна
                    asyncio.create_task(self._reset_rate_cooldown())
                
                return False
            return True

    async def _check_burst_limit(self, request_name):
        """Проверяет общее ограничение (Burst)"""
        async with self._burst_lock:
            current_time = time.perf_counter()
            
            # Добавляем текущий запрос
            self._burst_requests.append(current_time)
            
            # Проверяем превышение лимита
            if len(self._burst_requests) > self.burst_max_requests:
                if not self._burst_cooldown:
                    self._burst_cooldown = asyncio.Event()
                    error_msg = (f"BurstLimitExceeded - wait {self.burst_cooldown_duration} seconds\n"
                               f"Сделано {len(self._burst_requests)} запросов подряд, "
                               f"максимум разрешено {self.burst_max_requests}")
                    logger.warning(error_msg)
                    
                    # Запускаем сброс кулдауна
                    asyncio.create_task(self._reset_burst_cooldown())
                
                return False
            
            return True

    async def _reset_rate_cooldown(self):
        """Сбрасывает флаги кулдауна для ограничения скорости"""
        await asyncio.sleep(self.rate_cooldown_duration)
        async with self._rate_lock:
            self._rate_requests.clear()
            if self._rate_cooldown:
                self._rate_cooldown.set()
                self._rate_cooldown = None
        logger.info("Rate limit cooldown finished")

    async def _reset_burst_cooldown(self):
        """Сбрасывает флаги кулдауна для общего ограничения"""
        await asyncio.sleep(self.burst_cooldown_duration)
        async with self._burst_lock:
            self._burst_requests.clear()
            if self._burst_cooldown:
                self._burst_cooldown.set()
                self._burst_cooldown = None
        logger.info("Burst limit cooldown finished")

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

            # Получаем имя метода
            request_name = type(request).__name__
            
            # Проверяем общее ограничение (Burst)
            burst_allowed = await self._check_burst_limit(request_name)
            if not burst_allowed and self._burst_cooldown:
                await self._burst_cooldown.wait()
                # После ожидания снова проверяем
                burst_allowed = await self._check_burst_limit(request_name)
                if not burst_allowed:
                    # Если все еще не разрешено, ждем окончания кулдауна
                    await self._burst_cooldown.wait()
            
            # Проверяем ограничение скорости (Rate)
            rate_allowed = await self._check_rate_limit(request_name)
            if not rate_allowed and self._rate_cooldown:
                await self._rate_cooldown.wait()
                # После ожидания снова проверяем
                rate_allowed = await self._check_rate_limit(request_name)
                if not rate_allowed:
                    # Если все еще не разрешено, ждем окончания кулдауна
                    await self._rate_cooldown.wait()
            
            return await old_call(sender, request, ordered, flood_sleep_threshold)

        # Сохраняем оригинальный метод и заменяем его
        self.bot.client._call = new_call
        self.bot.client._call._api_limiter_installed = True
        logger.info("✅ API protection installed with dual limiting")
