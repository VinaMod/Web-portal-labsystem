#!/bin/bash

# Ensure permissions
chown -R www-data:www-data /var/www/html

# Get date in GMT+7 timezone (Asia/Ho_Chi_Minh)
GMT7_DATE=$(TZ=Asia/Ho_Chi_Minh date +%d%m%Y)

# Get email from environment variable, default to "admin@example.com" if not set
EMAIL_VALUE="${EMAIL:-admin@example.com}"
RK=${RANDOM_KEY:-undefined}

# Calculate flag for display in logs
FLAG1_STRING="${GMT7_DATE}_${EMAIL_VALUE}_image_extraction_user"
FLAG1_HASH=$(echo -n "$FLAG1_STRING" | sha1sum | cut -d' ' -f1)
FLAG1="FLAG{${FLAG1_HASH}}:${RK}"

echo "============================================"
echo "Flags generated successfully!"
echo "Date (GMT+7): $GMT7_DATE"
echo "Email: $EMAIL_VALUE"
echo "User Flag: $FLAG1"
echo "============================================"

# Start Apache in foreground
exec apache2-foreground
