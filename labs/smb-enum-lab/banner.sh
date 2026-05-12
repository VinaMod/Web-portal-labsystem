#!/bin/bash
# Banner script hiển thị IP và hostname của victim

# Resolve IP của SMB server (victim)
VICTIM_IP=$(getent hosts smb-target | awk '{print $1}' | head -n1)

# Nếu không resolve được, thử với service name
if [ -z "$VICTIM_IP" ]; then
    VICTIM_IP=$(getent hosts smb-server | awk '{print $1}' | head -n1)
fi

# Nếu vẫn không có, dùng ping để lấy IP
if [ -z "$VICTIM_IP" ]; then
    VICTIM_IP=$(ping -c 1 smb-target 2>/dev/null | grep -oP '(\d+\.){3}\d+' | head -n1)
fi

# Hiển thị banner
echo ""
echo "============================================"
echo "   SECURECORP SMB ENUMERATION LAB"
echo "   CLIENT CONTAINER"
echo "============================================"
if [ -n "$VICTIM_IP" ]; then
    echo "Victim IP: $VICTIM_IP"
else
    echo "Victim IP: Resolving..."
fi
echo "Victim Hostname: smb-target"
echo "============================================"
echo ""

