# Hướng Dẫn Tạo Flag Dynamic

Bài lab này sử dụng cơ chế tạo Flag động.

## 1. Công thức tạo Flag
`FLAG{sha1(ddmmyyyy_email_suffix)}`

## 2. Các tham số của bài Lab này

| Loại Flag | Suffix (Hậu tố) | Đường dẫn trong Container |
|-----------|-----------------|--------------------------|
| **User Flag** | `image_extraction_user` | Hiển thị sau login tại `/portal/login.php` |

## 3. Lệnh tạo Flag mẫu (Bash)

**Bước 1: Đặt biến Email**
```bash
EMAIL="admin@example.com"
```

**Bước 2: Tạo User Flag**
```bash
echo -n "$(TZ=Asia/Ho_Chi_Minh date +%d%m%Y)_${EMAIL}_image_extraction_user" | sha1sum | awk '{print "FLAG{"$1"}"}'
```
