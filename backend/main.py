from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import datetime

from . import database, schemas
from .database import SessionLocal, engine, Config, SpotTrade, Basis, LargeTradeAlert

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/api/pairs", response_model=List[str])
async def get_pairs():
    # Статический список популярных пар (можно расширить)
    return ["BTC_USDT", "ETH_USDT", "XRP_USDT", "ADA_USDT", "DOT_USDT", "LINK_USDT"]

@app.get("/api/config")
async def get_config(db: Session = Depends(get_db)):
    cfg = {}
    for key in ['current_pair', 'volume_threshold_std', 'basis_mean_window']:
        entry = db.query(Config).filter(Config.key == key).first()
        cfg[key] = entry.value if entry else None
    return cfg

@app.post("/api/config")
async def update_config(config_data: dict, db: Session = Depends(get_db)):
    for key, value in config_data.items():
        if key not in ['current_pair', 'volume_threshold_std', 'basis_mean_window']:
            continue
        entry = db.query(Config).filter(Config.key == key).first()
        if entry:
            entry.value = str(value)
        else:
            entry = Config(key=key, value=str(value))
            db.add(entry)
    db.commit()
    return {"status": "ok"}

@app.get("/api/stats/spot_trades", response_model=List[schemas.SpotTradeSchema])
async def get_spot_trades(pair: str, limit: int = 100, db: Session = Depends(get_db)):
    trades = db.query(SpotTrade).filter(SpotTrade.pair == pair).order_by(SpotTrade.timestamp.desc()).limit(limit).all()
    return trades

@app.get("/api/stats/basis", response_model=List[schemas.BasisSchema])
async def get_basis(pair: str, minutes: int = 60, db: Session = Depends(get_db)):
    since = int((datetime.datetime.utcnow() - datetime.timedelta(minutes=minutes)).timestamp())
    basis = db.query(Basis).filter(Basis.pair == pair, Basis.timestamp >= since).order_by(Basis.timestamp).all()
    return basis

@app.get("/api/stats/large_trades", response_model=List[schemas.LargeTradeAlertSchema])
async def get_large_trades(pair: str, limit: int = 20, db: Session = Depends(get_db)):
    trades = db.query(LargeTradeAlert).filter(LargeTradeAlert.pair == pair).order_by(LargeTradeAlert.timestamp.desc()).limit(limit).all()
    return trades

@app.get("/api/stats/summary", response_model=schemas.SummarySchema)
async def get_summary(pair: str, db: Session = Depends(get_db)):
    last_basis = db.query(Basis).filter(Basis.pair == pair).order_by(Basis.timestamp.desc()).first()
    hour_ago = int((datetime.datetime.utcnow() - datetime.timedelta(hours=1)).timestamp())
    large_count = db.query(LargeTradeAlert).filter(LargeTradeAlert.pair == pair, LargeTradeAlert.timestamp >= hour_ago).count()
    return {
        "spot_price": last_basis.spot_price if last_basis else None,
        "futures_price": last_basis.futures_price if last_basis else None,
        "basis_percent": last_basis.basis_percent if last_basis else None,
        "large_trades_1h": large_count
    }
    