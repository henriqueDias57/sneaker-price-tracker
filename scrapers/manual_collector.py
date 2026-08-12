from typing import Dict, Any, Optional
from scrapers.base_scraper import BaseScraper
from utils.logger import setup_logger

logger = setup_logger("ManualCollector")

class ManualCollector(BaseScraper):
    def __init__(self, predefined_prices: Optional[Dict[str, float]] = None):
        self.predefined_prices = predefined_prices or {}

    def fetch_price(self, source_config: Dict[str, Any]) -> Dict[str, Any]:
        source_name = source_config.get("name", "Entrada Manual")
        sneaker_id = source_config.get("sneaker_id", "")
        key = f"{sneaker_id}:{source_name}"

        if key in self.predefined_prices:
            price = self.predefined_prices[key]
            logger.info(f"Usando preço pré-definido para {key}: R$ {price:.2f}")
            return {
                "price": price,
                "in_stock": True,
                "source": source_name,
                "error": None
            }

        logger.info(f"Fonte {source_name} requer entrada de preço para {source_config.get('url', 'produto')}")
        return {
            "price": None,
            "in_stock": True,
            "source": source_name,
            "error": "Entrada manual pendente"
        }
