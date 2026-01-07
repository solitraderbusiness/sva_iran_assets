// SVA Iran Assets Trading Chart Application
// Configuration is loaded from config.js

class TradingChart {
    constructor() {
        this.chart = null;
        this.candlestickSeries = null;
        this.cvdSeries = null;
        this.cvdEnabled = false;
        this.indicators = [];
        this.currentAsset = 'USDTIRT';
        this.timeframe = '15m';
        this.candleData = [];
        this.cvdData = [];
        this.useRealCVD = CONFIG.USE_REAL_CVD;
        this.refreshInterval = null;
        this.isLoading = false;

        this.init();
    }

    init() {
        this.createChart();
        this.setupEventListeners();
        this.loadData();

        // Start auto-refresh if enabled
        if (CONFIG.AUTO_REFRESH) {
            this.startAutoRefresh();
        }
    }

    createChart() {
        const chartContainer = document.getElementById('chartContainer');
        console.log('Creating chart...');
        console.log('Chart container dimensions:', chartContainer.clientWidth, 'x', chartContainer.clientHeight);

        this.chart = LightweightCharts.createChart(chartContainer, {
            width: chartContainer.clientWidth,
            height: chartContainer.clientHeight,
            layout: {
                background: { color: '#131722' },
                textColor: '#d1d4dc',
            },
            grid: {
                vertLines: { color: '#1e222d' },
                horzLines: { color: '#1e222d' },
            },
            crosshair: {
                mode: LightweightCharts.CrosshairMode.Normal,
            },
            rightPriceScale: {
                borderColor: '#2a2e39',
            },
            timeScale: {
                borderColor: '#2a2e39',
                timeVisible: true,
                secondsVisible: false,
            },
        });

        this.candlestickSeries = this.chart.addCandlestickSeries({
            upColor: '#089981',
            downColor: '#f23645',
            borderDownColor: '#f23645',
            borderUpColor: '#089981',
            wickDownColor: '#f23645',
            wickUpColor: '#089981',
        });

        // Handle window resize
        window.addEventListener('resize', () => {
            this.chart.applyOptions({
                width: chartContainer.clientWidth,
                height: chartContainer.clientHeight,
            });
        });
    }

    setupEventListeners() {
        document.getElementById('toggleCVD').addEventListener('click', () => {
            this.toggleCVD();
        });

        document.getElementById('refreshData').addEventListener('click', () => {
            this.loadData();
        });

        document.getElementById('assetSelect').addEventListener('change', (e) => {
            this.currentAsset = e.target.value;
            this.loadData();
        });

        document.getElementById('timeframeSelect').addEventListener('change', (e) => {
            this.timeframe = e.target.value;
            this.loadData();
        });

        document.getElementById('runScript').addEventListener('click', () => {
            this.runPineScript();
        });

        document.getElementById('loadCVDExample').addEventListener('click', () => {
            this.loadCVDExample();
        });

        document.getElementById('clearEditor').addEventListener('click', () => {
            document.getElementById('pineEditor').value = '';
            this.setStatus('');
        });
    }

    async loadData() {
        console.log('Loading data...');
        this.setStatus('Loading data...', 'info');

        try {
            if (this.currentAsset === 'BTCUSDT') {
                // Load BTC data from Finnhub
                await this.loadBTCData();
            } else {
                // Load USDT/IRT data from Nobitex
                await this.loadNobitexData();
            }

            console.log('Generated', this.candleData.length, 'candles');

            // Load real CVD data from server if enabled (for both USDT/IRT and BTC)
            if (this.useRealCVD) {
                await this.loadRealCVD();
            }

            this.updatePriceDisplay();
            this.setStatus('Data loaded successfully', 'success');

        } catch (error) {
            console.log('Error loading data:', error.message);
            this.generateMockData();
            this.updatePriceDisplay();
            this.setStatus('Error loading data, using mock data', 'error');
        }
    }

