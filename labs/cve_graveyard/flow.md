**<span style="color:red">Lab: Tomcat RCE (CVE-2017-12615)</span>**

Bài lab này tập trung vào một quy trình khai thác hoàn chỉnh (Exploit Kill-chain) đối với máy chủ ứng dụng Apache Tomcat. Mục tiêu là lợi dụng cấu hình sai ngớ ngẩn từ quản trị viên (`readonly=false`), vượt qua cơ chế từ chối file JSP của hệ thống để tải lên một Web Shell độc hại, từ đó giành quyền thực thi mã từ xa (RCE) và chiếm hoàn toàn quyền điều khiển máy chủ.

**Bài lab đáp ứng các CLO nào**

**CLO 6**: Nhận diện, phân loại và khai thác các lỗ hổng rò rỉ thông tin (Information Disclosure) và cấu hình sai hệ thống (Security Misconfiguration) trên web. Cụ thể ở đây là khai thác lỗ hổng cấu hình sai quyền ghi HTTP (`PUT` method).

**CLO 3**: Vận dụng thành thạo các công cụ phân tích và tương tác mạng (ví dụ: `nmap`, `curl`, `Burp Suite`) để dò tìm tín hiệu cổng, kiểm tra phương thức HTTP và trực tiếp gửi payload độc ác tới mục tiêu.

**CLO 6**: Có kỹ năng phân tích hành vi của hệ thống bảo vệ (WAF/Filter), phát triển phương pháp lách luật (Bypass bằng ký tự `/` hoặc `%20`) và tư duy triển khai mã độc (Web Shell) để chiếm cờ cuối cùng (Post-Exploitation).

**Kỹ thuật dự kiến làm bài Lab Tomcat RCE.**

1. Khai thác Reconnaissance & Method Enumeration: Sử dụng `nmap` để phát hiện phiên bản Tomcat. Dùng `cURL` hoặc `Burp Suite` đẩy thử các HTTP request method `PUT` để kiểm tra khả năng Ghi file trực tiếp lên Webroot của máy chủ.

2. Kỹ thuật Filter Bypass & Web Shell Uploading: Lách qua cơ chế phòng thủ từ chối tệp tin đuôi `.jsp` của Tomcat bằng kỹ thuật nối chuỗi (nối thêm một dấu `/` ngay sau `shell.jsp/` trong HTTP Request). Mã độc tải lên thành công dưới dạng một backdoor cực nhỏ xử lý parameter OS Command.

3. Kỹ thuật Remote Code Execution: Tương tác qua giao thức HTTP GET/POST tới Web Shell vừa tải lên. Gọi và thực thi các câu lệnh Linux trực tiếp trên máy chủ bằng quyền của Tomcat service để đọc nội dung file Flag bí mật (`/flag.txt`) ẩn trong hệ thống.
