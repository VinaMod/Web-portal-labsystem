# 🏗️ Kiến Trúc Lab Leaky Webroot

## 1. Mô hình triển khai (Deployment Model)

Dưới đây là sơ đồ kiến trúc của bài lab, mô tả cách các thành phần kết nối với nhau trong môi trường Docker.

```mermaid
graph TD
    subgraph "Máy Người Dùng (Student Machine)"
        Student["User/Student<br/>(Kali Linux / Browser)"]
    end

    subgraph "Docker Lab Environment (lab-net)"
        subgraph "Victim Side"
            WebServer["Web Server Container<br/>(leaky_webroot-web)<br/>Hostname: web"]
            
            subgraph "Web Root content"
                Public["index.php<br/>products.php<br/>robots.txt"]
                BackupDir["/backup/<br/>(backup.sql)"]
                AdminDir["/admin/<br/>(login.php, flag.txt)"]
            end
            
            WebServer --- Public
            WebServer --- BackupDir
            WebServer --- AdminDir
        end
    end

    Student -- "HTTP (Port 8081)" --> WebServer
    WebServer -- "Port Mapping" --> HostPort["Host Port: 8081"]
```

---

## 2. Luồng khai thác (Exploitation Flow)

Sơ đồ trình tự mô tả các giai đoạn tấn công từ khi thu thập thông tin đến khi lấy được Flag.

```mermaid
sequenceDiagram
    participant Attacker as Attacker (Student)
    participant Server as Web Server (Apache/PHP)

    Note over Attacker, Server: Giai đoạn 1: Thu thập thông tin (Reconnaissance)
    Attacker->>Server: Truy cập /robots.txt
    Server-->>Attacker: Trả về Disallow: /backup/

    Note over Attacker, Server: Giai đoạn 2: Liệt kê thư mục (Directory Enumeration)
    Attacker->>Server: ffuf quét thư mục trực tuyến
    Server-->>Attacker: Tìm thấy /backup và /admin

    Note over Attacker, Server: Giai đoạn 3: Tìm kiếm tệp tin (File Discovery)
    Attacker->>Server: ffuf quét tệp .sql trong /backup/
    Server-->>Attacker: Tìm thấy backup.sql

    Note over Attacker, Server: Giai đoạn 4: Trích xuất dữ liệu (Extraction)
    Attacker->>Server: Tải tệp backup.sql
    Server-->>Attacker: Nội dung SQL (Chứa MD5 Hash của admin)

    Note over Attacker, Server: Giai đoạn 5: Bẻ khóa mật khẩu (Cracking)
    Attacker->>Attacker: Sử dụng Hashcat/John để crack MD5
    Note right of Attacker: password = 'password'

    Note over Attacker, Server: Giai đoạn 6: Đăng nhập quản trị (Admin Access)
    Attacker->>Server: Truy cập /admin/login.php
    Attacker->>Server: Đăng nhập với admin:password
    Server-->>Attacker: Đăng nhập thành công!
    Attacker->>Server: Truy cập Dashboard
    Server-->>Attacker: Hiển thị USER FLAG
```

---

## 3. Thành phần hệ thống

- **Web Server**: Sử dụng PHP 8.2 trên nền Apache.
- **Port Mapping**: Port 80 của container được map ra port 8081 của Host máy người dùng.
- **Dynamic Flag**: Flag được sinh ra tự động dựa trên ngày và email cấu hình trong `docker-compose.yml`.
