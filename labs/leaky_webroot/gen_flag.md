# Hướng Dẫn Tạo Flag Dynamic

Bài lab này sử dụng cơ chế tạo Flag động tương tự như `vul_scan_nuclei`.

## 1. Công thức tạo Flag
`FLAG{sha1(ddmmyyyy_email_suffix)}`

## 2. Các tham số của bài Lab này

| Loại Flag | Suffix (Hậu tố) | Đường dẫn trong Container |
|-----------|-----------------|--------------------------|
| **User Flag** | `leaky_webroot_user` | `/var/www/html/admin/flag.txt` |

## 3. Lệnh tạo Flag mẫu (Bash)

**Bước 1: Đặt biến Email (nếu bạn thay đổi trong docker-compose hoặc lệnh chạy)**
```bash
EMAIL="admin@example.com"
```

**Bước 2: Tạo User Flag**
```bash
echo -n "$(TZ=Asia/Ho_Chi_Minh date +%d%m%Y)_${EMAIL}_leaky_webroot_user" | sha1sum | awk '{print "FLAG{"$1"}"}'
```
