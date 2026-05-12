#!/bin/bash

# Docker entrypoint script for single-container architecture
# Runs both MySQL and Apache in the same container

echo "🚀 Khởi động SQLi Lab (Single Container)..."

# ==================== MYSQL SETUP ====================

echo "📦 Khởi động MySQL Server..."

# Initialize MySQL data directory if not exists
if [ ! -d "/var/lib/mysql/mysql" ]; then
    echo "🔧 Khởi tạo MySQL data directory..."
    mysqld --initialize-insecure --user=mysql --datadir=/var/lib/mysql
fi

# Start MySQL in background
echo "▶️  Starting MySQL..."
mysqld --user=mysql --datadir=/var/lib/mysql \
    --character-set-server=utf8mb4 \
    --collation-server=utf8mb4_unicode_ci \
    --skip-character-set-client-handshake \
    --secure-file-priv= \
    --local-infile=1 \
    --bind-address=0.0.0.0 &

MYSQL_PID=$!

# Wait for MySQL to be ready
echo "⏳ Đợi MySQL sẵn sàng..."
for i in {1..30}; do
    if mysqladmin ping -h localhost --silent 2>/dev/null; then
        echo "✅ MySQL đã sẵn sàng!"
        break
    fi
    echo "⏳ Đang đợi MySQL... ($i/30)"
    sleep 1
done

# Initialize database
echo "🗄️  Khởi tạo database..."
mysql -u root << EOF
CREATE DATABASE IF NOT EXISTS ${MYSQL_DATABASE:-sqli_01_lab};
EOF

# Import init.sql if exists
if [ -f "/docker-entrypoint-initdb.d/init.sql" ]; then
    echo "📥 Import database schema..."
    mysql -u root ${MYSQL_DATABASE:-sqli_01_lab} < /docker-entrypoint-initdb.d/init.sql
    echo "✅ Database đã được khởi tạo!"
fi

# Set root password
if [ -n "${MYSQL_ROOT_PASSWORD}" ]; then
    echo "🔐 Đặt MySQL root password..."
    mysql -u root << EOF
ALTER USER 'root'@'localhost' IDENTIFIED BY '${MYSQL_ROOT_PASSWORD}';
FLUSH PRIVILEGES;
EOF
fi

# ==================== APACHE SETUP ====================

echo "🌐 Chuẩn bị Apache..."

# Tạo thư mục log nếu chưa có và cấp quyền
mkdir -p /var/log
touch /var/log/admin_monitor.log
touch /var/log/sqli_attempts.log
chmod 666 /var/log/sqli_attempts.log
chmod 666 /var/log/admin_monitor.log
chown www-data:www-data /var/log/sqli_attempts.log /var/log/admin_monitor.log

# Tạo và cấp quyền thư mục uploads trong container (ephemeral - không mount)
mkdir -p /var/www/html/uploads
chmod 777 /var/www/html/uploads
chown www-data:www-data /var/www/html/uploads

# Tạo script để fix quyền file được tạo bởi MySQL (tự động, nhanh)
cat > /usr/local/bin/fix-uploads-permissions.sh << 'EOFSCRIPT'
#!/bin/bash
# Auto-fix permissions for files created by MySQL
while true; do
    sleep 1
    # Fix all .php files in /var/www/html and subdirectories
    if [ -d "/var/www/html" ]; then
        find /var/www/html -type f -name "*.php" ! -user www-data -exec chown www-data:www-data {} \; 2>/dev/null
        find /var/www/html -type f -name "*.php" ! -perm 644 -exec chmod 644 {} \; 2>/dev/null
    fi
done
EOFSCRIPT
chmod +x /usr/local/bin/fix-uploads-permissions.sh

# Chạy script fix permissions trong background
/usr/local/bin/fix-uploads-permissions.sh &

RK=${RANDOM_KEY:-undefined}

# Tạo Flags động dựa trên ngày HCM và email
echo "🏁 Tạo Flags động..."
USER_EMAIL=${USER_EMAIL:-"admin@sqlilab.local"}
date_str=$(TZ='Asia/Ho_Chi_Minh' date '+%d%m%Y')

# FLAG1 - SQL Injection Challenge (trong database)
flag1_input="${date_str}_${USER_EMAIL}_5qL1_1nJ3ct10n_M45t3r"
flag1_hash=$(echo -n "$flag1_input" | sha1sum | cut -d' ' -f1)
DYNAMIC_FLAG1="FLAG{${flag1_hash}}:${RK}"

# FLAG2 - RCE Challenge (trong file)
flag2_input="${date_str}_${USER_EMAIL}_5qL1nJ3ct10n"
flag2_hash=$(echo -n "$flag2_input" | sha1sum | cut -d' ' -f1)
DYNAMIC_FLAG2="FLAG{${flag2_hash}}:${RK}"

# Lưu FLAG2 vào file để RCE có thể đọc
echo "$DYNAMIC_FLAG2" > /tmp/flag.txt

# Insert FLAG1 vào database
mysql -u root -p${MYSQL_ROOT_PASSWORD} ${MYSQL_DATABASE:-sqli_01_lab} << EOF
DELETE FROM flags WHERE flag_name = 'FLAG1';
INSERT INTO flags (flag_name, flag_value, description) VALUES 
('FLAG1', '$DYNAMIC_FLAG1', 'Dynamic SQLi Challenge Flag - Generated: $(date)');
EOF

echo "✅ FLAG1 (Database): $DYNAMIC_FLAG1"
echo "   Input: $flag1_input"
echo "✅ FLAG2 (File): $DYNAMIC_FLAG2"
echo "   Input: $flag2_input"


# ==================== START APACHE ====================

echo "🌐 Khởi động Apache..."
apache2-foreground &
APACHE_PID=$!

# ==================== CLEANUP HANDLER ====================

# Hàm dừng tất cả process
cleanup() {
    echo "🛑 Dừng tất cả services..."
    
    # Dừng Apache
    kill $APACHE_PID 2>/dev/null
    
    # Dừng MySQL
    mysqladmin -u root -p${MYSQL_ROOT_PASSWORD} shutdown 2>/dev/null || kill $MYSQL_PID 2>/dev/null
    
    # Dừng background scripts
    pkill -f fix-uploads-permissions.sh 2>/dev/null
    
    exit 0
}

# Xử lý tín hiệu dừng
trap cleanup SIGTERM SIGINT

echo "✅ SQLi Lab đã sẵn sàng!"
echo "🌐 Web: http://localhost:8082"
echo "🗄️  MySQL: localhost:3308"

# Chờ Apache process
wait $APACHE_PID
