import json
import os
from pathlib import Path

# Путь к папке data в корне проекта
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

def load_json(filename: str) -> list | dict:
    """Загружает данные из JSON-файла. Если файла нет — возвращает пустой список."""
    filepath = DATA_DIR / filename
    if not filepath.exists():
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_json(filename: str, data: list | dict) -> None:
    """Сохраняет данные в JSON-файл."""
    os.makedirs(DATA_DIR, exist_ok=True)
    filepath = DATA_DIR / filename
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)