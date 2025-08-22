#!/bin/bash

# Цвета для вывода
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

# Функция для проверки и установки необходимых пакетов
install_required_packages() {
    echo -e "${YELLOW}Checking and installing required system packages...${NC}"
    
    # Проверяем и устанавливаем Python если не установлен
    if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
        echo "Installing Python..."
        pkg install python -y
    fi
    
    # Устанавливаем необходимые системные зависимости
    echo "Installing system dependencies..."
    pkg install clang libffi openssl -y
    
    echo -e "${GREEN}System packages installed successfully!${NC}"
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
    pkg install --upgrade pip
    pip install -r requirements.txt
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}All dependencies installed successfully!${NC}"
        return 0
    else
        show_error "Failed to install some dependencies"
        return 1
    fi
}

# Функция для получения текущего префикса из базы данных
get_current_prefix() {
    db_path="cash/config.db"
    if [ -f "$db_path" ]; then
        python -c "
import sqlite3
conn = sqlite3.connect('$db_path')
c = conn.cursor()
c.execute(\"SELECT value FROM global_config WHERE key='command_prefix'\")
result = c.fetchone()
conn.close()
print(result[0] if result else '.')
"
    else
        # Если базы данных нет, возвращаем значение по умолчанию из config.py
        python -c "
with open('config.py', 'r') as f:
    content = f.read()
import re
match = re.search(r'COMMAND_PREFIX\s*=\s*[\"\\'](.*?)[\"\\']', content)
if match:
    print(match.group(1))
else:
    print('.')
"
    fi
}

# Функция для установки префикса в базу данных
set_prefix_in_db() {
    db_path="cash/config.db"
    new_prefix="$1"
    
    # Создаем папку cash если её нет
    mkdir -p cash
    
    python -c "
import sqlite3
conn = sqlite3.connect('$db_path')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS global_config (
             key TEXT PRIMARY KEY,
             value TEXT)''')
c.execute(\"INSERT OR REPLACE INTO global_config (key, value) VALUES ('command_prefix', ?)\", ('$new_prefix',))
conn.commit()
conn.close()
"
}

# Функция для получения текущего статуса автоклинера
get_current_autoclean_status() {
    db_path="cash/config.db"
    if [ -f "$db_path" ]; then
        python -c "
import sqlite3
conn = sqlite3.connect('$db_path')
c = conn.cursor()
c.execute(\"SELECT value FROM global_config WHERE key='autoclean_enabled'\")
result = c.fetchone()
conn.close()
print(result[0] if result else 'True')
"
    else
        echo "True"
    fi
}

# Функция для получения текущего времени автоклинера
get_current_autoclean_time() {
    db_path="cash/config.db"
    if [ -f "$db_path" ]; then
        python -c "
import sqlite3
conn = sqlite3.connect('$db_path')
c = conn.cursor()
c.execute(\"SELECT value FROM global_config WHERE key='autoclean_delay'\")
result = c.fetchone()
conn.close()
print(result[0] if result else '1800')
"
    else
        echo "1800"
    fi
}

# Функция для установки настроек в базу данных
set_config_in_db() {
    db_path="cash/config.db"
    key="$1"
    value="$2"
    
    # Создаем папку cash если её нет
    mkdir -p cash
    
    python -c "
import sqlite3
conn = sqlite3.connect('$db_path')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS global_config (
             key TEXT PRIMARY KEY,
             value TEXT)''')
c.execute(\"INSERT OR REPLACE INTO global_config (key, value) VALUES (?, ?)\", ('$key', '$value'))
conn.commit()
conn.close()
"
}

# Функция для изменения префикса
change_prefix() {
    while true; do
        clear
        show_header
        echo -e "${CYAN}CONFIGURE COMMAND PREFIX${NC}"
        current_prefix=$(get_current_prefix)
        echo "Current prefix: '$current_prefix'"
        echo
        echo "Enter new prefix (or '0' to go back):"
        read -p "Enter: " new_prefix
        
        if [ "$new_prefix" = "0" ]; then
            return
        elif [ -z "$new_prefix" ]; then
            show_error "Prefix cannot be empty"
        else
            # Устанавливаем префикс в базу данных
            set_config_in_db "command_prefix" "$new_prefix"
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}Prefix updated successfully!${NC}"
                sleep 1
                return
            else
                show_error "Failed to update prefix"
            fi
        fi
    done
}

# Функция для изменения времени автоочистки
change_autoclean_time() {
    while true; do
        clear
        show_header
        echo -e "${CYAN}CONFIGURE AUTOCLEAN TIME${NC}"
        current_time=$(get_current_autoclean_time)
        echo "Current autoclean time: $current_time seconds"
        echo
        echo "Enter new time in seconds (or '0' to go back):"
        read -p "Enter: " new_time
        
        if [ "$new_time" = "0" ]; then
            return
        elif ! [[ "$new_time" =~ ^[0-9]+$ ]]; then
            show_error "Please enter a valid number"
        else
            # Устанавливаем новое время в базу данных
            set_config_in_db "autoclean_delay" "$new_time"
            echo -e "${GREEN}Autoclean time updated successfully!${NC}"
            sleep 1
            return
        fi
    done
}

# Функция для включения/выключения автоклинера
toggle_autoclean() {
    while true; do
        clear
        show_header
        echo -e "${CYAN}CONFIGURE AUTOCLEANER${NC}"
        current_status=$(get_current_autoclean_status)
        echo "Current status: $current_status"
        echo
        echo "Select option:"
        echo "1. Enable autocleaner"
        echo "2. Disable autocleaner"
        echo "0. Go back"
        read -p "Enter: " choice
        
        case $choice in
            1)
                # Включаем автоклинер
                set_config_in_db "autoclean_enabled" "True"
                echo -e "${GREEN}Autocleaner enabled!${NC}"
                sleep 1
                return
                ;;
            2)
                # Выключаем автоклинер
                set_config_in_db "autoclean_enabled" "False"
                echo -e "${GREEN}Autocleaner disabled!${NC}"
                sleep 1
                return
                ;;
            0)
                return
                ;;
            *)
                show_error "Invalid option"
                ;;
        esac
    done
}

