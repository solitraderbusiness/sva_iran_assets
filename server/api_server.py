#!/usr/bin/env python3
"""
CVD Data API Server
Serves historical CVD data to the frontend
"""

import sqlite3
import json
import os
from flask import Flask, jsonify, request
from flask_cors import CORS
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# Configuration from environment variables
DB_PATH_USDT = os.getenv('DB_PATH_USDT', '/var/lib/sva_iran_assets/cvd_data.db')
DB_PATH_BTC = os.getenv('DB_PATH_BTC', '/var/lib/sva_iran_assets/cvd_btc_data.db')

def get_db_connection(asset='USDTIRT'):
    """Get database connection based on asset"""
    db_path = DB_PATH_BTC if asset == 'BTCUSDT' else DB_PATH_USDT
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'service': 'CVD Data API'})

@app.route('/api/cvd', methods=['GET'])
def get_cvd_data():
    """
    Get CVD data for specified timeframe
    Query params:
    - asset: USDTIRT or BTCUSDT (default: USDTIRT)
    - from: Unix timestamp (optional)
    - to: Unix timestamp (optional)
    - limit: Max records to return (default: 1000)
    """
    try:
        asset = request.args.get('asset', default='USDTIRT', type=str)
        from_ts = request.args.get('from', type=int)
        to_ts = request.args.get('to', type=int)
        limit = request.args.get('limit', default=1000, type=int)

        conn = get_db_connection(asset)
        cursor = conn.cursor()

        # Build query
        query = 'SELECT * FROM cvd_data WHERE 1=1'
        params = []

        if from_ts:
            query += ' AND timestamp >= ?'
            params.append(from_ts)

        if to_ts:
            query += ' AND timestamp <= ?'
            params.append(to_ts)

        query += ' ORDER BY timestamp ASC LIMIT ?'
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        # Convert to list of dicts
        data = []
        for row in rows:
            data.append({
                'time': row['timestamp'],
                'buy_volume': row['buy_volume'],
                'sell_volume': row['sell_volume'],
                'volume_delta': row['volume_delta'],
                'cvd': row['cvd'],
                'trade_count': row['trade_count'],
                'avg_price': row['avg_price']
            })

        conn.close()

        return jsonify({
            'success': True,
            'data': data,
            'count': len(data)
        })

    except Exception as e:
        logger.error(f"Error fetching CVD data: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/cvd/latest', methods=['GET'])
def get_latest_cvd():
    """
    Get latest CVD value
    Query params:
    - asset: USDTIRT or BTCUSDT (default: USDTIRT)
    """
    try:
        asset = request.args.get('asset', default='USDTIRT', type=str)
        conn = get_db_connection(asset)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM cvd_data
            ORDER BY timestamp DESC
            LIMIT 1
        ''')

        row = cursor.fetchone()
        conn.close()

        if row:
            return jsonify({
                'success': True,
                'data': {
                    'time': row['timestamp'],
                    'cvd': row['cvd'],
                    'volume_delta': row['volume_delta'],
                    'avg_price': row['avg_price']
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No data available'
            }), 404

    except Exception as e:
        logger.error(f"Error fetching latest CVD: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """
    Get database statistics
    Query params:
    - asset: USDTIRT or BTCUSDT (default: USDTIRT)
    """
    try:
        asset = request.args.get('asset', default='USDTIRT', type=str)
        conn = get_db_connection(asset)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) as count FROM cvd_data')
        count = cursor.fetchone()['count']

        cursor.execute('SELECT MIN(timestamp) as first, MAX(timestamp) as last FROM cvd_data')
        stats = cursor.fetchone()

        conn.close()

        return jsonify({
            'success': True,
            'stats': {
                'total_records': count,
                'first_timestamp': stats['first'],
                'last_timestamp': stats['last']
            }
        })

    except Exception as e:
        logger.error(f"Error fetching stats: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/debug/recent', methods=['GET'])
def get_debug_recent():
    """
    Get detailed information about recent data for debugging
    Query params:
    - asset: USDTIRT or BTCUSDT (default: USDTIRT)
    """
    try:
        asset = request.args.get('asset', default='USDTIRT', type=str)
        conn = get_db_connection(asset)
        cursor = conn.cursor()

        # Get last 5 records with full details
        cursor.execute('''
            SELECT * FROM cvd_data
            ORDER BY timestamp DESC
            LIMIT 5
        ''')
        rows = cursor.fetchall()

        # Convert to detailed format
        data = []
        for row in rows:
            data.append({
                'timestamp': row['timestamp'],
                'buy_volume': row['buy_volume'],
                'sell_volume': row['sell_volume'],
                'volume_delta': row['volume_delta'],
                'cvd': row['cvd'],
                'trade_count': row['trade_count'],
                'avg_price': row['avg_price']
            })

        conn.close()

        # Calculate some validation metrics
        if len(data) >= 2:
            cvd_change = data[0]['cvd'] - data[1]['cvd']
            expected_change = data[0]['volume_delta']

            validation = {
                'cvd_accumulation_correct': abs(cvd_change - expected_change) < 0.01,
                'latest_cvd_change': cvd_change,
                'latest_volume_delta': expected_change
            }
        else:
            validation = {}

        return jsonify({
            'success': True,
            'data': data,
            'validation': validation
        })

    except Exception as e:
        logger.error(f"Error in debug endpoint: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    # Configuration from environment variables
    host = os.getenv('API_HOST', '0.0.0.0')
    port = int(os.getenv('API_PORT', '5000'))

    logger.info(f"Starting CVD API Server on {host}:{port}")
    app.run(host=host, port=port, debug=False)
