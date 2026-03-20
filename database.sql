-- Таблица config
CREATE TABLE IF NOT EXISTS config (
    key VARCHAR(50) PRIMARY KEY,
    value VARCHAR(200),
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Таблица spot_trades
CREATE TABLE IF NOT EXISTS spot_trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_id VARCHAR(50) UNIQUE,
    pair VARCHAR(20),
    price REAL,
    amount REAL,
    volume REAL,
    side VARCHAR(10),
    timestamp INTEGER,
    is_large BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_spot_trades_pair_timestamp ON spot_trades(pair, timestamp);

-- Таблица futures_trades
CREATE TABLE IF NOT EXISTS futures_trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_id VARCHAR(50) UNIQUE,
    contract VARCHAR(20),
    price REAL,
    amount REAL,
    volume REAL,
    side VARCHAR(10),
    timestamp INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_futures_trades_contract_timestamp ON futures_trades(contract, timestamp);

-- Таблица basis
CREATE TABLE IF NOT EXISTS basis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pair VARCHAR(20),
    spot_price REAL,
    futures_price REAL,
    basis REAL,
    basis_percent REAL,
    timestamp INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_basis_pair_timestamp ON basis(pair, timestamp);

-- Таблица large_trade_alerts
CREATE TABLE IF NOT EXISTS large_trade_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pair VARCHAR(20),
    trade_id VARCHAR(50),
    volume REAL,
    price REAL,
    side VARCHAR(10),
    timestamp INTEGER,
    threshold_used REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_large_trade_alerts_pair_timestamp ON large_trade_alerts(pair, timestamp);

-- Начальные настройки
INSERT OR IGNORE INTO config (key, value) VALUES ('current_pair', 'BTC_USDT');
INSERT OR IGNORE INTO config (key, value) VALUES ('volume_threshold_std', '2.5');
INSERT OR IGNORE INTO config (key, value) VALUES ('basis_mean_window', '60');