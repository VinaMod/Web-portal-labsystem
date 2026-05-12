# 🎓 IDOR Lab - Student Grade System

Hệ thống thực hành lỗ hổng IDOR (Insecure Direct Object Reference) với ứng dụng quản lý điểm sinh viên.

## 📋 Tổng quan

Lab mô phỏng hệ thống tra cứu điểm với lỗ hổng IDOR có thể cấu hình. Sinh viên có thể khai thác để xem điểm của người khác hoặc truy cập lớp học không được phép.

**Đặc điểm nổi bật:**
- ✅ Auto-generate random data mỗi lần chạy
- ✅ FLAG động dựa trên SHA1(date_email_IDOR)
- ✅ 2.000 sinh viên, 50 lớp học (40 bạn/lớp), 12 môn học
- ✅ Giao diện web hiện đại
- ✅ Docker compose - Chạy ngay

## 🚀 Quick Start

```bash
cd idor-lab
ENV=student_id EMAIL=ntlong@email.com docker-compose up -d
```

Truy cập: **http://localhost:8080**

Login: `alice` / `alice123`

FLAG location: http://localhost:8080/FLAG_INFO.json

## 📂 Cấu trúc

```
idor-lab/
├── docker-compose.yml          # Docker orchestration
├── Dockerfile                  # PHP web server
├── Dockerfile.db               # MySQL with auto-gen
├── docker-entrypoint-db.sh     # Auto-generate data
├── docker-entrypoint-web.sh    # Web server setup
├── generate_sql.py             # Data generator
├── demo_flags.sh               # FLAG demo script
├── README.md                   # This file
├── FLAG_GENERATION.md          # FLAG system docs
└── src/                        # PHP application
    ├── index.php              # Login
    ├── grades.php             # Grade view (IDOR)
    ├── logout.php             # Logout
    └── db.php                 # Database config
```

## 🎯 Xem chi tiết

- [README.md](README.md) - Hướng dẫn chi tiết
- [FLAG_GENERATION.md](FLAG_GENERATION.md) - Hệ thống FLAG

## 🔧 Commands

**Start lab:**
```bash
ENV=student_id EMAIL=me@mail.com docker-compose up -d
```

**Stop lab:**
```bash
docker-compose down -v
```

**View FLAG:**
```bash
curl http://localhost:8080/FLAG_INFO.json
```

## 📝 License

MIT - Dự án học tập mã nguồn mở
