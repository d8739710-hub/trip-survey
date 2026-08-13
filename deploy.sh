#!/bin/bash
# ============================================================
#  部門旅遊調查 - Linux 部署腳本（無 sudo，適用一般帳號）
#  在 twn153 上執行：bash ~/trip-survey/deploy.sh
# ============================================================

APP_DIR="$HOME/trip-survey"
PID_FILE="$APP_DIR/.server.pid"
LOG_FILE="$APP_DIR/server.log"
PORT=8080

start() {
  if [ -f "$PID_FILE" ] && kill -0 "$(cat $PID_FILE)" 2>/dev/null; then
    echo "⚠️  伺服器已在執行中 (PID $(cat $PID_FILE))"
    return
  fi
  mkdir -p "$APP_DIR/data"
  cd "$APP_DIR"
  PORT=$PORT nohup python3 server.py > "$LOG_FILE" 2>&1 &
  echo $! > "$PID_FILE"
  sleep 1
  echo "✅ 伺服器已啟動 (PID $(cat $PID_FILE))"
  echo "   網址：http://$(hostname -I | awk '{print $1}'):$PORT"
  echo "   Log ：tail -f $LOG_FILE"
}

stop() {
  if [ ! -f "$PID_FILE" ]; then echo "伺服器未執行"; return; fi
  kill "$(cat $PID_FILE)" 2>/dev/null && rm "$PID_FILE"
  echo "🛑 伺服器已停止"
}

status() {
  if [ -f "$PID_FILE" ] && kill -0 "$(cat $PID_FILE)" 2>/dev/null; then
    echo "✅ 執行中 (PID $(cat $PID_FILE))"
  else
    echo "🔴 未執行"
  fi
}

case "${1:-start}" in
  start)  start  ;;
  stop)   stop   ;;
  restart) stop; sleep 1; start ;;
  status) status ;;
  *) echo "用法：bash deploy.sh [start|stop|restart|status]" ;;
esac
