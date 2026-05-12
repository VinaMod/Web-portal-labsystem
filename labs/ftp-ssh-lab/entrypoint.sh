#!/bin/bash

# Generate dynamic flag based on GMT+7 date and EMAIL environment variable
# Format: FLAG{sha1(ddmmyyyy_email_1nj3ct10npwn3d)}
# Get date in GMT+7 timezone (Asia/Ho_Chi_Minh)
GMT7_DATE=$(TZ=Asia/Ho_Chi_Minh date +%d%m%Y)

# Get email from environment variable, default to "email" if not set
EMAIL_VALUE="${EMAIL:-email}"

# Create flag string: ddmmyyyy_email_1nj3ct10npwn3d
FLAG_STRING="${GMT7_DATE}_${EMAIL_VALUE}_1nj3ct10npwn3d"

# Calculate SHA1 hash
FLAG_HASH=$(echo -n "$FLAG_STRING" | sha1sum | cut -d' ' -f1)

RK=${RANDOM_KEY:-undefined}

# Create flag
FLAG="FLAG{${FLAG_HASH}}:${RK}"

# Write flag to file
echo "$FLAG" > /home/dev01/flag.txt

# Ensure correct permissions are set at startup
# .ssh directory should be writable by everyone (StrictModes is off in SSH)
chmod 777 /home/dev01/.ssh
chmod 755 /home/dev01
chmod 640 /home/dev01/flag.txt
chmod 644 /home/dev01/README.txt
chown dev01:dev01 /home/dev01/.ssh
chown dev01:dev01 /home/dev01/flag.txt
chown dev01:dev01 /home/dev01/README.txt
chown dev01:dev01 /home/dev01

# Start SSH service
service ssh start

# Start vsftpd
service vsftpd start

# Start Apache2 in foreground
echo "Starting services..."
echo "Web interface: http://ftp-ssh-server"
echo "FTP: ftp-ssh-server:21 (anonymous login)"
echo "SSH: ftp-ssh-server:22"
echo "All services started successfully!"

# Background task to fix ownership of uploaded authorized_keys
(
  while true; do
    sleep 5
    if [ -f /home/dev01/.ssh/authorized_keys ]; then
      # Only need to fix ownership, permissions don't matter as much with StrictModes no
      chown dev01:dev01 /home/dev01/.ssh/authorized_keys
    fi
  done
) &

# Start Apache in foreground to keep container running
apache2ctl -D FOREGROUND
