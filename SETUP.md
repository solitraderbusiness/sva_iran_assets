# SVA Iran Assets - Complete Setup Guide

## Overview

This project uses environment variables for configuration to keep API keys and sensitive data secure. Configuration is managed through:
- **Server-side (Python)**: `.env` file
- **Client-side (JavaScript)**: `config.js` file

## Prerequisites

- Ubuntu 24 server
- Python 3
- Web browser
- Finnhub API key (free from https://finnhub.io/)

## Setup Instructions

### Step 1: Configure Environment Variables

#### Server Configuration (.env)

1. Create `.env` file from the template:
```bash
cd ~/sva_iran_assets
cp .env.example .env
```

2. Edit `.env` and add your Finnhub API key:
```bash
nano .env
```

3. Update the following line:
```env
FINNHUB_API_KEY=your_actual_api_key_here
```

4. Review other settings (usually defaults are fine):
```env
CVD_API_URL=http://31.97.32.203:5000
DB_PATH_USDT=/var/lib/sva_iran_assets/cvd_data.db
DB_PATH_BTC=/var/lib/sva_iran_assets/cvd_btc_data.db
UPDATE_INTERVAL=10
```

#### Client Configuration (config.js)

1. Create `config.js` from the template:
```bash
cp config.example.js config.js
```

2. Edit `config.js`:
```bash
nano config.js
```

3. Update the configuration:
```javascript
const CONFIG = {
    CVD_API_URL: 'http://31.97.32.203:5000',
    FINNHUB_API_KEY: 'your_actual_api_key_here',
    USE_REAL_CVD: true,
    AUTO_REFRESH: true,
    REFRESH_INTERVAL: 10000,
};
```

### Step 2: Install USDT/IRT Collector

```bash
cd ~/sva_iran_assets/server
sudo bash setup.sh
```

This will:
- Install Python dependencies (flask, requests, python-dotenv)
- Set up the USDT/IRT collector from Nobitex
- Start collecting CVD data every 10 seconds
- Start the API server on port 5000

### Step 3: Install BTC/USDT Collector

```bash
cd ~/sva_iran_assets/server
sudo bash setup_btc.sh
```

This will:
- Check your .env configuration
- Install WebSocket dependencies
- Copy .env to /opt/sva_iran_assets/
- Set up the BTC/USDT collector from Finnhub
- Start collecting real-time BTC trades

### Step 4: Verify Services

Check all services are running:
```bash
sudo systemctl status sva-cvd-collector  # USDT collector
sudo systemctl status sva-cvd-btc        # BTC collector
sudo systemctl status sva-cvd-api        # API server
```

View logs:
```bash
# USDT collector
sudo journalctl -u sva-cvd-collector -f

# BTC collector
sudo journalctl -u sva-cvd-btc -f

# API server
sudo journalctl -u sva-cvd-api -f
```

### Step 5: Deploy Frontend

1. Copy files to your web server:
```bash
# If using the server's web directory
sudo cp ~/sva_iran_assets/index.html /var/www/html/
sudo cp ~/sva_iran_assets/styles.css /var/www/html/
sudo cp ~/sva_iran_assets/app.js /var/www/html/
sudo cp ~/sva_iran_assets/config.js /var/www/html/
```

2. Access the application:
```
http://your-server-ip/
```

## Security Notes

### What Gets Committed to Git

✅ **Committed (safe to share)**:
- `.env.example` - Template with example values
- `config.example.js` - Template with example values
- All source code

❌ **NOT Committed (contains secrets)**:
- `.env` - Contains your actual API keys
- `config.js` - Contains your actual configuration

These are automatically ignored by `.gitignore`.

### Best Practices

1. **Never commit `.env` or `config.js`** to version control
2. **Always use `.env.example`** as a template for new installations
3. **Rotate API keys** if accidentally exposed
4. **Use environment-specific values** (different keys for dev/production)

## Configuration Reference

### .env File

All server-side Python scripts load configuration from `.env`:

```env
# Finnhub API Key
FINNHUB_API_KEY=your_api_key_here

# CVD API Server
CVD_API_URL=http://31.97.32.203:5000

# Database Paths
DB_PATH_USDT=/var/lib/sva_iran_assets/cvd_data.db
DB_PATH_BTC=/var/lib/sva_iran_assets/cvd_btc_data.db

# Update Interval (seconds)
UPDATE_INTERVAL=10

# Log Paths
LOG_PATH_USDT=/var/log/sva_cvd_collector.log
LOG_PATH_BTC=/var/log/sva_cvd_btc.log

# API Server
API_HOST=0.0.0.0
API_PORT=5000
```

### config.js File

Frontend JavaScript loads configuration from `config.js`:

```javascript
const CONFIG = {
    CVD_API_URL: 'http://31.97.32.203:5000',
    FINNHUB_API_KEY: 'your_api_key_here',
    USE_REAL_CVD: true,
    AUTO_REFRESH: true,
    REFRESH_INTERVAL: 10000,
};
```

## Updating Configuration

### Server Configuration

1. Edit `.env` file:
```bash
nano ~/sva_iran_assets/.env
```

2. Copy to production:
```bash
sudo cp ~/sva_iran_assets/.env /opt/sva_iran_assets/
```

3. Restart services:
```bash
sudo systemctl restart sva-cvd-collector
sudo systemctl restart sva-cvd-btc
sudo systemctl restart sva-cvd-api
```

### Client Configuration

1. Edit `config.js`:
```bash
nano ~/sva_iran_assets/config.js
```

2. Copy to web server:
```bash
sudo cp ~/sva_iran_assets/config.js /var/www/html/
```

3. Clear browser cache and reload

## Troubleshooting

### API Key Errors

**Error**: `FINNHUB_API_KEY not set in .env file!`

**Solution**:
1. Check `.env` exists: `ls -la ~/sva_iran_assets/.env`
2. Check it's copied to production: `ls -la /opt/sva_iran_assets/.env`
3. Verify API key is set: `grep FINNHUB_API_KEY ~/sva_iran_assets/.env`

### Config File Not Found

**Error**: `config.js:1 Uncaught SyntaxError`

**Solution**:
1. Create config.js: `cp config.example.js config.js`
2. Set your API key in config.js
3. Copy to web server

### Services Not Starting

**Error**: `Failed to start sva-cvd-btc.service`

**Solution**:
```bash
# Check logs for specific error
sudo journalctl -u sva-cvd-btc -n 50

# Verify .env file exists in working directory
ls -la /opt/sva_iran_assets/.env

# Restart service
sudo systemctl restart sva-cvd-btc
```

## Getting Help

If you encounter issues:

1. Check service logs: `sudo journalctl -u <service-name> -n 100`
2. Verify .env file is configured correctly
3. Ensure all Python dependencies are installed
4. Check API key is valid at https://finnhub.io/dashboard

## Environment-Specific Setup

### Development

```bash
# Use local .env
cp .env.example .env
nano .env  # Set development API keys

# Run services locally
python3 server/data_collector.py
python3 server/api_server.py

# Serve frontend
cd ~/sva_iran_assets
python3 -m http.server 8000
```

### Production

```bash
# Use setup scripts (handles .env automatically)
cd server
sudo bash setup.sh
sudo bash setup_btc.sh
```
