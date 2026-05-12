#!/bin/bash

# Script để khởi động lab với tham số XSS được chỉ định
# Usage: ./scripts/start_lab.sh [field_name] [email]
# Hoặc: ENV=display_name USER_EMAIL=email@domain.com docker compose up -d

XSS_FIELD=${1:-${ENV:-comment}}
USER_EMAIL_PARAM=${2:-${USER_EMAIL:-admin@xsslab.local}}

# Danh sách các field hợp lệ
VALID_FIELDS=("display_name" "display_email" "title" "comment" "rating" "name" "username" "email" "product_name" "description" "users" "products" "comments")

if [[ ! " ${VALID_FIELDS[@]} " =~ " ${XSS_FIELD} " ]]; then
    echo "❌ Lỗi: Tham số không hợp lệ!"
    echo ""
    echo "Usage:"
    echo "  ./scripts/start_lab.sh [field_name] [email]"
    echo "  hoặc"
    echo "  ENV=field_name USER_EMAIL=email@domain.com docker compose up -d"
    echo ""
    echo "Các field hợp lệ (chỉ định field cụ thể):"
    echo "  - display_name: Tên hiển thị trong bình luận"
    echo "  - display_email: Email hiển thị trong bình luận"
    echo "  - title: Tiêu đề bình luận"
    echo "  - comment: Nội dung bình luận"
    echo "  - rating: Đánh giá (1-5 sao)"
    echo "  - name: Tên user (từ bảng users)"
    echo "  - username: Username"
    echo "  - email: Email user (từ bảng users)"
    echo "  - product_name: Tên sản phẩm"
    echo "  - description: Mô tả sản phẩm"
    echo ""
    echo "Hoặc nhóm field (backward compatibility):"
    echo "  - users: Tất cả field user (name, username, email, display_name, display_email)"
    echo "  - products: Tất cả field product (product_name, description)"
    echo "  - comments: Tất cả field comment (title, comment)"
    echo ""
    echo "Mặc định: comment"
    exit 1
fi

echo "🚀 Khởi động XSS Lab với XSS_VULN_FIELD=$XSS_FIELD"
echo "📧 Email: $USER_EMAIL_PARAM"
echo ""

# Export biến môi trường để docker-compose sử dụng
export ENV=$XSS_FIELD
export USER_EMAIL=$USER_EMAIL_PARAM

# Khởi động docker compose
docker compose down
docker compose up -d --build

echo ""
echo "✅ Lab đã khởi động!"
echo "📋 XSS_VULN_FIELD=$XSS_FIELD"
echo "📧 USER_EMAIL=$USER_EMAIL_PARAM"
echo "🌐 Ứng dụng: http://localhost:8081"
echo ""
echo "Để xem log:"
echo "  docker exec xss_02_web tail -f /var/log/admin_monitor.log"
echo ""
echo "Để xem Flag được tạo:"
echo "  docker exec xss_02_web cat /var/www/html/flag.txt"

