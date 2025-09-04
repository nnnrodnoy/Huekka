# ©️ nnnrodnoy, 2025
# 💬 @nnnrodnoy
# This file is part of Huekka
# 🌐 https://github.com/nnnrodnoy/Huekka/
# You can redistribute it and/or modify it under the terms of the MIT License
# 🔑 https://opensource.org/licenses/MIT
import os
import sys
import shutil
import tempfile
import subprocess
import asyncio
import json
import time
from pathlib import Path
from config import BotConfig

logger = logging.getLogger("UserBot.Updater")

class GitHubUpdater:
    def __init__(self, bot):
        self.bot = bot
        self.repo_url = BotConfig.UPDATER["repo_url"]
        self.update_files = BotConfig.UPDATER["system_files"]
        self.update_dirs = ['asset', 'arts', 'core']
        self.last_update_file = Path("data") / "last_update.txt"
        self.last_update_file.parent.mkdir(exist_ok=True)
    
    async def get_latest_commit_date(self):
        """Получает дату последнего коммита из репозитория"""
        try:
            # Используем GitHub API для получения информации о репозитории
            result = subprocess.run([
                'curl', '-s', 
                f'https://api.github.com/repos/nnnrodnoy/Huekka/commits?per_page=1'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                commits = json.loads(result.stdout)
                if commits and len(commits) > 0:
                    return commits[0]['commit']['committer']['date']
        except Exception as e:
            logger.error(f"Ошибка получения даты коммита: {str(e)}")
        
        return None
    
    async def get_local_last_update(self):
        """Получает дату последнего обновления из файла"""
        if self.last_update_file.exists():
            try:
                with open(self.last_update_file, 'r') as f:
                    return float(f.read().strip())
            except:
                pass
        return 0
    
    async def set_local_last_update(self):
        """Устанавливает текущее время как дату последнего обновления"""
        try:
            with open(self.last_update_file, 'w') as f:
                f.write(str(time.time()))
            return True
        except Exception as e:
            logger.error(f"Ошибка записи даты обновления: {str(e)}")
            return False
    
    async def check_for_updates(self):
        """Проверяет наличие обновлений"""
        try:
            # Получаем дату последнего коммита
            commit_date_str = await self.get_latest_commit_date()
            if not commit_date_str:
                return False
            
            # Конвертируем в timestamp
            from datetime import datetime
            commit_date = datetime.strptime(commit_date_str, '%Y-%m-%dT%H:%M:%SZ')
            commit_timestamp = commit_date.timestamp()
            
            # Получаем дату последнего локального обновления
            local_timestamp = await self.get_local_last_update()
            
            # Если коммит новее нашего последнего обновления
            return commit_timestamp > local_timestamp
            
        except Exception as e:
            logger.error(f"Ошибка проверки обновлений: {str(e)}")
            return False
    
    async def perform_update(self):
        """Выполняет обновление файлов"""
        temp_dir = tempfile.mkdtemp(prefix="huekka_update_")
        
        try:
            # Клонируем репозиторий
            result = subprocess.run([
                'git', 'clone', '--depth', '1', self.repo_url, temp_dir
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                logger.error(f"Ошибка клонирования репозитория: {result.stderr}")
                return False
            
            # Обновляем файлы
            for file in self.update_files:
                repo_file = Path(temp_dir) / file
                local_file = Path(file)
                
                if repo_file.exists():
                    if local_file.exists():
                        local_file.unlink()
                    shutil.copy2(repo_file, local_file)
            
            # Обновляем папки
            for dir_name in self.update_dirs:
                repo_dir = Path(temp_dir) / dir_name
                local_dir = Path(dir_name)
                
                if repo_dir.exists():
                    if local_dir.exists():
                        shutil.rmtree(local_dir)
                    shutil.copytree(repo_dir, local_dir)
            
            # Сохраняем время обновления
            await self.set_local_last_update()
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка выполнения обновления: {str(e)}")
            return False
        finally:
            # Очищаем временные файлы
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    async def auto_update(self):
        """Автоматическая проверка и установка обновлений"""
        try:
            has_update = await self.check_for_updates()
            
            if has_update:
                logger.info("Обнаружены обновления, начинаю установку...")
                success = await self.perform_update()
                
                if success:
                    logger.info("Обновление успешно установлено")
                    return True
                else:
                    logger.error("Ошибка установки обновления")
            
            return False
            
        except Exception as e:
            logger.error(f"Ошибка автоматического обновления: {str(e)}")
            return False

# Для использования в main.py
async def check_and_update():
    """Функция для автоматической проверки обновлений при запуске"""
    updater = GitHubUpdater(None)  # None т.к. бот еще не создан
    
    try:
        # Проверяем и устанавливаем обновления
        needs_restart = await updater.auto_update()
        return needs_restart
    except Exception as e:
        logger.error(f"Ошибка при проверке обновлений: {str(e)}")
        return False

# Для использования в модуле бота
async def setup(bot):
    """Настройка модуля обновления"""
    updater = GitHubUpdater(bot)
    
    @bot.register_command("update", update_handler, "Проверить обновления", "Updater")
    @bot.register_command("upcheck", upcheck_handler, "Проверить обновления", "Updater")
    
    async def update_handler(event):
        """Обработчик команды update"""
        try:
            has_update = await updater.check_for_updates()
            
            if has_update:
                await event.edit("‼️ Доступно обновление! Используйте `.upgrade` для установки")
            else:
                await event.edit("✅ У вас актуальная версия бота")
        except Exception as e:
            await event.edit(f"⚠️ Ошибка проверки обновлений: {str(e)}")
    
    async def upcheck_handler(event):
        """Обработчик команды upcheck (алиас для update)"""
        await update_handler(event)
    
    @bot.register_command("upgrade", upgrade_handler, "Установить обновления", "Updater")
    async def upgrade_handler(event):
        """Обработчик команды upgrade"""
        try:
            msg = await event.edit("🔄 Начинаю процесс обновления...")
            
            success = await updater.perform_update()
            
            if success:
                await msg.edit("✅ Обновление успешно установлено! Перезагрузка...")
                # Добавляем действие после перезагрузки
                bot.add_post_restart_action(lambda: None)
                await asyncio.sleep(2)
                await bot.restart()
            else:
                await msg.edit("⚠️ Ошибка при установке обновления")
                
        except Exception as e:
            await event.edit(f"⚠️ Ошибка обновления: {str(e)}")
