#!/bin/bash

# Script khởi động lab SMB Enumeration

echo "====================================="
echo "   SMB ENUMERATION LAB - START"
echo "====================================="
echo ""

# Build và start containers
echo "[*] Building and starting containers..."
docker compose up -d --build

echo ""
echo "[*] Waiting for services to be ready..."
sleep 5

echo ""
echo "====================================="
echo "   LAB IS READY!"
echo "====================================="
echo ""
echo "📋 Lab Information:"
echo "   - Company Website: http://localhost:8080 🌐"
echo "   - SMB Server: smb-target:445 (internal only)"
echo "   - SSH Server: smb-target:22 (internal only)"
echo "   - Client: smb_client"
echo "   - Scenario: Internal network penetration test"
echo ""
echo "🎯 Objective:"
echo "   Enumerate SMB shares, find credentials, and gain SSH access"
echo ""
echo "🚀 Quick Start:"
echo "   1. Access client container:"
echo "      docker exec -it smb_client bash"
echo ""
echo "   2. Scan for SMB service:"
echo "      nmap -p 445 smb-target"
echo ""
echo "   3. Enumerate SMB shares:"
echo "      smbclient -L //smb-target -N"
echo "      enum4linux -a smb-target"
echo ""
echo "   4. Access public share (documents) to find hints"
echo ""
echo "   5. Password spray on protected shares (config, backup)"
echo ""
echo "   6. Find credentials and SSH login"
echo ""
echo "📊 Useful commands:"
echo "   - View logs: docker compose logs -f"
echo "   - Stop lab: docker compose down"
echo "   - Restart: docker compose restart"
echo ""
echo "====================================="

