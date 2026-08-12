import random
from datetime import datetime, timedelta
from typing import Dict, Any, List
from scrapers.base_scraper import BaseScraper
from utils.logger import setup_logger

logger = setup_logger("MockCollector")

class MockCollector(BaseScraper):
    """
    Coletor simulador de dados para testes de portfólio, demonstração e geração
    de séries temporais realistas dos modelos de tênis.
    """
    
    BASE_PRICES = {
        "nike-vomero-5-cobblestone": {
            "StockX": 1050.0,
            "Loja Nike": 1199.9,
            "Kicks Store (Demo)": 1120.0
        },
        "nike-air-force-1-07-white": {
            "StockX": 680.0,
            "Centauro": 799.9
        },
        "nike-dunk-low-panda": {
            "StockX": 820.0,
            "Farfetch": 950.0
        }
    }

    def fetch_price(self, source_config: Dict[str, Any]) -> Dict[str, Any]:
        sneaker_id = source_config.get("sneaker_id", "")
        source_name = source_config.get("name", "MockStore")

        sneaker_prices = self.BASE_PRICES.get(sneaker_id, {})
        base_price = sneaker_prices.get(source_name, 890.0)

        # Pequena variação aleatória de preço (ex: -5% a +5%)
        variation = random.uniform(-0.05, 0.05)
        simulated_price = round(base_price * (1 + variation), 2)

        return {
            "price": simulated_price,
            "in_stock": True,
            "source": source_name,
            "error": None
        }

    def generate_historical_dataset(self, sneakers_list: List[Dict[str, Any]], days: int = 30) -> List[Dict[str, Any]]:
        """
        Gera um conjunto histórico de N dias retroativos com tendência realista de preço.
        """
        history_records = []
        now = datetime.now()

        for sneaker in sneakers_list:
            sneaker_id = sneaker["id"]
            target_price = sneaker["target_price"]

            for source in sneaker.get("sources", []):
                source_name = source.get("source_name") or source.get("name", "Fonte")
                base_price = self.BASE_PRICES.get(sneaker_id, {}).get(source_name, target_price * 1.15)

                current_price = base_price
                for i in range(days, -1, -1):
                    dt = now - timedelta(days=i)

                    # Tendência suave com volatilidade aleatória
                    drift = random.choice([-15.0, -10.0, -5.0, 0.0, 5.0, 10.0])
                    current_price = max(target_price * 0.85, current_price + drift)
                    
                    history_records.append({
                        "sneaker_id": sneaker_id,
                        "source_name": source_name,
                        "price": round(current_price, 2),
                        "currency": "BRL",
                        "in_stock": 1,
                        "timestamp": dt.strftime("%Y-%m-%d %H:%M:%S")
                    })

        logger.info(f"Gerados {len(history_records)} registros simulados para os últimos {days} dias.")
        return history_records
