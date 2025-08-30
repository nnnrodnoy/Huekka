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

# Функция для установки Python зависимостей
install_python_dependencies() {
    echo -e "${YELLOW}Checking virtual environment...${NC}"
    
    # Создаем виртуальное окружение если его нет
    if [ ! -d "Huekka" ]; then
        echo -e "${YELLOW}Creating virtual environment...${NC}"
        python3 -m venv Huekka
        if [ $? -ne 0 ]; then
            show_error "Failed to create virtual environment!"
            return 1
        fi
    fi
    
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source Huekka/bin/activate
    
    echo -e "${YELLOW}Installing Python dependencies...${NC}"
    
    # Проверяем наличие файла requirements.txt
    if [ ! -f "requirements.txt" ]; then
        show_error "requirements.txt not found!"
        deactivate
        return 1
    fi
    
    # Устанавливаем зависимости
    pip install -r requirements.txt
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}All dependencies installed successfully!${NC}"
        deactivate
        return 0
    else
        show_error "Failed to install some dependencies"
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
    
    echo -e "${GREEN}Environment setup completed!${NC}"
}

# Основная логика скрипта
main() {
    show_header
    
    echo -e "${GREEN}Starting installation...${NC}"
    echo
    
    # Устанавливаем зависимости
    if install_python_dependencies; then
        # Настраиваем окружение
        setup_environment
        
        echo -e "${GREEN}Installation completed successfully!${NC}"
        echo -e "${CYAN}To start the bot, run: ./start_bot.sh${NC}"
        echo -e "${YELLOW}Note: On first run, you will need to enter your API credentials.${NC}"
    else
        show_error "Failed to install dependencies. Please check your internet connection and try again."
        exit 1
    fi
}

# Начало выполнения скрипта
clear
show_header
main
