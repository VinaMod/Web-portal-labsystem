# 🚩 Công thức tạo Flag

Lab sử dụng 2 flags động được tạo dựa trên ngày hiện tại (theo giờ Việt Nam) và email người dùng.

## 🕒 Biến số chung

- **Timezone**: `Asia/Ho_Chi_Minh`
- **Date Format**: `ddmmyyyy` (Ví dụ: 21112025)
- **Default Email**: `admin@sqlilab.local` (có thể thay đổi qua biến môi trường `USER_EMAIL`)

---

## 🏳️ FLAG 1 (SQL Injection Challenge)

Flag này nằm trong database `sqli_01_lab`, bảng `flags`.

### Công thức:
```bash
INPUT = "{DATE}_{EMAIL}_5qL1_1nJ3ct10n_M45t3r"
HASH  = SHA1(INPUT)
FLAG  = "FLAG1{HASH}"
```

### Ví dụ:
- **Date**: `21112025`
- **Email**: `admin@sqlilab.local`
- **Input**: `21112025_admin@sqlilab.local_5qL1_1nJ3ct10n_M45t3r`
- **Hash**: `4c52ea2f08b78e72dc7f444db22deb5e6c42ea8f`
- **Result**: `FLAG1{4c52ea2f08b78e72dc7f444db22deb5e6c42ea8f}`

---

## 🏴 FLAG 2 (RCE Challenge)

Flag này nằm trong file `/tmp/flag.txt`.

### Công thức:
```bash
INPUT = "{DATE}_{EMAIL}_5qL1nJ3ct10n"
HASH  = SHA1(INPUT)
FLAG  = "FLAG2{HASH}"
```

### Ví dụ:
- **Date**: `21112025`
- **Email**: `admin@sqlilab.local`
- **Input**: `21112025_admin@sqlilab.local_5qL1nJ3ct10n`
- **Hash**: `ad4beb414dcc1b52ccfc11c63e654879cc532084`
- **Result**: `FLAG2{ad4beb414dcc1b52ccfc11c63e654879cc532084}`
