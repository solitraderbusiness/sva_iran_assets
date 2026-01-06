# SVA Iran Assets Trading Chart

A TradingView-like charting application for Iranian assets (USDT/IRT, Gold, Coins) with CVD indicator support and Pine Script editor.

## Features

- Real-time USDT/IRT price chart from Nobitex API
- CVD (Cumulative Volume Delta) indicator
- Pine Script editor for custom indicators
- Professional trading interface

## Getting Started

1. Open `index.html` in a modern web browser
2. Or run a local server:
   ```bash
   npm start
   # or
   python3 -m http.server 8000
   ```
3. Navigate to `http://localhost:8000`

## Data Source

- USDT/IRT data from Nobitex API: https://apiv2.nobitex.ir/v3/orderbook/USDTIRT

## Technologies

- Lightweight Charts by TradingView
- CodeMirror for Pine Script editor
- Vanilla JavaScript (no framework dependencies)
