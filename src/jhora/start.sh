#!/usr/bin/env bash
# Запуск GUI PyJHora (PyQt6).
# При першому запуску створює .venv і встановлює залежності.
set -euo pipefail

# Каталог скрипта (src/jhora) і корінь проєкту (два рівні вище)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
PY="$VENV_DIR/bin/python"

cd "$PROJECT_ROOT"

if [ ! -d "$VENV_DIR" ]; then
    echo "Створюю .venv..."
    python3 -m venv "$VENV_DIR"
fi

# Залежності — тільки якщо ще не встановлені (наприклад, порожній .venv)
# Увага: pyswisseph встановлює модуль swisseph (import pyswisseph не працює!)
if ! "$PY" -c "import PyQt6, swisseph, dateutil, pyIslam" >/dev/null 2>&1; then
    echo "Встановлюю залежності з requirements.txt (може зайняти кілька хвилин)..."
    "$VENV_DIR/bin/pip" install -r "$SCRIPT_DIR/requirements.txt"
fi

# Запуск GUI-інтерфейсу (пакет jhora лежить у src/)
export PYTHONPATH="$PROJECT_ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
exec "$PY" -m jhora.ui.horo_chart_tabs "$@"
