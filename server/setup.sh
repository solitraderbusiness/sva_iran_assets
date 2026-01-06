#!/bin/bash
#
# Setup script for SVA Iran Assets CVD Data Collection System
# Run this on your Ubuntu server as root
#

set -e

echo "=========================================="
echo "  SVA Iran Assets - CVD System Setup"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "ERROR: Please run as root (use sudo)"
  exit 1
fi

echo "[1/7] Installing Python dependencies..."
apt-get update
apt-get install -y python3 python3-pip python3-venv

echo ""
echo "[2/7] Creating directories..."
mkdir -p /opt/sva_iran_assets/server
mkdir -p /var/lib/sva_iran_assets
mkdir -p /var/log

echo ""
echo "[3/7] Copying files..."
cp data_collector.py /opt/sva_iran_assets/server/
cp api_server.py /opt/sva_iran_assets/server/
cp requirements.txt /opt/sva_iran_assets/server/

chmod +x /opt/sva_iran_assets/server/data_collector.py
chmod +x /opt/sva_iran_assets/server/api_server.py

echo ""
echo "[4/7] Installing Python packages..."
pip3 install -r /opt/sva_iran_assets/server/requirements.txt --break-system-packages

echo ""
echo "[5/7] Installing systemd services..."
cp sva-cvd-collector.service /etc/systemd/system/
cp sva-cvd-api.service /etc/systemd/system/

systemctl daemon-reload

echo ""
echo "[6/7] Starting services..."
systemctl enable sva-cvd-collector
systemctl enable sva-cvd-api

systemctl start sva-cvd-collector
systemctl start sva-cvd-api

echo ""
echo "[7/7] Checking status..."
sleep 2

echo ""
echo "Data Collector Status:"
systemctl status sva-cvd-collector --no-pager -l | head -20

echo ""
echo "API Server Status:"
systemctl status sva-cvd-api --no-pager -l | head -20

echo ""
echo "=========================================="
echo "  Installation Complete!"
echo "=========================================="
echo ""
echo "Services installed:"
echo "  - sva-cvd-collector (Data collection)"
echo "  - sva-cvd-api (API server on port 5000)"
echo ""
echo "Useful commands:"
echo "  sudo systemctl status sva-cvd-collector"
echo "  sudo systemctl status sva-cvd-api"
echo "  sudo journalctl -u sva-cvd-collector -f"
echo "  sudo journalctl -u sva-cvd-api -f"
echo "  tail -f /var/log/sva_cvd_collector.log"
echo ""
echo "API endpoints:"
echo "  http://YOUR_SERVER_IP:5000/api/health"
echo "  http://YOUR_SERVER_IP:5000/api/cvd"
echo "  http://YOUR_SERVER_IP:5000/api/cvd/latest"
echo "  http://YOUR_SERVER_IP:5000/api/stats"
echo ""
echo "Database location:"
echo "  /var/lib/sva_iran_assets/cvd_data.db"
echo ""
