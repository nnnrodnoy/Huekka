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

# Функция для установки Python зависимостей
install_python_dependencies() {
    echo -e "${YELLOW}Installing Python dependencies...${NC}"
    
    # Проверяем наличие файла requirements.txt
    if [ ! -f "requirements.txt" ]; then
        show_error "requirements.txt not found!"
        return 1
    fi
    
    # Устанавливаем зависимости
    pip install -r requirements.txt
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}All dependencies installed successfully!${NC}"
        return 0
    else
        show_error "Failed to install some dependencies"
        return 1
    fi
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

# Функция для настройки автозапуска
setup_autostart() {
    echo -e "${YELLOW}Setting up autostart...${NC}"
    
    # Даем права на выполнение start_bot.sh
    chmod +x start_bot.sh
    
    # Определяем ОС и настраиваем автозапуск соответствующим образом
    if [ -d "/data/data/com.termux/files/usr" ]; then
        # Это Termux
        setup_bashrc
    elif [ -f /etc/os-release ]; then
        # Это Linux система
        . /etc/os-release
        if [ "$ID" = "ubuntu" ] || [ "$ID" = "debian" ]; then
            # Для Ubuntu/Debian используем systemd сервис
            setup_systemd_service
        else
            # Для других Linux систем используем crontab
            setup_crontab
        fi
    else
        # Для других систем используем crontab
        setup_crontab
    fi
}

# Функция для настройки автозапуска через systemd (Ubuntu/Debian)
setup_systemd_service() {
    echo -e "${YELLOW}Setting up systemd service for Ubuntu/Debian...${NC}"
    
    # Проверяем, есть ли права sudo
    if ! command -v sudo &> /dev/null; then
        echo -e "${YELLOW}sudo not available, using crontab instead${NC}"
        setup_crontab
        return
    fi
    
    SERVICE_FILE="/etc/systemd/system/huekka.service"
    BOT_DIR=$(pwd)
    USER_NAME=$(whoami)
    
    # Создаем сервисный файл
    sudo tee $SERVICE_FILE > /dev/null <<EOF
[Unit]
Description=Huekka UserBot
After=network.target

[Service]
Type=simple
User=$USER_NAME
WorkingDirectory=$BOT_DIR
ExecStart=$BOT_DIR/start_bot.sh
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}Failed to create systemd service, using crontab instead${NC}"
        setup_crontab
        return
    fi

    # Включаем и запускаем сервис
    sudo systemctl daemon-reload
    sudo systemctl enable huekka
    sudo systemctl start huekka
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Systemd service created and started!${NC}"
        echo -e "${YELLOW}To check status: sudo systemctl status huekka${NC}"
        echo -e "${YELLOW}To view logs: sudo journalctl -u huekka -f${NC}"
    else
        echo -e "${YELLOW}Failed to start systemd service, using crontab instead${NC}"
        setup_crontab
    fi
}

# Функция для настройки автозапуска через crontab
setup_crontab() {
    echo -e "${YELLOW}Setting up crontab for autostart...${NC}"
    
    BOT_DIR=$(pwd)
    START_SCRIPT="$BOT_DIR/start_bot.sh"
    CRON_JOB="@reboot sleep 30 && bash '$START_SCRIPT' > '$BOT_DIR/bot.log' 2>&1"
    
    # Добавляем задание в crontab
    (crontab -l 2>/dev/null | grep -v "start_bot.sh"; echo "$CRON_JOB") | crontab -
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Crontab configured!${NC}"
        echo -e "${YELLOW}Bot logs will be saved to: $BOT_DIR/bot.log${NC}"
    else
        echo -e "${RED}Failed to configure crontab${NC}"
    fi
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
    
    # Устанавливаем настройки по умолчанию через Python
    python3 -c "
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
    
    echo -e "${GREEN}Default configuration applied successfully!${NC}"
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
        setup_default_config
        
        # Настраиваем автозапуск
        setup_autostart
        
        # Запускаем бота
        echo -e "${GREEN}Starting bot...${NC}"
        bash start_bot.sh
    else
        show_error "Failed to install dependencies. Please check your internet connection and try again."
        exit 1
    fi
}

# Начало выполнения скрипта
clear
show_header
main
