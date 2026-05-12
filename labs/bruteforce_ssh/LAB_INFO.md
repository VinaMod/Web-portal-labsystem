# SSH Bruteforce Lab - Complete Package

## 📁 Lab Structure

```
bruteforce_ssh/
├── docker-compose.yml      # Infrastructure definition
├── entrypoint.sh           # Dynamic flag generation & service startup
├── backup.sh               # Vulnerable script (for SSH server)
├── website/               
│   ├── index.html          # Company landing page
│   └── style.css           # Professional styling
├── start-lab.sh            # Start script
├── stop-lab.sh             # Stop script
├── banner.sh               # Client container banner
├── FLOW.md                 # Complete attack walkthrough
├── FLAG_GENERATION.md      # Dynamic flag documentation
├── README.md               # Lab documentation
└── LAB_INFO.md             # This file - Quick reference
```

---

## 🎯 Complete Attack Chain

### Phase 1: SSH Bruteforce
1. OSINT from website
2. Identify target (CTO Carl)
3. Extract username from email
4. Create wordlist
5. Network enumeration
6. Hydra bruteforce
7. SSH access → Flag #1

### Phase 2: Privilege Escalation
8. Enumerate with `sudo -l`
9. Analyze `/usr/local/bin/backup.sh`
10. Find `eval` vulnerability
11. Command injection exploit
12. Root access → Flag #2

---

## 🏆 Two Flags

**Flag #1 - User Access:**
```
Location: /home/carl/flag.txt
Method: SSH bruteforce
Format: FLAG{sha1_hash} (dynamically generated based on date and email)
```

**Flag #2 - Root Access:**
```
Location: /root/root_flag.txt
Method: Command injection via backup.sh
Format: FLAG{sha1_hash} (dynamically generated based on date and email)
```

> **Note**: Flags are generated dynamically using SHA1 hash of:
> - Date in GMT+7 timezone (ddmmyyyy format)
> - Email environment variable (default: carl@techvision.com)
> - Unique suffix for each flag
> 
> See [FLAG_GENERATION.md](FLAG_GENERATION.md) for details.

---

## 🔑 Credentials

- **SSH Target**: carl / password1
- **Client Container**: admin / admin123

---

## 🚀 Quick Start

```bash
./start-lab.sh

# Access client
docker exec -it bruteforce_client bash

# Follow FLOW.md for complete walkthrough
```

---

## 📚 Documentation

- **FLOW.md**: Detailed step-by-step guide with explanations
- **FLAG_GENERATION.md**: How dynamic flags work
- **README.md**: Lab overview and objectives
- **LAB_SUMMARY.txt**: Challenge mode summary

---

**Lab ready for training!** 🎓
