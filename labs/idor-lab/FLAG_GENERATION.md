# 🔐 FLAG Generation System

## Công thức

FLAG được tạo động dựa trên:
```
FLAG{SHA1(DDMMYYYY_email_IDOR)}
```

- **DDMMYYYY**: Ngày hiện tại theo GMT+7 (Giờ HCM)
- **email**: Email được truyền vào qua biến môi trường
- **IDOR**: Hằng số suffix

## Ví dụ

### Ngày 24/11/2025

**Email: `long@mail.com`**
```
Input:  24112025_long@mail.com_IDOR
SHA1:   b22f5db2bcba00ea4cea3010136b5faa766944e2
FLAG:   FLAG{b22f5db2bcba00ea4cea3010136b5faa766944e2}
```

**Email: `admin@example.com`**
```
Input:  24112025_admin@example.com_IDOR
SHA1:   afc7a522f3afd06e4ea05a3756c7b70e96b51667
FLAG:   FLAG{afc7a522f3afd06e4ea05a3756c7b70e96b51667}
```

## Cách sử dụng

### Tạo FLAG với EMAIL tùy chỉnh

```bash
ENV=student_id EMAIL=myname@domain.com docker-compose up -d
```

### Tạo FLAG với EMAIL mặc định

```bash
ENV=student_id docker-compose up -d
# Sẽ dùng: default@example.com
```

## Lưu ý

- Mỗi EMAIL khác nhau sẽ tạo ra FLAG khác nhau
- Mỗi ngày khác nhau sẽ tạo ra FLAG khác nhau
- FLAG được lưu trong database và hiển thị ở phần "comments" của điểm số
- Khi `ENV=student_id`, FLAG luôn nằm ở một student ID trong khoảng **1-40** (40 sinh viên đầu tiên của lớp bất kỳ)
- Khi `ENV=class_id`, FLAG luôn nằm ở một class ID random trong khoảng **100-500** (tổng cộng 50 lớp được sinh mỗi lần)

## Kiểm tra FLAG hiện tại

```bash
# Xem FLAG info
curl http://localhost:8080/FLAG_INFO.json

# Hoặc xem logs
docker-compose logs db | grep FLAG
```

## Demo Script

Chạy script demo để xem các ví dụ:
```bash
./demo_flags.sh
```
