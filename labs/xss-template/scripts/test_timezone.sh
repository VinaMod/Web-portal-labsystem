#!/bin/bash

# Script test timezone
echo "🕒 Test Timezone..."
echo ""

echo "System default timezone:"
date '+%d/%m/%Y %H:%M:%S %Z'

echo ""
echo "Asia/Ho_Chi_Minh timezone (GMT+7):"
TZ='Asia/Ho_Chi_Minh' date '+%d/%m/%Y %H:%M:%S %Z'

echo ""
echo "Date format for Flag (ddmmyyyy):"
date_str=$(TZ='Asia/Ho_Chi_Minh' date '+%d%m%Y')
echo $date_str

echo ""
echo "Test Flag generation:"
USER_EMAIL="test@example.com"
flag_input="${date_str}_${USER_EMAIL}_Cr0ssS1teScr1pt1ng"
flag_hash=$(echo -n "$flag_input" | sha1sum | cut -d' ' -f1)
echo "Input: $flag_input"
echo "SHA1: $flag_hash"
echo "Flag: FLAG{${flag_hash}}"
