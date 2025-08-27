# ©️ nnnrodnoy, 2025
# 💬 @nnnrodnoy
# This file is part of Huekka
# 🌐 https://github.com/nnnrodnoy/Huekka/
# You can redistribute it and/or modify it under the terms of the MIT License
# 🔑 https://opensource.org/licenses/MIT
class BotConfig:
    # Основные настройки бота
    COMMAND_PREFIX = "."
    OWNER_ID = 0
    LOG_LEVEL = "INFO"
    VERSION = "1.1.0"
    
    # Список основных модулей ядра
    CORE_MODULES = ["Help", "System", "Loader", "Updater", "Configurator"]
    
    # Настройки загрузчика модулей
    LOADER = {
        "min_animation_time": 2.0,
        "delete_delay": 50
    }
    
    # ID эмодзи для различных статусов
    EMOJI_IDS = {
        "loader": 4904936030232117798,
        "loaded": 5422360919453756368,
        "command": 5251481573953405172,
        "dev": 5233732265120394046,
        "info": 5251522431977291010
    }
    
    # Смайлики по умолчанию
    DEFAULT_SMILES = [
        "╰(^∇^)╯", "(〜￣▽￣)〜", "٩(◕‿◕｡)۶"
    ]
    
    # Маппинг импортов на имена пакетов pip
    PACKAGE_MAPPING = {
        'PIL': 'pillow',
        'cv2': 'opencv-python',
        'yaml': 'pyyaml',
        'bs4': 'beautifulsoup4',
        'mysql': 'mysql-connector-python'
    }
