#!/bin/bash

# Đặt múi giờ
export TZ=Asia/Ho_Chi_Minh

EMAIL=${EMAIL:-admin@example.com}
DATE_STR=$(date +%d%m%Y)

# Random key (RK)
RK=${RANDOM_KEY:-undefined}

# Hash content trước
RAW_CONTENT="${DATE_STR}_${EMAIL}_mqtt_leak_flag"
HASH=$(echo -n "$RAW_CONTENT" | sha1sum | awk '{print $1}')

# Format: FLAG{hash}:RK
export IOT_FLAG="FLAG{${HASH}}:${RK}"

# Generate UUID cho session
export DOOR_PIN=$(cat /proc/sys/kernel/random/uuid)

# Start mosquitto
mosquitto -c /etc/mosquitto/mosquitto.conf &
MOSQUITTO_PID=$!
sleep 2

# Start app
python3 app.py

wait $MOSQUITTO_PID