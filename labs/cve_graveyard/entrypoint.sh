#!/bin/bash

# Default email if not provided
USER_EMAIL=${EMAIL:-admin@example.com}

# Generate dynamic flag and save to /flag.txt
FLAG_CONTENT="$(TZ=Asia/Ho_Chi_Minh date +%d%m%Y)_${USER_EMAIL}_tomcat_rce_flag"
RK=${RANDOM_KEY:-undefined}
# Hash FLAG_CONTENT
HASH=$(echo -n "$FLAG_CONTENT" | sha1sum | awk '{print $1}')

# Format: FLAG{hash}:RK
echo -n "FLAG{${HASH}}:${RK}" > /flag.txt

# Ensure only root can read it directly but tomcat user (if any) can read it?
# In tomcat:7 container, it runs as root by default, so chmod 644 is fine.
chmod 644 /flag.txt

# Start Tomcat
exec catalina.sh run
