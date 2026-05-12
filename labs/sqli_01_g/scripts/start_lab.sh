#!/bin/bash

echo "======================================"
echo "      SQL Injection Lab - Bookstore"
echo "======================================"
echo ""

# Script để khởi động lab với tham số SQLi được chỉ định
# Usage: ./scripts/start_lab.sh [field_name] [email]
# Hoặc: ENV=field_name USER_EMAIL=email@domain.com docker compose up -d

SQLI_FIELD=${1:-${ENV:-title}}
USER_EMAIL_PARAM=${2:-${USER_EMAIL:-admin@sqlilab.local}}

# Danh sách các field hợp lệ
VALID_FIELDS=("title" "author" "publisher" "category" "year" "isbn" "language" "book_info" "people" "publisher_info" "categories" "search_all")

# Kiểm tra Docker và Docker Compose
if ! command -v docker &> /dev/null; then
    echo "❌ Docker chưa được cài đặt!"
    echo "Vui lòng cài đặt Docker trước khi chạy lab."
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! command -v docker &> /dev/null; then
    echo "❌ Docker Compose chưa được cài đặt!"
    echo "Vui lòng cài đặt Docker Compose trước khi chạy lab."
    exit 1
fi

# Kiểm tra tham số
if [[ ! " ${VALID_FIELDS[@]} " =~ " ${SQLI_FIELD} " ]]; then
    echo "❌ Lỗi: Tham số không hợp lệ!"
    echo ""
    echo "Usage:"
    echo "  ./scripts/start_lab.sh [field_name] [email]"
    echo "  hoặc"
    echo "  ENV=field_name USER_EMAIL=email@domain.com docker compose up -d"
    echo ""
    echo "Các field hợp lệ (chỉ định field cụ thể):"
    echo "  - title: Tên sách"
    echo "  - author: Tác giả"
    echo "  - publisher: Nhà xuất bản"
    echo "  - category: Thể loại sách"
    echo "  - year: Năm xuất bản"
    echo "  - isbn: Mã ISBN"
    echo "  - language: Ngôn ngữ"
    echo ""
    echo "Hoặc nhóm field:"
    echo "  - book_info: Tất cả field sách (title, isbn, language, year)"
    echo "  - people: Tác giả (author)"
    echo "  - publisher_info: Nhà xuất bản (publisher)"
    echo "  - categories: Thể loại (category)"
    echo "  - search_all: Tất cả field có thể tìm kiếm"
    echo ""
    echo "Mặc định: title"
    exit 1
fi

# Kiểm tra cổng đã được sử dụng chưa
if lsof -Pi :8082 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Cảnh báo: Cổng 8082 đã được sử dụng!"
    echo "Bạn có muốn tiếp tục không? Lab có thể không hoạt động đúng cách."
    read -p "Tiếp tục? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

if lsof -Pi :3308 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Cảnh báo: Cổng 3308 (MySQL) đã được sử dụng!"
    echo "Bạn có muốn tiếp tục không? Database có thể không hoạt động đúng cách."
    read -p "Tiếp tục? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "🚀 Bắt đầu khởi động SQL Injection Lab..."
echo "📋 SQLI_VULN_FIELD: $SQLI_FIELD"
echo "📧 USER_EMAIL: $USER_EMAIL_PARAM"
echo ""

# Export biến môi trường để docker-compose sử dụng
export ENV=$SQLI_FIELD
export USER_EMAIL=$USER_EMAIL_PARAM

# Dừng container cũ nếu có
echo "🛑 Dừng container cũ..."
docker compose down -v 2>/dev/null

# Build và khởi động container mới
echo "🔨 Build và khởi động container..."
docker compose up -d --build

# Chờ container khởi động
echo "⏳ Chờ container khởi động..."
sleep 10

# Kiểm tra trạng thái container
if docker compose ps | grep -q "Up"; then
    echo ""
    echo "✅ SQL Injection Lab đã khởi động thành công!"
    echo ""
    echo "📋 Thông tin truy cập:"
    echo "   🌐 Web Application: http://localhost:8082"
    echo "   📊 Admin Panel: http://localhost:8082/admin.php"
    echo "   🗄️  MySQL Database: localhost:3308"
    echo ""
    echo "🔧 Cấu hình lab:"
    echo "   🎯 Trường có lỗ hổng: $SQLI_FIELD"
    echo "   📧 Email: $USER_EMAIL_PARAM"
    echo ""
    echo "👤 Tài khoản mặc định:"
    echo "   📧 Admin: admin@bookstore.local / admin123"
    echo "   👨‍💼 User: user@bookstore.local / user123"
    echo ""
    echo "� Mục tiêu Lab:"
    echo "   • Tìm và khai thác lỗ hổng SQL Injection"
    echo "   • Lấy được FLAG từ admin panel"
    echo "   • Thử nghiệm các kỹ thuật SQLi khác nhau"
    echo ""
    echo "🔧 Hướng dẫn:"
    echo "   • Thử tìm kiếm sách với các ký tự đặc biệt"
    echo "   • Sử dụng các payload SQLi trong các trường tìm kiếm"
    echo "   • Quan sát phản hồi của ứng dụng"
    echo ""
    echo "⚡ Lệnh hữu ích:"
    echo "   • Xem log: docker compose logs -f"
    echo "   • Dừng lab: docker compose down"
    echo "   • Reset lab: ./scripts/reset_lab.sh"
    echo "   • Xem log SQLi: docker exec sqli_01_web tail -f /var/log/sqli_attempts.log"
    echo "   • Xem Flag: docker exec sqli_01_web cat /var/www/html/flag.txt"
    echo ""
    
    # Kiểm tra kết nối web
    echo "🔍 Kiểm tra kết nối web..."
    if curl -s http://localhost:8082 >/dev/null 2>&1; then
        echo "✅ Web application đã sẵn sàng!"
        echo ""
        echo "🎉 Chúc bạn học tập vui vẻ và hiệu quả!"
        echo "🌐 Mở trình duyệt và truy cập: http://localhost:8082"
    else
        echo "⚠️  Web application có thể chưa sẵn sàng."
        echo "Vui lòng đợi thêm vài giây và thử lại."
    fi
else
    echo ""
    echo "❌ Có lỗi xảy ra khi khởi động lab!"
    echo ""
    echo "🔍 Kiểm tra lỗi:"
    docker compose logs
    echo ""
    echo "💡 Gợi ý khắc phục:"
    echo "   • Kiểm tra Docker đã chạy chưa"
    echo "   • Kiểm tra cổng 8082 và 3308 có bị chiếm dụng không"
    echo "   • Chạy lại lệnh: ./scripts/start_lab.sh"
    echo "   • Xem log chi tiết: docker compose logs -f"
fi

echo ""
echo "======================================"
