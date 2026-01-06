#!/usr/bin/env python3
"""
Nobitex WebSocket CVD Data Collector
Real-time CVD calculation from WebSocket trades
"""

import asyncio
import json
import sqlite3
import time
import logging
import websockets
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/sva_cvd_websocket.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Configuration
DB_PATH = '/var/lib/sva_iran_assets/cvd_data.db'
WEBSOCKET_URL = 'wss://api.nobitex.ir/ws'
UPDATE_INTERVAL = 10  # Aggregate and store every 10 seconds

class CVDWebSocketCollector:
    def __init__(self):
        self.trades_buffer = []
        self.last_save_time = time.time()
        self.last_cvd = self.get_last_cvd()

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
            trade_type = trade['type']

            total_volume += volume
            total_price += price * volume

            if trade_type == 'buy':
                buy_volume += volume
            elif trade_type == 'sell':
                sell_volume += volume
            else:
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

            logger.info(f"Stored CVD: timestamp={timestamp}, "
                       f"buy={aggregated_data['buy_volume']:.2f}, "
                       f"sell={aggregated_data['sell_volume']:.2f}, "
                       f"delta={aggregated_data['volume_delta']:.2f}, "
                       f"cvd={current_cvd:.2f}")

        except Exception as e:
            logger.error(f"Error storing data: {e}")

    async def handle_trade(self, trade_data):
        """Process incoming trade"""
        try:
            # Parse trade data
            trade = {
                'type': trade_data.get('type', '').lower(),
                'volume': float(trade_data.get('volume', 0)),
                'price': float(trade_data.get('price', 0)),
                'time': trade_data.get('time', time.time())
            }

            self.trades_buffer.append(trade)

            # Check if we should save
            current_time = time.time()
            if current_time - self.last_save_time >= UPDATE_INTERVAL:
                aggregated = self.aggregate_trades()
                if aggregated:
                    self.store_data(aggregated)

                # Clear buffer and reset timer
                self.trades_buffer = []
                self.last_save_time = current_time

        except Exception as e:
            logger.error(f"Error handling trade: {e}")

    async def connect_and_listen(self):
        """Connect to WebSocket and listen for trades"""
        while True:
            try:
                logger.info(f"Connecting to Nobitex WebSocket: {WEBSOCKET_URL}")

                async with websockets.connect(WEBSOCKET_URL) as websocket:
                    logger.info("Connected to WebSocket!")

                    # Subscribe to USDT/IRT trades
                    subscribe_message = {
                        "event": "subscribe",
                        "channel": "trades",
                        "pair": "USDTIRT"
                    }

                    await websocket.send(json.dumps(subscribe_message))
                    logger.info("Subscribed to USDTIRT trades")

                    # Listen for messages
                    async for message in websocket:
                        try:
                            data = json.loads(message)

                            # Handle different message types
                            if data.get('event') == 'trade':
                                await self.handle_trade(data)
                            elif data.get('event') == 'subscribed':
                                logger.info(f"Subscription confirmed: {data}")

                        except json.JSONDecodeError:
                            logger.error(f"Invalid JSON: {message}")
                        except Exception as e:
                            logger.error(f"Error processing message: {e}")

            except websockets.exceptions.ConnectionClosed:
                logger.warning("WebSocket connection closed. Reconnecting in 5 seconds...")
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"WebSocket error: {e}. Reconnecting in 5 seconds...")
                await asyncio.sleep(5)

async def main():
    """Main async loop"""
    logger.info("Starting Nobitex WebSocket CVD Collector...")
    logger.info(f"Update interval: {UPDATE_INTERVAL} seconds")

    collector = CVDWebSocketCollector()
    await collector.connect_and_listen()

if __name__ == '__main__':
    asyncio.run(main())
