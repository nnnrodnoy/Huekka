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

# Основная логика скрипта
main() {
    show_header
    echo -e "${PURPLE}Запуск Huekka Userbot...${NC}"
    python main.py
}

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
