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

| Loại Flag | Suffix (Hậu tố) | Nơi lưu trữ / Cung cấp |
|-----------|-----------------|------------------------|
| **Door PIN Flag** | `mqtt_leak_flag` | Bị rò rỉ liên tục qua MQTT topic `home/security/door_pin` |

## 3. Lệnh tạo Flag mẫu (Bash)

Bạn có thể sử dụng lệnh sau để tính toán Flag của ngày hôm nay nhằm đối chiếu lại kết quả khai thác được:

**Bước 1: Đặt biến Email (nếu bạn thay đổi trong docker-compose)**
```bash
EMAIL="admin@example.com"
```

**Bước 2: Tạo Flag mô phỏng**
```bash
echo -n "$(TZ=Asia/Ho_Chi_Minh date +%d%m%Y)_${EMAIL}_mqtt_leak_flag" | sha1sum | awk '{print "FLAG{"$1"}"}'
```
