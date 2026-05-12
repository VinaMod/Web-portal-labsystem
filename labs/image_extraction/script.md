# Lab 1.2 – The Careless Employee

**Topic:** Metadata & OSINT Extraction
**Difficulty:** Easy → Medium
**Category:** Web Recon / Information Leakage

---

# 1. Scenario

Công ty **BlueMoon Fashion** có một trang **About Us** giới thiệu công ty và đội ngũ nhân viên.

Trang web cho phép tải xuống một số tài liệu nội bộ như:

* Employee Handbook (PDF)
* Meeting Notes (Word)
* High resolution office images

Một nhân viên đã vô tình **không xóa metadata trước khi publish tài liệu**.

Metadata của các file này chứa:

* Tên nhân viên
* Username nội bộ
* Software version
* Comment ẩn
* Gợi ý password

Một attacker có thể tải các file này xuống và sử dụng các công cụ forensic như **exiftool** hoặc **strings** để trích xuất thông tin.

Bằng cách **ghép các mảnh thông tin lại**, attacker có thể tìm ra **username hợp lệ và gợi ý password** để đăng nhập vào cổng nội bộ.

---

# 2. Learning Objectives

Sau khi hoàn thành lab, sinh viên sẽ học được:

* Phân tích metadata trong file
* Sử dụng công cụ **exiftool**
* Sử dụng **strings** để tìm thông tin ẩn
* OSINT từ tài liệu công ty
* Ghép nhiều nguồn thông tin nhỏ thành credential

---

# 3. Lab Architecture

```id="s7j1p9"
Student (Kali)
      |
      | HTTP
      v
Docker Web Server
      |
      ├── index.html
      ├── about.html
      ├── assets/
      │     ├── employee_handbook.pdf
      │     ├── meeting_notes.docx
      │     └── office.jpg
      │
      └── portal/
            └── login.php
```

---

# 4. Website Content

Trang **About Us**:

```html id="bnv4xl"
Welcome to BlueMoon Fashion

We are proud of our team and our transparent company culture.

Download our company documents below:

Employee Handbook
Meeting Notes
Office Gallery
```

Links download:

```id="3u3kz2"
/assets/employee_handbook.pdf
/assets/meeting_notes.docx
/assets/office.jpg
```

---

# 5. Student Tasks

Sinh viên cần:

1. Download các file từ website
2. Extract metadata
3. Phân tích thông tin rò rỉ
4. Ghép thông tin để tìm username
5. Tìm gợi ý password
6. Đăng nhập vào internal portal

---

# 6. File 1 – Employee Handbook (PDF)

Metadata được seed sẵn:

```text id="j0c3vi"
Author: Nguyen Minh Anh
Creator: Microsoft Word 2019
Company: BlueMoon Fashion
Last Modified By: manh.dev
```

Sinh viên chạy:

```bash id="6n5kac"
exiftool employee_handbook.pdf
```

Thông tin quan trọng:

```text id="7v27gq"
Last Modified By: manh.dev
```

=> Gợi ý **username**

---

# 7. File 2 – Meeting Notes (Word)

Trong file Word có **comment ẩn**.

Comment:

```text id="r1ljif"
Reminder: temporary password still set to Summer2026!
Need to change it after deployment.
```

Sinh viên có thể tìm bằng:

```bash id="5kg0ow"
strings meeting_notes.docx
```

Hoặc:

```bash id="p2xyh0"
exiftool meeting_notes.docx
```

---

# 8. File 3 – Office Image

Image metadata chứa thông tin:

```text id="b63yq6"
GPS Latitude: 21.0285
GPS Longitude: 105.8542
Camera: iPhone 14
Artist: Minh Anh
Software: Photoshop 2026
```

Thông tin này không trực tiếp cho credential nhưng cho thấy:

* Ảnh chưa được **sanitized**
* Có thể leak **location / device**

---

# 9. Credential Assembly

Sinh viên phải ghép thông tin:

```text id="qrf1k5"
Username: manh.dev
Password hint: Summer2026
```

---

# 10. Internal Portal

Truy cập:

```id="xv9qde"
http://lab.local/portal/login.php
```

Credential:

```text id="f2if6k"
Username: manh.dev
Password: Summer2026
```

Sau khi login thành công:

```text id="n6n95v"
Welcome to the internal employee portal.
```

---

# 11. Expected Attack Chain

```id="1mxu5u"
Recon
 ↓
Download company documents
 ↓
Metadata extraction
 ↓
Discover username
 ↓
Discover password hint
 ↓
Credential assembly
 ↓
Portal login
```

---

# 12. Key Security Lessons

Các lỗi bảo mật phổ biến:

* Không xóa metadata trong tài liệu
* Leaking username qua metadata
* Comment nội bộ trong tài liệu public
* Image metadata chứa thông tin nhạy cảm

---

# 13. Tools Recommended

```text id="ck9ziv"
exiftool
strings
binwalk
file
```

---

# 14. Example Commands

Extract metadata:

```bash id="i79mml"
exiftool employee_handbook.pdf
```

Find hidden strings:

```bash id="b6dquq"
strings meeting_notes.docx | less
```

---

# 15. Optional Flag

Nếu muốn thêm CTF element:

```text id="xg0lbc"
FLAG{metadata_can_leak_credentials}
```

---

# 16. Lab Outcome

Sau khi hoàn thành lab này sinh viên sẽ hiểu:

* Metadata là một **nguồn thông tin OSINT rất giá trị**
* Nhiều công ty vô tình leak **username và internal info**
* Attackers có thể **ghép nhiều thông tin nhỏ** để tạo thành credential hợp lệ
* Data sanitization là bước quan trọng trước khi publish tài liệu
