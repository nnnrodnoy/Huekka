# ©️ nnnrodnoy, 2025
# 💬 @nnnrodnoy
# This file is part of Huekka
# 🌐 https://github.com/nnnrodnoy/Huekka/
# You can redistribute it and/or modify it under the terms of the MIT License
# 🔑 https://opensource.org/licenses/MIT
class BotConfig:
    # Основные настройки бота (статичные)
    OWNER_ID = 0          # ID владельца бота (не изменяется)
    LOG_LEVEL = "INFO"    # Уровень логирования
    VERSION = "1.1.0"     # Версия бота
    GITHUB_URL = "https://github.com/stepka5/Huekka"
    
    # Список основных модулей ядра (статичный)
    CORE_MODULES = ["Help", "System", "Loader", "Updater", "Configurator", 
                    "AutoCleaner", "LimiterTest", "DependencyInstaller"]
    
    # Список стандартных модулей для help (статичный)
    STOCK_MODULES = ["Help", "System", "Loader", "Updater", "Configurator", 
                     "AutoCleaner"]
    
    # Настройки APILimiter (статичные)
    API_LIMITER = {
        "time_sample": 60,       # 60-секундное окно
        "threshold": 90,         # 90 запросов в минуту (оптимально)
        "local_floodwait": 60,   # 30-секундная блокировка
        "monitored_groups": [    # Группы методов для мониторинга
            "account", "auth", "bots", "channels", "contacts", "folders", 
            "help", "langpack", "messages", "payments", "phone", "photos", 
            "stickers", "updates", "upload", "users", "stats", "invites",
            "messages", "updates", "photos", "help", "channels", "phone",
            "langpack", "folders", "stats", "bots", "stickers", "payments"
        ],
        "forbidden_methods": [   # Запрещенные методы
            "channels.joinChannel", "messages.importChatInvite",
            "contacts.addContact", "account.deleteAccount",
            "channels.deleteChannel", "messages.sendInlineBotResult"
        ]
    }
    
    # Настройки загрузчика модулей (статичные)
    LOADER = {
        "min_animation_time": 2.0,    # Минимальное время анимации (сек)
        "delete_delay": 50             # Задержка удаления сообщений (сек)
    }
    
    # Настройки для Updater (статичные)
    UPDATER = {
        "repo_url": "https://github.com/stepka5/Huekka",
        "system_files": [        # Файлы для проверки обновлений
            "main.py",
            "userbot.py",
            "core/parser.py",
            "core/__init__.py"
        ],
        "min_display_time": 2.0  # Минимальное время отображения сообщения
    }
    
    # Настройки для автоочистки (ТОЛЬКО значения по умолчанию)
    AUTOCLEAN = {
        "tracked_commands": [    # Шаблоны команд для автоочистки (статичные)
            r'^{}\s*(ulm|unload)\b',
            r'^{}\s*lm\b',
            r'^{}\s*(help|h|помощь)\b',
            r'^{}\s*(restart|reboot)\b',
            r'^{}\s*(update|upgrade)\b',
            r'^{}\s*(upcheck|checkupdate)\b',
            r'^{}\s*(config|conf|настройки)\b',
            r'^{}\s*config\s+prefix\b'
        ]
    }
    
    # ID эмодзи для различных статусов (статичные)
    EMOJI_IDS = {
        "loader": 4904936030232117798,    # ⚙️
        "loaded": 5422360919453756368,    # 🌘
        "command": 5251481573953405172,   # ▫️
        "dev": 5233732265120394046,       # 🫶
        "info": 5251522431977291010,      # ℹ️
        "total": 5422360919453756368,     # 🕒
        "section": 5377520790868603876,   # 👁️
        "stock": 5251522431977291010,     # ℹ️
        "custom": 5251481573953405172,    # ▫️
        "restart": 4904936030232117798,   # ⚙️
        "clock": 5422360919453756368,     # 🕒
        "eye": 5377520790868603876,       # 👁️
        "warn": 5422360919453756368,      # ⚠️
        "check": 5377520790868603876      # 👁️ (или другой для check)
    }
    
    # Смайлики по умолчанию (статичные)
    DEFAULT_SMILES = [
        "╰(^∇^)╯", "(〜￣▽￣)〜", "٩(◕‿◕｡)۶", "ヾ(＾-＾)ノ", 
        "ʕ•́ᴥ•̀ʔっ", "(◠‿◠✿)", "(◕ω◕✿)", "(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧", 
        "♡(˃͈ દ ˂͈ ༶ )", "ヽ(♡‿♡)ノ"
    ]
    
    # Настройки для System модуля (статичные)
    SYSTEM = {
        "info_file": "core/information.txt"  # Файл с информацией о боте
    }
    
    # Настройки для парсера (статичные)
    PARSER = {
        "max_message_length": 4096  # Максимальная длина сообщения
    }
    
    # Маппинг импортов на имена пакетов pip (статичный)
    PACKAGE_MAPPING = {
        'PIL': 'pillow',
        'cv2': 'opencv-python',
        'yaml': 'pyyaml',
        'bs4': 'beautifulsoup4',
        'mysql': 'mysql-connector-python'
    }
