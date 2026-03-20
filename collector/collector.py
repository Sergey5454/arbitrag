import time
import requests
import os
import numpy as np
import logging
from datetime import datetime
from sqlalchemy.orm import sessionmaker
from sqlalchemy import desc
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.database import engine, SpotTrade, FuturesTrade, Basis, LargeTradeAlert, Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GateIORestCollector:
    def __init__(self):
        self.Session = sessionmaker(bind=engine)
        self.current_pair = None
        self.volume_threshold_std = 2.5
        self.basis_mean_window = 60
        self.spot_last_id = None
        self.futures_last_id = None
        self.volume_history = []
        self.max_volume_history = 100
        self.basis_history = []
        self.running = True
        self.req_session = requests.Session()

    def load_config(self):
        with self.Session() as session:
            configs = session.query(Config).all()
            config_dict = {c.key: c.value for c in configs}
            self.current_pair = config_dict.get('current_pair', 'BTC_USDT')
            self.volume_threshold_std = float(config_dict.get('volume_threshold_std', 2.5))
            self.basis_mean_window = int(config_dict.get('basis_mean_window', 60))
            logger.debug(f"Config loaded: pair={self.current_pair}, threshold={self.volume_threshold_std}")

    def get_spot_trades(self, pair, limit=100):
        url = "https://api.gateio.ws/api/v4/spot/trades"
        params = {'currency_pair': pair, 'limit': limit}
        try:
            resp = self.req_session.get(url, params=params, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Spot trades request failed: {e}")
            return []

    def get_futures_trades(self, contract, limit=100):
        url = "https://api.gateio.ws/api/v4/futures/usdt/trades"
        params = {'contract': contract, 'limit': limit}
        try:
            resp = self.req_session.get(url, params=params, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Futures trades request failed: {e}")
            return []

    def process_spot_trades(self, trades):
        if not trades:
            return
        new_trades = []
        for trade in trades:
            trade_id = trade['id']
            if trade_id == self.spot_last_id:
                break
            new_trades.append(trade)
        new_trades.reverse()

        with self.Session() as session:
            for trade in new_trades:
                pair = trade['currency_pair']
                if pair != self.current_pair:
                    continue
                trade_id = trade['id']
                price = float(trade['price'])
                amount = float(trade['amount'])
                volume = price * amount
                side = trade['side']
                ts = int(trade['create_time'])

                exists = session.query(SpotTrade).filter_by(trade_id=trade_id).first()
                if not exists:
                    spot_trade = SpotTrade(
                        trade_id=trade_id,
                        pair=pair,
                        price=price,
                        amount=amount,
                        volume=volume,
                        side=side,
                        timestamp=ts
                    )
                    session.add(spot_trade)
                    session.commit()

                    self.volume_history.append(volume)
                    if len(self.volume_history) > self.max_volume_history:
                        self.volume_history.pop(0)

                    if self.is_large_trade(volume):
                        alert = LargeTradeAlert(
                            pair=pair,
                            trade_id=trade_id,
                            volume=volume,
                            price=price,
                            side=side,
                            timestamp=ts,
                            threshold_used=self.volume_threshold_std
                        )
                        session.add(alert)
                        session.commit()
                        logger.info(f"LARGE TRADE: {volume:.2f} USDT {side} at {price}")

        if new_trades:
            self.spot_last_id = new_trades[-1]['id']
            logger.debug(f"Processed {len(new_trades)} new spot trades")

    def process_futures_trades(self, trades):
        if not trades:
            return
        new_trades = []
        for trade in trades:
            trade_id = trade['id']
            if trade_id == self.futures_last_id:
                break
            new_trades.append(trade)
        new_trades.reverse()

        with self.Session() as session:
            for trade in new_trades:
                contract = trade['contract']
                if contract != self.current_pair:
                    continue
                trade_id = trade['id']
                price = float(trade['price'])
                amount = float(trade['amount'])
                volume = price * amount
                side = 'buy' if trade['size'] > 0 else 'sell'
                ts = int(trade['create_time'])

                exists = session.query(FuturesTrade).filter_by(trade_id=trade_id).first()
                if not exists:
                    fut_trade = FuturesTrade(
                        trade_id=trade_id,
                        contract=contract,
                        price=price,
                        amount=amount,
                        volume=volume,
                        side=side,
                        timestamp=ts
                    )
                    session.add(fut_trade)
                    session.commit()

        if new_trades:
            self.futures_last_id = new_trades[-1]['id']
            logger.debug(f"Processed {len(new_trades)} new futures trades")

    def is_large_trade(self, volume):
        if len(self.volume_history) < 20:
            return False
        mean = np.mean(self.volume_history)
        std = np.std(self.volume_history)
        if std == 0:
            return False
        return volume > mean + self.volume_threshold_std * std

    def update_basis(self):
        with self.Session() as session:
            spot = session.query(SpotTrade).filter_by(pair=self.current_pair).order_by(desc(SpotTrade.timestamp)).first()
            futures = session.query(FuturesTrade).filter_by(contract=self.current_pair).order_by(desc(FuturesTrade.timestamp)).first()
            if spot and futures:
                basis_val = futures.price - spot.price
                basis_percent = (futures.price / spot.price - 1) * 100 if spot.price != 0 else 0
                ts = int(time.time())
                basis_entry = Basis(
                    pair=self.current_pair,
                    spot_price=spot.price,
                    futures_price=futures.price,
                    basis=basis_val,
                    basis_percent=basis_percent,
                    timestamp=ts
                )
                session.add(basis_entry)
                session.commit()
                self.basis_history.append((ts, basis_percent))
                cutoff = ts - self.basis_mean_window * 60
                self.basis_history = [(t, v) for t, v in self.basis_history if t >= cutoff]
                logger.debug(f"Basis updated: {basis_percent:.4f}%")

    def run(self):
        logger.info("Collector started")
        self.load_config()
        with self.Session() as session:
            last_spot = session.query(SpotTrade).filter_by(pair=self.current_pair).order_by(desc(SpotTrade.timestamp)).first()
            if last_spot:
                self.spot_last_id = last_spot.trade_id
            last_fut = session.query(FuturesTrade).filter_by(contract=self.current_pair).order_by(desc(FuturesTrade.timestamp)).first()
            if last_fut:
                self.futures_last_id = last_fut.trade_id

        cycle_count = 0
        while self.running:
            try:
                cycle_count += 1
                if cycle_count % 10 == 0:
                    self.load_config()

                spot_trades = self.get_spot_trades(self.current_pair)
                futures_trades = self.get_futures_trades(self.current_pair)

                self.process_spot_trades(spot_trades)
                self.process_futures_trades(futures_trades)

                if int(time.time()) % 5 == 0:
                    self.update_basis()

                time.sleep(2)

            except KeyboardInterrupt:
                logger.info("Stopping collector...")
                break
            except Exception as e:
                logger.exception("Unexpected error")
                time.sleep(5)

if __name__ == "__main__":
    collector = GateIORestCollector()
    collector.run()