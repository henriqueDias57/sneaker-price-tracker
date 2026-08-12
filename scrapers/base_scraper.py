from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseScraper(ABC):
    @abstractmethod
    def fetch_price(self, source_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Coleta o preço atual de um tênis a partir das configurações da fonte.
        Retorna um dicionário com:
        - price (float)
        - in_stock (bool)
        - source (str)
        - error (str | None)
        """
        pass
