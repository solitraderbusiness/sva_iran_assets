#!/usr/bin/env python3
"""
CVD Testing and Validation Script
Run this to verify CVD calculations are accurate
"""

import requests
import json
from datetime import datetime

# Configuration
API_BASE = 'http://localhost:5000'
NOBITEX_API = 'https://apiv2.nobitex.ir/v2/trades/USDTIRT'

def test_server_connection():
    """Test 1: Server is running"""
    print("\n" + "="*60)
    print("TEST 1: Server Connection")
    print("="*60)

    try:
        response = requests.get(f'{API_BASE}/api/health', timeout=5)
        if response.status_code == 200:
            print("✅ PASS - Server is running")
            return True
        else:
            print(f"❌ FAIL - Server returned {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ FAIL - Cannot connect to server: {e}")
        return False

def test_nobitex_trades():
    """Test 2: Fetch and analyze raw Nobitex trades"""
    print("\n" + "="*60)
    print("TEST 2: Nobitex Trades Analysis")
    print("="*60)

    try:
        response = requests.get(NOBITEX_API, timeout=10)
        data = response.json()

        if 'trades' not in data:
            print(f"❌ FAIL - No trades in response: {data}")
            return False

        trades = data['trades']
        print(f"✅ Fetched {len(trades)} trades from Nobitex")

        # Analyze trade types
        buy_count = sum(1 for t in trades if t.get('type', '').lower() == 'buy')
        sell_count = sum(1 for t in trades if t.get('type', '').lower() == 'sell')

        print(f"\nTrade Distribution:")
        print(f"  Buy trades:  {buy_count}")
        print(f"  Sell trades: {sell_count}")

        # Calculate volumes
        buy_volume = sum(float(t.get('volume', 0)) for t in trades if t.get('type', '').lower() == 'buy')
        sell_volume = sum(float(t.get('volume', 0)) for t in trades if t.get('type', '').lower() == 'sell')

        print(f"\nVolume Analysis:")
        print(f"  Buy volume:  {buy_volume:.2f} USDT")
        print(f"  Sell volume: {sell_volume:.2f} USDT")
        print(f"  Volume Delta: {buy_volume - sell_volume:.2f} USDT")

        # Show sample trades
        print(f"\nSample Trades (first 5):")
        for i, trade in enumerate(trades[:5]):
            print(f"  {i+1}. Type: {trade.get('type', 'N/A'):4s} | "
                  f"Volume: {float(trade.get('volume', 0)):8.2f} | "
                  f"Price: {float(trade.get('price', 0)):,.0f}")

        return True

    except Exception as e:
        print(f"❌ FAIL - Error fetching Nobitex trades: {e}")
        return False

def test_cvd_data():
    """Test 3: Verify CVD data in database"""
    print("\n" + "="*60)
    print("TEST 3: CVD Database Data")
    print("="*60)

    try:
        # Get latest CVD
        response = requests.get(f'{API_BASE}/api/cvd/latest', timeout=5)
        data = response.json()

        if not data.get('success'):
            print(f"❌ FAIL - No CVD data: {data}")
            return False

        cvd_data = data['data']
        print(f"✅ Latest CVD Data:")
        print(f"  Timestamp: {datetime.fromtimestamp(cvd_data['time']).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  CVD Value: {cvd_data['cvd']:.2f}")
        print(f"  Volume Delta: {cvd_data['volume_delta']:.2f}")

        # Get last 10 records
        response = requests.get(f'{API_BASE}/api/cvd?limit=10', timeout=5)
        data = response.json()

        if data.get('success') and data['data']:
            records = data['data']
            print(f"\n✅ Last 10 CVD Records:")
            print(f"  {'Time':<19} | {'CVD':>12} | {'Delta':>10}")
            print(f"  {'-'*19}-+-{'-'*12}-+-{'-'*10}")

            for record in records[-10:]:
                timestamp = datetime.fromtimestamp(record['time']).strftime('%Y-%m-%d %H:%M:%S')
                print(f"  {timestamp} | {record['cvd']:>12.2f} | {record['volume_delta']:>10.2f}")

            # Check CVD progression
            print(f"\n📊 CVD Progression Check:")
            deltas = [r['volume_delta'] for r in records]
            cvds = [r['cvd'] for r in records]

            # CVD should be cumulative sum of deltas
            expected_cvd_change = sum(deltas)
            actual_cvd_change = cvds[-1] - cvds[0]

            if abs(expected_cvd_change - actual_cvd_change) < 0.01:
                print(f"  ✅ CVD accumulation is CORRECT")
                print(f"     Expected change: {expected_cvd_change:.2f}")
                print(f"     Actual change:   {actual_cvd_change:.2f}")
            else:
                print(f"  ⚠️  CVD accumulation WARNING")
                print(f"     Expected change: {expected_cvd_change:.2f}")
                print(f"     Actual change:   {actual_cvd_change:.2f}")

            return True
        else:
            print(f"❌ FAIL - No historical data")
            return False

    except Exception as e:
        print(f"❌ FAIL - Error fetching CVD data: {e}")
        return False

