#!/bin/bash

# Script dừng và dọn dẹp lab

echo "====================================="
echo "   SMB ENUMERATION LAB - STOP"
echo "====================================="
echo ""

echo "[*] Stopping containers..."
docker compose down

echo ""
echo "[*] Lab stopped successfully!"
echo ""
echo "To start again, run: ./start-lab.sh"
echo "====================================="

