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
    echo "Виртуальное окружение не найдено. Запустите installer.sh сначала."
    exit 1
fi

# Активируем виртуальное окружение
source Huekka/bin/activate

# Запускаем бота
python3 main.py
