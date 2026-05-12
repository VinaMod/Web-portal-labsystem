#!/bin/bash
# Simple backup utility
echo "[*] TechVision Backup Utility v1.0"
echo "[*] Running as: $(whoami)"
echo ""
if [ -z "$1" ]; then
    echo "Usage: backup.sh <filename>"
    echo "Example: sudo backup.sh /etc/hosts"
    exit 1
fi

FILENAME="$1"
echo "[*] Backing up: $FILENAME"

# VULNERABLE: No input sanitization!
eval "cat $FILENAME"