    async loadNobitexData() {
        // Calculate time range (last 200 candles)
        const to = Math.floor(Date.now() / 1000);
        const intervalSeconds = this.getIntervalSeconds();
        const from = to - (200 * intervalSeconds);

        // Map timeframe to Nobitex resolution
        const resolutionMap = {
            '1m': '1',
            '5m': '5',
            '15m': '15',
            '1h': '60',
            '4h': '240',
            '1d': 'D'
        };
        const resolution = resolutionMap[this.timeframe] || '15';

        // Fetch real OHLCV data from Nobitex
        const url = `https://apiv2.nobitex.ir/market/udf/history?symbol=USDTIRT&resolution=${resolution}&from=${from}&to=${to}`;
        console.log('Fetching from Nobitex API:', url);

        const response = await fetch(url);

        if (!response.ok) {
            throw new Error('Nobitex API not available');
        }

        const data = await response.json();
        console.log('Nobitex API data received:', data);

        if (data.s === 'ok' && data.t && data.t.length > 0) {
            this.processRealData(data);
        } else {
            throw new Error('No data returned from Nobitex API');
        }
    }

    async loadBTCData() {
        // Calculate time range (last 200 candles)
        const to = Math.floor(Date.now() / 1000);
        const intervalSeconds = this.getIntervalSeconds();
        const from = to - (200 * intervalSeconds);

        // Map timeframe to Finnhub resolution
        const resolutionMap = {
            '1m': '1',
            '5m': '5',
            '15m': '15',
            '1h': '60',
            '4h': '240',
            '1d': 'D'
        };
        const resolution = resolutionMap[this.timeframe] || '15';

        // Fetch BTC/USDT data from Finnhub
        const url = `https://finnhub.io/api/v1/crypto/candle?symbol=OANDA:BTC_USD&resolution=${resolution}&from=${from}&to=${to}&token=${CONFIG.FINNHUB_API_KEY}`;
        console.log('Fetching from Finnhub API:', url);

        const response = await fetch(url);

        if (!response.ok) {
            throw new Error('Finnhub API not available');
        }

        const data = await response.json();
        console.log('Finnhub API data received:', data);

        if (data.s === 'ok' && data.t && data.t.length > 0) {
            this.processRealData(data);
        } else {
            throw new Error('No data returned from Finnhub API');
        }
    }

    async loadRealCVD() {
        try {
            console.log(`Fetching real CVD data from server for ${this.currentAsset}...`);

            // Calculate time range for CVD data (match candle data range)
            if (this.candleData.length === 0) {
                console.log('No candle data available, skipping CVD fetch');
                return;
            }

            const fromTime = this.candleData[0].time;
            const toTime = this.candleData[this.candleData.length - 1].time;

            const url = `${CONFIG.CVD_API_URL}/api/cvd?asset=${this.currentAsset}&from=${fromTime}&to=${toTime}&limit=10000`;
            console.log('Fetching CVD from:', url);

            const response = await fetch(url);

            if (!response.ok) {
                throw new Error(`Server returned ${response.status}`);
            }

            const result = await response.json();

            if (result.success && result.data && result.data.length > 0) {
                // Aggregate CVD data to match price candle timeframe
                const aggregatedCVD = this.aggregateCVDToTimeframe(result.data);

                this.cvdData = aggregatedCVD;

                console.log(`Loaded and aggregated ${this.cvdData.length} CVD candles (from ${result.data.length} data points)`);

                // Update CVD series if it's currently displayed
                if (this.cvdEnabled && this.cvdSeries) {
                    this.cvdSeries.setData(this.cvdData);
                }

                this.setStatus('Real CVD data loaded from server', 'success');
            } else {
                throw new Error('No CVD data available');
            }

        } catch (error) {
            console.log('Could not load real CVD from server:', error.message);
            console.log('Using estimated CVD instead');
            this.setStatus('Using estimated CVD (server unavailable)', 'info');
            // cvdData already contains estimated CVD from processRealData
        }
    }

