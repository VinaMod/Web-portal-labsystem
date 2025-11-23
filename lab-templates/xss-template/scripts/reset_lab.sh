#!/bin/bash

# Script reset lab về trạng thái ban đầu
echo "🔄 Reset XSS Lab về trạng thái ban đầu..."

# Dừng và xóa tất cả container
echo "🛑 Dừng và xóa container..."
docker compose down

# Xóa tất cả volume (nếu có)
echo "🗑️  Xóa volume cũ..."
docker volume prune -f

# Xóa image cũ (tùy chọn)
read -p "Xóa image cũ để rebuild hoàn toàn? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🗑️  Xóa image cũ..."
    docker image rm xss_02-web 2>/dev/null || true
fi

# Khởi động lại lab
echo "🚀 Khởi động lab mới..."
docker compose up -d --build

# Chờ lab khởi động
echo "⏳ Chờ lab khởi động..."
sleep 30

# Kiểm tra trạng thái
echo "📊 Kiểm tra trạng thái..."
docker compose ps

echo "✅ Lab đã được reset và khởi động!"
echo "🌐 Truy cập: http://localhost:8081"
echo "📊 Monitor logs: docker exec xss_02_web tail -f /var/log/admin_monitor.log"
