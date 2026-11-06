from pathlib import Path


class SettingsLoader:
    """Синглтон для загрузки и хранения конфигурации.

    Реализован через __new__, так как это самый простой и читаемый
    способ создания синглтона в Python (не требует создания метаклассов,
    а также исключает создание дополнительных экземпляров при импортах).
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Инициализация конфига при первом создании
            cls._instance._config = {
                "data_dir": Path(__file__).resolve().parent.parent.parent / "data",
                "rates_ttl_seconds": 300,  # 5 минут (политика свежести курсов)
                "default_base_currency": "USD",
                "log_file": "logs/actions.log",
            }
        return cls._instance

    def get(self, key: str, default=None):
        """Возвращает значение конфигурации по ключу."""
        return self._config.get(key, default)

    def reload(self):
        """Перезагрузка конфигурации (в текущей реализации — заглушка)."""
        print("Конфигурация перезагружена (in-memory).")