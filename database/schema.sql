-- Schema do Banco de Dados SQLite para o Sneaker Price Tracker

CREATE TABLE IF NOT EXISTS sneakers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    colorway TEXT NOT NULL,
    size TEXT NOT NULL DEFAULT 'BR 40',
    target_price REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sneaker_id TEXT NOT NULL,
    source_name TEXT NOT NULL,
    url TEXT NOT NULL,
    source_type TEXT NOT NULL DEFAULT 'manual',
    css_selector TEXT,
    FOREIGN KEY (sneaker_id) REFERENCES sneakers(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS price_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sneaker_id TEXT NOT NULL,
    source_name TEXT NOT NULL,
    price REAL NOT NULL,
    currency TEXT NOT NULL DEFAULT 'BRL',
    in_stock INTEGER NOT NULL DEFAULT 1,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sneaker_id) REFERENCES sneakers(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_price_history_sneaker ON price_history(sneaker_id);
CREATE INDEX IF NOT EXISTS idx_price_history_timestamp ON price_history(timestamp);