    aggregateCVDToTimeframe(rawCVDData) {
        // Aggregate 1-minute CVD data to match the price candle timeframe
        const intervalSeconds = this.getIntervalSeconds();
        const aggregated = [];

        // Group CVD data by price candle time buckets
        for (let i = 0; i < this.candleData.length; i++) {
            const candleTime = this.candleData[i].time;
            const nextCandleTime = candleTime + intervalSeconds;

            // Find all CVD points within this candle's time range
            const cvdPointsInRange = rawCVDData.filter(point =>
                point.time >= candleTime && point.time < nextCandleTime
            );

            if (cvdPointsInRange.length > 0) {
                // Get CVD values for this period
                const cvdValues = cvdPointsInRange.map(p => p.cvd);

                // Create OHLC for this CVD candle
                const open = cvdPointsInRange[0].cvd;
                const close = cvdPointsInRange[cvdPointsInRange.length - 1].cvd;
                const high = Math.max(...cvdValues);
                const low = Math.min(...cvdValues);

                aggregated.push({
                    time: candleTime,
                    open: open,
                    high: high,
                    low: low,
                    close: close
                });
            } else {
                // No CVD data for this period, use previous close or 0
                const prevCVD = i > 0 && aggregated[i - 1] ? aggregated[i - 1].close : 0;

                aggregated.push({
                    time: candleTime,
                    open: prevCVD,
                    high: prevCVD,
                    low: prevCVD,
                    close: prevCVD
                });
            }
        }

        return aggregated;
    }

    processRealData(data) {
        // Process real OHLCV data from Nobitex API
        // Data format: { s: 'ok', t: [times], o: [opens], h: [highs], l: [lows], c: [closes], v: [volumes] }

        this.candleData = [];
        this.cvdData = [];
        let cvd = 0;

        for (let i = 0; i < data.t.length; i++) {
            const open = parseFloat(data.o[i]);
            const high = parseFloat(data.h[i]);
            const low = parseFloat(data.l[i]);
            const close = parseFloat(data.c[i]);
            const volume = parseFloat(data.v[i] || 0);

            // Calculate volume delta using close position in candle range
            // This estimates buying vs selling pressure based on where the close is
            const range = high - low;
            let volumeDelta = 0;

            if (range > 0) {
                // Calculate where close is in the range (0 = at low, 1 = at high)
                const closePosition = (close - low) / range;

                // Split volume based on close position
                // If close is at high (1.0), all volume is buy
                // If close is at low (0.0), all volume is sell
                const buyVolume = volume * closePosition;
                const sellVolume = volume * (1 - closePosition);
                volumeDelta = buyVolume - sellVolume;
            } else {
                // No range (open = high = low = close), no delta
                volumeDelta = 0;
            }

            cvd += volumeDelta;

            this.candleData.push({
                time: data.t[i],
                open: open,
                high: high,
                low: low,
                close: close,
                volume: volume
            });

            this.cvdData.push({
                time: data.t[i],
                value: cvd
            });
        }

        console.log('Processed', this.candleData.length, 'real candles from Nobitex');
        this.candlestickSeries.setData(this.candleData);

        if (this.cvdEnabled && this.cvdSeries) {
            // Convert to candlestick format
            const candlestickData = this.cvdData.map((item, index) => {
                const prevValue = index > 0 ? this.cvdData[index - 1].value : 0;
                const currentValue = item.value;
                return {
                    time: item.time,
                    open: prevValue,
                    high: Math.max(prevValue, currentValue),
                    low: Math.min(prevValue, currentValue),
                    close: currentValue
                };
            });
            this.cvdSeries.setData(candlestickData);
        }
    }

