import re
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional
from scrapers.base_scraper import BaseScraper
from utils.logger import setup_logger

logger = setup_logger("HTMLScraper")

class HTMLScraper(BaseScraper):
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7"
        }

    def fetch_price(self, source_config: Dict[str, Any]) -> Dict[str, Any]:
        url = source_config.get("url")
        source_name = source_config.get("name", "Desconhecido")
        css_selector = source_config.get("css_selector")

        if not url or not css_selector:
            return {
                "price": None,
                "in_stock": False,
                "source": source_name,
                "error": "URL ou seletor CSS ausente no contrato da fonte"
            }

        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            if response.status_code != 200:
                logger.warning(f"Erro HTTP {response.status_code} ao acessar {url}")
                return {
                    "price": None,
                    "in_stock": False,
                    "source": source_name,
                    "error": f"Erro HTTP {response.status_code}"
                }

            soup = BeautifulSoup(response.text, "html.parser")
            element = soup.select_one(css_selector)

            if not element:
                logger.warning(f"Elemento com seletor '{css_selector}' não localizado em {url}")
                return {
                    "price": None,
                    "in_stock": False,
                    "source": source_name,
                    "error": f"Seletor '{css_selector}' não encontrado na página"
                }

            price = self._parse_price(element.get_text())
            if price is None:
                return {
                    "price": None,
                    "in_stock": False,
                    "source": source_name,
                    "error": "Não foi possível converter o valor lido da página"
                }

            return {
                "price": price,
                "in_stock": True,
                "source": source_name,
                "error": None
            }

        except requests.RequestException as e:
            logger.error(f"Falha de conexão com {url}: {e}")
            return {
                "price": None,
                "in_stock": False,
                "source": source_name,
                "error": f"Exceção de rede: {str(e)}"
            }

    @staticmethod
    def _parse_price(text: str) -> Optional[float]:
        cleaned = re.sub(r"[^\d,\.]", "", text)
        if not cleaned:
            return None
        if "," in cleaned and "." in cleaned:
            cleaned = cleaned.replace(".", "").replace(",", ".")
        elif "," in cleaned:
            cleaned = cleaned.replace(",", ".")
        try:
            return float(cleaned)
        except ValueError:
            return None
