#!/bin/bash
# ©️ nnnrodnoy, 2025
# 💬 @nnnrodnoy
# This file is part of Huekka
# 🌐 https://github.com/nnnrodnoy/Huekka/
# You can redistribute it and/or modify it under the terms of the MIT License
# 🔑 https://opensource.org/licenses/MIT

# Определяем директорию, где находится скрипт
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Цвета для вывода
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функция для отображения статуса
print_status() {
    echo -e "${PURPLE}[Huekka]${NC} $1"
}

# Функция для отображения ошибки
print_error() {
    echo -e "${RED}[Error]${NC} $1"
}

print_status "Checking dependencies..."
# Проверяем установлены ли зависимости
if ! python -c "import telethon" 2>/dev/null; then
    print_status "Installing dependencies..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        print_error "Failed to install dependencies!"
        exit 1
    fi
fi

print_status "Starting Huekka UserBot..."
python main.py
