from abc import ABC, abstractmethod

from .exceptions import CurrencyNotFoundError


class Currency(ABC):
    """Абстрактный базовый класс для всех валют."""

    def __init__(self, name: str, code: str):
        if not name or not name.strip():
            raise ValueError("Имя валюты не может быть пустым")

        code = code.strip().upper()
        if not (2 <= len(code) <= 5) or " " in code:
            raise ValueError(f"Некорректный код валюты: '{code}'")

        self.name = name
        self.code = code

    @abstractmethod
    def get_display_info(self) -> str:
        """Возвращает строковое представление для UI/логов."""
        pass


class FiatCurrency(Currency):
    """Фиатная валюта (обычные деньги)."""

    def __init__(self, name: str, code: str, issuing_country: str):
        super().__init__(name, code)
        self.issuing_country = issuing_country

    def get_display_info(self) -> str:
        return f"[FIAT] {self.code} — {self.name} (Issuing: {self.issuing_country})"


class CryptoCurrency(Currency):
    """Криптовалюта."""

    def __init__(self, name: str, code: str, algorithm: str, market_cap: float):
        super().__init__(name, code)
        self.algorithm = algorithm
        self.market_cap = market_cap

    def get_display_info(self) -> str:
        return (
            f"[CRYPTO] {self.code} — {self.name} "
            f"(Algo: {self.algorithm}, MCAP: {self.market_cap:.2e})"
        )


# --- Реестр валют (Фабрика) ---
_CURRENCIES = {
    "USD": FiatCurrency("US Dollar", "USD", "United States"),
    "EUR": FiatCurrency("Euro", "EUR", "Eurozone"),
    "RUB": FiatCurrency("Russian Ruble", "RUB", "Russia"),
    "BTC": CryptoCurrency("Bitcoin", "BTC", "SHA-256", 1.12e12),
    "ETH": CryptoCurrency("Ethereum", "ETH", "Ethash", 3.5e11),
}


def get_currency(code: str) -> Currency:
    """Фабричный метод для получения валюты по коду."""
    code = code.strip().upper()
    if code not in _CURRENCIES:
        raise CurrencyNotFoundError(code)
    return _CURRENCIES[code]