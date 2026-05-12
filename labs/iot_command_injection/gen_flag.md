# Hướng Dẫn Tạo Flag Dynamic - Lab 4.2 Pro: The Mirai Target

Bài lab này sử dụng **2 Flag** tương ứng với 2 giai đoạn tấn công khác nhau. Cả hai đều tuân theo công thức tạo Flag chuẩn.

## 1. Công thức tạo Flag

```
FLAG{sha1(ddmmyyyy_email_suffix)}
```

## 2. Các tham số của bài Lab

| Giai đoạn | Loại Flag | Suffix (Hậu tố) | Vị trí trong Container | Quyền đọc |
|-----------|-----------|-----------------|-------------------------|-----------|
| **Stage 1** | User Flag | `iot_command_injection_user` | `/home/user_flag.txt` | `iot_user` (low-priv) |
| **Stage 2** | Root Flag | `iot_command_injection_root` | `/root/root_flag.txt` | `root` only |

## 3. Lệnh tạo Flag mẫu (Bash)

**Bước 1: Đặt biến Email**
```bash
EMAIL="admin@example.com"
```

**Bước 2: Tạo User Flag (Stage 1 - Command Injection)**
```bash
echo -n "$(TZ=Asia/Ho_Chi_Minh date +%d%m%Y)_${EMAIL}_iot_command_injection_user" | sha1sum | awk '{print "FLAG{"$1"}"}'
```

**Bước 3: Tạo Root Flag (Stage 2 - Privilege Escalation)**
```bash
echo -n "$(TZ=Asia/Ho_Chi_Minh date +%d%m%Y)_${EMAIL}_iot_command_injection_root" | sha1sum | awk '{print "FLAG{"$1"}"}'
```

**Ví dụ kết quả vào ngày 11/04/2026:**
```
User Flag: FLAG{...}  (đọc được sau Command Injection thành công)
Root Flag: FLAG{...}  (đọc được sau leo thang đặc quyền thành công)
```

## 4. Cấu hình trong Dockerfile (Mặc định)

```dockerfile
# Stage 1 - User Flag (đọc được bởi iot_user)
RUN echo "FLAG{$(echo -n '11042026_admin@example.com_iot_command_injection_user' | sha1sum | awk '{print $1}')}" > /home/user_flag.txt
RUN chmod 644 /home/user_flag.txt

# Stage 2 - Root Flag (chỉ đọc được khi có quyền root)
RUN echo "FLAG{$(echo -n '11042026_admin@example.com_iot_command_injection_root' | sha1sum | awk '{print $1}')}" > /root/root_flag.txt
RUN chmod 600 /root/root_flag.txt
```

## 5. Lưu ý cho Giảng viên

- **User Flag** sẽ bị lộ ngay khi sinh viên bypass được Security Filter.
- **Root Flag** được bảo vệ ở mức OS — chỉ tiết lộ sau khi sinh viên thực hiện thành công kỹ thuật **PATH Hijacking SUID**.
- Để cập nhật Flag cho kỳ thi mới, thay ngày (`11042026`) và Email trong `Dockerfile` rồi rebuild container.
