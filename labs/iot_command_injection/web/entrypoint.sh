#!/bin/sh

set -e

# fallback ENV
EMAIL=${EMAIL:-admin@example.com}
RANDOM_KEY=${RANDOM_KEY:-$(head /dev/urandom | tr -dc a-z0-9 | head -c 16)}

CURRENT_DATE=$(date +%d%m%Y)

USER_HASH=$(echo -n "${CURRENT_DATE}_${EMAIL}_iot_command_injection_user" | sha1sum | awk '{print $1}')
ROOT_HASH=$(echo -n "${CURRENT_DATE}_${EMAIL}_iot_command_injection_root" | sha1sum | awk '{print $1}')

# USER FLAG
echo "FLAG{${USER_HASH}}:${RANDOM_KEY}" > /home/user_flag.txt
chmod 644 /home/user_flag.txt
chown iot_user:iot_user /home/user_flag.txt

# ROOT FLAG
mkdir -p /root
echo "FLAG{${ROOT_HASH}}:${RANDOM_KEY}" > /root/root_flag.txt
chmod 600 /root/root_flag.txt

# chạy app
exec su -s /bin/sh iot_user -c "$*"

