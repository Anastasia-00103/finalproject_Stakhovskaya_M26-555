import json

from .settings import SettingsLoader


class DatabaseManager:
    """Синглтон для безопасной работы с JSON-файлами.

    Оборачивает операции чтения и записи в методы, чтобы бизнес-логика
    не зависела от конкретного пути к файлам.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Сразу подтягиваем настройки пути
            cls._instance.settings = SettingsLoader()
        return cls._instance

    def _get_path(self, filename: str):
        """Возвращает полный путь к JSON-файлу."""
        return self.settings.get("data_dir") / filename

    def load(self, filename: str) -> list | dict:
        """Загружает данные из JSON. Если файла нет — возвращает пустой список."""
        filepath = self._get_path(filename)
        if not filepath.exists():
            return []
        with open(filepath, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []

    def save(self, filename: str, data: list | dict) -> None:
        """Сохраняет данные в JSON-файл."""
        filepath = self._get_path(filename)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)