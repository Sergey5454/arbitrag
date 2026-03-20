from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ConfigSchema(BaseModel):
    key: str
    value: str

class SpotTradeSchema(BaseModel):
    trade_id: str
    pair: str
    price: float
    amount: float
    volume: float
    side: str
    timestamp: int

    class Config:
        orm_mode = True

class FuturesTradeSchema(BaseModel):
    trade_id: str
    contract: str
    price: float
    amount: float
    volume: float
    side: str
    timestamp: int

    class Config:
        orm_mode = True

class BasisSchema(BaseModel):
    pair: str
    spot_price: float
    futures_price: float
    basis: float
    basis_percent: float
    timestamp: int

    class Config:
        orm_mode = True

class LargeTradeAlertSchema(BaseModel):
    pair: str
    trade_id: str
    volume: float
    price: float
    side: str
    timestamp: int
    threshold_used: float

    class Config:
        orm_mode = True

class SummarySchema(BaseModel):
    spot_price: Optional[float]
    futures_price: Optional[float]
    basis_percent: Optional[float]
    large_trades_1h: int
