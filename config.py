# ©️ nnnrodnoy, 2025
# 💬 @nnnrodnoy
# This file is part of Huekka
# 🌐 https://github.com/stepka5/Huekka
# You can redistribute it and/or modify it under the terms of the MIT License
# 🔑 https://opensource.org/licenses/MIT
class BotConfig:
    COMMAND_PREFIX = "."  
    OWNER_ID = 0          
    LOG_LEVEL = "INFO"   
    VERSION = "1.1.0"     
    GITHUB_URL = "https://github.com/stepka5/Huekka"
    
    CORE_MODULES = ["Help", "System", "Loader", "Updater", "Configurator", 
                    "AutoCleaner", "LimiterTest", "Database"]
    
    STOCK_MODULES = ["Help", "System", "Loader", "Updater", "Configurator", 
                     "AutoCleaner", "Database"]
    
    # Настройки APILimiter
    API_LIMITER = {
        "time_sample": 60,   
        "threshold": 90,         
        "local_floodwait": 60,  
        "monitored_groups": [  
            "account", "auth", "bots", "channels", "contacts", "folders", 
            "help", "langpack", "messages", "payments", "phone", "photos", 
            "stickers", "updates", "upload", "users", "stats", "invites",
            "messages", "updates", "photos", "help", "channels", "phone",
            "langpack", "folders", "stats", "bots", "stickers", "payments"
        ],
        "forbidden_methods": [   
            "channels.joinChannel", "messages.importChatInvite",
            "contacts.addContact", "account.deleteAccount",
            "channels.deleteChannel", "messages.sendInlineBotResult"
        ]
    }
    
    LOADER = {
        "min_animation_time": 2.0,   
        "delete_delay": 50             
    }
    
    UPDATER = {
        "repo_url": "https://github.com/stepka5/Huekka",
        "system_files": [      
            "main.py",
            "userbot.py",
            "core/parser.py",
            "core/__init__.py"
        ],
        "min_display_time": 2.0 
    }
    
    AUTOCLEAN = {
        "enabled": True,        
        "default_delay": 1800,  
        "tracked_commands": [   
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
    
    EMOJI_IDS = {
        "loader": 4904936030232117798,   
        "loaded": 5422360919453756368,    
        "command": 5251481573953405172,  
        "dev": 5233732265120394046,      
        "info": 5251522431977291010,      
        "total": 5422360919453756368,    
        "section": 5377520790868603876,  
        "stock": 5251522431977291010,    
        "custom": 5251481573953405172,   
        "restart": 4904936030232117798,   
        "clock": 5422360919453756368,    
        "eye": 5377520790868603876,      
        "warn": 5422360919453756368,     
        "check": 5377520790868603876     
    }
    
    DEFAULT_SMILES = [
        "╰(^∇^)╯", "(〜￣▽￣)〜", "٩(◕‿◕｡)۶", "ヾ(＾-＾)ノ", 
        "ʕ•́ᴥ•̀ʔっ", "(◠‿◠✿)", "(◕ω◕✿)", "(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧", 
        "♡(˃͈ દ ˂͈ ༶ )", "ヽ(♡‿♡)ノ"
    ]
    
    SYSTEM = {
        "info_file": "core/information.txt"  # Файл с информацией о боте
    }
    
    PARSER = {
        "max_message_length": 4096  # Максимальная длина сообщения
    }
