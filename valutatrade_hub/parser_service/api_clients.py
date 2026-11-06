from abc import ABC, abstractmethod

import requests

from valutatrade_hub.core.exceptions import ApiRequestError

from .config import ParserConfig


class BaseApiClient(ABC):
    """Абстрактный базовый класс для API-клиентов."""

    @abstractmethod
    def fetch_rates(self) -> dict[str, float]:
        """Возвращает словарь вида {'BTC_USD': 59337.21}."""
        pass


class CoinGeckoClient(BaseApiClient):
    """Клиент для получения курсов криптовалют с CoinGecko."""

    def __init__(self, config: ParserConfig):
        self.config = config

    def fetch_rates(self) -> dict[str, float]:
        ids = ",".join(self.config.CRYPTO_ID_MAP.values())
        params = {
            "ids": ids,
            "vs_currencies": self.config.BASE_CURRENCY.lower(),
        }

        try:
            response = requests.get(
                self.config.COINGECKO_URL,
                params=params,
                timeout=self.config.REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()

            rates = {}
            for code, cg_id in self.config.CRYPTO_ID_MAP.items():
                if cg_id in data and "usd" in data[cg_id]:
                    rates[f"{code}_USD"] = float(data[cg_id]["usd"])
            return rates

        except requests.exceptions.RequestException as e:
            raise ApiRequestError(f"CoinGecko network error: {e}")
        except (ValueError, KeyError) as e:
            raise ApiRequestError(f"CoinGecko data parsing error: {e}")


class ExchangeRateApiClient(BaseApiClient):
    """Клиент для получения фиатных курсов с ExchangeRate-API."""

    def __init__(self, config: ParserConfig):
        self.config = config

    def fetch_rates(self) -> dict[str, float]:
        if (
            not self.config.EXCHANGERATE_API_KEY
            or self.config.EXCHANGERATE_API_KEY == "YOUR_API_KEY_HERE"
        ):
            raise ApiRequestError("ExchangeRate-API key is missing")

        base_url = self.config.EXCHANGERATE_API_URL
        key = self.config.EXCHANGERATE_API_KEY
        url = f"{base_url}/{key}/latest/USD"

        try:
            response = requests.get(url, timeout=self.config.REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()

            if data.get("result") != "success":
                raise ApiRequestError(f"API returned error: {data.get('error-type')}")

            rates = {}
            all_rates = data.get("rates", {})
            for code in self.config.FIAT_CURRENCIES:
                if code in all_rates:
                    # API отдает 1 USD = X EUR, нам нужно X EUR = 1 USD
                    rates[f"{code}_USD"] = 1.0 / float(all_rates[code])
            return rates

        except requests.exceptions.RequestException as e:
            raise ApiRequestError(f"ExchangeRate-API network error: {e}")
        except (ValueError, KeyError) as e:
            raise ApiRequestError(f"ExchangeRate-API data parsing error: {e}")