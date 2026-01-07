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

# Check if Finnhub API key is set
echo "[1/6] Checking Finnhub API key..."
if grep -q "YOUR_FINNHUB_API_KEY" data_collector_btc.py; then
    echo ""
    echo "WARNING: Finnhub API key not set!"
    echo "Please edit data_collector_btc.py and replace YOUR_FINNHUB_API_KEY with your actual API key"
    echo ""
    read -p "Press Enter after you've set your API key, or Ctrl+C to cancel..."
fi

echo ""
echo "[2/6] Installing WebSocket dependencies..."
pip3 install websocket-client==1.6.4 --break-system-packages

echo ""
echo "[3/6] Creating data directory..."
mkdir -p /var/lib/sva_iran_assets
mkdir -p /var/log

echo ""
echo "[4/6] Copying BTC collector..."
cp data_collector_btc.py /opt/sva_iran_assets/server/
chmod +x /opt/sva_iran_assets/server/data_collector_btc.py

echo ""
echo "[5/6] Installing systemd service..."
cp sva-cvd-btc.service /etc/systemd/system/
systemctl daemon-reload

echo ""
echo "[6/6] Starting BTC CVD collector..."
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
