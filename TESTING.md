# Quick Testing Guide

## ✅ What You Need to Check

### 1. Server is Collecting Data
```bash
# SSH to your server (31.97.32.203)
ssh username@31.97.32.203

# Check if services are running
sudo systemctl status sva-cvd-collector
sudo systemctl status sva-cvd-api

# Watch data being collected (live)
sudo journalctl -u sva-cvd-collector -f

# You should see:
# "Received 127 trades"
# "Stored data: buy=1234.56, sell=987.65, cvd=12345.67"
```

### 2. API is Accessible from Your PC
Open browser and visit:
```
http://31.97.32.203:5000/api/health
```

Should return:
```json
{"status":"ok","service":"CVD Data API"}
```

If it doesn't work:
- Check firewall: `sudo ufw allow 5000/tcp`
- Check service: `sudo systemctl restart sva-cvd-api`

### 3. Test the Frontend
On your Windows PC:
```batch
cd B:\projects\sva_iran_assets\sva_iran_assets
git pull origin claude/add-cvd-indicator-kB13H
start.bat
```

Then open: http://localhost:8000

**Check Console (F12):**
You should see:
```
Fetching real CVD data from server...
Fetching CVD from: http://31.97.32.203:5000/api/cvd?from=...
Loaded 120 real CVD data points from server
```

**Click "Toggle CVD":**
- Should show: "CVD (Real)" in indicators
- Status message: "Real CVD indicator added (from server)"
- Blue CVD line should appear

### 4. Troubleshooting

**If CVD shows "CVD (Estimated)":**
- Server might be down or unreachable
- Check server status (Step 1)
- Check API access (Step 2)
- Check browser console for error messages

**If no data being collected:**
- Server needs time to collect (wait 2-3 minutes)
- Check: `curl http://31.97.32.203:5000/api/stats`

**If CORS error in browser:**
- Check api_server.py has `CORS(app)` enabled
- Restart API: `sudo systemctl restart sva-cvd-api`

## 🎯 Expected Behavior

**After 5 minutes of server running:**
- CVD data available for last 5 minutes
- "CVD (Real)" shows on chart
- CVD line moves with price action

**After 24 hours:**
- Full day of accurate CVD history
- Can switch timeframes (1h, 4h, 1d)
- CVD persists across page refreshes

## 📊 Configuration

**To disable real CVD** (use estimated):
Edit `app.js` line 6:
```javascript
USE_REAL_CVD: false,  // Change to false
```

**To change server IP:**
Edit `app.js` line 5:
```javascript
CVD_API_URL: 'http://YOUR_NEW_IP:5000',
```

## ✨ Success Indicators

✅ Services running on server
✅ API returns health check
✅ Frontend shows "CVD (Real)"
✅ CVD line appears on chart
✅ Console shows "Loaded X real CVD data points"
