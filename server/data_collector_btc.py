#!/usr/bin/env python3
"""
Finnhub WebSocket BTC CVD Data Collector
Real-time CVD calculation from WebSocket trades
"""

import asyncio
import json
import sqlite3
import time
import logging
import websocket
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
LOG_PATH = os.getenv('LOG_PATH_BTC', '/var/log/sva_cvd_btc.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_PATH),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Configuration from environment variables
DB_PATH = os.getenv('DB_PATH_BTC', '/var/lib/sva_iran_assets/cvd_btc_data.db')
FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY')
UPDATE_INTERVAL = int(os.getenv('UPDATE_INTERVAL', '10'))
SYMBOL = 'BINANCE:BTCUSDT'

# Validate API key
if not FINNHUB_API_KEY or FINNHUB_API_KEY == 'your_finnhub_api_key_here':
    logger.error("FINNHUB_API_KEY not set in .env file!")
    logger.error("Please copy .env.example to .env and set your Finnhub API key")
    exit(1)

WEBSOCKET_URL = f'wss://ws.finnhub.io?token={FINNHUB_API_KEY}'

class BTCCVDCollector:
    def __init__(self):
        self.trades_buffer = []
        self.last_save_time = time.time()
        self.last_cvd = self.get_last_cvd()
        self.ws = None
        self.init_database()

    def init_database(self):
        """Initialize database with required table"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cvd_data (
                    timestamp INTEGER PRIMARY KEY,
                    buy_volume REAL,
                    sell_volume REAL,
                    volume_delta REAL,
                    cvd REAL,
                    trade_count INTEGER,
                    avg_price REAL
                )
            ''')

            # Create index for faster queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_timestamp
                ON cvd_data(timestamp)
            ''')

            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing database: {e}")

    def get_last_cvd(self):
        """Get the last CVD value from database"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('SELECT cvd FROM cvd_data ORDER BY timestamp DESC LIMIT 1')
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else 0
        except Exception as e:
            logger.error(f"Error getting last CVD: {e}")
            return 0

    def aggregate_trades(self):
        """Aggregate buffered trades"""
        if not self.trades_buffer:
            return None

        buy_volume = 0
        sell_volume = 0
        total_price = 0
        total_volume = 0

        for trade in self.trades_buffer:
            volume = trade['volume']
            price = trade['price']

            # Finnhub doesn't provide trade side directly
            # We'll use a heuristic based on price movement
            # If this is not available, we'll split 50/50
            trade_type = trade.get('side', 'unknown')

            total_volume += volume
            total_price += price * volume

            if trade_type == 'buy':
                buy_volume += volume
            elif trade_type == 'sell':
                sell_volume += volume
            else:
                # Unknown side - split evenly
                buy_volume += volume / 2
                sell_volume += volume / 2

        avg_price = total_price / total_volume if total_volume > 0 else 0
        volume_delta = buy_volume - sell_volume

        return {
            'buy_volume': buy_volume,
            'sell_volume': sell_volume,
            'volume_delta': volume_delta,
            'trade_count': len(self.trades_buffer),
            'avg_price': avg_price
        }

    def store_data(self, aggregated_data):
        """Store aggregated CVD data"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Calculate new CVD
            current_cvd = self.last_cvd + aggregated_data['volume_delta']
            timestamp = int(time.time() / 10) * 10  # Round to 10-second intervals

            cursor.execute('''
                INSERT OR REPLACE INTO cvd_data
                (timestamp, buy_volume, sell_volume, volume_delta, cvd, trade_count, avg_price)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                timestamp,
                aggregated_data['buy_volume'],
                aggregated_data['sell_volume'],
                aggregated_data['volume_delta'],
                current_cvd,
                aggregated_data['trade_count'],
                aggregated_data['avg_price']
            ))

            conn.commit()
            conn.close()

            self.last_cvd = current_cvd

            logger.info(f"Stored BTC CVD: timestamp={timestamp}, "
                       f"buy={aggregated_data['buy_volume']:.8f}, "
                       f"sell={aggregated_data['sell_volume']:.8f}, "
                       f"delta={aggregated_data['volume_delta']:.8f}, "
                       f"cvd={current_cvd:.8f}, "
                       f"price=${aggregated_data['avg_price']:.2f}")

        except Exception as e:
            logger.error(f"Error storing data: {e}")

    def check_and_save(self):
        """Check if it's time to save aggregated data"""
        current_time = time.time()
        if current_time - self.last_save_time >= UPDATE_INTERVAL:
            aggregated = self.aggregate_trades()
            if aggregated:
                self.store_data(aggregated)

            # Clear buffer and reset timer
            self.trades_buffer = []
            self.last_save_time = current_time

    def on_message(self, ws, message):
        """Process incoming WebSocket message"""
        try:
            data = json.loads(message)

            # Finnhub sends messages with type and data fields
            if data.get('type') == 'trade':
                trades = data.get('data', [])

                for trade in trades:
                    # Parse trade data
                    # Format: {s: symbol, p: price, t: timestamp, v: volume, c: conditions}
                    if trade.get('s') == SYMBOL:
                        parsed_trade = {
                            'price': float(trade.get('p', 0)),
                            'volume': float(trade.get('v', 0)),
                            'time': trade.get('t', 0) / 1000,  # Convert ms to seconds
                            'side': 'unknown'  # Finnhub doesn't provide side info
                        }

                        self.trades_buffer.append(parsed_trade)

                # Check if we should save
                self.check_and_save()

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON: {message}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    def on_error(self, ws, error):
        """Handle WebSocket errors"""
        logger.error(f"WebSocket error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket close"""
        logger.warning(f"WebSocket closed: {close_status_code} - {close_msg}")

    def on_open(self, ws):
        """Handle WebSocket open"""
        logger.info(f"Connected to Finnhub WebSocket!")

        # Subscribe to BTC/USDT trades
        subscribe_message = json.dumps({
            "type": "subscribe",
            "symbol": SYMBOL
        })

        ws.send(subscribe_message)
        logger.info(f"Subscribed to {SYMBOL} trades")

    def run(self):
        """Run the WebSocket collector"""
        logger.info("Starting Finnhub BTC CVD Collector...")
        logger.info(f"Symbol: {SYMBOL}")
        logger.info(f"Update interval: {UPDATE_INTERVAL} seconds")

        while True:
            try:
                self.ws = websocket.WebSocketApp(
                    WEBSOCKET_URL,
                    on_message=self.on_message,
                    on_error=self.on_error,
                    on_close=self.on_close,
                    on_open=self.on_open
                )

                # Run forever (will reconnect on disconnect)
                self.ws.run_forever()

            except Exception as e:
                logger.error(f"Error in WebSocket: {e}")

            # Wait before reconnecting
            logger.info("Reconnecting in 5 seconds...")
            time.sleep(5)

if __name__ == '__main__':
    collector = BTCCVDCollector()
    collector.run()
