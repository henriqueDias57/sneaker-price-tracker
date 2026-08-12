import sqlite3
import os
import json
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
            
            # Migração dinâmica de colunas caso a tabela já existisse
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(sneakers)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if "is_pinned" not in columns:
                cursor.execute("ALTER TABLE sneakers ADD COLUMN is_pinned INTEGER NOT NULL DEFAULT 1")
            if "image_url" not in columns:
                cursor.execute("ALTER TABLE sneakers ADD COLUMN image_url TEXT")

            conn.commit()
        logger.info("Banco de dados inicializado e migrado com sucesso.")

    def save_sneaker(self, sneaker: Dict[str, Any], is_pinned: int = 1) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO sneakers (id, name, colorway, size, target_price, is_pinned, image_url)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name=excluded.name,
                    colorway=excluded.colorway,
                    size=excluded.size,
                    target_price=excluded.target_price,
                    is_pinned=excluded.is_pinned,
                    image_url=excluded.image_url
                """,
                (
                    sneaker["id"],
                    sneaker["name"],
                    sneaker["colorway"],
                    sneaker.get("size", "BR 40"),
                    sneaker["target_price"],
                    is_pinned,
                    sneaker.get("image_url")
                )
            )

            # Limpa e reinsere as fontes
            cursor.execute("DELETE FROM sources WHERE sneaker_id = ?", (sneaker["id"],))
            for source in sneaker.get("sources", []):
                src_name = source.get("source_name") or source.get("name", "Fonte")
                cursor.execute(
                    """
                    INSERT INTO sources (sneaker_id, source_name, url, source_type, css_selector)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        sneaker["id"],
                        src_name,
                        source["url"],
                        source.get("type", "manual"),
                        source.get("css_selector")
                    )
                )
            conn.commit()

    def pin_sneaker(self, sneaker: Dict[str, Any]) -> None:
        self.save_sneaker(sneaker, is_pinned=1)
        logger.info(f"Tênis '{sneaker['name']}' fixado com sucesso.")

    def unpin_sneaker(self, sneaker_id: str) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE sneakers SET is_pinned = 0 WHERE id = ?", (sneaker_id,))
            conn.commit()
        logger.info(f"Tênis ID '{sneaker_id}' desafixado do radar.")

    def get_all_sneakers(self, pinned_only: bool = True) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM sneakers WHERE is_pinned = 1" if pinned_only else "SELECT * FROM sneakers"
            cursor.execute(query)
            sneakers = [dict(row) for row in cursor.fetchall()]

            for s in sneakers:
                cursor.execute("SELECT * FROM sources WHERE sneaker_id = ?", (s["id"],))
                s["sources"] = [dict(row) for row in cursor.fetchall()]
            return sneakers

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

    def get_price_history_dataframe(self, sneaker_id: Optional[str] = None) -> pd.DataFrame:
        query = """
            SELECT ph.id, ph.sneaker_id, s.name as sneaker_name, s.colorway, s.size, s.image_url,
                   ph.source_name, ph.price, ph.currency, ph.in_stock, ph.timestamp, s.target_price
            FROM price_history ph
            JOIN sneakers s ON ph.sneaker_id = s.id
            WHERE s.is_pinned = 1
        """
        params = []
        if sneaker_id:
            query += " AND ph.sneaker_id = ?"
            params.append(sneaker_id)
        
        query += " ORDER BY ph.timestamp ASC"

        with self.get_connection() as conn:
            df = pd.read_sql_query(query, conn, params=params)
            if not df.empty:
                df["timestamp"] = pd.to_datetime(df["timestamp"])
            return df

    def get_search_cache(self, query: str) -> Optional[List[Dict[str, Any]]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT results_json FROM search_cache
                WHERE query = ? AND datetime(updated_at, '+1 hour') >= datetime('now')
                """,
                (query.strip().lower(),)
            )
            row = cursor.fetchone()
            if row:
                return json.loads(row["results_json"])
            return None

    def save_search_cache(self, query: str, results: List[Dict[str, Any]]) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO search_cache (query, results_json, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(query) DO UPDATE SET
                    results_json=excluded.results_json,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (query.strip().lower(), json.dumps(results))
            )
            conn.commit()
