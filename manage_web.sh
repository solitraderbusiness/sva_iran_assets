#!/bin/bash
# Web Server Management Script

case "$1" in
    start)
        echo "Starting web server on port 80..."
        cd /home/user/sva_iran_assets
        nohup python3 -m http.server 80 > /var/log/sva_web.log 2>&1 &
        echo "Web server started (PID: $!)"
        echo "Access at: http://$(hostname -I | awk '{print $1}')"
        ;;
    stop)
        echo "Stopping web server..."
        pkill -f "python3 -m http.server 80"
        echo "Web server stopped"
        ;;
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
    status)
        if pgrep -f "python3 -m http.server 80" > /dev/null; then
            echo "Web server is running"
            echo "Access at: http://$(hostname -I | awk '{print $1}')"
            ps aux | grep "python3 -m http.server 80" | grep -v grep
        else
            echo "Web server is not running"
        fi
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac
