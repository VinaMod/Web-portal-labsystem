# OAuth 2.0 Account Takeover Lab

## 🎯 Mục Tiêu
Lab này mô phỏng lỗ hổng **OAuth 2.0 Account Takeover** thông qua việc thao túng tham số `redirect_uri`. Bạn cần chiếm quyền truy cập vào tài khoản Admin của **PhotoApp** để lấy Flag.

## 🏗️ Kiến Trúc
- **PhotoApp** (http://localhost:8083): Ứng dụng client, nơi chứa Flag.
- **SocialID** (http://localhost:3000): OAuth Provider.
- **Admin Bot**: Mô phỏng nạn nhân, sẽ click vào link bạn gửi.

## 🚀 Hướng Dẫn Setup

### Cách 1: Sử Dụng Script (Khuyên Dùng)
Chạy script khởi động và truyền vào IP máy của bạn (nếu muốn truy cập từ máy khác trong mạng LAN):

```bash
# Chạy với IP tự động (nhận localhost)
./scripts/start-lab.sh

# Chạy với IP cụ thể (ví dụ: IP LAN của bạn)
./scripts/start-lab.sh 192.168.1.13
```

### Cách 2: Sử Dụng Docker Compose Trực Tiếp
Nếu bạn quen dùng lệnh `docker compose up`, hãy cấu hình IP thông qua file `.env`:

1.  Mở file `.env` (nằm cùng thư mục với `docker-compose.yml`).
2.  Sửa đổi biến `LAB_HOST`.
    ```env
    LAB_HOST=192.168.1.13
    ```
    *(Mặc định là localhost)*
3.  Chạy lệnh:
    ```bash
    docker compose up -d
    ```

## 🕵️ Hướng Dẫn Khai Thác
Xem chi tiết tại file [FLOW.md](FLOW.md).

1.  Truy cập PhotoApp và thử chức năng "Login with SocialID".
2.  Quan sát URL khi được chuyển hướng sang SocialID.
3.  Tìm cách thay đổi `redirect_uri` để đánh cắp `authorization_code` của Admin.
4.  Gửi link exploit của bạn thông qua chức năng "Report Bug" trên PhotoApp.
5.  Sử dụng code lấy được để đăng nhập vào tài khoản Admin.

## 💡 Hint
- `redirect_uri` có được kiểm tra chặt chẽ không?
- Bạn có thể dựng một server đơn giản: `python3 -m http.server 9999`.
- Sau đó trỏ `redirect_uri` về IP của bạn: `http://<YOUR_IP>:9999/callback`.

## ⚠️ Lưu ý
Bot sẽ click link ngay lập tức. Hãy mở sẵn server nghe lén trước khi gửi link.
