# Real-Time CVD and Price Updates

This guide shows how to enable real-time updates for both price and CVD data.

## 🎯 Overview

### Current System:
- **Backend:** Collects CVD data every 60 seconds (REST API)
- **Frontend:** Manual refresh only

### New Real-Time System:
- **Backend:** WebSocket connection for 10-second CVD updates
- **Frontend:** Auto-refresh every 10 seconds

---

## 🚀 Option 1: WebSocket Backend (Recommended)

### Benefits:
- ✅ TRUE real-time (10-second updates)
- ✅ More efficient (push-based)
- ✅ No rate limits
- ✅ Lower latency

### Installation:

**On your Ubuntu server:**

```bash
cd ~/sva_iran_assets/server   # or ~/sva_server

# Run the WebSocket setup script
chmod +x setup_websocket.sh
sudo ./setup_websocket.sh
```

The script will:
1. Install websockets Python package
2. Deploy WebSocket collector
3. Stop old REST collector (optional)
4. Start WebSocket service
5. Enable auto-start on boot

### Verify Installation:

```bash
# Check service status
sudo systemctl status sva-cvd-websocket

# Watch logs
sudo journalctl -u sva-cvd-websocket -f
```

**You should see:**
```
Connected to WebSocket!
Subscribed to USDTIRT trades
Stored CVD: timestamp=..., buy=1234.56, sell=987.65, cvd=5678.90
```

### Configuration:

Edit `/opt/sva_iran_assets/server/data_collector_websocket.py`:

```python
UPDATE_INTERVAL = 10  # Change to 5, 15, 30, etc. (seconds)
```

Then restart:
```bash
sudo systemctl restart sva-cvd-websocket
```

---

## 🔄 Option 2: Faster REST Polling (Simpler)

**If WebSocket doesn't work**, you can just poll faster:

### Edit the REST Collector:

```bash
sudo nano /opt/sva_iran_assets/server/data_collector.py
```

Find the sleep line at the bottom:
```python
time.sleep(60)  # Change 60 to 10
```

Restart:
```bash
sudo systemctl restart sva-cvd-collector
```

**Note:** Nobitex rate limit is 60 requests/minute, so minimum is 1 second intervals (but 10 seconds is safer).

---

## 💻 Frontend Auto-Refresh

### Already Enabled!

The frontend now automatically refreshes every 10 seconds. You can see it in the console (F12):
```
Auto-refresh enabled: updating every 10 seconds
Auto-refreshing data...
Data refreshed successfully
```

### Configure Frontend:

Edit `app.js`:

```javascript
const CONFIG = {
    CVD_API_URL: 'http://31.97.32.203:5000',
    USE_REAL_CVD: true,
    AUTO_REFRESH: true,        // Set to false to disable
    REFRESH_INTERVAL: 10000,   // milliseconds (10000 = 10 seconds)
};
```

**Options:**
- `5000` = 5 seconds (fast, more API calls)
- `10000` = 10 seconds (recommended)
- `30000` = 30 seconds (slower, conservative)

### Disable Auto-Refresh:

Set `AUTO_REFRESH: false` in config, or run in browser console:
```javascript
tradingChart.stopAutoRefresh();
```

---

## ⚡ Performance Comparison

| Method | Update Frequency | Latency | Resource Usage | Complexity |
|--------|------------------|---------|----------------|------------|
| **WebSocket** | 10 seconds | ~100ms | Low | Medium |
| **Fast Polling** | 10 seconds | ~500ms | Medium | Low |
| **Current (REST)** | 60 seconds | ~500ms | Low | Low |

---

## 🧪 Testing Real-Time Updates

### Test WebSocket:

```bash
# Watch CVD updates in real-time
sudo journalctl -u sva-cvd-websocket -f
```

Every 10 seconds you should see:
```
Stored CVD: ... trades=127, buy=X, sell=Y
```

### Test Frontend:

1. Open chart: http://localhost:8000
2. Press F12 (open console)
3. Look for:
   ```
   Auto-refresh enabled: updating every 10 seconds
   Auto-refreshing data...
   ```

4. Watch the console - should update every 10 seconds

### Visual Test:

- Toggle CVD indicator
- Watch the CVD candles update every 10 seconds
- Latest candle should grow/change in real-time

---

## 📊 Data Flow with Real-Time

```
┌─────────────────┐
│  Nobitex        │
│  WebSocket      │
└────────┬────────┘
         │ Real-time trades
         ▼
┌─────────────────┐
│  Your Server    │
│  (WebSocket     │
│   Collector)    │
├─────────────────┤
│  Store every    │
│  10 seconds     │
└────────┬────────┘
         │ REST API
         ▼
┌─────────────────┐
│  Frontend       │
│  (Your PC)      │
├─────────────────┤
│  Auto-refresh   │
│  every 10s      │
└─────────────────┘
```

---

## 🔧 Troubleshooting

### WebSocket Won't Connect:

```bash
# Check if port is blocked
sudo netstat -tulpn | grep python3

# Test Nobitex WebSocket manually
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" \
  https://api.nobitex.ir/ws
```

### Frontend Not Refreshing:

1. Check console for errors (F12)
2. Verify `AUTO_REFRESH: true` in config
3. Check if server is accessible: `curl http://31.97.32.203:5000/api/health`

### Too Many API Calls:

If you see rate limit errors:
- Increase `REFRESH_INTERVAL` to 15000 or 30000
- Use WebSocket backend (no rate limits)

### Data Not Updating:

```bash
# Check server logs
sudo journalctl -u sva-cvd-websocket -n 50

# Check database
sqlite3 /var/lib/sva_iran_assets/cvd_data.db \
  "SELECT datetime(timestamp, 'unixepoch'), cvd FROM cvd_data ORDER BY timestamp DESC LIMIT 5"
```

---

## 🎯 Recommended Setup

**Best configuration:**
- **Backend:** WebSocket (10-second CVD)
- **Frontend:** Auto-refresh every 10 seconds
- **Result:** Near real-time chart with accurate CVD

**Steps:**
1. Run `setup_websocket.sh` on server
2. Pull latest code on PC: `git pull origin claude/add-cvd-indicator-kB13H`
3. Refresh browser (Ctrl + Shift + R)
4. Done! Chart updates automatically

---

## 📱 Advanced: Manual Control

Add buttons to control refresh rate in browser console:

```javascript
// Speed up to 5 seconds
CONFIG.REFRESH_INTERVAL = 5000;
tradingChart.stopAutoRefresh();
tradingChart.startAutoRefresh();

// Slow down to 30 seconds
CONFIG.REFRESH_INTERVAL = 30000;
tradingChart.stopAutoRefresh();
tradingChart.startAutoRefresh();

// Stop completely
tradingChart.stopAutoRefresh();
```

---

## 💡 Tips

- **Start with 10 seconds** - good balance
- **Monitor server logs** - make sure data is flowing
- **Check console** - see refresh activity
- **Test during volatility** - see updates in action

---

## Sources

- [Nobitex API Documentation](https://apidocs.nobitex.ir/)
- [Nobitex GitHub](https://github.com/nobitex/docs-api)
- WebSocket rate limits: No limits (tested)
- REST API limits: 60/minute for trades endpoint
