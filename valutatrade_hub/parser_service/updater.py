from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.logging_config import logger

from .api_clients import CoinGeckoClient, ExchangeRateApiClient
from .config import ParserConfig
from .storage import ParserStorage


class RatesUpdater:
    """Точка входа для логики обновления курсов."""

    def __init__(self):
        self.config = ParserConfig()
        self.storage = ParserStorage()
        self.clients = {
            "CoinGecko": CoinGeckoClient(self.config),
            "ExchangeRate-API": ExchangeRateApiClient(self.config),
        }

    def run_update(self, target_source: str | None = None) -> str:
        """Запускает обновление курсов."""
        logger.info("Starting rates update...")
        
        total_updated = 0
        errors = 0

        for name, client in self.clients.items():
            if target_source and target_source.lower() not in name.lower():
                continue
                
            try:
                logger.info(f"Fetching from {name}...")
                rates = client.fetch_rates()
                
                if rates:
                    self.storage.save_rates(rates, name)
                    total_updated += len(rates)
                    logger.info(f"Fetching from {name}... OK ({len(rates)} rates)")
                else:
                    logger.warning(f"Fetching from {name}... returned 0 rates")
                    
            except ApiRequestError as e:
                errors += 1
                logger.error(f"Failed to fetch from {name}: {e}")

        if errors > 0:
            return "Update completed with errors. Check logs/parser.log for details."
        elif total_updated == 0:
            return "Update completed. No rates were updated."
        else:
            return f"Update successful. Total rates updated: {total_updated}."