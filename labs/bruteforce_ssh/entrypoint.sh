#!/bin/bash

# Generate dynamic flags based on GMT+7 date and EMAIL environment variable
# Format: FLAG{sha1(ddmmyyyy_email_suffix)}

# Get date in GMT+7 timezone (Asia/Ho_Chi_Minh)
GMT7_DATE=$(TZ=Asia/Ho_Chi_Minh date +%d%m%Y)

# Get email from environment variable, default to "carl@techvision.com" if not set
EMAIL_VALUE="${EMAIL:-carl@techvision.com}"

RK=${RANDOM_KEY:-undefined}
# ============================================
# FLAG #1: User flag (SSH bruteforce success)
# ============================================
FLAG1_STRING="${GMT7_DATE}_${EMAIL_VALUE}_ssh_bruteforce"
FLAG1_HASH=$(echo -n "$FLAG1_STRING" | sha1sum | cut -d' ' -f1)
FLAG1="FLAG{${FLAG1_HASH}}:${RK}"

# Write flag to carl's home directory
echo "$FLAG1" > /home/carl/flag.txt
chown carl:carl /home/carl/flag.txt
chmod 600 /home/carl/flag.txt

# ============================================
# FLAG #2: Root flag (privilege escalation)
# ============================================
FLAG2_STRING="${GMT7_DATE}_${EMAIL_VALUE}_privesc_root"
FLAG2_HASH=$(echo -n "$FLAG2_STRING" | sha1sum | cut -d' ' -f1)
FLAG2="FLAG{${FLAG2_HASH}}:${RK}"

# Write flag to root directory
echo "$FLAG2" > /root/root_flag.txt
chmod 600 /root/root_flag.txt

echo "============================================"
echo "Flags generated successfully!"
echo "Date (GMT+7): $GMT7_DATE"
echo "Email: $EMAIL_VALUE"
echo "============================================"

# Start SSH service
service ssh start
echo "✓ SSH service started on port 22"

echo "============================================"
echo "All services ready!"
echo "Web interface: http://ssh-target"
echo "SSH: ssh-target:22"
echo "============================================"

# Start Nginx in foreground to keep container running
echo "Starting Nginx..."
exec nginx -g 'daemon off;'
