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
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Функция для отображения заголовка
show_header() {
    clear
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║                  ${CYAN}HUEKKA USERBOT INSTALLER${PURPLE}                  ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
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

# Функция для создания виртуального окружения
setup_virtual_environment() {
    echo -e "${YELLOW}Creating Python virtual environment...${NC}"
    
    # Создаем виртуальное окружение если его нет
    if [ ! -d "Huekka" ]; then
        echo -e "${YELLOW}Setting up virtual environment...${NC}"
        python -m venv Huekka
        if [ $? -ne 0 ]; then
            show_error "Failed to create virtual environment!"
            return 1
        fi
        echo -e "${GREEN}✓ Virtual environment created successfully${NC}"
    else
        echo -e "${GREEN}✓ Virtual environment already exists${NC}"
    fi
    
    echo -e "${YELLOW}Installing dependencies...${NC}"
    source Huekka/bin/activate
    
    # Обновляем pip
    pip install --upgrade pip
    
    # Устанавливаем зависимости в виртуальном окружении
    pip install -r requirements.txt
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ All dependencies installed successfully${NC}"
        deactivate
        return 0
    else
        show_error "Failed to install dependencies"
        deactivate
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
    
    # Проверяем существование виртуального окружения
    if [ ! -d "Huekka" ]; then
        show_error "Virtual environment not found. Please run dependency installation first."
        return 1
    fi
    
    # Активируем виртуальное окружение и устанавливаем настройки
    source Huekka/bin/activate
    
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
    
    deactivate
    
    echo -e "${GREEN}✓ Default configuration applied successfully${NC}"
    return 0
}

# Функция для отображения текущих настроек
show_current_settings() {
    echo -e "${MAGENTA}════════════════════ CURRENT SETTINGS ════════════════════${NC}"
    echo -e "${CYAN}Command Prefix:${NC} ."
    echo -e "${CYAN}Autocleaner:${NC} Enabled (1800s)"
    echo -e "${CYAN}Autostart:${NC} Enabled"
    echo -e "${CYAN}Virtual Environment:${NC} Huekka/"
    echo -e "${CYAN}Log File:${NC} bot.log"
    echo -e "${MAGENTA}══════════════════════════════════════════════════════════${NC}"
    echo
    echo -e "${YELLOW}Please review these settings. Press ENTER to continue...${NC}"
    read -n 1
}

# Основная логика скрипта
main() {
    show_header
    
    echo -e "${GREEN}Starting installation process...${NC}"
    echo
    
    # Создаем виртуальное окружение и устанавливаем зависимости
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
