#!/bin/bash
#
# Setup WebSocket CVD Collector
#

set -e

echo "=========================================="
echo "  SVA - WebSocket CVD Collector Setup"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "ERROR: Please run as root (use sudo)"
  exit 1
fi

echo "[1/5] Installing WebSocket dependencies..."
pip3 install websockets==12.0 --break-system-packages

echo ""
echo "[2/5] Copying WebSocket collector..."
cp data_collector_websocket.py /opt/sva_iran_assets/server/
chmod +x /opt/sva_iran_assets/server/data_collector_websocket.py

echo ""
echo "[3/5] Installing systemd service..."
cp sva-cvd-websocket.service /etc/systemd/system/
systemctl daemon-reload

echo ""
echo "[4/5] Stopping old REST collector (optional)..."
systemctl stop sva-cvd-collector || true
systemctl disable sva-cvd-collector || true

echo ""
echo "[5/5] Starting WebSocket collector..."
systemctl enable sva-cvd-websocket
systemctl start sva-cvd-websocket

echo ""
echo "=========================================="
echo "  WebSocket Collector Installed!"
echo "=========================================="
echo ""
echo "Check status:"
echo "  sudo systemctl status sva-cvd-websocket"
echo ""
echo "View logs:"
echo "  sudo journalctl -u sva-cvd-websocket -f"
echo "  tail -f /var/log/sva_cvd_websocket.log"
echo ""
echo "CVD now updates every 10 seconds from real-time trades!"
echo ""
