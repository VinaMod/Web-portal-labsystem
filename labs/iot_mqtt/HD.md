# Hướng Dẫn Khai Thác Lab 4.1: The Chatty Smart Home (MQTT Protocol Abuse)

Giao thức MQTT là một giao thức nhắn tin cực kỳ phổ biến trong các thiết bị Internet of Things (IoT). Nó hoạt động dựa trên mô hình Publish/Subscribe (Xuất bản/Đăng ký) thông qua một máy chủ trung tâm gọi là MQTT Broker.

Tuy nhiên, rất nhiều hệ thống IoT được triển khai mặc định không có xác thực (Authentication) hoặc không mã hóa dữ liệu. Nếu kẻ tấn công có thể tiếp cận được MQTT Broker mạng nội bộ hoặc trên public internet, họ có thể theo dõi mọi giao tiếp của các thiết bị thông minh trong nhà, thậm chí gửi lệnh điều khiển giả mạo.

---

## 1. Mục tiêu
Bài lab này mô phỏng một hệ thống Smart Home giả lập đăng tải các sự kiện của nhà thông minh lên MQTT Broker (Eclipse Mosquitto). Máy chủ Mosquitto này hiện đang bị cấu hình sai, cho phép bất kỳ ai cũng có thể kết nối mà không cần tài khoản (`allow_anonymous true`). 
Mục tiêu của bạn là:
1. Kết nối vào MQTT Broker ẩn danh.
2. Lắng nghe (Subscribe) toàn bộ các luồng tin nhắn đang được gửi trong nhà.
3. Bắt được mã PIN mở khóa thiết bị bị rò rỉ.
4. Đăng nhập vào Smart Home Web Dashboard bằng mã PIN đó để chiếm Flag.

---

## 2. Chuẩn bị môi trường (Setup)

Khởi động môi trường lab bằng Docker Compose. 

```bash
docker compose up -d --build
```
*(Bạn cũng có thể truyền biến `EMAIL=yourname@example.com` như các bài lab trước để nhận Flag cá nhân hóa).*

Sau khi chạy, hệ thống sẽ mở 2 cổng:
- Cổng **1883**: Dịch vụ MQTT Broker.
- Cổng **8092**: Giao diện Web Smart Home Dashboard.

---

## 3. Các bước thực hiện

### Bước 1: Dò quét và Nhận dạng cổng MQTT
Bạn có thể sử dụng `nmap` để quét cổng và xác nhận các dịch vụ:
```bash
nmap -p 80,1883 -sV 127.0.0.1
```

### Bước 2: Cài đặt công cụ MQTT Client
Bạn cần cài đặt các công cụ dòng lệnh của Mosquitto để tương tác.
- **Trên Linux (Ubuntu/Debian):** `sudo apt install mosquitto-clients`
- Hoặc bạn có thể dùng các công cụ có giao diện đồ họa (GUI) như **MQTT Explorer**.

### Bước 3: Lắng nghe toàn bộ lưu lượng (Eavesdropping)
Trong MQTT, các tin nhắn được gửi theo từng "chủ đề" (Topic), ví dụ `home/livingroom/temp`.
Để lắng nghe tất cả các chủ đề, MQTT hỗ trợ ký tự đại diện (wildcard) là dấu thăng `#`.

Chạy lệnh sau để kết nối không cần mật khẩu và lắng nghe mọi thứ:
```bash
mosquitto_sub -h 127.0.0.1 -p 1883 -t "#" -v
```
*(Trong đó: `-h`: host, `-p`: port, `-t`: topic, `-v`: verbose để in ra tên topic)*

Bạn sẽ thấy màn hình liên tục in ra các bản tin như nhiệt độ phòng khách, trạng thái thiết bị:
```text
home/livingroom/temp 23.4°C
home/frontdoor/status LOCKED
```

### Bước 4: Chộp lấy mã PIN thao tác bị rò rỉ
Nếu bạn quan sát kỹ luồng log, cứ khoảng một thời gian ngắn, thiết bị điều khiển sẽ vô tình gửi bản tin chứa mã xác thực (PIN) lên topic `home/security/door_pin`.
Ví dụ:
```text
home/security/door_pin {"device": "smart_bulb_controller", "auth_pin": "a3f7c820-1d2e-4b56-9f0a-8c3e7d1f2a4b", "status": "ready"}
```
Bạn hãy sao chép **toàn bộ chuỗi UUID** (định dạng `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`) này.

### Bước 5: Truy cập Bảng điều khiển (Smart Home Dashboard)
Hệ thống này có một giao diện quản lý chạy trên nền tảng Web.
Hãy mở trình duyệt và truy cập vào địa chỉ: `http://127.0.0.1:8092/` (hoặc IP của victim kèm port 8092).

Tại đây, bạn sẽ thấy giao diện điều khiển đèn/cửa thông minh với phong cách hiện đại. Hãy dán **chuỗi UUID** mà bạn vừa bắt được vào ô nhập liệu và nhấn *Unlock Device*.

Nếu mã chính xác, hệ thống sẽ khởi động thiết bị và nhả ra cho bạn **FLAG** của bài lab! Chúc mừng!