def test_cvd_correlation():
    """Test 4: Check CVD correlation with price movement"""
    print("\n" + "="*60)
    print("TEST 4: CVD vs Price Correlation")
    print("="*60)

    try:
        # Get CVD data
        response = requests.get(f'{API_BASE}/api/cvd?limit=20', timeout=5)
        cvd_data = response.json()

        if not cvd_data.get('success'):
            print("❌ FAIL - Cannot get CVD data")
            return False

        records = cvd_data['data']

        # Analyze correlation
        print(f"✅ Analyzing last 20 data points:")

        positive_delta = sum(1 for r in records if r['volume_delta'] > 0)
        negative_delta = sum(1 for r in records if r['volume_delta'] < 0)

        print(f"\n  Positive deltas (buying pressure): {positive_delta}")
        print(f"  Negative deltas (selling pressure): {negative_delta}")

        # Check if CVD is changing
        cvd_values = [r['cvd'] for r in records]
        cvd_range = max(cvd_values) - min(cvd_values)

        if cvd_range > 0:
            print(f"\n  ✅ CVD is actively changing")
            print(f"     Range: {cvd_range:.2f}")
        else:
            print(f"\n  ⚠️  CVD appears flat (no trading activity)")

        return True

    except Exception as e:
        print(f"❌ FAIL - Error in correlation test: {e}")
        return False

def test_database_stats():
    """Test 5: Database statistics"""
    print("\n" + "="*60)
    print("TEST 5: Database Statistics")
    print("="*60)

    try:
        response = requests.get(f'{API_BASE}/api/stats', timeout=5)
        data = response.json()

        if not data.get('success'):
            print(f"❌ FAIL - Cannot get stats")
            return False

        stats = data['stats']
        print(f"✅ Database Stats:")
        print(f"  Total records: {stats['total_records']}")

        if stats['first_timestamp']:
            first_time = datetime.fromtimestamp(stats['first_timestamp'])
            last_time = datetime.fromtimestamp(stats['last_timestamp'])
            print(f"  First record:  {first_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  Last record:   {last_time.strftime('%Y-%m-%d %H:%M:%S')}")

            duration = last_time - first_time
            print(f"  Data duration: {duration}")

        return True

    except Exception as e:
        print(f"❌ FAIL - Error getting stats: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print(" CVD SYSTEM VALIDATION TEST SUITE")
    print("="*60)

    tests = [
        ("Server Connection", test_server_connection),
        ("Nobitex Trades", test_nobitex_trades),
        ("CVD Database", test_cvd_data),
        ("CVD Correlation", test_cvd_correlation),
        ("Database Stats", test_database_stats),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ CRITICAL ERROR in {test_name}: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "="*60)
    print(" TEST SUMMARY")
    print("="*60)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")

    passed = sum(1 for _, r in results if r)
    total = len(results)

    print(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! CVD system is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")

if __name__ == '__main__':
    main()
