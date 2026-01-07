// SVA Iran Assets - Frontend Configuration Template
// Copy this file to config.js and fill in your actual values
// IMPORTANT: config.js is gitignored and won't be committed to the repository

const CONFIG = {
    // CVD API Server URL
    CVD_API_URL: 'http://31.97.32.203:5000',

    // Finnhub API Key (get from https://finnhub.io/)
    FINNHUB_API_KEY: 'your_finnhub_api_key_here',

    // CVD Settings
    USE_REAL_CVD: true,  // Set to false to use estimated CVD

    // Auto-refresh Settings
    AUTO_REFRESH: true,  // Auto-refresh chart data
    REFRESH_INTERVAL: 10000,  // Refresh every 10 seconds (10000ms)
};
