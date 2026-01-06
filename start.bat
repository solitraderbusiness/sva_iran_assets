@echo off
echo ========================================
echo  SVA Iran Assets - Starting Server
echo ========================================
echo.
echo Server starting on http://localhost:8000
echo.
echo Press Ctrl+C to stop the server
echo Then open: http://localhost:8000 in your browser
echo.
echo ========================================
echo.

python -m http.server 8000
