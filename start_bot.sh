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

# Проверяем существование виртуального окружения
if [ ! -d "Huekka" ]; then
    echo "Виртуальное окружение не найдено. Создаем..."
    python3 -m venv Huekka
    if [ $? -ne 0 ]; then
        echo "Ошибка при создании виртуального окружения!"
        exit 1
    fi
    
    # Активируем виртуальное окружение
    source Huekka/bin/activate
    
    # Устанавливаем зависимости
    echo "Устанавливаем зависимости..."
    pip install --upgrade pip
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "Ошибка при установке зависимостей!"
        exit 1
    fi
else
    # Активируем существующее виртуальное окружение
    source Huekka/bin/activate
fi

# Запускаем бота
python3 main.py
