# CVD Calculation Validation Guide

This guide explains how to verify that CVD (Cumulative Volume Delta) is being calculated correctly.

## 🎯 What is CVD?

**CVD = Cumulative sum of (Buy Volume - Sell Volume)**

- **Positive CVD change**: More buying than selling → Bullish pressure
- **Negative CVD change**: More selling than buying → Bearish pressure
- **CVD trend up**: Sustained buying pressure
- **CVD trend down**: Sustained selling pressure

## ✅ How to Validate CVD

### 1. Run Automated Tests

```bash
cd ~/sva_iran_assets/server
python3 test_cvd.py
```

This will run 5 comprehensive tests:
- ✅ Server connection
- ✅ Raw Nobitex trade data analysis
- ✅ CVD database integrity
- ✅ CVD correlation with market
- ✅ Database statistics

### 2. Manual Verification Steps

#### Step A: Check Raw Trade Data

```bash
# Fetch raw trades from Nobitex
curl "https://apiv2.nobitex.ir/v2/trades/USDTIRT" | jq '.trades[:5]'
```

**What to check:**
- Each trade has `type: "buy"` or `type: "sell"`
- Each trade has `volume` (amount traded)
- Trades are recent (within last few minutes)

#### Step B: Verify Buy/Sell Split

```bash
# Get latest CVD from your server
curl "http://YOUR_SERVER_IP:5000/api/cvd/latest" | jq
```

**Expected output:**
```json
{
  "success": true,
  "data": {
    "time": 1736174400,
    "cvd": 12345.67,
    "volume_delta": 23.45,
    "avg_price": 1478000
  }
}
```

**What to check:**
- `volume_delta` should match: (buy_volume - sell_volume) from trades
- `cvd` should accumulate over time
- Positive delta during price rallies, negative during dumps

#### Step C: Check CVD Accumulation

```bash
# Get last 10 CVD records
curl "http://YOUR_SERVER_IP:5000/api/cvd?limit=10" | jq '.data'
```

**Manual calculation:**
1. Take the CVD values: `[100, 105, 103, 110, 108, ...]`
2. Calculate deltas: `[5, -2, 7, -2, ...]`
3. Sum of deltas should equal: `CVD[last] - CVD[first]`

#### Step D: Visual Correlation Test

1. Open your chart: http://localhost:8000
2. Toggle CVD indicator
3. **Look for these patterns:**

**✅ CORRECT Behavior:**
- Price goes UP → CVD usually goes UP (green candles)
- Price goes DOWN → CVD usually goes DOWN (red candles)
- Strong price move → Large CVD candles
- Consolidation → Small CVD candles

**❌ INCORRECT Behavior:**
- CVD always flat (no movement)
- CVD moves opposite to price consistently
- CVD has impossible values (negative when should be positive)

### 3. Compare with Expected Patterns

#### Pattern 1: Bullish Trend
```
Price:  ↗️ ↗️ ↗️ ↗️
CVD:    ↗️ ↗️ ↗️ ↗️  ✅ Correct - CVD rises with price
```

#### Pattern 2: Bearish Trend
```
Price:  ↘️ ↘️ ↘️ ↘️
CVD:    ↘️ ↘️ ↘️ ↘️  ✅ Correct - CVD falls with price
```

#### Pattern 3: Divergence (Advanced)
```
Price:  ↗️ ↗️ ↗️
CVD:    → ↘️ ↘️  ⚠️  Bearish divergence - Warning sign!
```

### 4. Database Query Tests

If you have sqlite3 installed:

```bash
sqlite3 /var/lib/sva_iran_assets/cvd_data.db

# Check total records
SELECT COUNT(*) FROM cvd_data;

# Check latest 10 records
SELECT
    datetime(timestamp, 'unixepoch') as time,
    buy_volume,
    sell_volume,
    volume_delta,
    cvd
FROM cvd_data
ORDER BY timestamp DESC
LIMIT 10;

# Verify CVD calculation
SELECT
    timestamp,
    volume_delta,
    cvd,
    cvd - LAG(cvd) OVER (ORDER BY timestamp) as calculated_delta
FROM cvd_data
ORDER BY timestamp DESC
LIMIT 10;
```

**What to check:**
- `calculated_delta` should approximately equal `volume_delta`
- CVD should increase/decrease smoothly (no huge jumps)

## 🔍 Common Issues and Fixes

### Issue 1: CVD is Always Flat

**Symptoms:**
- CVD value never changes
- All volume_delta = 0

**Possible causes:**
- No trades being fetched
- API blocked
- Trade type field missing

**Fix:**
```bash
# Check logs
sudo journalctl -u sva-cvd-collector -n 50

# Should see: "Received 127 trades"
# If not, API might be blocked
```

### Issue 2: CVD Values Too Large/Small

**Symptoms:**
- CVD = 1,000,000+ (unrealistically high)
- CVD = 0.0001 (unrealistically low)

**Possible causes:**
- Volume calculation error
- Wrong data format

**Fix:**
- Check trade volumes are reasonable (10-1000 USDT typically)
- Verify `volume` field in trade data

### Issue 3: CVD Doesn't Match Price

**Symptoms:**
- Price up, CVD down consistently
- No correlation at all

**Possible causes:**
- Buy/sell types might be reversed
- Incorrect aggregation

**Fix:**
```bash
# Check raw trade data
curl "https://apiv2.nobitex.ir/v2/trades/USDTIRT" | jq '.trades[0]'

# Verify 'type' field shows 'buy' or 'sell'
```

## 📊 Expected Values for USDT/IRT

**Typical volume per minute:**
- Buy volume: 100-5000 USDT
- Sell volume: 100-5000 USDT
- Volume delta: -1000 to +1000 USDT

**CVD behavior:**
- Should change every minute
- Typical range over 1 hour: -10,000 to +10,000
- Should correlate with price trend

## ✨ Final Validation Checklist

- [ ] All automated tests pass (`python3 test_cvd.py`)
- [ ] CVD changes every minute (not flat)
- [ ] CVD generally correlates with price direction
- [ ] No errors in collector logs
- [ ] Database shows increasing record count
- [ ] Volume deltas are reasonable (-5000 to +5000)
- [ ] CVD accumulation math checks out
- [ ] Visual chart shows CVD candles matching price candles

## 🎓 Understanding CVD Limitations

**Our CVD uses estimations because:**
1. Nobitex only provides trade type (buy/sell), not actual taker side
2. We don't have orderbook depth data
3. Some trades might not have type information

**Despite this:**
- CVD is still highly useful for trend analysis
- Relative changes are accurate
- Divergences are detectable
- Better than no CVD at all!

## 📞 Troubleshooting

If CVD seems wrong:
1. Run `python3 test_cvd.py` - check all tests
2. Check server logs: `sudo journalctl -u sva-cvd-collector -f`
3. Verify API access: `curl https://apiv2.nobitex.ir/v2/trades/USDTIRT`
4. Check database: `sqlite3 /var/lib/sva_iran_assets/cvd_data.db "SELECT COUNT(*) FROM cvd_data"`

Still issues? Check:
- Server time is correct (affects timestamps)
- No data gaps (might need to backfill)
- Firewall allows API access
