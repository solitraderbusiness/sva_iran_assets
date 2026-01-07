# BTC/USDT Setup Guide

## Overview
You can now compare CVD calculations between USDT/IRT (Nobitex) and BTC/USDT (Finnhub) to validate the CVD implementation by comparing with TradingView.

## How to Get Finnhub API Key

1. Go to https://finnhub.io/
2. Click "Get free API key" or "Sign up"
3. Create a free account
4. After logging in, you'll see your API key on the dashboard
5. Copy the API key

## Setup Instructions

1. Open `app.js` in a text editor
2. Find line 9 where it says:
   ```javascript
   FINNHUB_API_KEY: 'YOUR_FINNHUB_API_KEY',
   ```
3. Replace `YOUR_FINNHUB_API_KEY` with your actual Finnhub API key:
   ```javascript
   FINNHUB_API_KEY: 'cqabcd1234567890',
   ```
4. Save the file

## How to Use

1. Open your browser and go to http://localhost or your server URL
2. In the header, you'll see an asset selector dropdown
3. Select either:
   - **USDT/IRT**: Shows Iranian Toman price from Nobitex with real CVD from server
   - **BTC/USDT**: Shows Bitcoin USD price from Finnhub with estimated CVD

## Comparing with TradingView

To validate our CVD calculation:

1. Select **BTC/USDT** in the asset dropdown
2. Click **Toggle CVD** to show the CVD indicator
3. Open TradingView: https://www.tradingview.com/chart/
4. Search for **BTCUSD** or **BTC/USDT**
5. Add the **Cumulative Volume Delta (CVD)** indicator to TradingView
6. Compare the CVD patterns:
   - Do they move in the same direction?
   - Are the peaks and valleys similar?
   - Does the overall trend match?

## Notes

- **USDT/IRT**: Uses real CVD data from your server (calculated from actual buy/sell trades)
- **BTC/USDT**: Uses estimated CVD (calculated from close position in candle range)
- Both use the same CVD estimation formula for comparison
- Finnhub free tier has API rate limits (60 calls/minute)
- For best comparison, use the same timeframe on both charts

## Troubleshooting

**BTC data not loading:**
- Check your Finnhub API key is correct
- Check browser console (F12) for errors
- Make sure you have internet connection
- Verify Finnhub API is accessible from your location

**CVD looks different from TradingView:**
- Make sure you're using the same timeframe (15m, 1h, etc.)
- Remember: Our CVD is estimated from OHLC data, TradingView may use tick data
- The pattern should be similar even if exact values differ
- Focus on the direction and trend, not exact numbers