    generateMockData(basePrice = 1480000) {
        const now = Date.now() / 1000;
        const candleCount = 100;
        const interval = this.getIntervalSeconds();

        this.candleData = [];
        this.cvdData = [];

        let price = basePrice;
        let cvd = 0;

        for (let i = candleCount; i >= 0; i--) {
            const time = now - (i * interval);

            // Generate realistic price movement
            const change = (Math.random() - 0.48) * (basePrice * 0.002);
            price = Math.max(price + change, basePrice * 0.95);

            const open = price;
            const high = price + (Math.random() * basePrice * 0.001);
            const low = price - (Math.random() * basePrice * 0.001);
            const close = low + (Math.random() * (high - low));

            // Generate volume (buy and sell)
            const buyVolume = Math.random() * 1000000;
            const sellVolume = Math.random() * 1000000;
            const volume = buyVolume + sellVolume;

            // Calculate CVD
            const volumeDelta = buyVolume - sellVolume;
            cvd += volumeDelta;

            this.candleData.push({
                time: Math.floor(time),
                open: parseFloat(open.toFixed(0)),
                high: parseFloat(high.toFixed(0)),
                low: parseFloat(low.toFixed(0)),
                close: parseFloat(close.toFixed(0)),
                volume: parseFloat(volume.toFixed(0)),
                buyVolume: parseFloat(buyVolume.toFixed(0)),
                sellVolume: parseFloat(sellVolume.toFixed(0)),
            });

            this.cvdData.push({
                time: Math.floor(time),
                value: cvd,
            });

            price = close;
        }

        this.candlestickSeries.setData(this.candleData);

        if (this.cvdEnabled && this.cvdSeries) {
            // Convert to candlestick format
            const candlestickData = this.cvdData.map((item, index) => {
                const prevValue = index > 0 ? this.cvdData[index - 1].value : 0;
                const currentValue = item.value;
                return {
                    time: item.time,
                    open: prevValue,
                    high: Math.max(prevValue, currentValue),
                    low: Math.min(prevValue, currentValue),
                    close: currentValue
                };
            });
            this.cvdSeries.setData(candlestickData);
        }
    }

    getIntervalSeconds() {
        const intervals = {
            '1m': 60,
            '5m': 300,
            '15m': 900,
            '1h': 3600,
            '4h': 14400,
            '1d': 86400,
        };
        return intervals[this.timeframe] || 900;
    }

    toggleCVD() {
        this.cvdEnabled = !this.cvdEnabled;
        const button = document.getElementById('toggleCVD');

        if (this.cvdEnabled) {
            button.classList.add('active');
            this.addCVDIndicator();
        } else {
            button.classList.remove('active');
            this.removeCVDIndicator();
        }
    }

    addCVDIndicator() {
        if (!this.cvdSeries) {
            // Use candlestick series for CVD to show OHLC
            this.cvdSeries = this.chart.addCandlestickSeries({
                upColor: '#26a69a',
                downColor: '#ef5350',
                borderUpColor: '#26a69a',
                borderDownColor: '#ef5350',
                wickUpColor: '#26a69a',
                wickDownColor: '#ef5350',
                priceScaleId: 'cvd',
                title: 'CVD',
            });

            this.chart.priceScale('cvd').applyOptions({
                scaleMargins: {
                    top: 0.7,
                    bottom: 0,
                },
            });
        }

        // Check if CVD data is already in OHLC format or needs conversion
        let candlestickData;

        if (this.cvdData.length > 0 && this.cvdData[0].open !== undefined) {
            // Already in OHLC format (from real CVD server)
            candlestickData = this.cvdData;
        } else {
            // Convert from simple value format (estimated CVD)
            candlestickData = this.cvdData.map((item, index) => {
                const prevValue = index > 0 ? this.cvdData[index - 1].value : 0;
                const currentValue = item.value;

                return {
                    time: item.time,
                    open: prevValue,
                    high: Math.max(prevValue, currentValue),
                    low: Math.min(prevValue, currentValue),
                    close: currentValue
                };
            });
        }

        this.cvdSeries.setData(candlestickData);

        // Indicate if using real or estimated CVD
        const cvdType = this.useRealCVD ? 'CVD (Real)' : 'CVD (Estimated)';
        this.addIndicatorTag(cvdType, '#2962ff');

        const statusMsg = this.useRealCVD ?
            'Real CVD indicator added (from server)' :
            'Estimated CVD indicator added';
        this.setStatus(statusMsg, 'success');
    }

    removeCVDIndicator() {
        if (this.cvdSeries) {
            this.chart.removeSeries(this.cvdSeries);
            this.cvdSeries = null;
        }
        // Remove tag with correct name
        const cvdType = this.useRealCVD ? 'CVD (Real)' : 'CVD (Estimated)';
        this.removeIndicatorTag(cvdType);
        this.setStatus('CVD indicator removed', 'info');
    }

