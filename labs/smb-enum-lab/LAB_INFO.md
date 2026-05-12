# SMB Enumeration Lab - SecureCorp Internal Network

## 📁 Lab Structure

```
smb-enum-lab/
├── docker-compose.yml      # Infrastructure definition
├── entrypoint.sh           # Dynamic flag generation & service startup
├── smb-config/
│   └── smb.conf            # Samba configuration
├── website/               
│   ├── index.html          # Company landing page
│   └── style.css           # Professional styling
├── start-lab.sh            # Start script
├── stop-lab.sh             # Stop script
├── banner.sh               # Client container banner
├── FLOW.md                 # Complete attack walkthrough
├── LAB_INFO.md             # This file - Quick reference
└── README.md               # Lab documentation
```

---

## 🎯 Complete Attack Chain

### Phase 1: SMB Enumeration
1. Network scan (nmap)
2. SMB enumeration (smbclient/enum4linux)
3. Access public share (documents) → Find hint
4. User enumeration
5. Password spraying on config share
6. Access config share → Find credentials
7. SSH login → Flag #1

---

## 🏆 Flag

**Flag #1 - User Access:**
```
Location: /home/sysadmin/flag.txt
Method: SMB enumeration + password spraying + SSH login
Format: FLAG{sha1_hash} (dynamically generated based on date and email)
```

> **Note**: Flag is generated dynamically using SHA1 hash of:
> - Date in GMT+7 timezone (ddmmyyyy format)
> - Email environment variable (default: sysadmin@securecorp.com)
> - Unique suffix: `smb_enum_success`
> 
> Example: `05122025_sysadmin@securecorp.com_smb_enum_success` → SHA1 hash

---

## 🔑 Credentials

- **SMB Target**: sysadmin / Sy54dm1n
- **SSH Target**: system / 657sdfh85d
- **Client Container**: admin / admin123

---

## 🚀 Quick Start

```bash
./start-lab.sh

# Access client
docker exec -it smb_client bash

# Follow FLOW.md for complete walkthrough
```

---

## 📚 Documentation

- **FLOW.md**: Detailed step-by-step guide with explanations
- **LAB_INFO.md**: This file - Quick reference
- **README.md**: Lab overview and objectives

---

## 🔧 Services

- **Web Server**: Port 80 (exposed as 8080)
- **SMB Server**: Ports 139, 445 (internal only)
- **SSH Server**: Port 22 (internal only)

---

## 📋 SMB Shares

1. **documents** - Anonymous access (read-only)
   - Contains: `readme.txt` với SMB credentials:
     - `SMB Username: sysadmin`
     - `SMB Password: Sy54dm1n`
   
2. **config** - Requires authentication
   - Accessible via SMB với: `sysadmin / Sy54dm1n`
   - Contains: `config.txt` với SSH credentials:
     - `SSH Username: system`
     - `SSH Password: 657sdfh85d`

3. **backup** - Requires authentication
   - Backup files (optional)
   - Accessible via SMB với: `sysadmin / Sy54dm1n`

---

## 🎭 Scenario

**Kịch bản:** Internal Network Penetration Test
- Bạn là pentester được thuê để test bảo mật
- Đã có quyền truy cập vào internal network
- Nhiệm vụ: Enumerate services, tìm credentials, gain access

**Khác biệt với các lab khác:**
- Không có OSINT từ website (website chỉ là thông tin công ty)
- Focus vào network enumeration và SMB exploitation
- Từ documents (anonymous) lấy SMB credentials (sysadmin/Sy54dm1n)
- Dùng sysadmin/Sy54dm1n để truy cập config, lấy SSH credentials (system/657sdfh85d)
- Kịch bản internal network, không phải external attack

---

**Lab ready for training!** 🎓
