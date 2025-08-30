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
NC='\033[0m' # No Color

# Функция для отображения заголовка
show_header() {
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════╗"
    echo "║                 HUEKKA USERBOT INSTALLER            ║"
    echo "╚══════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Функция для отображения ошибки
show_error() {
    echo -e "${RED}Error: $1${NC}"
    exit 1
}

# Функция для создания виртуального окружения
setup_virtual_environment() {
    echo -e "${YELLOW}Setting up virtual environment...${NC}"
    
    # Создаем виртуальное окружение если его нет
    if [ ! -d "Huekka" ]; then
        echo -e "${YELLOW}Creating virtual environment...${NC}"
        python3 -m venv Huekka
        if [ $? -ne 0 ]; then
            show_error "Failed to create virtual environment!"
            return 1
        fi
    fi
    
    echo -e "${YELLOW}Installing dependencies in virtual environment...${NC}"
    source Huekka/bin/activate
    
    # Устанавливаем зависимости в виртуальном окружении
    pip install -r requirements.txt
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}All dependencies installed successfully in virtual environment!${NC}"
        deactivate
        return 0
    else
        show_error "Failed to install some dependencies in virtual environment"
        deactivate
        return 1
    fi
}

# Функция для настройки окружения
setup_environment() {
    echo -e "${YELLOW}Setting up environment...${NC}"
    
    # Создаем необходимые папки
    mkdir -p cash
    mkdir -p session
    
    # Даем права на выполнение скриптов
    chmod +x start_bot.sh
    
    # Создаем базу данных конфигурации
    python3 -c "
import sqlite3
conn = sqlite3.connect('cash/config.db')
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
"
    
    echo -e "${GREEN}Environment setup completed!${NC}"
}

# Основная логика скрипта
main() {
    show_header
    
    echo -e "${GREEN}Starting installation...${NC}"
    echo
    
    # Создаем виртуальное окружение и устанавливаем зависимости
    if setup_virtual_environment; then
        # Настраиваем окружение
        setup_environment
        
        # Запускаем бота
        echo -e "${GREEN}Starting bot...${NC}"
        ./start_bot.sh
    else
        show_error "Failed to install dependencies. Please check your internet connection and try again."
        exit 1
    fi
}

# Начало выполнения скрипта
clear
show_header
main
