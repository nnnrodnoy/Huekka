#!/bin/bash
# ©️ nnnrodnoy, 2025
# 💬 @nnnrodnoy
# This file is part of Huekka
# 🌐 https://github.com/stepka5/Huekka
# You can redistribute it and/or modify it under the terms of the MIT License
# 🔑 https://opensource.org/licenses/MIT

PURPLE='\033[0;35m'
CYAN='\033[0;36m'
GREEN='\033[0;32m'
BOLD_GREEN='\033[1;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Функция для отображения заголовка
show_header() {
    clear
    echo -e "${BOLD_GREEN}"
    echo "  _____              _           _  _ "
    echo " |_   _|            | |         | || | "
    echo "   | |   _ __   ___ | |_   __ _ | || |  ___  _ __ "
    echo "   | |  | '_ \ / __|| __| / _\` || || | / _ \| '__| "
    echo "  _| |_ | | | |\__ \| |_ | (_| || || ||  __/| | "
    echo " |_____||_| |_||___/ \__| \__,_||_||_| \___||_| "
    echo -e "${NC}"
    echo -e "${BLUE}           Telegram: @BotHuekka | GitHub: nnnrodnoy${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
    echo
}

# Функция для отображения ошибки
show_error() {
    echo -e "${RED}✗ Error: $1${NC}"
    echo "Press any key to continue..."
    read -n 1
}

# Функция для создания виртуального окружения в Termux
setup_virtual_environment() {
    echo -e "${YELLOW}Setting up Python environment for Termux...${NC}"
    
    # В Termux используем pip без виртуального окружения
    # Устанавливаем зависимости глобально
    echo -e "${YELLOW}Installing dependencies...${NC}"
    
    # В Termux не обновляем pip, так как это запрещено
    # Устанавливаем зависимости
    pip install -r requirements.txt
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ All dependencies installed successfully${NC}"
        return 0
    else
        show_error "Failed to install dependencies"
        return 1
    fi
}

# Функция для настройки автозапуска через .bashrc (Termux)
setup_autostart() {
    echo -e "${YELLOW}Configuring autostart for Termux...${NC}"
    
    # Даем права на выполнение start_bot.sh
    chmod +x start_bot.sh
    
    # Настраиваем автозапуск через .bashrc
    setup_bashrc
}

# Функция для настройки автозапуска через .bashrc (Termux)
setup_bashrc() {
    echo -e "${YELLOW}Setting up .bashrc for autostart...${NC}"
    
    BOT_DIR=$(pwd)
    
    # Создаем .bashrc, если его нет
    if [ ! -f ~/.bashrc ]; then
        touch ~/.bashrc
        echo -e "${GREEN}✓ Created .bashrc file${NC}
    fi
    
    # Включаем автозапуск через start_bot.sh
    if ! grep -q "cd $BOT_DIR && bash start_bot.sh" ~/.bashrc; then
        echo -e "\n# Huekka UserBot Autostart\ncd $BOT_DIR && bash start_bot.sh > bot.log 2>&1" >> ~/.bashrc
        echo -e "${GREEN}✓ Autostart configured in .bashrc${NC}"
    else
        echo -e "${GREEN}✓ Autostart already configured${NC}"
    fi
    
    echo -e "${YELLOW}Bot logs will be saved to: $BOT_DIR/bot.log${NC}"
}

# Функция для установки настроек по умолчанию
setup_default_config() {
    echo -e "${YELLOW}Applying default configuration...${NC}"
    
    # Создаем папку cash если её нет
    mkdir -p cash
    
    # Устанавливаем настройки по умолчанию через Python
    python -c "
import sqlite3
import os

db_path = 'cash/config.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS global_config (
             key TEXT PRIMARY KEY,
             value TEXT)''')
# Устанавливаем префикс по умолчанию
c.execute(\"INSERT OR REPLACE INTO global_config (key, value) VALUES ('command_prefix', '.')\")
# Включаем автоклинер
c.execute(\"INSERT OR REPLACE INTO global_config (key, value) VALUES ('autoclean_enabled', 'True')\")
# Устанавливаем время автоклинера
c.execute(\"INSERT OR REPLACE INTO global_config (key, value) VALUES ('autoclean_delay', '1800')\")
conn.commit()
conn.close()
print('Database configuration completed successfully')
"
    
    echo -e "${GREEN}✓ Default configuration applied successfully${NC}"
    return 0
}

# Функция для отображения текущих настроек
show_current_settings() {
    echo -e "${MAGENTA}════════════════════ CURRENT SETTINGS ════════════════════${NC}"
    echo -e "${CYAN}Command Prefix:${NC} ."
    echo -e "${CYAN}Autocleaner:${NC} Enabled (1800s)"
    echo -e "${CYAN}Autostart:${NC} Enabled"
    echo -e "${CYAN}Environment:${NC} Termux (global packages)"
    echo -e "${CYAN}Log File:${NC} bot.log"
    echo -e "${MAGENTA}══════════════════════════════════════════════════════════${NC}"
    echo
    echo -e "${YELLOW}Please review these settings. Press ENTER to continue...${NC}"
    read -n 1
}

# Проверяем зависимости
check_dependencies() {
    echo -e "${YELLOW}Checking dependencies...${NC}"
    
    # Проверяем наличие Python
    if ! command -v python &> /dev/null; then
        echo -e "${RED}Python is not installed. Please install Python in Termux.${NC}"
        exit 1
    fi
    
    # Проверяем наличие pip
    if ! command -v pip &> /dev/null; then
        echo -e "${RED}pip is not installed. Please install pip in Termux.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ All required dependencies are available${NC}"
}

# Основная логика скрипта
main() {
    show_header
    
    echo -e "${GREEN}Starting installation process...${NC}"
    echo
    
    # Проверяем зависимости
    check_dependencies
    
    # Устанавливаем зависимости
    if setup_virtual_environment; then
        # Настраиваем параметры по умолчанию
        if setup_default_config; then
            # Настраиваем автозапуск
            setup_autostart
            
            # Показываем текущие настройки
            show_current_settings
            
            # Запускаем бота
            echo -e "${GREEN}Starting Huekka UserBot...${NC}"
            echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
            bash start_bot.sh
        else
            show_error "Failed to setup default config"
            exit 1
        fi
    else
        show_error "Failed to install dependencies. Please check your internet connection and try again."
        exit 1
    fi
}

# Начало выполнения скрипта
main
