import sqlite3
import os
from typing import List, Dict, Any, Optional
import pandas as pd
from utils.logger import setup_logger

logger = setup_logger("DBManager")

class DatabaseManager:
    def __init__(self, db_path: str = "database/sneakers.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
        if not os.path.exists(schema_path):
            logger.error(f"Arquivo de schema não encontrado: {schema_path}")
            return
        
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()

        with self.get_connection() as conn:
            conn.executescript(schema_sql)
            conn.commit()
        logger.info("Banco de dados inicializado com sucesso.")

    def save_sneaker(self, sneaker: Dict[str, Any]) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO sneakers (id, name, colorway, size, target_price)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name=excluded.name,
                    colorway=excluded.colorway,
                    size=excluded.size,
                    target_price=excluded.target_price
                """,
                (
                    sneaker["id"],
                    sneaker["name"],
                    sneaker["colorway"],
                    sneaker.get("size", "BR 40"),
                    sneaker["target_price"]
                )
            )

            for source in sneaker.get("sources", []):
                cursor.execute(
                    """
                    INSERT INTO sources (sneaker_id, source_name, url, source_type, css_selector)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        sneaker["id"],
                        source["name"],
                        source["url"],
                        source.get("type", "manual"),
                        source.get("css_selector")
                    )
                )
            conn.commit()

    def save_price_record(
        self,
        sneaker_id: str,
        source_name: str,
        price: float,
        currency: str = "BRL",
        in_stock: bool = True,
        timestamp: Optional[str] = None
    ) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if timestamp:
                cursor.execute(
                    """
                    INSERT INTO price_history (sneaker_id, source_name, price, currency, in_stock, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (sneaker_id, source_name, price, currency, 1 if in_stock else 0, timestamp)
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO price_history (sneaker_id, source_name, price, currency, in_stock)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (sneaker_id, source_name, price, currency, 1 if in_stock else 0)
                )
            conn.commit()

    def get_all_sneakers(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sneakers")
            sneakers = [dict(row) for row in cursor.fetchall()]

            for s in sneakers:
                cursor.execute("SELECT * FROM sources WHERE sneaker_id = ?", (s["id"],))
                s["sources"] = [dict(row) for row in cursor.fetchall()]
            return sneakers

    def get_price_history_dataframe(self, sneaker_id: Optional[str] = None) -> pd.DataFrame:
        query = """
            SELECT ph.id, ph.sneaker_id, s.name as sneaker_name, s.colorway, s.size,
                   ph.source_name, ph.price, ph.currency, ph.in_stock, ph.timestamp, s.target_price
            FROM price_history ph
            JOIN sneakers s ON ph.sneaker_id = s.id
        """
        params = []
        if sneaker_id:
            query += " WHERE ph.sneaker_id = ?"
            params.append(sneaker_id)
        
        query += " ORDER BY ph.timestamp ASC"

        with self.get_connection() as conn:
            df = pd.read_sql_query(query, conn, params=params)
            if not df.empty:
                df["timestamp"] = pd.to_datetime(df["timestamp"])
            return df

    def get_lowest_price_ever(self, sneaker_id: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT ph.price, ph.source_name, ph.timestamp, s.name, s.colorway
                FROM price_history ph
                JOIN sneakers s ON ph.sneaker_id = s.id
                WHERE ph.sneaker_id = ?
                ORDER BY ph.price ASC, ph.timestamp DESC
                LIMIT 1
                """,
                (sneaker_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