# Функция для настройки автозапуска
configure_autostart() {
    while true; do
        clear
        show_header
        echo -e "${CYAN}CONFIGURE AUTOSTART${NC}"
        if grep -q "cd $(pwd) && python main.py" ~/.bashrc; then
            autostart_setting="YES"
        else
            autostart_setting="NO"
        fi
        echo "Current setting: $autostart_setting"
        echo
        echo "Select option:"
        echo "1. Enable autostart"
        echo "2. Disable autostart"
        echo "0. Go back"
        read -p "Enter: " choice
        
        case $choice in
            1)
                # Включаем автозапуск
                if ! grep -q "cd $(pwd) && python main.py" ~/.bashrc; then
                    echo "cd $(pwd) && python main.py" >> ~/.bashrc
                fi
                echo -e "${GREEN}Autostart enabled!${NC}"
                sleep 1
                return
                ;;
            2)
                # Выключаем автозапуск
                sed -i '/python main.py/d' ~/.bashrc
                echo -e "${GREEN}Autostart disabled!${NC}"
                sleep 1
                return
                ;;
            0)
                return
                ;;
            *)
                show_error "Invalid option"
                ;;
        esac
    done
}

# Функция для отображения главного меню настроек
show_settings_menu() {
    while true; do
        clear
        show_header
        echo -e "${CYAN}MAIN SETTINGS MENU${NC}"
        echo
        
        # Получаем текущие настройки
        current_prefix=$(get_current_prefix)
        current_time=$(get_current_autoclean_time)
        current_status=$(get_current_autoclean_status)
        
        if grep -q "cd $(pwd) && python main.py" ~/.bashrc; then
            autostart_setting="YES"
        else
            autostart_setting="NO"
        fi
        
        echo "1. Prefix - '$current_prefix'"
        echo "2. Autocleaner - ${current_time}s (Status: $current_status)"
        echo "3. Inline - Unavailable"
        echo "4. Auto-start - $autostart_setting"
        echo "5. Start bot with current settings"
        echo "0. Exit"
        echo
        read -p "Enter: " choice
        
        case $choice in
            1)
                change_prefix
                ;;
            2)
                clear
                show_header
                echo -e "${CYAN}AUTOCLEANER SETTINGS${NC}"
                echo "1. Change autoclean time"
                echo "2. Toggle autocleaner (enable/disable)"
                echo "0. Go back"
                read -p "Enter: " subchoice
                
                case $subchoice in
                    1)
                        change_autoclean_time
                        ;;
                    2)
                        toggle_autoclean
                        ;;
                    0)
                        ;;
                    *)
                        show_error "Invalid option"
                        ;;
                esac
                ;;
            3)
                clear
                show_header
                echo -e "${CYAN}INLINE MODULE${NC}"
                echo "The inline module is temporarily unavailable"
                echo
                echo "Press any key to continue..."
                read -n 1
                ;;
            4)
                configure_autostart
                ;;
            5)
                echo -e "${GREEN}Starting bot...${NC}"
                python main.py
                exit 0
                ;;
            0)
                echo -e "${GREEN}Goodbye!${NC}"
                exit 0
                ;;
            *)
                show_error "Invalid option"
                ;;
        esac
    done
}

# Основная логика скрипта
main() {
    show_header
    echo -e "${PURPLE}Select installation type:${NC}"
    echo -e "${CYAN}1. Default settings${NC}"
    echo -e "${CYAN}2. Custom settings${NC}"
    echo
    read -p "Enter: " choice
    
    case $choice in
        1)
            echo -e "${GREEN}Starting with default settings...${NC}"
            python main.py
            ;;
        2)
            show_settings_menu
            ;;
        *)
            show_error "Invalid option"
            main
            ;;
    esac
}

# Начало выполнения скрипта
clear
show_header

# Проверяем и устанавливаем необходимые пакеты
install_required_packages

# Устанавливаем зависимости
if install_python_dependencies; then
    # Запускаем основную функцию
    main
else
    show_error "Failed to install dependencies. Please check your internet connection and try again."
    exit 1
fi