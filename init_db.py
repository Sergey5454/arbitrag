import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from backend.database import init_db, engine
from sqlalchemy import text

if __name__ == "__main__":
    init_db()
    print("Таблицы созданы")
    # Добавим начальные настройки
    with engine.connect() as conn:
        conn.execute(
            text("INSERT OR IGNORE INTO config (key, value) VALUES ('current_pair', 'BTC_USDT')")
        )
        conn.execute(
            text("INSERT OR IGNORE INTO config (key, value) VALUES ('volume_threshold_std', '2.5')")
        )
        conn.execute(
            text("INSERT OR IGNORE INTO config (key, value) VALUES ('basis_mean_window', '60')")
        )
        conn.commit()
    print("Настройки по умолчанию добавлены")