#!/bin/bash

# Lấy port từ ENV hoặc mặc định 50000
PORT=${clientTestPort:-50000}

echo "Starting ttyd on port $PORT with writable mode..."

# Giải thích các cờ:
# -W : Quan trọng nhất, cho phép gõ (Write)
# -p : Cổng chạy webshell
# -i : Lắng nghe trên mọi interface (0.0.0.0)
ttyd -i 0.0.0.0 -p "$PORT" -W bash &

echo "Webshell is running at http://0.0.0.0:$PORT"

# Giữ container
tail -f /dev/null