    addIndicatorTag(name, color) {
        const indicatorList = document.getElementById('indicatorList');

        // Check if already exists
        if (document.getElementById(`indicator-${name}`)) {
            return;
        }

        const tag = document.createElement('div');
        tag.className = 'indicator-tag';
        tag.id = `indicator-${name}`;
        tag.innerHTML = `
            <span style="width: 12px; height: 2px; background: ${color};"></span>
            <span>${name}</span>
            <span class="remove" onclick="tradingChart.removeIndicatorByName('${name}')">×</span>
        `;
        indicatorList.appendChild(tag);
    }

    removeIndicatorTag(name) {
        const tag = document.getElementById(`indicator-${name}`);
        if (tag) {
            tag.remove();
        }
    }

    removeIndicatorByName(name) {
        if (name === 'CVD' || name === 'CVD (Real)' || name === 'CVD (Estimated)') {
            this.cvdEnabled = false;
            document.getElementById('toggleCVD').classList.remove('active');
            this.removeCVDIndicator();
        }
    }

    updatePriceDisplay() {
        if (this.candleData.length === 0) return;

        const latestCandle = this.candleData[this.candleData.length - 1];
        const previousCandle = this.candleData[this.candleData.length - 2];

        const currentPrice = latestCandle.close;
        const change = currentPrice - previousCandle.close;
        const changePercent = (change / previousCandle.close) * 100;

        // Format price based on selected asset
        let priceText;
        let changeText;
        if (this.currentAsset === 'BTCUSDT') {
            priceText = '$' + currentPrice.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
            changeText = `${change >= 0 ? '+' : ''}$${Math.abs(change).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} (${changePercent.toFixed(2)}%)`;
        } else {
            priceText = currentPrice.toLocaleString('fa-IR') + ' ریال';
            changeText = `${change >= 0 ? '+' : ''}${change.toLocaleString('fa-IR')} (${changePercent.toFixed(2)}%)`;
        }

        document.getElementById('currentPrice').textContent = priceText;

        const priceChangeEl = document.getElementById('priceChange');
        priceChangeEl.textContent = changeText;
        priceChangeEl.className = `price-change ${change >= 0 ? 'positive' : 'negative'}`;
    }

    runPineScript() {
        const code = document.getElementById('pineEditor').value.trim();

        if (!code) {
            this.setStatus('Please enter Pine Script code', 'error');
            return;
        }

        this.setStatus('Executing Pine Script...', 'info');

        try {
            // Parse and execute Pine Script
            const result = this.executePineScript(code);

            if (result.success) {
                this.setStatus('Script executed successfully!', 'success');

                if (result.series) {
                    this.addCustomIndicator(result);
                }
            } else {
                this.setStatus('Error: ' + result.error, 'error');
            }
        } catch (error) {
            this.setStatus('Error: ' + error.message, 'error');
        }
    }

