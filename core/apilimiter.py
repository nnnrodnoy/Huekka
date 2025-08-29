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
        
        # Для ограничения по количеству запросов
        self._period_requests = deque()
        self._period_lock = asyncio.Lock()
        self._period_cooldown = None
        
        # Для ограничения по скорости
        self._speed_requests = deque()
        self._speed_lock = asyncio.Lock()
        self._speed_cooldown = None
        
        # Настройки из конфига
        api_limiter_config = BotConfig.API_LIMITER
        
        # Ограничение по количеству запросов
        self.requests_per_period = api_limiter_config["requests_per_period"]
        self.period_duration = api_limiter_config["period_duration"]
        self.cooldown_after_period = api_limiter_config["cooldown_after_period"]
        
        # Ограничение по скорости
        self.max_requests_per_second = api_limiter_config["max_requests_per_second"]
        self.high_load_cooldown = api_limiter_config["high_load_cooldown"]
        
        self.monitored_groups = api_limiter_config["monitored_groups"]
        self.forbidden_methods = api_limiter_config["forbidden_methods"]
        
        # Устанавливаем защиту
        self._install_protection()
        logger.info("API Limiter инициализирован с новой логикой ограничений")

    def _should_monitor(self, request):
        """Определяем, нужно ли мониторить этот запрос"""
        module_name = request.__class__.__module__.split('.')[-1]
        return module_name in self.monitored_groups

    def _is_forbidden(self, request):
        """Проверяет, запрещен ли этот запрос"""
        request_name = type(request).__name__
        return request_name in self.forbidden_methods

    async def _check_period_limit(self, request_name):
        """Проверяет ограничение по количеству запросов за период"""
        async with self._period_lock:
            current_time = time.perf_counter()
            
            # Удаляем старые запросы
            while self._period_requests and current_time - self._period_requests[0] > self.period_duration:
                self._period_requests.popleft()
            
            # Добавляем текущий запрос
            self._period_requests.append(current_time)
            
            # Проверяем превышение лимита
            if len(self._period_requests) > self.requests_per_period:
                if not self._period_cooldown:
                    self._period_cooldown = asyncio.Event()
                    error_msg = (f"PeriodLimitExceeded - wait {self.cooldown_after_period} seconds\n"
                               f"Запросов: {len(self._period_requests)}/{self.requests_per_period} "
                               f"за {self.period_duration} сек")
                    logger.warning(error_msg)
                    
                    # Запускаем сброс кулдауна
                    asyncio.create_task(self._reset_period_cooldown())
                
                return False
            return True

    async def _check_speed_limit(self, request_name):
        """Проверяет ограничение по скорости (запросов в секунду)"""
        async with self._speed_lock:
            current_time = time.perf_counter()
            
            # Удаляем запросы старше 1 секунды
            while self._speed_requests and current_time - self._speed_requests[0] > 1:
                self._speed_requests.popleft()
            
            # Добавляем текущий запрос
            self._speed_requests.append(current_time)
            
            # Проверяем превышение лимита
            if len(self._speed_requests) > self.max_requests_per_second:
                if not self._speed_cooldown:
                    self._speed_cooldown = asyncio.Event()
                    error_msg = (f"SpeedLimitExceeded - wait {self.high_load_cooldown} seconds\n"
                               f"Скорость: {len(self._speed_requests)} запросов/сек, "
                               f"максимум разрешено {self.max_requests_per_second}")
                    logger.warning(error_msg)
                    
                    # Запускаем сброс кулдауна
                    asyncio.create_task(self._reset_speed_cooldown())
                
                return False
            
            return True

    async def _reset_period_cooldown(self):
        """Сбрасывает флаги кулдауна для ограничения по количеству"""
        await asyncio.sleep(self.cooldown_after_period)
        async with self._period_lock:
            self._period_requests.clear()
            if self._period_cooldown:
                self._period_cooldown.set()
                self._period_cooldown = None
        logger.info("Period limit cooldown finished")

    async def _reset_speed_cooldown(self):
        """Сбрасывает флаги кулдауна для ограничения по скорости"""
        await asyncio.sleep(self.high_load_cooldown)
        async with self._speed_lock:
            self._speed_requests.clear()
            if self._speed_cooldown:
                self._speed_cooldown.set()
                self._speed_cooldown = None
        logger.info("Speed limit cooldown finished")

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
            
            # Проверяем ограничение по скорости
            speed_allowed = await self._check_speed_limit(request_name)
            if not speed_allowed and self._speed_cooldown:
                await self._speed_cooldown.wait()
                # После ожидания снова проверяем
                speed_allowed = await self._check_speed_limit(request_name)
                if not speed_allowed:
                    # Если все еще не разрешено, ждем окончания кулдауна
                    await self._speed_cooldown.wait()
            
            # Проверяем ограничение по количеству
            period_allowed = await self._check_period_limit(request_name)
            if not period_allowed and self._period_cooldown:
                await self._period_cooldown.wait()
                # После ожидания снова проверяем
                period_allowed = await self._check_period_limit(request_name)
                if not period_allowed:
                    # Если все еще не разрешено, ждем окончания кулдауна
                    await self._period_cooldown.wait()
            
            return await old_call(sender, request, ordered, flood_sleep_threshold)

        # Сохраняем оригинальный метод и заменяем его
        self.bot.client._call = new_call
        self.bot.client._call._api_limiter_installed = True
        logger.info("✅ API protection installed with new limiting logic")
