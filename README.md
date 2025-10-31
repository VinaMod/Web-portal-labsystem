# WebSocket Terminal Server

Một ứng dụng terminal web sử dụng Flask, Socket.IO và xterm.js cho phép bạn truy cập terminal từ trình duyệt web.

## 🚀 Tính năng

- **Terminal thời gian thực**: Sử dụng WebSocket để giao tiếp real-time
- **Giao diện đẹp**: Sử dụng xterm.js cho trải nghiệm terminal giống native
- **Hỗ trợ PowerShell**: Tối ưu cho Windows PowerShell
- **Responsive**: Giao diện thích ứng với nhiều kích thước màn hình
- **Phím tắt**: Hỗ trợ Ctrl+C, Ctrl+Z, Tab completion
- **Nhiều session**: Mỗi client có session terminal riêng biệt

## 📋 Yêu cầu hệ thống

- Python 3.7 trở lên
- Windows (cho phiên bản PowerShell)
- Trình duyệt web hiện đại (Chrome, Firefox, Edge, Safari)

## ⚡ Cài đặt nhanh

### 1. Kích hoạt virtual environment
```powershell
# Nếu đã có .venv
.\.venv\Scripts\Activate.ps1

# Nếu chưa có, tạo mới
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Cài đặt dependencies
```powershell
pip install -r requirements.txt
```

### 3. Chạy server
```powershell
# Phiên bản Windows (khuyến nghị cho Windows)
python app_windows.py

# Hoặc phiên bản Unix/Linux
python app.py
```

### 4. Mở trình duyệt
Truy cập: http://localhost:5000

## 📁 Cấu trúc project

```
websocket_terminal/
├── app.py                 # Server chính (Unix/Linux)
├── app_windows.py         # Server cho Windows
├── requirements.txt       # Dependencies
├── templates/
│   └── index.html        # Giao diện web
├── .venv/                # Virtual environment
└── README.md             # Tài liệu này
```

## 🛠️ Cấu hình

### Thay đổi port
Sửa trong file `app_windows.py`:
```python
socketio.run(app, host='0.0.0.0', port=5000, debug=True)
```

### Bảo mật
Đổi secret key trong file `app_windows.py`:
```python
app.config['SECRET_KEY'] = 'your-new-secret-key'
```

### CORS
Để cho phép truy cập từ domain khác:
```python
socketio = SocketIO(app, cors_allowed_origins=["http://yourdomain.com"])
```

## 🎯 Sử dụng

1. **Kết nối**: Mở trình duyệt và truy cập server
2. **Gõ lệnh**: Nhập lệnh PowerShell bình thường
3. **Phím tắt**: 
   - `Ctrl+C`: Ngắt lệnh đang chạy
   - `Ctrl+Z`: Tạm dừng process
   - `Tab`: Auto-completion
4. **Copy/Paste**: Chuột phải để copy/paste
5. **Fullscreen**: Nhấn nút maximize màu xanh

## 🔧 Troubleshooting

### Lỗi không kết nối được
- Kiểm tra firewall Windows
- Đảm bảo port 5000 không bị chiếm dụng
- Chạy PowerShell với quyền Administrator

### Terminal không hiển thị output
- Restart server
- Refresh trang web
- Kiểm tra console browser (F12)

### Lỗi import module
```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

## 🚨 Bảo mật quan trọng

⚠️ **CẢNH BÁO**: Ứng dụng này cho phép thực thi lệnh trên server. Chỉ sử dụng trong môi trường tin cậy!

### Khuyến nghị bảo mật:
- Không expose ra internet công cộng
- Sử dụng firewall để giới hạn truy cập
- Chạy với user có quyền hạn chế
- Thêm authentication nếu cần thiết

## 🔄 Phát triển thêm

### Thêm authentication
```python
from flask_login import login_required

@app.route('/')
@login_required
def index():
    return render_template('index.html')
```

### Logging
```python
import logging
logging.basicConfig(level=logging.INFO)
```

### SSL/HTTPS
```python
socketio.run(app, host='0.0.0.0', port=5000, 
            keyfile='key.pem', certfile='cert.pem')
```

## 📝 Dependencies

- **Flask**: Web framework
- **Flask-SocketIO**: WebSocket support
- **python-socketio**: Socket.IO implementation
- **eventlet**: Async networking library

## 🐛 Báo lỗi

Nếu gặp lỗi, vui lòng:
1. Kiểm tra console browser (F12)
2. Kiểm tra log server terminal
3. Đảm bảo tất cả dependencies đã cài đặt

## 📄 License

MIT License - Sử dụng tự do cho mục đích học tập và phát triển.

---

**Lưu ý**: Đây là tool dành cho development và testing. Không khuyến nghị sử dụng trong production environment mà không có các biện pháp bảo mật phù hợp.