    executePineScript(code) {
        // Simple Pine Script parser for demonstration
        // This is a simplified version - full Pine Script is much more complex

        try {
            // Extract indicator name
            const indicatorMatch = code.match(/indicator\(['"](.+?)['"]/);
            const indicatorName = indicatorMatch ? indicatorMatch[1] : 'Custom Indicator';

            // Check for SMA
            if (code.includes('ta.sma')) {
                const lengthMatch = code.match(/length\s*=\s*(?:input\()?(\d+)/);
                const length = lengthMatch ? parseInt(lengthMatch[1]) : 20;

                const smaData = this.calculateSMA(this.candleData, length);

                return {
                    success: true,
                    name: indicatorName,
                    series: smaData,
                    type: 'line',
                    color: '#2962ff',
                };
            }

            // Check for EMA
            if (code.includes('ta.ema')) {
                const lengthMatch = code.match(/length\s*=\s*(?:input\()?(\d+)/);
                const length = lengthMatch ? parseInt(lengthMatch[1]) : 20;

                const emaData = this.calculateEMA(this.candleData, length);

                return {
                    success: true,
                    name: indicatorName,
                    series: emaData,
                    type: 'line',
                    color: '#f23645',
                };
            }

            return {
                success: false,
                error: 'Unsupported Pine Script function. Try ta.sma() or ta.ema()',
            };

        } catch (error) {
            return {
                success: false,
                error: error.message,
            };
        }
    }

    calculateSMA(data, period) {
        const result = [];

        for (let i = period - 1; i < data.length; i++) {
            let sum = 0;
            for (let j = 0; j < period; j++) {
                sum += data[i - j].close;
            }
            result.push({
                time: data[i].time,
                value: sum / period,
            });
        }

        return result;
    }

    calculateEMA(data, period) {
        const result = [];
        const multiplier = 2 / (period + 1);

        // First EMA is SMA
        let ema = 0;
        for (let i = 0; i < period; i++) {
            ema += data[i].close;
        }
        ema = ema / period;

        result.push({
            time: data[period - 1].time,
            value: ema,
        });

        // Calculate EMA for remaining data
        for (let i = period; i < data.length; i++) {
            ema = (data[i].close - ema) * multiplier + ema;
            result.push({
                time: data[i].time,
                value: ema,
            });
        }

        return result;
    }

    addCustomIndicator(result) {
        const series = this.chart.addLineSeries({
            color: result.color,
            lineWidth: 2,
            title: result.name,
        });

        series.setData(result.series);
        this.indicators.push({ name: result.name, series });
        this.addIndicatorTag(result.name, result.color);
    }

    loadCVDExample() {
        const cvdExample = `// Cumulative Volume Delta (CVD) Indicator
//@version=5
indicator('CVD - Cumulative Volume Delta', overlay=false)

// CVD calculates the cumulative difference between buying and selling volume
// Positive CVD indicates more buying pressure
// Negative CVD indicates more selling pressure

// This is a simplified example
// In the actual implementation, CVD is calculated from order book data

plot(cvd, color=color.blue, linewidth=2, title='CVD')
hline(0, color=color.gray, linestyle=hline.style_dashed)`;

        document.getElementById('pineEditor').value = cvdExample;
        this.setStatus('CVD example loaded. Click "Toggle CVD" to see the indicator on chart.', 'success');
    }

    setStatus(message, type = 'info') {
        const statusEl = document.getElementById('editorStatus');
        statusEl.textContent = message;
        statusEl.className = `status-message ${type}`;
    }

    startAutoRefresh() {
        console.log(`Auto-refresh enabled: updating every ${CONFIG.REFRESH_INTERVAL / 1000} seconds`);

        this.refreshInterval = setInterval(async () => {
            if (!this.isLoading) {
                console.log('Auto-refreshing data...');
                await this.refreshData();
            }
        }, CONFIG.REFRESH_INTERVAL);
    }

    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
            console.log('Auto-refresh stopped');
        }
    }

    async refreshData() {
        if (this.isLoading) {
            console.log('Already loading, skipping refresh');
            return;
        }

        try {
            this.isLoading = true;

            // Load data based on current asset
            if (this.currentAsset === 'BTCUSDT') {
                await this.loadBTCData();
            } else {
                await this.loadNobitexData();
            }

            // Refresh CVD if enabled (for both assets)
            if (this.useRealCVD) {
                await this.loadRealCVD();
            }

            console.log('Data refreshed successfully');

        } catch (error) {
            console.error('Error refreshing data:', error);
        } finally {
            this.isLoading = false;
        }
    }
}

// Initialize the application
let tradingChart;
window.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing application...');

    // Check if LightweightCharts is available
    if (typeof LightweightCharts === 'undefined') {
        console.error('LightweightCharts library not loaded! Check your internet connection.');
        document.getElementById('currentPrice').textContent = 'Error: Chart library failed to load';
        document.getElementById('currentPrice').style.color = '#f23645';
        return;
    }

    console.log('LightweightCharts loaded successfully');

    try {
        tradingChart = new TradingChart();
        console.log('TradingChart initialized successfully');
    } catch (error) {
        console.error('Error initializing TradingChart:', error);
        document.getElementById('currentPrice').textContent = 'Error: ' + error.message;
        document.getElementById('currentPrice').style.color = '#f23645';
    }
});
