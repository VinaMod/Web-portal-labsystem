# Hướng dẫn Khai thác Race Condition bằng Burp Suite

Tài liệu này hướng dẫn chi tiết cách sử dụng **Burp Suite** để khai thác lỗ hổng Race Condition trong bài lab `race_condition2`.

Mục tiêu: Gửi nhiều requests đồng thời đến endpoint `apply_coupon.php` để giảm giá về 0.

## Cách 1: Sử dụng Repeater (Send Group / Parallel) - Dễ nhất

Phiên bản Burp Suite 2023 trở lên hỗ trợ gửi request song song ngay trong Repeater.

### Bước 1: Bắt Request
1.  Bật Burp Proxy và chặn request khi bạn bấm nút **[ Apply Code: CTF50 ]** trên trình duyệt.
2.  Gửi request đó sang **Repeater** (Ctrl + R).

### Bước 2: Chuẩn bị Group
1.  Trong Repeater, chuột phải vào tab request vừa gửi, chọn **Duplicate Tab** khoảng 10-20 lần (tạo ra 10-20 tab giống hệt nhau).
2.  Bấm vào dấu `+` ở thanh tab, chọn **Create tab group**.
3.  Chọn tất cả các tab bạn vừa duplicate, đặt tên group (ví dụ: `RaceAttack`), chọn màu đỏ cho ngầu -> **Create**.

### Bước 3: Cấu hình Gửi Song Song
1.  Nhìn lên thanh điều khiển của Group (ngay dưới tên Group), phần **Send mode**.
2.  Đổi từ **Send sequentially (single connection)** sang **Send group in parallel (burst)**.

### Bước 4: Tấn công
1.  Vào Dashboard web, bấm **RESET ORDER** để giá về 100.
2.  Quay lại Burp Repeater, bấm nút **Send group (parallel)** màu cam to đùng.
3.  Chờ tất cả các tab chạy xong.
4.  Quay lại web, refresh trang Dashboard (F5).
5.  Kiểm tra: Nếu giá về 0 và Flag hiện ra -> **Thành công**.

---

## Cách 2: Sử dụng Turbo Intruder (Nâng cao & Mạnh mẽ)

Turbo Intruder là một extension cực mạnh cho Race Condition.

### Bước 1: Cài đặt
1.  Vào tab **Extensions** -> **BApp Store**.
2.  Tìm **Turbo Intruder** và cài đặt.

### Bước 2: Gửi sang Turbo Intruder
1.  Bắt request `POST /apply_coupon.php` (hoặc GET tùy code).
2.  Chuột phải vào request -> **Extensions** -> **Turbo Intruder** -> **Send to Turbo Intruder**.

### Bước 3: Cấu hình Script Python
Trong cửa sổ Turbo Intruder hiện ra, copy đoạn code sau vào khung Python bên dưới:

```python
def queueRequests(target, wordlists):
    engine = RequestEngine(endpoint=target.endpoint,
                           concurrentConnections=30, # Số kết nối đồng thời
                           requestsPerConnection=100,
                           pipeline=False
                           )
    
    # Gửi 20 request cùng lúc vào hàng đợi
    for i in range(20):
        engine.queue(target.req, gate='race1') # gate='race1' dùng để đồng bộ hóa
    
    # Mở cổng để 20 request lao đi cùng lúc
    engine.openGate('race1')

    engine.complete(timeout=60)

def handleResponse(req, interesting):
    # Chỉ hiện các response có status khác 400 hoặc độ dài lạ (nếu cần)
    table.add(req)
```

### Bước 4: Tấn công
1.  Bấm nút **Attack** (dưới cùng).
2.  Quan sát bảng kết quả. Nếu thấy nhiều dòng trả về `200 OK` hoặc text "Coupon applied successfully" thì khả năng cao là ăn.
3.  Quay lại web và tận hưởng Flag.

## Tại sao lại làm được?

Trong code server (`apply_coupon.php`):
1.  Server đọc dữ liệu đơn hàng (`SELECT`).
2.  Server ngủ 1 giây (`sleep(1)`).
3.  Server cập nhật dữ liệu (`UPDATE`).

Bằng cách gửi song song, chúng ta ép nhiều luồng chạy lệnh `SELECT` **cùng lúc** khi chưa có luồng nào kịp chạy xong lệnh `UPDATE`. Tất cả đều thấy "Coupon chưa dùng" và đều cho phép trừ tiền.
