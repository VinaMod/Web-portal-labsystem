#!/bin/bash

echo "======================================"
echo "      Reset SQL Injection Lab"
echo "======================================"
echo ""

echo "🔄 Đang reset SQL Injection Lab..."

# Dừng tất cả container
echo "🛑 Dừng tất cả container..."
docker compose down -v

# Xóa các volume và dữ liệu cũ
echo "🗑️  Xóa dữ liệu cũ..."
docker system prune -f 2>/dev/null
docker volume prune -f 2>/dev/null

# Xóa các image build cũ nếu có
echo "📦 Xóa image cũ..."
docker rmi sqli_01_web 2>/dev/null || true

echo ""
echo "✅ Lab đã được reset thành công!"
echo ""
echo "🚀 Để khởi động lại lab, sử dụng:"
echo "   ./scripts/start_lab.sh"
echo ""
echo "📋 Hoặc với cấu hình cụ thể:"
echo "   ./scripts/start_lab.sh title admin@sqlilab.local"
echo ""
echo "======================================"
