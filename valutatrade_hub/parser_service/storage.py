import json
from datetime import datetime, timezone
from pathlib import Path


class ParserStorage:
    """Класс для безопасного сохранения курсов."""

    def __init__(self):
        # Ищем папку data в корне проекта
        self.data_dir = Path(__file__).resolve().parent.parent.parent / "data"
        self.rates_file = self.data_dir / "rates.json"
        self.history_file = self.data_dir / "exchange_rates.json"

    def _atomic_write(self, filepath: Path, data: dict | list):
        """Атомарная запись (через временный файл)."""
        temp_file = filepath.with_suffix(".tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        temp_file.replace(filepath)

    def save_rates(self, new_rates: dict[str, float], source_name: str):
        """Сохраняет текущие курсы в rates.json и историю."""
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # 1. Обновляем текущий кэш (rates.json)
        cache_data = {}
        if self.rates_file.exists():
            with open(self.rates_file, "r", encoding="utf-8") as f:
                try:
                    cache_data = json.load(f)
                except json.JSONDecodeError:
                    pass

        if "pairs" not in cache_data:
            cache_data["pairs"] = {}

        for pair, rate in new_rates.items():
            cache_data["pairs"][pair] = {
                "rate": rate,
                "updated_at": now_iso,
                "source": source_name
            }
        cache_data["last_refresh"] = now_iso
        self._atomic_write(self.rates_file, cache_data)

        # 2. Обновляем историю (exchange_rates.json)
        history_data = []
        if self.history_file.exists():
            with open(self.history_file, "r", encoding="utf-8") as f:
                try:
                    history_data = json.load(f)
                except json.JSONDecodeError:
                    pass

        for pair, rate in new_rates.items():
            from_curr, to_curr = pair.split("_")
            record = {
                "id": f"{pair}_{now_iso}",
                "from_currency": from_curr,
                "to_currency": to_curr,
                "rate": rate,
                "timestamp": now_iso,
                "source": source_name,
            }
            history_data.append(record)
            
        self._atomic_write(self.history_file, history_data)