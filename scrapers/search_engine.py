import re
from typing import List, Dict, Any, Optional
from utils.logger import setup_logger

logger = setup_logger("SearchEngine")

class SneakerSearchEngine:
    """
    Mecanismo de busca multi-fonte e catálogo expandido de sneakers
    com suporte a filtragem por palavras-chave e prévias visuais em alta resolução.
    """
    
    CATALOG = [
        {
            "id": "nike-vomero-5-cobblestone",
            "name": "Nike Zoom Vomero 5",
            "colorway": "Cobblestone / Flat Pewter",
            "size": "BR 40",
            "target_price": 950.0,
            "estimated_price": 910.0,
            "image_url": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=600&auto=format&fit=crop&q=80",
            "sources": [
                {"name": "StockX", "url": "https://stockx.com/nike-zoom-vomero-5-cobblestone", "type": "manual"},
                {"name": "Loja Nike", "url": "https://www.nike.com.br/snkrs/vomero-5", "type": "manual"}
            ]
        },
        {
            "id": "nike-air-force-1-07-white",
            "name": "Nike Air Force 1 '07",
            "colorway": "Triple White",
            "size": "BR 40",
            "target_price": 700.0,
            "estimated_price": 649.9,
            "image_url": "https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?w=600&auto=format&fit=crop&q=80",
            "sources": [
                {"name": "Centauro", "url": "https://www.centauro.com.br/air-force-1", "type": "manual"},
                {"name": "StockX", "url": "https://stockx.com/nike-air-force-1-low-07-white", "type": "manual"}
            ]
        },
        {
            "id": "nike-dunk-low-panda",
            "name": "Nike Dunk Low",
            "colorway": "Black White (Panda)",
            "size": "BR 40",
            "target_price": 800.0,
            "estimated_price": 780.0,
            "image_url": "https://images.unsplash.com/photo-1600185365926-3a2ce3cdb9eb?w=600&auto=format&fit=crop&q=80",
            "sources": [
                {"name": "StockX", "url": "https://stockx.com/nike-dunk-low-retro-white-black-2021", "type": "manual"},
                {"name": "Farfetch", "url": "https://www.farfetch.com/br/shopping/men/nike-dunk-low.aspx", "type": "manual"}
            ]
        },
        {
            "id": "adidas-samba-og-white",
            "name": "Adidas Samba OG",
            "colorway": "Cloud White / Core Black",
            "size": "BR 40",
            "target_price": 650.0,
            "estimated_price": 699.9,
            "image_url": "https://images.unsplash.com/photo-1584735935682-2f2b69dff9d2?w=600&auto=format&fit=crop&q=80",
            "sources": [
                {"name": "Adidas BR", "url": "https://www.adidas.com.br/samba-og", "type": "manual"},
                {"name": "StockX", "url": "https://stockx.com/adidas-samba-og-cloud-white-core-black", "type": "manual"}
            ]
        },
        {
            "id": "new-balance-9060-rain-cloud",
            "name": "New Balance 9060",
            "colorway": "Rain Cloud Grey",
            "size": "BR 40",
            "target_price": 1100.0,
            "estimated_price": 1199.9,
            "image_url": "https://images.unsplash.com/photo-1539185441755-769473a23570?w=600&auto=format&fit=crop&q=80",
            "sources": [
                {"name": "New Balance BR", "url": "https://www.newbalance.com.br/9060", "type": "manual"},
                {"name": "StockX", "url": "https://stockx.com/new-balance-9060-rain-cloud", "type": "manual"}
            ]
        },
        {
            "id": "asics-gel-kayano-14-silver",
            "name": "Asics GEL-Kayano 14",
            "colorway": "Metallic Plum / Cream",
            "size": "BR 40",
            "target_price": 980.0,
            "estimated_price": 1050.0,
            "image_url": "https://images.unsplash.com/photo-1551107696-a4b0c5a0d9a2?w=600&auto=format&fit=crop&q=80",
            "sources": [
                {"name": "Asics BR", "url": "https://www.asics.com.br/gel-kayano-14", "type": "manual"},
                {"name": "StockX", "url": "https://stockx.com/asics-gel-kayano-14-metallic-plum", "type": "manual"}
            ]
        },
        {
            "id": "air-jordan-1-retro-high-chicago",
            "name": "Air Jordan 1 Retro High OG",
            "colorway": "Chicago Lost & Found",
            "size": "BR 40",
            "target_price": 1800.0,
            "estimated_price": 1950.0,
            "image_url": "https://images.unsplash.com/photo-1516478177764-9fe5bd7e9717?w=600&auto=format&fit=crop&q=80",
            "sources": [
                {"name": "StockX", "url": "https://stockx.com/air-jordan-1-retro-high-og-chicago-reimagined-lost-and-found", "type": "manual"},
                {"name": "SNKRS BR", "url": "https://www.nike.com.br/snkrs/jordan-1", "type": "manual"}
            ]
        }
    ]

    def search(self, query: str) -> List[Dict[str, Any]]:
        query_clean = query.strip().lower()
        if not query_clean:
            return self.CATALOG

        results = []
        tokens = query_clean.split()

        for sneaker in self.CATALOG:
            searchable_text = f"{sneaker['name']} {sneaker['colorway']} {sneaker['id']}".lower()
            if all(token in searchable_text for token in tokens):
                results.append(sneaker)

        logger.info(f"Busca por '{query}' retornou {len(results)} resultados.")
        return results
