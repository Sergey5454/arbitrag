from sqlalchemy import create_engine, Column, Integer, String, Float, BigInteger, DateTime, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///arbitrage.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Config(Base):
    __tablename__ = "config"
    key = Column(String(50), primary_key=True)
    value = Column(String(200))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SpotTrade(Base):
    __tablename__ = "spot_trades"
    id = Column(Integer, primary_key=True)
    trade_id = Column(String(50), unique=True)
    pair = Column(String(20), index=True)
    price = Column(Float)
    amount = Column(Float)
    volume = Column(Float)
    side = Column(String(10))
    timestamp = Column(BigInteger, index=True)
    is_large = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('ix_spot_trades_pair_timestamp', 'pair', 'timestamp'),
    )

class FuturesTrade(Base):
    __tablename__ = "futures_trades"
    id = Column(Integer, primary_key=True)
    trade_id = Column(String(50), unique=True)
    contract = Column(String(20), index=True)
    price = Column(Float)
    amount = Column(Float)
    volume = Column(Float)
    side = Column(String(10))
    timestamp = Column(BigInteger, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('ix_futures_trades_contract_timestamp', 'contract', 'timestamp'),
    )

class Basis(Base):
    __tablename__ = "basis"
    id = Column(Integer, primary_key=True)
    pair = Column(String(20), index=True)
    spot_price = Column(Float)
    futures_price = Column(Float)
    basis = Column(Float)
    basis_percent = Column(Float)
    timestamp = Column(BigInteger, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('ix_basis_pair_timestamp', 'pair', 'timestamp'),
    )

class LargeTradeAlert(Base):
    __tablename__ = "large_trade_alerts"
    id = Column(Integer, primary_key=True)
    pair = Column(String(20))
    trade_id = Column(String(50))
    volume = Column(Float)
    price = Column(Float)
    side = Column(String(10))
    timestamp = Column(BigInteger)
    threshold_used = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('ix_large_trade_alerts_pair_timestamp', 'pair', 'timestamp'),
    )

def init_db():
    Base.metadata.create_all(bind=engine)