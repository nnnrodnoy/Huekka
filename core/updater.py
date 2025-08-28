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
from pathlib import Path
from config import BotConfig

class Updater:
    def __init__(self, bot):
        self.bot = bot
        self.repo_url = BotConfig.UPDATER["repo_url"]
        self.exclude_dirs = ['modules', 'session', 'cash', 'logs']
        self.update_files = ['config.py']
        self.update_dirs = ['asset', 'arts', 'core']
    
    async def check_update(self):
        """Проверяет наличие обновлений в репозитории"""
        try:
            temp_dir = tempfile.mkdtemp(prefix="huekka_update_")
            
            subprocess.run(['git', 'clone', self.repo_url, temp_dir], 
                         check=True, capture_output=True)
            
            current_commit = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                cwd=os.getcwd(),
                capture_output=True,
                text=True
            ).stdout.strip() if os.path.exists('.git') else None
            
            latest_commit = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                cwd=temp_dir,
                capture_output=True,
                text=True
            ).stdout.strip()
            
            shutil.rmtree(temp_dir)
            
            if current_commit and current_commit != latest_commit:
                return latest_commit
                
            return None
            
        except Exception as e:
            return None

    async def perform_update(self):
        try:
            temp_dir = tempfile.mkdtemp(prefix="huekka_update_")
            current_dir = os.getcwd()
            
            subprocess.run(['git', 'clone', self.repo_url, temp_dir], 
                         check=True, capture_output=True)
            
            # Обновляем файлы
            for file in self.update_files:
                repo_file = os.path.join(temp_dir, file)
                local_file = os.path.join(current_dir, file)
                
                if os.path.exists(repo_file):
                    if os.path.exists(local_file):
                        os.remove(local_file)
                    shutil.copy2(repo_file, local_file)
            
            # Обновляем папки
            for dir_name in self.update_dirs:
                repo_dir = os.path.join(temp_dir, dir_name)
                local_dir = os.path.join(current_dir, dir_name)
                
                if os.path.exists(repo_dir):
                    if os.path.exists(local_dir):
                        shutil.rmtree(local_dir)
                    shutil.copytree(repo_dir, local_dir)
            
            shutil.rmtree(temp_dir)
            
            return True
            
        except Exception as e:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
            return False

async def setup(bot):
    """Настройка модуля обновления"""
    updater = Updater(bot)
    
    @bot.register_command("update", update_handler, "Проверить обновления", "Updater")
    @bot.register_command("upcheck", upcheck_handler, "Проверить обновления", "Updater")
    
    async def update_handler(event):
        """Обработчик команды update"""
        try:
            latest_commit = await updater.check_update()
            if latest_commit:
                await event.edit("‼️ Доступно обновление! Используйте `/upgrade` для установки")
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
            msg = await event.edit("🔄 Проверка обновлений...")
            latest_commit = await updater.check_update()
            
            if not latest_commit:
                await msg.edit("✅ У вас актуальная версия бота")
                return
            
            await msg.edit("‼️ Обновление обнаружено! Начинаю процесс обновления...")
            
            success = await updater.perform_update()
            
            if success:
                await msg.edit("✅ Обновление успешно установлено! Перезагрузка...")
                bot.add_post_restart_action(lambda: None)
                await bot.restart()
            else:
                await msg.edit("⚠️ Ошибка при установке обновления")
                
        except Exception as e:
            await event.edit(f"⚠️ Ошибка обновления: {str(e)}")
