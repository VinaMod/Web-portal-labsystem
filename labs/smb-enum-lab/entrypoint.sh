#!/bin/bash

# Generate dynamic flags based on GMT+7 date and EMAIL environment variable
# Format: FLAG{sha1(ddmmyyyy_email_suffix)}

# Get date in GMT+7 timezone (Asia/Ho_Chi_Minh)
GMT7_DATE=$(TZ=Asia/Ho_Chi_Minh date +%d%m%Y)

# Get email from environment variable, default to "sysadmin@securecorp.com" if not set
EMAIL_VALUE="${EMAIL:-sysadmin@securecorp.com}"
RK=${RANDOM_KEY:-undefined}

# ============================================
# FLAG #1: User flag (SSH access via SMB enumeration)
# ============================================
FLAG1_STRING="${GMT7_DATE}_${EMAIL_VALUE}_smb_enum_success"
FLAG1_HASH=$(echo -n "$FLAG1_STRING" | sha1sum | cut -d' ' -f1)
FLAG1="FLAG{${FLAG1_HASH}}:${RK}"

# Write flag to system's home directory (SSH target user)
echo "$FLAG1" > /home/system/flag.txt
chown system:system /home/system/flag.txt
chmod 600 /home/system/flag.txt

# Create README for user
echo "Chúc mừng! Bạn đã khai thác SMB thành công!" > /home/sysadmin/README.txt
echo "Flag của bạn nằm trong file flag.txt" >> /home/sysadmin/README.txt
chown sysadmin:sysadmin /home/sysadmin/README.txt

echo "============================================"
echo "Flags generated successfully!"
echo "Date (GMT+7): $GMT7_DATE"
echo "Email: $EMAIL_VALUE"
echo "============================================"

# Start SSH service
service ssh start
echo "✓ SSH service started on port 22"

# Create Samba user (cần tạo sau khi Samba đã được cài đặt)
# SMB account: sysadmin / Sy54dm1n
echo -e "Sy54dm1n\nSy54dm1n" | smbpasswd -a -s sysadmin 2>/dev/null || true

# Start Samba service
# Create necessary directories
mkdir -p /var/run/samba
mkdir -p /var/log/samba

# Start Samba in background
smbd -D
nmbd -D
echo "✓ Samba service started on ports 139, 445"

echo "============================================"
echo "All services ready!"
echo "Web interface: http://smb-target"
echo "SMB: smb-target:445"
echo "SSH: smb-target:22"
echo "============================================"

# Start Nginx in foreground to keep container running
echo "Starting Nginx..."
exec nginx -g 'daemon off;'

