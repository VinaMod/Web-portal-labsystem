#!/bin/bash

# Script để kiểm tra Flag hiện tại
echo "🏁 Kiểm tra Flag hiện tại..."
echo ""

# Kiểm tra container có đang chạy không
if ! docker ps | grep -q "sqli_01_web"; then
    echo "❌ Container sqli_01_web không đang chạy!"
    echo "Khởi động lab trước:"
    echo "  ./scripts/start_lab.sh [field_name] [email]"
    exit 1
fi

# Lấy thông tin Flag
echo "📋 Thông tin Flag:"
docker exec sqli_01_web bash -c '
if [ -f /var/www/html/flag.txt ]; then
    flag=$(cat /var/www/html/flag.txt)
    echo "Flag: $flag"
    
    # Lấy thông tin từ biến môi trường
    user_email=${USER_EMAIL:-"admin@sqlilab.local"}
    date_str=$(TZ="Asia/Ho_Chi_Minh" date "+%d%m%Y")
    flag_input="${date_str}_${user_email}_5qL1nJ3ct10n"
    
    echo "Email: $user_email"
    echo "Ngày (HCM): $date_str"
    echo "Input: $flag_input"
    echo "SHA1: $(echo -n "$flag_input" | sha1sum | cut -d\" \" -f1)"
    
    # Thời gian tạo Flag
    flag_time=$(stat -c %Y /var/www/html/flag.txt 2>/dev/null)
    if [ "$flag_time" != "" ]; then
        echo "Thời gian tạo: $(TZ="Asia/Ho_Chi_Minh" date -d @$flag_time "+%d/%m/%Y %H:%M:%S")"
    fi
else
    echo "❌ Flag chưa được tạo!"
fi
'

echo ""
echo "🌐 Truy cập Admin Panel để xem Flag:"
echo "  http://localhost:8082/admin.php"
