#!/bin/bash
# Banner script hiển thị IP và hostname của victim

# Resolve IP của SSH server (victim)
VICTIM_IP=$(getent hosts ssh-target | awk '{print $1}' | head -n1)

# Nếu không resolve được, thử với service name
if [ -z "$VICTIM_IP" ]; then
    VICTIM_IP=$(getent hosts ssh-server | awk '{print $1}' | head -n1)
fi

# Nếu vẫn không có, dùng ping để lấy IP
if [ -z "$VICTIM_IP" ]; then
    VICTIM_IP=$(ping -c 1 ssh-target 2>/dev/null | grep -oP '(\d+\.){3}\d+' | head -n1)
fi

# Hiển thị banner
echo ""
if [ -n "$VICTIM_IP" ]; then
    echo "Victim IP: $VICTIM_IP"
else
    echo "Victim IP: Resolving..."
fi
echo "Victim Hostname: ssh-target"
echo ""

