# ©️ nnnrodnoy, 2025
# 💬 @nnnrodnoy
# This file is part of Huekka
# 🌐 https://github.com/nnnrodnoy/Huekka/
# You can redistribute it and/or modify it under the terms of the MIT License
# 🔑 https://opensource.org/licenses/MIT
import os
import sys
import subprocess
import importlib
import logging
import asyncio
from typing import List, Tuple
from config import BotConfig

logger = logging.getLogger("UserBot.DependencyInstaller")

class DependencyInstaller:
    def __init__(self):
        self.standard_libs = self.get_standard_libraries()
        self.package_mapping = BotConfig.PACKAGE_MAPPING
    
    def get_standard_libraries(self):
        """Получаем список стандартных библиотек Python"""
        try:
            if hasattr(sys, 'stdlib_module_names'):
                return sys.stdlib_module_names
            else:
                import distutils.sysconfig
                standard_lib_path = distutils.sysconfig.get_python_lib(standard_lib=True)
                standard_modules = set()
                
                for name in os.listdir(standard_lib_path):
                    if name.endswith('.py'):
                        standard_modules.add(name[:-3])
                    elif os.path.isdir(os.path.join(standard_lib_path, name)) and not name.startswith('_'):
                        standard_modules.add(name)
                
                return standard_modules
        except Exception as e:
            logger.error(f"Ошибка получения стандартных библиотек: {str(e)}")
            return set()
    
    def extract_imports(self, file_path: str):
        """Извлекает все импорты из файла Python"""
        imports = set()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            import re
            
            import_pattern = r'^\s*import\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\s*,\s*[a-zA-Z_][a-zA-Z0-9_]*)*)'
            from_pattern = r'^\s*from\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)\s+import'
            
            for line in content.split('\n'):
                if line.strip().startswith('#'):
                    continue
                
                import_match = re.match(import_pattern, line)
                if import_match:
                    modules = import_match.group(1).split(',')
                    for module in modules:
                        module_name = module.strip().split('.')[0]
                        if module_name and module_name not in self.standard_libs:
                            imports.add(module_name)
                
                from_match = re.match(from_pattern, line)
                if from_match:
                    module_name = from_match.group(1).split('.')[0]
                    if module_name and module_name not in self.standard_libs:
                        imports.add(module_name)
        
        except Exception as e:
            logger.error(f"Ошибка извлечения импортов из {file_path}: {str(e)}")
        
        return imports
    
    def is_package_installed(self, package_name: str) -> bool:
        """Проверяет, установлен ли пакет"""
        try:
            spec = importlib.util.find_spec(package_name)
            return spec is not None
        except Exception:
            return False
    
    def get_pip_package_name(self, import_name: str) -> str:
        """Получает имя пакета в pip для импорта"""
        return self.package_mapping.get(import_name, import_name)
    
    async def install_dependencies(self, file_path: str) -> Tuple[List[str], List[str]]:
        """
        Устанавливает зависимости для модуля
        Возвращает кортеж (установленные_пакеты, ошибки)
        """
        imports = self.extract_imports(file_path)
        installed = []
        errors = []
        
        # Проверяем, есть ли зависимости для установки
        needs_installation = False
        for import_name in imports:
            if import_name not in self.standard_libs and not self.is_package_installed(import_name):
                needs_installation = True
                break
        
        if not needs_installation:
            return installed, errors  # Пустые списки - зависимости не требуются
        
        for import_name in imports:
            if import_name in self.standard_libs or self.is_package_installed(import_name):
                continue
            
            package_name = self.get_pip_package_name(import_name)
            
            try:
                process = await asyncio.create_subprocess_exec(
                    sys.executable, '-m', 'pip', 'install', package_name,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )

                stdout, stderr = await process.communicate()
                
                if process.returncode == 0:
                    installed.append(package_name)
                    logger.info(f"Установлен пакет: {package_name}")
                else:
                    error_msg = stderr.decode().strip() if stderr else "Неизвестная ошибка"
                    errors.append(f"{package_name}: {error_msg}")
                    logger.error(f"Ошибка установки {package_name}: {error_msg}")
            
            except Exception as e:
                error_msg = f"{package_name}: {str(e)}"
                errors.append(error_msg)
                logger.error(f"Исключение при установке {package_name}: {str(e)}")
        
        return installed, errors

dependency_installer = DependencyInstaller()

async def install_module_dependencies(file_path: str) -> Tuple[List[str], List[str]]:
    return await dependency_installer.install_dependencies(file_path)

def setup(bot):
    bot.dependency_installer = dependency_installer
    logger.info("Dependency Installer инициализирован")
