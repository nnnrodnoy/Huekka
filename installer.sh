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

# Функция для настройки автозапуска через systemd (Ubuntu/Debian)
setup_systemd_service() {
    echo -e "${YELLOW}Setting up systemd service for Ubuntu/Debian...${NC}"
    
    SERVICE_FILE="/etc/systemd/system/huekka.service"
    BOT_DIR=$(pwd)
    
    # Создаем сервисный файл
    sudo tee $SERVICE_FILE > /dev/null <<EOF
[Unit]
Description=Huekka UserBot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$BOT_DIR
ExecStart=$BOT_DIR/start_bot.sh
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

    # Включаем и запускаем сервис
    sudo systemctl daemon-reload
    sudo systemctl enable huekka
    sudo systemctl start huekka
    
    echo -e "${GREEN}Systemd service created and started!${NC}"
}

# Функция для настройки автозапуска через crontab
setup_crontab() {
    echo -e "${YELLOW}Setting up crontab for autostart...${NC}"
    
    BOT_DIR=$(pwd)
    CRON_JOB="@reboot sleep 30 && cd $BOT_DIR && ./start_bot.sh"
    
    # Добавляем задание в crontab
    (crontab -l 2>/dev/null | grep -v "start_bot.sh"; echo "$CRON_JOB") | crontab -
    
    echo -e "${GREEN}Crontab configured!${NC}"
}

# Функция для настройки автозапуска через .bashrc (Termux)
setup_bashrc() {
    echo -e "${YELLOW}Setting up .bashrc for autostart...${NC}"
    
    # Включаем автозапуск через start_bot.sh
    if ! grep -q "cd $(pwd) && ./start_bot.sh" ~/.bashrc; then
        echo -e "\n# Автозапуск Huekka UserBot\ncd $(pwd) && ./start_bot.sh" >> ~/.bashrc
    fi
    
    echo -e "${GREEN}.bashrc configured!${NC}"
}

# Функция для настройки автозапуска
setup_autostart() {
    echo -e "${YELLOW}Setting up autostart...${NC}"
    
    # Даем права на выполнение start_bot.sh
    chmod +x start_bot.sh
    
    # Определяем ОС и настраиваем автозапуск соответствующим образом
    if [ -f /etc/os-release ]; then
        # Это Linux система (скорее всего Ubuntu)
        . /etc/os-release
        if [ "$ID" = "ubuntu" ] || [ "$ID" = "debian" ]; then
            # Для Ubuntu/Debian используем systemd сервис
            setup_systemd_service
        else
            # Для других Linux систем используем crontab
            setup_crontab
        fi
    else
        # Для Termux используем .bashrc
        setup_bashrc
    fi
}

# Основная логика скрипта
main() {
    show_header
    
    echo -e "${GREEN}Starting installation...${NC}"
    echo
    
    # Устанавливаем зависимости
    if install_python_dependencies; then
        # Настраиваем автозапуск
        setup_autostart
        
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
