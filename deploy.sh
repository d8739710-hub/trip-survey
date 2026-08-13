#!/bin/bash
# ============================================================
#  部門旅遊調查 - Linux 伺服器部署腳本
#  執行方式：sudo bash deploy.sh
# ============================================================

set -e

APP_USER="tripsurvey"
APP_DIR="/opt/trip-survey"
PORT=8080

echo "=== [1/4] 建立應用程式目錄 ==="
mkdir -p "$APP_DIR/data"

echo "=== [2/4] 複製程式檔案 ==="
cp index.html "$APP_DIR/"
cp server.py  "$APP_DIR/"
chown -R "$APP_USER" "$APP_DIR" 2>/dev/null || true   # 若帳號不存在則略過

echo "=== [3/4] 建立 systemd 服務 ==="
cat > /etc/systemd/system/trip-survey.service << EOF
[Unit]
Description=Trip Survey Python Server
After=network.target

[Service]
Type=simple
WorkingDirectory=$APP_DIR
ExecStart=$(which python3) $APP_DIR/server.py
Environment=PORT=$PORT
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

echo "=== [4/4] 啟動服務 ==="
systemctl daemon-reload
systemctl enable trip-survey
systemctl restart trip-survey
systemctl status trip-survey --no-pager

echo ""
echo "✅ 部署完成！"
echo "   伺服器網址：http://$(hostname -I | awk '{print $1}'):$PORT"
