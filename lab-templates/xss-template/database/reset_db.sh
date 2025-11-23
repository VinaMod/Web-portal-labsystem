#!/bin/bash

# Script để reset database mỗi lần container khởi động
# Xóa thư mục dữ liệu MySQL để đảm bảo database được tạo lại từ đầu

echo "🔄 Resetting database - Xóa dữ liệu cũ..."

# Xóa thư mục dữ liệu MySQL nếu tồn tại (trừ khi đang chạy)
if [ -d "/var/lib/mysql/mysql" ]; then
    # Chỉ xóa nếu MySQL chưa chạy
    if ! pgrep -x mysqld > /dev/null; then
        rm -rf /var/lib/mysql/*
        echo "✅ Đã xóa dữ liệu database cũ"
    fi
fi

# Chạy MySQL entrypoint mặc định
# MySQL sẽ tự động chạy init.sql khi khởi tạo database mới
exec /entrypoint.sh mysqld

