# Quick Start Guide

## First-Time Setup (5 minutes)

### 1. Get Finnhub API Key
- Go to https://finnhub.io/
- Sign up (free)
- Copy your API key

### 2. Configure Server

```bash
cd ~/sva_iran_assets

# Create .env file
cp .env.example .env

# Edit and add your API key
nano .env
```

Set this line:
```
FINNHUB_API_KEY=your_actual_api_key_here
```

Save and exit (Ctrl+X, Y, Enter)

### 3. Configure Frontend

```bash
# Create config.js
cp config.example.js config.js

# Edit and add your API key
nano config.js
```

Set this line:
```javascript
FINNHUB_API_KEY: 'your_actual_api_key_here',
```

Save and exit (Ctrl+X, Y, Enter)

### 4. Install Services

```bash
cd server

# Install USDT/IRT collector
sudo bash setup.sh

# Install BTC/USDT collector
sudo bash setup_btc.sh
```

### 5. Deploy Frontend

```bash
cd ~/sva_iran_assets

# Copy to web server
sudo cp index.html /var/www/html/
sudo cp styles.css /var/www/html/
sudo cp app.js /var/www/html/
sudo cp config.js /var/www/html/
```

### 6. Open in Browser

```
http://your-server-ip/
```

## Quick Commands

### Check Services
```bash
sudo systemctl status sva-cvd-collector  # USDT
sudo systemctl status sva-cvd-btc        # BTC
sudo systemctl status sva-cvd-api        # API
```

### View Logs
```bash
sudo journalctl -u sva-cvd-collector -f  # USDT logs
sudo journalctl -u sva-cvd-btc -f        # BTC logs
sudo journalctl -u sva-cvd-api -f        # API logs
```

### Restart Services
```bash
sudo systemctl restart sva-cvd-collector
sudo systemctl restart sva-cvd-btc
sudo systemctl restart sva-cvd-api
```

## Validate CVD with TradingView

1. **Your Chart**: Select BTC/USDT, toggle CVD, set 15m timeframe
2. **TradingView**: Open BTCUSDT, add CVD indicator, set 15m
3. **Compare**: Peaks, valleys, and trends should align

If they match → Your CVD is validated! ✅

## Troubleshooting

**API key error?**
```bash
# Check .env exists
cat ~/sva_iran_assets/.env | grep FINNHUB

# Copy to production if needed
sudo cp ~/sva_iran_assets/.env /opt/sva_iran_assets/

# Restart services
sudo systemctl restart sva-cvd-btc
```

**Frontend not loading?**
```bash
# Check config.js exists
ls -la /var/www/html/config.js

# If missing, copy it
sudo cp ~/sva_iran_assets/config.js /var/www/html/
```

## Files You Need to Configure

✅ **`.env`** - Server configuration (API keys, database paths)
✅ **`config.js`** - Frontend configuration (API URL, keys)

❌ **Never edit**:
- `.env.example` (this is the template)
- `config.example.js` (this is the template)

## That's It!

You should now have:
- ✅ USDT/IRT CVD collecting from Nobitex
- ✅ BTC/USDT CVD collecting from Finnhub
- ✅ API server running
- ✅ Frontend displaying both assets with real CVD

For detailed documentation, see [SETUP.md](SETUP.md) and [BTC_SETUP.md](BTC_SETUP.md).
