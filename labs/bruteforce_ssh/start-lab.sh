#!/bin/bash

# Script khởi động lab bruteforce SSH

echo "====================================="
echo "   SSH BRUTEFORCE LAB - START"
echo "====================================="
echo ""

# Build và start containers
echo "[*] Building and starting containers..."
docker-compose up -d --build

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
echo "   - SSH Server: ssh-target:22 (internal only)"
echo "   - Client: bruteforce_client"
echo "   - Target: CTO Carl"
echo ""
echo "🚀 Quick Start:"
echo "   1. Open browser and visit:"
echo "      http://localhost:8080"
echo "      (Find info about CTO Carl)"
echo ""
echo "   2. Access client container:"
echo "      docker exec -it bruteforce_client bash"
echo ""
echo "   3. Read instructions inside:"
echo "      cat README.md"
echo ""
echo "   4. Recon - Check company website:"
echo "      curl http://ssh-target"
echo ""
echo "   5. Run bruteforce attack:"
echo "      hydra -l carl -P /home/admin/passwords.txt ssh://ssh-target -t 4"
echo ""
echo "📊 Useful commands:"
echo "   - View logs: docker-compose logs -f"
echo "   - Stop lab: docker-compose down"
echo "   - Restart: docker-compose restart"
echo ""
echo "====================================="
