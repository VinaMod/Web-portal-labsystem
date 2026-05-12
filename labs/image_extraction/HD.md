# Hướng Dẫn Khai Thác Lab: The Careless Employee
ExifTool là một công cụ mã nguồn mở cực kỳ mạnh mẽ, chạy trên dòng lệnh (command-line), được thiết kế để đọc, ghi và chỉnh sửa metadata (siêu dữ liệu) của nhiều loại tệp khác nhau (hình ảnh, tài liệu PDF, video, v.v.). Metadata là những dữ liệu ẩn bên trong tệp, cung cấp thông tin mô tả về tệp đó (ví dụ: người tạo, thời gian tạo, phần mềm sử dụng, tọa độ GPS,...).

Strings là một tiện ích dòng lệnh có sẵn trên hầu hết các nền tảng hệ điều hành nhân Linux/Unix. Chức năng của nó rất đơn giản: quét qua toàn bộ một tệp (thường là tệp nhị phân hoặc tệp đã nén) và in ra màn hình tất cả các chuỗi ký tự có thể đọc được (printable characters) có độ dài nhất định sắp xếp liền nhau.



## 1. Mục tiêu
Mục tiêu của bài lab này là trích xuất các thông tin nhạy cảm (metadata và ẩn trong tệp) từ các tài liệu được công khai trên website. Sau đó, ghép các thông tin này lại để tìm ra thông tin đăng nhập và truy cập vào Employee Portal.

---

## 2. Chuẩn bị môi trường (Setup)

Khởi động môi trường lab bằng Docker Compose.

```bash
docker compose up -d --build
```

Sau khi khởi động, website sẽ chạy tại địa chỉ: `http://[VICTIM HOST]:8082`

---

## 3. Các bước thực hiện

### Bước 1: Thu thập tài liệu (Asset Harvesting)
Truy cập trang **About Us** (`/about.php`) và tải xuống tất cả các tài liệu được cung cấp:
- `employee_handbook.pdf`
- `meeting_notes.docx`
- `office.jpg`

### Bước 2: Trích xuất Metadata từ PDF
Sử dụng công cụ `exiftool` để kiểm tra thông tin của tệp PDF:
```bash
exiftool employee_handbook.pdf
```
Chú ý trường **Author** hoặc các thông tin về người chỉnh sửa cuối cùng. Bạn sẽ thấy gợi ý về **username**: `manh.dev` (hoặc tên nhân viên để suy luận).

### Bước 3: Tìm kiếm thông tin ẩn trong DOCX
Tệp DOCX thực chất là một kho lưu trữ ZIP chứa các tệp XML. Bạn có thể sử dụng `strings` để tìm kiếm các chuỗi văn bản nhạy cảm hoặc giải nén tệp để kiểm tra các comment.
```bash
strings meeting_notes.docx
```
Tìm kiếm các dòng có chứa "password" hoặc "Summer". Bạn sẽ thấy một ghi chú: `Reminder: temporary password still set to Summer2026!`.

### Bước 4: Kiểm tra Metadata của Image
Mặc dù không chứa credential trực tiếp, việc kiểm tra metadata của tệp ảnh giúp bạn hiểu về các thiết bị và phần mềm được sử dụng trong công ty:
```bash
exiftool office.jpg
```

### Bước 5: Ghép thông tin và Đăng nhập (Credential Assembly)
Từ các bước trên, bạn có được:
- **Username:** `manh.dev`
- **Password:** `Summer2026!`

Truy cập **Employee Portal** tại `http://[VICTIM HOST]:8082/portal/login.php` và đăng nhập.

### Bước 6: Lấy User Flag
Sau khi đăng nhập thành công, Flag sẽ hiển thị trên màn hình portal.

---

## 4. Xác minh Flag Dynamic
Bài lab này sử dụng **flag động**, thay đổi theo ngày và email.

**User Flag:**
```bash
echo -n "$(TZ=Asia/Ho_Chi_Minh date +%d%m%Y)_admin@example.com_image_extraction_user" | sha1sum
```
