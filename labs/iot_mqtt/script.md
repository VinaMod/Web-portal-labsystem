# Kịch bản Khai thác (Exploitation Script) - Lab 4.1: The Chatty Smart Home

Bài lab giả lập lỗi cấu hình sai (misconfiguration) thiếu xác thực trên MQTT Broker của một hệ thống Smart Home, kết hợp với lỗ hổng tiết lộ thông tin nhạy cảm.

## 1. Mục tiêu: Dịch vụ MQTT Mosquitto (Port 1883) & Web Server (Port 8092)

### Lỗ hổng: Unauthenticated MQTT Access / Information Disclosure
*(Lưu ý: Lỗ hổng xảy ra do cấu hình `allow_anonymous true` trong `mosquitto.conf`)*
* **Nguyên nhân:** MQTT Broker cho phép truy cập nặc danh. Nếu các thiết bị IoT trao đổi dữ liệu nhạy cảm (như mật mã, PIN thẻ) qua kênh chat không mã hóa, hacker có thể nghe trộm. Tệ hơn, họ có thể sử dụng các thông tin rò rỉ này ở các giao thức khác (như Web Dashboard) để leo thang đặc quyền.
* **Phương pháp khai thác:**
  1. Sử dụng lệnh `mosquitto_sub` theo dõi tất cả topic bằng wildcard `#`:
     ```bash
     mosquitto_sub -h 127.0.0.1 -t "#" -v
     ```
  2. Bắt được cấu trúc JSON bị rò rỉ mã `auth_pin` dạng UUID (ví dụ: `a3f7c820-1d2e-4b56-9f0a-8c3e7d1f2a4b`) trong topic `home/security/door_pin`.
  3. Truy cập vào giao diện Web Dashboard tại `http://127.0.0.1:8092/`.
  4. Nhập mã PIN vừa lấy được để mở khóa thiết bị, giao diện sẽ trả về bản rõ của `FLAG`.
