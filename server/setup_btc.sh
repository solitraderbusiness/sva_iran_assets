#!/bin/bash
#
# Setup BTC CVD Collector from Finnhub WebSocket
#

set -e

echo "=========================================="
echo "  SVA - BTC CVD Collector Setup"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "ERROR: Please run as root (use sudo)"
  exit 1
fi

echo "[1/7] Checking .env file..."
if [ ! -f "../.env" ]; then
    echo ""
    echo "WARNING: .env file not found!"
    echo "Creating .env from .env.example..."
    cp ../.env.example ../.env
    echo ""
    echo "Please edit .env and set your FINNHUB_API_KEY"
    echo "Example: nano ../.env"
    echo ""
    read -p "Press Enter after you've set your API key, or Ctrl+C to cancel..."
fi

# Validate API key is set
if grep -q "your_finnhub_api_key_here" ../.env; then
    echo ""
    echo "ERROR: FINNHUB_API_KEY not configured in .env file!"
    echo "Please edit ../.env and set your actual Finnhub API key"
    exit 1
fi

echo ""
echo "[2/7] Installing Python dependencies..."
pip3 install python-dotenv==1.0.0 websocket-client==1.6.4 --break-system-packages

echo ""
echo "[3/7] Creating data directory..."
mkdir -p /var/lib/sva_iran_assets
mkdir -p /var/log

echo ""
echo "[4/7] Copying .env file..."
cp ../.env /opt/sva_iran_assets/

echo ""
echo "[5/7] Copying BTC collector..."
cp data_collector_btc.py /opt/sva_iran_assets/server/
chmod +x /opt/sva_iran_assets/server/data_collector_btc.py

echo ""
echo "[6/7] Installing systemd service..."
cp sva-cvd-btc.service /etc/systemd/system/
systemctl daemon-reload

echo ""
echo "[7/7] Starting BTC CVD collector..."
systemctl enable sva-cvd-btc
systemctl start sva-cvd-btc

echo ""
echo "=========================================="
echo "  BTC CVD Collector Installed!"
echo "=========================================="
echo ""
echo "Check status:"
echo "  sudo systemctl status sva-cvd-btc"
echo ""
echo "View logs:"
echo "  sudo journalctl -u sva-cvd-btc -f"
echo "  tail -f /var/log/sva_cvd_btc.log"
echo ""
echo "BTC CVD now collecting from Finnhub WebSocket!"
echo "Data is stored in: /var/lib/sva_iran_assets/cvd_btc_data.db"
echo ""
echo "Don't forget to restart the API server to serve BTC data:"
echo "  sudo systemctl restart sva-cvd-api"
echo ""
