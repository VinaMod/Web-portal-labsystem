#!/bin/bash
# Script khởi động cả SSH và Nginx trong cùng container

# Khởi động SSH daemon ở background
/usr/sbin/sshd -D &

# Khởi động Nginx ở foreground (giữ container sống)
exec nginx -g "daemon off;"

