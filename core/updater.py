# ©️ nnnrodnoy, 2025
# 💬 @nnnrodnoyiiiii
# This file is part of Hueka
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
import hashlib
import logging
import requests
import zipfile
from pathlib import Path
from config import BotConfig

logger = logging.getLogger("UserBot.Updater")

# Цвета для красивого вывода
class UpdateColors:
    GREEN_BOLD = '\033[1;92m'  # Жирный зеленый цвет
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'

class GitHubUpdater:
    def __init__(self, bot=None):
        self.bot = bot
        self.repo_url = BotConfig.UPDATER["repo_url"]
        self.update_files = BotConfig.UPDATER["system_files"]
        self.update_dirs = ['asset', 'arts', 'core']
        self.last_update_file = Path("data") / "last_update.txt"
        self.last_update_file.parent.mkdir(exist_ok=True)
        
        # Папки и файлы, которые нужно игнорировать при обновлении
        self.ignore_dirs = {'session', 'logs', 'data', 'modules'}
        self.ignore_files = {'config.db'}
    
    def _print_update_status(self, message):
        """Красивый вывод статуса обновления"""
        print(f"{UpdateColors.GREEN_BOLD}[Huekka Update]{UpdateColors.ENDC} {message}")
    
    def _get_file_hash(self, file_path):
        """Вычисляет хэш файла для сравнения"""
        if not file_path.exists():
            return None
        
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            while True:
                data = f.read(65536)  # 64kb chunks
                if not data:
                    break
                hasher.update(data)
        return hasher.hexdigest()
    
    def _should_ignore(self, file_path):
        """Проверяет, нужно ли игнорировать файл/папку"""
        path_str = str(file_path)
        
        # Проверяем игнорируемые папки
        for ignore_dir in self.ignore_dirs:
            if ignore_dir in path_str.split(os.sep):
                return True
                
        # Проверяем игнорируемые файлы
        if file_path.name in self.ignore_files:
            return True
            
        return False
    
    async def get_latest_commit_info(self):
        """Получает информацию о последнем коммите из репозитория"""
        try:
            # Альтернативный способ получения информации о репозитории
            result = subprocess.run([
                'git', 'ls-remote', '--heads', self.repo_url
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                # Получаем хэш последнего коммита
                lines = result.stdout.strip().split('\n')
                if lines and lines[0]:
                    latest_commit_hash = lines[0].split()[0]
                    return latest_commit_hash
        except Exception as e:
            logger.error(f"Ошибка получения информации о коммите: {str(e)}")
        
        return None
    
    async def get_local_last_update(self):
        """Получает дату последнего обновления из файла"""
        if self.last_update_file.exists():
            try:
                with open(self.last_update_file, 'r') as f:
                    content = f.read().strip()
                    if content:
                        return content
            except:
                pass
        return ""
    
    async def set_local_last_update(self, commit_hash):
        """Устанавливает хэш коммита как дату последнего обновления"""
        try:
            with open(self.last_update_file, 'w') as f:
                f.write(commit_hash)
            return True
        except Exception as e:
            logger.error(f"Ошибка записи даты обновления: {str(e)}")
            return False
    
    async def check_for_updates(self):
        """Проверяет наличие обновлений"""
        try:
            # Получаем хэш последнего коммита
            latest_commit = await self.get_latest_commit_info()
            if not latest_commit:
                return False
            
            # Получаем хэш последнего локального обновления
            local_commit = await self.get_local_last_update()
            
            # Если коммиты разные, есть обновление
            return latest_commit != local_commit
            
        except Exception as e:
            logger.error(f"Ошибка проверки обновлений: {str(e)}")
            return False
    
    async def get_repo_file_list(self, extracted_dir):
        """Получает список всех файлов в репозитории"""
        repo_files = set()
        
        # Добавляем файлы из update_files
        for file in self.update_files:
            repo_file = extracted_dir / file
            if repo_file.exists():
                repo_files.add(str(file))
        
        # Добавляем файлы из update_dirs
        for dir_name in self.update_dirs:
            repo_dir = extracted_dir / dir_name
            if repo_dir.exists():
                for root, _, files in os.walk(repo_dir):
                    for file in files:
                        repo_file_path = Path(root) / file
                        relative_path = str(repo_file_path.relative_to(extracted_dir))
                        repo_files.add(relative_path)
        
        return repo_files
    
    async def remove_deleted_files(self, extracted_dir, repo_files):
        """Удаляет файлы, которые были удалены в репозитории, кроме игнорируемых"""
        removed_count = 0
        
        # Проверяем файлы из update_files
        for file in self.update_files:
            local_file = Path(file)
            repo_file = extracted_dir / file
            
            if local_file.exists() and not repo_file.exists() and not self._should_ignore(local_file):
                local_file.unlink()
                self._print_update_status(f"Removed: {file}")
                removed_count += 1
        
        # Проверяем файлы из update_dirs
        for dir_name in self.update_dirs:
            local_dir = Path(dir_name)
            repo_dir = extracted_dir / dir_name
            
            if local_dir.exists():
                for root, _, files in os.walk(local_dir):
                    for file in files:
                        local_file_path = Path(root) / file
                        relative_path = str(local_file_path.relative_to(local_dir.parent))
                        
                        # Если файл не существует в репозитории и не в списке игнорируемых
                        if (relative_path not in repo_files and 
                            not self._should_ignore(local_file_path)):
                            local_file_path.unlink()
                            self._print_update_status(f"Removed: {relative_path}")
                            removed_count += 1
        
        return removed_count
    
    async def perform_update(self):
        """Выполняет полное обновление с проверкой всех файлов"""
        temp_dir = tempfile.mkdtemp(prefix="huekka_update_")
        updated_files = 0
        removed_files = 0
        
        try:
            # Получаем хэш последнего коммита перед обновлением
            latest_commit = await self.get_latest_commit_info()
            if not latest_commit:
                return False
            
            # Скачиваем архив с репозиторием
            zip_url = f"{self.repo_url}/archive/refs/heads/main.zip"
            zip_path = Path(temp_dir) / "huekka.zip"
            
            response = requests.get(zip_url, timeout=60)
            if response.status_code != 200:
                return False
            
            with open(zip_path, 'wb') as f:
                f.write(response.content)
            
            # Распаковываем архив
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            extracted_dir = Path(temp_dir) / "Huekka-main"
            
            # Получаем список всех файлов в репозитории
            repo_files = await self.get_repo_file_list(extracted_dir)
            
            # Удаляем файлы, которых нет в репозитории (кроме игнорируемых)
            removed_files = await self.remove_deleted_files(extracted_dir, repo_files)
            
            # Обновляем файлы только если они изменились и не в списке игнорируемых
            for file in self.update_files:
                repo_file = extracted_dir / file
                local_file = Path(file)
                
                if repo_file.exists() and not self._should_ignore(local_file):
                    # Создаем директорию, если её нет
                    local_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Проверяем, изменился ли файл
                    repo_hash = self._get_file_hash(repo_file)
                    local_hash = self._get_file_hash(local_file)
                    
                    if repo_hash != local_hash:
                        # Копируем файл только если он изменился
                        shutil.copy2(repo_file, local_file)
                        self._print_update_status(f"Updated: {file}")
                        updated_files += 1
                    else:
                        logger.info(f"File unchanged: {file}")
            
            # Обновляем папки с проверкой изменений
            for dir_name in self.update_dirs:
                repo_dir = extracted_dir / dir_name
                local_dir = Path(dir_name)
                
                if repo_dir.exists():
                    # Рекурсивно обходим все файлы в директории
                    for root, _, files in os.walk(repo_dir):
                        for file in files:
                            repo_file_path = Path(root) / file
                            relative_path = repo_file_path.relative_to(repo_dir)
                            local_file_path = local_dir / relative_path
                            
                            # Пропускаем игнорируемые файлы
                            if self._should_ignore(local_file_path):
                                continue
                                
                            # Проверяем, изменился ли файл
                            repo_hash = self._get_file_hash(repo_file_path)
                            local_hash = self._get_file_hash(local_file_path)
                            
                            if repo_hash != local_hash:
                                # Создаем директорию, если её нет
                                local_file_path.parent.mkdir(parents=True, exist_ok=True)
                                
                                # Копируем файл только если он изменился
                                shutil.copy2(repo_file_path, local_file_path)
                                self._print_update_status(f"Updated: {local_file_path}")
                                updated_files += 1
                            else:
                                logger.info(f"File unchanged: {local_file_path}")
            
            if updated_files > 0 or removed_files > 0:
                # Сохраняем хэш коммита как дату последнего обновления
                await self.set_local_last_update(latest_commit)
                self._print_update_status(f"Updated {updated_files} files, removed {removed_files} files")
                return True
            else:
                self._print_update_status("No files need updating")
                return False
            
        except Exception as e:
            logger.error(f"Ошибка выполнения обновления: {str(e)}")
            return False
        finally:
            # Очищаем временные файлы
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    async def auto_update(self):
        """Автоматическая проверка и установка обновлений"""
        try:
            self._print_update_status("Checking for updates...")
            has_update = await self.check_for_updates()
            
            if has_update:
                self._print_update_status("Updates found, installing...")
                success = await self.perform_update()
                
                if success:
                    self._print_update_status("Update successfully installed")
                    return True
                else:
                    self._print_update_status("Error installing update")
            else:
                self._print_update_status("No updates available")
            
            return False
            
        except Exception as e:
            logger.error(f"Ошибка автоматического обновления: {str(e)}")
            return False

# Для использования в main.py
async def check_and_update():
    """Функция для автоматической проверки обновлений при запуске"""
    updater = GitHubUpdater()
    
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
