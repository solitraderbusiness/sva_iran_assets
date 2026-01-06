# SVA Iran Assets - CVD Data Collection Server

This directory contains the backend service for collecting and serving accurate CVD (Cumulative Volume Delta) data from Nobitex.

## 📋 System Requirements

- Ubuntu 24.04 (or any Linux with systemd)
- Python 3.10+
- 2GB RAM minimum (4GB recommended)
- Internet connection to Nobitex API

## 🚀 Installation on Ubuntu Server

### Step 1: Upload Files to Server

```bash
# On your Ubuntu server, create a directory
mkdir -p ~/sva_server
cd ~/sva_server

# Upload all files from the 'server' directory to this folder
# You can use scp, rsync, or any file transfer method
```

### Step 2: Run Setup Script

```bash
cd ~/sva_server
chmod +x setup.sh
sudo ./setup.sh
```

The setup script will:
1. Install Python dependencies
2. Create necessary directories
3. Copy files to `/opt/sva_iran_assets/server`
4. Install and start systemd services
5. Verify everything is running

### Step 3: Verify Services

```bash
# Check if services are running
sudo systemctl status sva-cvd-collector
sudo systemctl status sva-cvd-api

# View live logs
sudo journalctl -u sva-cvd-collector -f
sudo journalctl -u sva-cvd-api -f
```

### Step 4: Test API

```bash
# Health check
curl http://localhost:5000/api/health

# Get latest CVD
curl http://localhost:5000/api/cvd/latest

# Get statistics
curl http://localhost:5000/api/stats
```

## 📊 How It Works

### Data Collector (`data_collector.py`)
- Runs every 60 seconds
- Fetches recent trades from Nobitex `/v2/trades/USDTIRT`
- Aggregates buy volume vs sell volume
- Calculates CVD (cumulative)
- Stores in SQLite database

### API Server (`api_server.py`)
- Flask REST API on port 5000
- Serves historical CVD data
- Endpoints:
  - `/api/health` - Health check
  - `/api/cvd?from=X&to=Y` - Get CVD data for timerange
  - `/api/cvd/latest` - Get latest CVD value
  - `/api/stats` - Database statistics

### Database
- Location: `/var/lib/sva_iran_assets/cvd_data.db`
- Type: SQLite (lightweight, no setup needed)
- Auto-cleanup: Keeps 90 days of data
- Schema:
  ```sql
  CREATE TABLE cvd_data (
      timestamp INTEGER PRIMARY KEY,
      buy_volume REAL,
      sell_volume REAL,
      volume_delta REAL,
      cvd REAL,
      trade_count INTEGER,
      avg_price REAL
  )
  ```

## 🔧 Management Commands

### Service Control
```bash
# Start services
sudo systemctl start sva-cvd-collector
sudo systemctl start sva-cvd-api

# Stop services
sudo systemctl stop sva-cvd-collector
sudo systemctl stop sva-cvd-api

# Restart services
sudo systemctl restart sva-cvd-collector
sudo systemctl restart sva-cvd-api

# Enable auto-start on boot
sudo systemctl enable sva-cvd-collector
sudo systemctl enable sva-cvd-api
```

### View Logs
```bash
# Data collector logs
sudo journalctl -u sva-cvd-collector -f

# API server logs
sudo journalctl -u sva-cvd-api -f

# Application log file
tail -f /var/log/sva_cvd_collector.log
```

### Database Management
```bash
# View database
sqlite3 /var/lib/sva_iran_assets/cvd_data.db

# In SQLite shell:
# SELECT * FROM cvd_data ORDER BY timestamp DESC LIMIT 10;
# .quit
```

## 🌐 Firewall Configuration

If you want to access the API from other machines:

```bash
# Allow port 5000
sudo ufw allow 5000/tcp

# Or for specific IP:
sudo ufw allow from YOUR_IP to any port 5000
```

## 🔄 Updating the Code

```bash
# Stop services
sudo systemctl stop sva-cvd-collector sva-cvd-api

# Update files
cd ~/sva_server
# (upload new files)

# Copy to installation directory
sudo cp data_collector.py /opt/sva_iran_assets/server/
sudo cp api_server.py /opt/sva_iran_assets/server/

# Restart services
sudo systemctl restart sva-cvd-collector sva-cvd-api
```

## 📈 Performance

This system is very lightweight:
- CPU usage: < 1%
- RAM usage: < 100MB
- Disk usage: ~1MB per day (compressed)
- Network: ~1KB every minute

## 🐛 Troubleshooting

### Services won't start
```bash
# Check logs for errors
sudo journalctl -u sva-cvd-collector -n 50
sudo journalctl -u sva-cvd-api -n 50
```

### No data being collected
```bash
# Check if API is accessible
curl https://apiv2.nobitex.ir/v2/trades/USDTIRT

# Check database
sqlite3 /var/lib/sva_iran_assets/cvd_data.db "SELECT COUNT(*) FROM cvd_data"
```

### API not responding
```bash
# Check if service is running
sudo systemctl status sva-cvd-api

# Check if port is open
sudo netstat -tulpn | grep 5000
```

## 📝 Notes

- The system automatically starts on server boot
- Old data (>90 days) is automatically cleaned up
- All errors are logged to journald and `/var/log/sva_cvd_collector.log`
- Services auto-restart on failure
