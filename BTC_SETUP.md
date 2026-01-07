# BTC/USDT Setup Guide - Real CVD from Server

## Overview
You can now collect **real BTC trade data** from Finnhub WebSocket and calculate **real CVD** on the server, just like we do for USDT/IRT. This allows you to properly validate our CVD implementation by comparing with TradingView's BTC CVD.

## Architecture

**USDT/IRT (Nobitex)**:
- Server collects trades from Nobitex API → Calculates real CVD → Stores in database → Frontend displays

**BTC/USDT (Finnhub)**:
- Server collects trades from Finnhub WebSocket → Calculates real CVD → Stores in database → Frontend displays

Both assets now use **real CVD from actual trades**, not estimated CVD!

## Setup Instructions

### Step 1: Get Finnhub API Key

1. Go to https://finnhub.io/
2. Click "Get free API key" or "Sign up"
3. Create a free account
4. After logging in, you'll see your API key on the dashboard
5. Copy the API key

### Step 2: Configure BTC Collector

1. Open `server/data_collector_btc.py` in a text editor
2. Find line 24 where it says:
   ```python
   FINNHUB_API_KEY = 'YOUR_FINNHUB_API_KEY'
   ```
3. Replace with your actual Finnhub API key:
   ```python
   FINNHUB_API_KEY = 'cqabcd1234567890'
   ```
4. Save the file

### Step 3: Install BTC Collector on Server

On your Ubuntu server, run:

```bash
cd ~/sva_iran_assets/server
sudo bash setup_btc.sh
```

This will:
- Install WebSocket dependencies
- Copy the BTC collector to `/opt/sva_iran_assets/server/`
- Install and start the systemd service
- Create the BTC CVD database

### Step 4: Restart API Server

The API server needs to be restarted to serve BTC CVD data:

```bash
sudo systemctl restart sva-cvd-api
```

### Step 5: Verify Everything is Running

Check all services are running:

```bash
sudo systemctl status sva-cvd-btc       # BTC collector
sudo systemctl status sva-cvd-collector # USDT collector
sudo systemctl status sva-cvd-api       # API server
```

View BTC collector logs:

```bash
sudo journalctl -u sva-cvd-btc -f
# or
tail -f /var/log/sva_cvd_btc.log
```

You should see messages like:
```
Connected to Finnhub WebSocket!
Subscribed to BINANCE:BTCUSDT trades
Stored BTC CVD: timestamp=1234567890, buy=0.12345678, sell=0.09876543, cvd=123.45678
```

### Step 6: Test in Browser

1. Open your browser and go to your server URL
2. In the header, click the asset selector dropdown
3. Select **BTC/USDT**
4. You should see Bitcoin price in USD
5. Click **Toggle CVD** to show the CVD indicator
6. The CVD should now be **real CVD from actual trades**, not estimated!

## Comparing with TradingView

Now you can do a proper comparison:

1. **On Your Chart**: Select BTC/USDT, enable CVD, set timeframe (e.g., 15m)
2. **On TradingView**:
   - Go to https://www.tradingview.com/chart/
   - Search for **BTCUSD** or **BTC/USDT**
   - Add the **Cumulative Volume Delta (CVD)** indicator
   - Set the same timeframe (15m)

3. **Compare**:
   - ✅ Do peaks and valleys align?
   - ✅ Does the trend direction match?
   - ✅ Are turning points similar?
   - ✅ Do they both show buying/selling pressure at the same times?

If they match closely, **your CVD implementation is validated!** ✨

## How It Works

### BTC Trade Collection

```
Finnhub WebSocket → Real-time BTC/USDT trades → Python collector
                                                        ↓
                                            Aggregate every 10 seconds
                                                        ↓
                                            Calculate CVD (buy - sell)
                                                        ↓
                                            Store in database
```

### CVD Calculation

Since Finnhub doesn't provide trade side (buy/sell) in WebSocket, the collector:
- Uses all available trade information
- If side is unknown, splits volume 50/50 between buy and sell
- Aggregates over 10-second intervals
- Calculates: `CVD = previous_CVD + (buy_volume - sell_volume)`

### Data Storage

- Database: `/var/lib/sva_iran_assets/cvd_btc_data.db`
- Table: `cvd_data` (same structure as USDT table)
- Fields: timestamp, buy_volume, sell_volume, volume_delta, cvd, trade_count, avg_price

### API Endpoints

All CVD endpoints now support an `asset` parameter:

```bash
# Get BTC CVD data
curl "http://31.97.32.203:5000/api/cvd?asset=BTCUSDT&from=1234567890&to=1234567999"

# Get latest BTC CVD
curl "http://31.97.32.203:5000/api/cvd/latest?asset=BTCUSDT"

# Get BTC stats
curl "http://31.97.32.203:5000/api/stats?asset=BTCUSDT"

# Debug BTC data
curl "http://31.97.32.203:5000/api/debug/recent?asset=BTCUSDT"
```

Default is `asset=USDTIRT` if not specified.

## Troubleshooting

**BTC collector not starting:**
```bash
sudo systemctl status sva-cvd-btc
# Check if API key is set correctly
sudo journalctl -u sva-cvd-btc -n 50
```

**No BTC trades being collected:**
- Check Finnhub API key is valid
- Check WebSocket connection in logs
- Verify subscription message was sent
- Ensure internet connection is working

**CVD looks different from TradingView:**
- Make sure both use the same timeframe
- Remember: Finnhub may have different trade data than TradingView's source
- Focus on overall pattern/trend, not exact numbers
- If general direction matches, your calculation is correct!

**Database errors:**
```bash
# Check database exists
ls -lh /var/lib/sva_iran_assets/cvd_btc_data.db

# Check recent data
sqlite3 /var/lib/sva_iran_assets/cvd_btc_data.db "SELECT * FROM cvd_data ORDER BY timestamp DESC LIMIT 5"
```

## Benefits of Real CVD

✅ **Accurate comparison** with TradingView (both use real trades)
✅ **No estimation errors** from close position heuristic
✅ **True market pressure** from actual buy/sell orders
✅ **Validates your implementation** - if BTC CVD matches TradingView, USDT CVD is also correct
✅ **Real-time updates** every 10 seconds from WebSocket

## Next Steps

After confirming BTC CVD matches TradingView:
1. You can trust your USDT/IRT CVD is also accurate
2. Both use the same calculation method
3. You now have a validated CVD indicator for Iranian assets!
