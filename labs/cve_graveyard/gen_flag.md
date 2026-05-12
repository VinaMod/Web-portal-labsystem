# Hướng Dẫn Tạo Flag Dynamic

Bài lab này sử dụng cơ chế tạo Flag động dựa trên thời gian (GMT+7), Email người dùng và một chuỗi hậu tố (suffix) cố định. Điều này giúp mỗi ngày và mỗi người dùng sẽ có một Flag riêng biệt.

## 1. Công thức tạo Flag

Flag được tạo theo định dạng:
`FLAG{sha1(ddmmyyyy_email_suffix)}`

Trong đó:
- `ddmmyyyy`: Ngày hiện tại theo định dạng Ngày-Tháng-Năm (Múi giờ GMT+7).
- `email`: Địa chỉ email được cấu hình trong biến môi trường `EMAIL` (mặc định là `admin@example.com`).
- `suffix`: Chuỗi hậu tố cố định cho từng loại Flag.

## 2. Các tham số của bài Lab này

| Loại Flag | Suffix (Hậu tố) | Đường dẫn trong Container |
|-----------|-----------------|--------------------------|
| **RCE Flag** | `tomcat_rce_flag` | `/flag.txt` |

## 3. Lệnh tạo Flag mẫu (Bash)

Bạn có thể sử dụng các lệnh sau để tính toán Flag của ngày hôm nay:

**Bước 1: Đặt biến Email (nếu bạn thay đổi trong docker-compose)**
```bash
EMAIL="admin@example.com"
```

**Bước 2: Tạo RCE Flag**
```bash
echo -n "$(TZ=Asia/Ho_Chi_Minh date +%d%m%Y)_${EMAIL}_tomcat_rce_flag" | sha1sum | awk '{print "FLAG{"$1"}"}'
```

---
*Lưu ý: Flag được tự động cập nhật mỗi khi bạn khởi động lại bài lab bằng Docker Compose.*
