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
    echo -e "${RED}Ошибка: $1${NC}"
    echo "Нажмите любую клавишу для продолжения..."
    read -n 1
}

# Функция для установки Python зависимостей
install_python_dependencies() {
    echo -e "${YELLOW}Установка Python зависимостей...${NC}"
    
    # Проверяем наличие файла requirements.txt
    if [ ! -f "requirements.txt" ]; then
        show_error "Файл requirements.txt не найден!"
        return 1
    fi
    
    # Устанавливаем зависимости
    if command -v pip3 &> /dev/null; then
        pip3 install -r requirements.txt
    elif command -v pip &> /dev/null; then
        pip install -r requirements.txt
    else
        show_error "Pip не найден!"
        return 1
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Все зависимости успешно установлены!${NC}"
        return 0
    else
        show_error "Не удалось установить некоторые зависимости"
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
        echo -e "${CYAN}НАСТРОЙКА ПРЕФИКСА КОМАНД${NC}"
        current_prefix=$(get_current_prefix)
        echo "Текущий префикс: '$current_prefix'"
        echo
        echo "Введите новый префикс (или '0' для возврата):"
        read -p "Ввод: " new_prefix
        
        if [ "$new_prefix" = "0" ]; then
            return
        elif [ -z "$new_prefix" ]; then
            show_error "Префикс не может быть пустым"
        else
            # Устанавливаем префикс в базу данных
            set_config_in_db "command_prefix" "$new_prefix"
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}Префикс успешно обновлен!${NC}"
                sleep 1
                return
            else
                show_error "Не удалось обновить префикс"
            fi
        fi
    done
}

# Функция для изменения времени автоочистки
change_autoclean_time() {
    while true; do
        clear
        show_header
        echo -e "${CYAN}НАСТРОЙКА ВРЕМЕНИ АВТООЧИСТКИ${NC}"
        current_time=$(get_current_autoclean_time)
        echo "Текущее время автоочистки: $current_time секунд"
        echo
        echo "Введите новое время в секундах (или '0' для возврата):"
        read -p "Ввод: " new_time
        
        if [ "$new_time" = "0" ]; then
            return
        elif ! [[ "$new_time" =~ ^[0-9]+$ ]]; then
            show_error "Пожалуйста, введите корректное число"
        else
            # Устанавливаем новое время в базу данных
            set_config_in_db "autoclean_delay" "$new_time"
            echo -e "${GREEN}Время автоочистки успешно обновлено!${NC}"
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
        echo -e "${CYAN}НАСТРОЙКА АВТООЧИСТКИ${NC}"
        current_status=$(get_current_autoclean_status)
        echo "Текущий статус: $current_status"
        echo
        echo "Выберите опцию:"
        echo "1. Включить автоочистку"
        echo "2. Выключить автоочистку"
        echo "0. Назад"
        read -p "Ввод: " choice
        
        case $choice in
            1)
                # Включаем автоклинер
                set_config_in_db "autoclean_enabled" "True"
                echo -e "${GREEN}Автоочистка включена!${NC}"
                sleep 1
                return
                ;;
            2)
                # Выключаем автоклинер
                set_config_in_db "autoclean_enabled" "False"
                echo -e "${GREEN}Автоочистка выключена!${NC}"
                sleep 1
                return
                ;;
            0)
                return
                ;;
            *)
                show_error "Неверная опция"
                ;;
        esac
    done
}

# Функция для настройки автозапуска
configure_autostart() {
    while true; do
        clear
        show_header
        echo -e "${CYAN}НАСТРОЙКА АВТОЗАПУСКА${NC}"
        if grep -q "cd $(pwd) && python main.py" ~/.bashrc; then
            autostart_setting="ВКЛЮЧЕН"
        else
            autostart_setting="ВЫКЛЮЧЕН"
        fi
        echo "Текущая настройка: $autostart_setting"
        echo
        echo "Выберите опцию:"
        echo "1. Включить автозапуск"
        echo "2. Выключить автозапуск"
        echo "0. Назад"
        read -p "Ввод: " choice
        
        case $choice in
            1)
                # Включаем автозапуск
                if ! grep -q "cd $(pwd) && python main.py" ~/.bashrc; then
                    echo "cd $(pwd) && python main.py" >> ~/.bashrc
                fi
                echo -e "${GREEN}Автозапуск включен!${NC}"
                sleep 1
                return
                ;;
            2)
                # Выключаем автозапуск
                sed -i '/python main.py/d' ~/.bashrc
                echo -e "${GREEN}Автозапуск выключен!${NC}"
                sleep 1
                return
                ;;
            0)
                return
                ;;
            *)
                show_error "Неверная опция"
                ;;
        esac
    done
}

# Функция для отображения главного меню настроек
show_settings_menu() {
    while true; do
        clear
        show_header
        echo -e "${CYAN}ГЛАВНОЕ МЕНЮ НАСТРОЕК${NC}"
        echo
        
        # Получаем текущие настройки
        current_prefix=$(get_current_prefix)
        current_time=$(get_current_autoclean_time)
        current_status=$(get_current_autoclean_status)
        
        if grep -q "cd $(pwd) && python main.py" ~/.bashrc; then
            autostart_setting="ВКЛЮЧЕН"
        else
            autostart_setting="ВЫКЛЮЧЕН"
        fi
        
        echo "1. Префикс - '$current_prefix'"
        echo "2. Автоочистка - ${current_time}сек (Статус: $current_status)"
        echo "3. Автозапуск - $autostart_setting"
        echo "4. Запустить Huekka"
        echo "0. Выход"
        echo
        read -p "Ввод: " choice
        
        case $choice in
            1)
                change_prefix
                ;;
            2)
                clear
                show_header
                echo -e "${CYAN}НАСТРОЙКИ АВТООЧИСТКИ${NC}"
                echo "1. Изменить время автоочистки"
                echo "2. Переключить автоочистку (вкл/выкл)"
                echo "0. Назад"
                read -p "Ввод: " subchoice
                
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
                        show_error "Неверная опция"
                        ;;
                esac
                ;;
            3)
                configure_autostart
                ;;
            4)
                echo -e "${GREEN}Запуск Huekka...${NC}"
                python main.py
                exit 0
                ;;
            0)
                echo -e "${GREEN}До свидания!${NC}"
                exit 0
                ;;
            *)
                show_error "Неверная опция"
                ;;
        esac
    done
}

# Основная логика скрипта
main() {
    show_header
    echo -e "${PURPLE}Выберите тип установки:${NC}"
    echo -e "${CYAN}1. Стандартные настройки${NC}"
    echo -e "${CYAN}2. Пользовательские настройки${NC}"
    echo
    read -p "Ввод: " choice
    
    case $choice in
        1)
            echo -e "${GREEN}Запуск со стандартными настройками...${NC}"
            python main.py
            ;;
        2)
            show_settings_menu
            ;;
        *)
            show_error "Неверная опция"
            main
            ;;
    esac
}

# Обработка аргумента командной строки
if [ "$1" = "sitting" ]; then
    # Прямой запуск меню настроек
    show_settings_menu
else
    # Начало выполнения скрипта
    clear
    show_header
    
    # Устанавливаем зависимости
    if install_python_dependencies; then
        # Запускаем основную функцию
        main
    else
        show_error "Не удалось установить зависимости. Проверьте подключение к интернету и попробуйте снова."
        exit 1
    fi
fi
