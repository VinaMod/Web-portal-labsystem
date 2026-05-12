# 🏗️ Kiến Trúc Lab Image Extraction

## 1. Mô hình triển khai (Deployment Model)

```mermaid
graph TD
    subgraph "Máy Người Dùng (Student Machine)"
        Student["User/Student<br/>(Kali Linux / Browser)"]
    end

    subgraph "Docker Lab Environment (lab-net)"
        subgraph "Victim Side"
            WebServer["Web Server Container<br/>(image_extraction-web)<br/>Hostname: web"]
            
            subgraph "Web Root content"
                Public["index.php<br/>about.php"]
                AssetsDir["/assets/<br/>(handbook.pdf, notes.docx, office.jpg)"]
                PortalDir["/portal/<br/>(login.php)"]
            end
            
            WebServer --- Public
            WebServer --- AssetsDir
            WebServer --- PortalDir
        end
    end

    Student -- "HTTP (Port 8082)" --> WebServer
    WebServer -- "Port Mapping" --> HostPort["Host Port: 8082"]
```

---

## 2. Luồng khai thác (Exploitation Flow)

```mermaid
sequenceDiagram
    participant Attacker as Attacker (Student)
    participant Server as Web Server (Apache/PHP)

    Note over Attacker, Server: Giai đoạn 1: Thu thập tài liệu (Reconnaissance)
    Attacker->>Server: Truy cập /about.php
    Attacker->>Server: Tải các tệp trong /assets/

    Note over Attacker, Server: Giai đoạn 2: Phân tích Metadata (Forensics)
    Attacker->>Attacker: exiftool employee_handbook.pdf
    Note right of Attacker: Tìm thấy Username: manh.dev
    
    Attacker->>Attacker: strings meeting_notes.docx
    Note right of Attacker: Tìm thấy Password Hint: Summer2026!

    Note over Attacker, Server: Giai đoạn 3: Đăng nhập (Exfiltration)
    Attacker->>Server: Truy cập /portal/login.php
    Attacker->>Server: Đăng nhập với manh.dev:Summer2026!
    Server-->>Attacker: Đăng nhập thành công!
    Server-->>Attacker: Hiển thị USER FLAG
```

---

## 3. Thành phần hệ thống

- **Web Server**: PHP 8.2 Apache.
- **Port Mapping**: Host port 8082 -> Container port 80.
- **Dynamic Flag**: Dựa trên ngày và email cấu hình.
