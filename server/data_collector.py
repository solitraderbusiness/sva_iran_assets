#!/usr/bin/env python3
"""
Nobitex CVD Data Collector
Fetches trades every minute and stores buy/sell volume data
"""

import sqlite3
import time
import requests
import json
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/sva_cvd_collector.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Database setup
DB_PATH = '/var/lib/sva_iran_assets/cvd_data.db'
API_URL = 'https://apiv2.nobitex.ir/v2/trades/USDTIRT'

def init_database():
    """Initialize SQLite database with required tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cvd_data (
            timestamp INTEGER PRIMARY KEY,
            buy_volume REAL NOT NULL,
            sell_volume REAL NOT NULL,
            volume_delta REAL NOT NULL,
            cvd REAL NOT NULL,
            trade_count INTEGER NOT NULL,
            avg_price REAL NOT NULL
        )
    ''')

    # Create index for faster queries
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_timestamp
        ON cvd_data(timestamp DESC)
    ''')

    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")

def fetch_trades():
    """Fetch recent trades from Nobitex API"""
    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()

        if 'trades' in data:
            return data['trades']
        else:
            logger.error(f"Unexpected API response format: {data}")
            return []

    except requests.RequestException as e:
        logger.error(f"Error fetching trades: {e}")
        return []

def aggregate_trades(trades):
    """Aggregate trades to calculate buy/sell volume"""
    buy_volume = 0
    sell_volume = 0
    total_volume = 0
    total_price = 0

    for trade in trades:
        volume = float(trade.get('volume', 0))
        price = float(trade.get('price', 0))
        trade_type = trade.get('type', '').lower()

        total_volume += volume
        total_price += price * volume

        if trade_type == 'buy':
            buy_volume += volume
        elif trade_type == 'sell':
            sell_volume += volume
        else:
            # If type is unknown, split evenly
            buy_volume += volume / 2
            sell_volume += volume / 2

    avg_price = total_price / total_volume if total_volume > 0 else 0

    return {
        'buy_volume': buy_volume,
        'sell_volume': sell_volume,
        'volume_delta': buy_volume - sell_volume,
        'trade_count': len(trades),
        'avg_price': avg_price
    }

def get_last_cvd():
    """Get the last CVD value from database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('SELECT cvd FROM cvd_data ORDER BY timestamp DESC LIMIT 1')
        result = cursor.fetchone()

        conn.close()

        return result[0] if result else 0

    except sqlite3.Error as e:
        logger.error(f"Database error getting last CVD: {e}")
        return 0

def store_data(timestamp, aggregated_data):
    """Store aggregated data in database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Get last CVD and add current delta
        last_cvd = get_last_cvd()
        current_cvd = last_cvd + aggregated_data['volume_delta']

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

        logger.info(f"Stored data: timestamp={timestamp}, "
                   f"buy={aggregated_data['buy_volume']:.2f}, "
                   f"sell={aggregated_data['sell_volume']:.2f}, "
                   f"delta={aggregated_data['volume_delta']:.2f}, "
                   f"cvd={current_cvd:.2f}")

    except sqlite3.Error as e:
        logger.error(f"Database error storing data: {e}")

def collect_data():
    """Main data collection function"""
    logger.info("Fetching trades from Nobitex...")

    trades = fetch_trades()

    if not trades:
        logger.warning("No trades received from API")
        return

    logger.info(f"Received {len(trades)} trades")

    # Aggregate trades for current minute
    aggregated = aggregate_trades(trades)

    # Use current minute timestamp (rounded down)
    timestamp = int(time.time() / 60) * 60

    # Store in database
    store_data(timestamp, aggregated)

def cleanup_old_data(days_to_keep=90):
    """Remove data older than specified days"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cutoff_timestamp = int(time.time()) - (days_to_keep * 24 * 60 * 60)

        cursor.execute('DELETE FROM cvd_data WHERE timestamp < ?', (cutoff_timestamp,))
        deleted = cursor.rowcount

        if deleted > 0:
            logger.info(f"Cleaned up {deleted} old records")

        conn.commit()
        conn.close()

    except sqlite3.Error as e:
        logger.error(f"Error cleaning up old data: {e}")

def main():
    """Main loop"""
    logger.info("Starting Nobitex CVD Data Collector...")

    # Initialize database
    init_database()

    # Main collection loop
    while True:
        try:
            collect_data()

            # Cleanup old data once per day (check every hour)
            if int(time.time()) % 3600 == 0:
                cleanup_old_data()

            # Wait 60 seconds before next collection
            time.sleep(60)

        except KeyboardInterrupt:
            logger.info("Shutting down gracefully...")
            break
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            time.sleep(60)  # Wait before retrying

if __name__ == '__main__':
    main()
