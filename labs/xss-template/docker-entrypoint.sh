#!/bin/bash

# Docker entrypoint script
# Khởi động Apache và admin monitor

echo "🚀 Khởi động XSS Lab..."

# Chờ MySQL sẵn sàng
echo "⏳ Đợi MySQL sẵn sàng..."
MYSQL_HOST=${MYSQL_HOST:-db}
MYSQL_USER=${MYSQL_USER:-root}
MYSQL_PASSWORD=${MYSQL_PASSWORD:-root123}
MYSQL_DATABASE=${MYSQL_DATABASE:-xss_02_lab}

until php -r "
\$conn = @new mysqli('$MYSQL_HOST', '$MYSQL_USER', '$MYSQL_PASSWORD', '$MYSQL_DATABASE');
if (\$conn->connect_error) {
    exit(1);
}
\$conn->close();
exit(0);
" 2>/dev/null; do
    echo "⏳ Đang đợi MySQL..."
    sleep 2
done
echo "✅ MySQL đã sẵn sàng!"

# Tạo thư mục log nếu chưa có
mkdir -p /var/log
touch /var/log/admin_monitor.log

# Tạo Flag động dựa trên ngày HCM và email
echo "🏁 Tạo Flag động..."
USER_EMAIL=${USER_EMAIL:-"admin@xsslab.local"}
echo "$USER_EMAIL"
date_str=$(TZ='Asia/Ho_Chi_Minh' date '+%d%m%Y')
echo "$date_str"
RK=${RANDOM_KEY:-undefined}
flag_input="${date_str}_${USER_EMAIL}_Cr0ssS1teScr1pt1ng"
flag_hash=$(echo -n "$flag_input" | sha1sum | cut -d' ' -f1)
DYNAMIC_FLAG="FLAG{${flag_hash}}:${RK}"
echo "$DYNAMIC_FLAG"
# Lưu flag vào file để admin.php có thể đọc
echo "$DYNAMIC_FLAG" > /var/www/html/flag.txt
echo "✅ Flag đã được tạo: $DYNAMIC_FLAG"
echo "📝 Input: $flag_input"

# Thiết lập cron: chạy admin_check.js mỗi 3 phút
echo "🔧 Thiết lập cron cho admin_check.js..."
echo "*/3 * * * * root cd /var/www/html && NODE_PATH=/usr/lib/node_modules PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium /usr/bin/node admin_check.js >> /var/log/admin_monitor.log 2>&1" > /etc/cron.d/admin_cron
chmod 0644 /etc/cron.d/admin_cron

# Khởi động cron
echo "🔄 Khởi động cron service..."
service cron start || cron

# Khởi động Apache trong background
echo "🌐 Khởi động Apache..."
apache2-foreground &
APACHE_PID=$!

# Hàm dừng tất cả process
cleanup() {
    echo "🛑 Dừng tất cả services..."
    
    # Dừng Apache
    kill $APACHE_PID 2>/dev/null
    
    # Dừng cron
    service cron stop 2>/dev/null || pkill cron 2>/dev/null
    
    exit 0
}

# Xử lý tín hiệu dừng
trap cleanup SIGTERM SIGINT

# Chờ Apache process
wait $APACHE_PID
