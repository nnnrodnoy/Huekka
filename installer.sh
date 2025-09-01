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
    echo "Press any key to continue..."
    read -n 1
}

# Функция для создания виртуального окружения
setup_virtual_environment() {
    echo -e "${YELLOW}Setting up virtual environment...${NC}"
    
    # Создаем виртуальное окружение если его нет
    if [ ! -d "Huekka" ]; then
        echo -e "${YELLOW}Creating virtual environment...${NC}"
        python -m venv Huekka
        if [ $? -ne 0 ]; then
            show_error "Failed to create virtual environment!"
            return 1
        fi
    fi
    
    echo -e "${YELLOW}Installing dependencies in virtual environment...${NC}"
    source Huekka/bin/activate
    
    # Обновляем pip
    pip install --upgrade pip
    
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

# Функция для настройки автозапуска через .bashrc (Termux)
setup_autostart() {
    echo -e "${YELLOW}Setting up autostart for Termux...${NC}"
    
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
        echo -e "\n# Автозапуск Huekka UserBot\ncd $BOT_DIR && bash start_bot.sh > bot.log 2>&1" >> ~/.bashrc
    fi
    
    echo -e "${GREEN}.bashrc configured!${NC}"
    echo -e "${YELLOW}Bot logs will be saved to: $BOT_DIR/bot.log${NC}"
}

# Функция для установки настроек по умолчанию
setup_default_config() {
    echo -e "${YELLOW}Setting up default configuration...${NC}"
    
    # Создаем папку cash если её нет
    mkdir -p cash
    
    # Проверяем существование виртуального окружения
    if [ ! -d "Huekka" ]; then
        show_error "Виртуальное окружение не найдено. Сначала запустите установку зависимостей."
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
    
    echo -e "${GREEN}Default configuration applied successfully!${NC}"
    return 0
}

# Основная логика скрипта
main() {
    show_header
    
    echo -e "${GREEN}Starting installation...${NC}"
    echo -e "${CYAN}Settings:${NC}"
    echo "- Prefix: '.'"
    echo "- Autocleaner: Enabled (1800s)"
    echo "- Autostart: Enabled"
    echo
    
    # Создаем виртуальное окружение и устанавливаем зависимости
    if setup_virtual_environment; then
        # Настраиваем параметры по умолчанию
        if setup_default_config; then
            # Настраиваем автозапуск
            setup_autostart
            
            # Запускаем бота
            echo -e "${GREEN}Starting bot...${NC}"
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
clear
show_header
main
