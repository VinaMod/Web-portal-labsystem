# 🏗️ Kiến Trúc Lab CVE Graveyard (Tomcat RCE)

## 1. Mô hình triển khai (Deployment Model)

Dưới đây là sơ đồ kiến trúc của bài lab, mô tả cách các thành phần kết nối với nhau trong môi trường Docker.

```mermaid
graph TD
    subgraph "Máy Người Dùng (Student Machine)"
        Student["User/Student<br/>(Kali Linux / Browser)"]
    end

    subgraph "Docker Lab Environment (cve_graveyard)"
        subgraph "Victim Side"
            TomcatServer["Tomcat Server Container<br/>(cve_tomcat_rce)<br/>Apache Tomcat 7.0.70"]
            
            subgraph "File System"
                WebRoot["Web Application Root<br/>(/usr/local/tomcat/webapps/ROOT/)<br/>Nơi lưu trữ webshell"]
                FlagFile["/flag.txt<br/>(Chứa RCE Flag)"]
            end
            
            TomcatServer --- WebRoot
            TomcatServer --- FlagFile
        end
    end

    Student -- "HTTP (Port 8080)" --> TomcatServer
    TomcatServer -- "Port Mapping" --> HostPort["Host Port: 8080"]
```

---

## 2. Luồng khai thác (Exploitation Flow)

Sơ đồ trình tự mô tả các giai đoạn tấn công từ khi thu thập thông tin đến khi tải lên được Webshell và đọc cờ ẩn.

```mermaid
sequenceDiagram
    participant Attacker as Attacker (Student)
    participant Server as Tomcat Server (Port 8080)

    Note over Attacker, Server: Giai đoạn 1: Thu thập thông tin & Dịch vụ (Reconnaissance)
    Attacker->>Server: Nmap quét cổng 8080
    Server-->>Attacker: Trả về dịch vụ Apache Tomcat 7.0.70

    Note over Attacker, Server: Giai đoạn 2: Kiểm tra phương thức HTTP (Method Enumeration)
    Attacker->>Server: Gửi request HTTP PUT với file test.txt
    Server-->>Attacker: HTTP 201 Created (Cho phép PUT do readonly=false)

    Note over Attacker, Server: Giai đoạn 3: Tải lên Web Shell (Bypass upload filter)
    Attacker->>Server: Gửi PUT /shell.jsp/ (Kèm mã độc JSP)
    Note right of Attacker: Sử dụng ký tự "/" hoặc "%20" ở cuối để bypass việc Tomcat chặn đuôi .jsp
    Server-->>Attacker: HTTP 201 Created (Lưu thành công shell.jsp)

    Note over Attacker, Server: Giai đoạn 4: Thực thi mã từ xa (RCE)
    Attacker->>Server: GET /shell.jsp?cmd=whoami
    Server-->>Attacker: Trả về 'root'

    Note over Attacker, Server: Giai đoạn 5: Đọc Flag hệ thống
    Attacker->>Server: GET /shell.jsp?cmd=cat+/flag.txt
    Server-->>Attacker: Trả về nội dung FLAG{...}
```

---

## 3. Thành phần hệ thống

- **Web Server**: Sử dụng Apache Tomcat phiên bản 7.0.70 (có tồn tại lỗ hổng CVE-2017-12615).
- **Cấu hình lỗi**: Tham số `readonly` trong `conf/web.xml` bị quản trị viên đặt sai thành `false`, dẫn đến cho phép ghi đè/tạo tệp tùy ý qua phương thức HTTP PUT.
- **Port Mapping**: Port 8080 của container được map ra port 8080 của Host máy người dùng.
- **Dynamic Flag**: Flag nằm ở `/flag.txt` và được sinh ra tự động dựa trên ngày hiện tại và email cấu hình trong `docker-compose.yml`.
