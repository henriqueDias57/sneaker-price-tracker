import pandas as pd
from typing import Dict, Any, List, Optional
from database.db_manager import DatabaseManager
from utils.logger import setup_logger

logger = setup_logger("PriceAnalyzer")

class PriceAnalyzer:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def analyze_all_sneakers(self) -> List[Dict[str, Any]]:
        df = self.db.get_price_history_dataframe()
        if df.empty:
            logger.warning("Nenhum dado histórico encontrado no banco de dados.")
            return []

        summaries = []
        grouped = df.groupby("sneaker_id")

        for sneaker_id, group in grouped:
            sneaker_name = group["sneaker_name"].iloc[0]
            colorway = group["colorway"].iloc[0]
            target_price = group["target_price"].iloc[0]
            size = group["size"].iloc[0]

            latest_records = group.sort_values("timestamp").groupby("source_name").last().reset_index()
            best_current_row = latest_records.sort_values("price").iloc[0]

            min_ever_row = group.sort_values("price").iloc[0]
            max_ever_price = group["price"].max()

            current_price = best_current_row["price"]
            min_ever_price = min_ever_row["price"]
            
            target_hit = current_price <= target_price
            all_time_low_hit = current_price <= min_ever_price

            discount_from_max = round(((max_ever_price - current_price) / max_ever_price) * 100, 1) if max_ever_price > 0 else 0.0

            summaries.append({
                "sneaker_id": sneaker_id,
                "name": sneaker_name,
                "colorway": colorway,
                "size": size,
                "target_price": target_price,
                "current_best_price": current_price,
                "current_best_source": best_current_row["source_name"],
                "all_time_lowest_price": min_ever_price,
                "all_time_lowest_source": min_ever_row["source_name"],
                "all_time_lowest_date": min_ever_row["timestamp"].strftime("%Y-%m-%d"),
                "discount_from_max_pct": discount_from_max,
                "target_hit": target_hit,
                "all_time_low_hit": all_time_low_hit
            })

        return summaries

    def check_alerts(self) -> List[Dict[str, Any]]:
        summaries = self.analyze_all_sneakers()
        alerts = []
        for s in summaries:
            if s["target_hit"]:
                alerts.append({
                    "type": "TARGET_PRICE_HIT",
                    "sneaker": f"{s['name']} ({s['colorway']})",
                    "message": f"Preço alvo atingido! Atual: R$ {s['current_best_price']:.2f} (Alvo: R$ {s['target_price']:.2f}) na loja {s['current_best_source']}"
                })
            if s["all_time_low_hit"]:
                alerts.append({
                    "type": "ALL_TIME_LOW",
                    "sneaker": f"{s['name']} ({s['colorway']})",
                    "message": f"Menor preço da história registrado! R$ {s['current_best_price']:.2f} na loja {s['current_best_source']}"
                })
        return alerts

