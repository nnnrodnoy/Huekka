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

# Функция для установки настроек по умолчанию
setup_default_config() {
    echo -e "${YELLOW}Setting up default configuration...${NC}"
    
    # Создаем папку cash если её нет
    mkdir -p cash
    
    # Устанавливаем настройки по умолчанию через Python
    python -c "
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
    
    # Даем права на выполнение start_bot.sh
    chmod +x start_bot.sh
    
    # Включаем автозапуск через start_bot.sh
    if ! grep -q "cd $(pwd) && ./start_bot.sh" ~/.bashrc; then
        echo "cd $(pwd) && ./start_bot.sh" >> ~/.bashrc
    fi
    
    echo -e "${GREEN}Default configuration applied successfully!${NC}"
}

# Основная логика скрипта
main() {
    show_header
    
    echo -e "${GREEN}Starting with default settings...${NC}"
    echo -e "${CYAN}Settings:${NC}"
    echo "- Prefix: '.'"
    echo "- Autocleaner: Enabled (1800s)"
    echo "- Autostart: Yes"
    echo
    
    # Устанавливаем зависимости
    if install_python_dependencies; then
        # Настраиваем параметры по умолчанию
        setup_default_config
        
        # Даем права на выполнение start_bot.sh
        chmod +x start_bot.sh
        
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
