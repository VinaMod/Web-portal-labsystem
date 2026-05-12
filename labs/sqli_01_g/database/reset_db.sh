#!/bin/bash

# Script reset database mỗi lần container khởi động
echo "🔄 Khởi tạo database SQLi Lab..."

# Chạy MySQL daemon trong background
docker-entrypoint.sh mysqld &
MYSQL_PID=$!

# Chờ MySQL khởi động
sleep 10

# Import database
mysql -uroot -p$MYSQL_ROOT_PASSWORD < /docker-entrypoint-initdb.d/init.sql

echo "✅ Database đã được khởi tạo!"

# Giữ MySQL chạy
wait $MYSQL_PID
