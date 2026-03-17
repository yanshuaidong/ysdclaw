#!/bin/bash
set -e

PROJECT_DIR=/home/ysdclaw
cd "$PROJECT_DIR"

echo "===== 1. 拉取最新代码 ====="
git pull origin main

echo "===== 2. 安装/更新 Python 依赖 ====="
cd backend
pip3 install -r requirements.txt -q

echo "===== 3. 初始化数据库 ====="
python3 init_db.py

echo "===== 4. 重启后端服务 ====="
pkill -f "uvicorn app.main:app" || true
sleep 1
nohup uvicorn app.main:app --host 127.0.0.1 --port 8000 > "$PROJECT_DIR/logs/backend.log" 2>&1 &
echo "后端已启动，PID: $!"

echo "===== 5. 更新 Nginx 配置并重载 ====="
cp "$PROJECT_DIR/deploy/nginx.conf" /etc/nginx/conf.d/ysdclaw.conf
nginx -t && nginx -s reload

echo ""
echo "===== 部署完成！====="
echo "访问地址: http://82.157.138.214"
