#!/bin/bash

# Test SHA1 calculation
email="hoangnthhe141575@fpt.edu.vn"
date_str="18112025"
flag_input="${date_str}_${email}_Cr0ssS1teScr1pt1ng"
flag_hash=$(echo -n "$flag_input" | sha1sum | cut -d' ' -f1)

echo "Input: $flag_input"
echo "SHA1: $flag_hash"
echo "Flag: FLAG{${flag_hash}}"

# Kiểm tra với kết quả bạn đưa ra
expected="9905636be052b07e5746e5abffc07a41b26f4e08"
if [ "$flag_hash" = "$expected" ]; then
    echo "✅ SHA1 khớp với ví dụ!"
else
    echo "❌ SHA1 không khớp với ví dụ ($expected)"
fi
