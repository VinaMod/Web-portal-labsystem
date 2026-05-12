#!/bin/bash

# Get date in GMT+7 timezone (Asia/Ho_Chi_Minh)
GMT7_DATE=$(TZ=Asia/Ho_Chi_Minh date +%d%m%Y)

# Get email from environment variable, default to "admin@example.com" if not set
EMAIL_VALUE="${EMAIL:-admin@example.com}"
RK=${RANDOM_KEY:-undefined}

# FLAG: User flag (Admin Login)
FLAG1_STRING="${GMT7_DATE}_${EMAIL_VALUE}_leaky_webroot_user"
FLAG1_HASH=$(echo -n "$FLAG1_STRING" | sha1sum | cut -d' ' -f1)
FLAG1="FLAG{${FLAG1_HASH}}:${RK}"

# Write flag to admin directory
echo "$FLAG1" > /var/www/html/admin/flag.txt
chown www-data:www-data /var/www/html/admin/flag.txt
chmod 644 /var/www/html/admin/flag.txt

echo "============================================"
echo "Flags generated successfully!"
echo "Date (GMT+7): $GMT7_DATE"
echo "Email: $EMAIL_VALUE"
echo "============================================"

# Hand over to apache
exec apache2-foreground
