# 🔍 Phân Tích Lỗ Hổng (Source Code Analysis)

Tại sao lại có thể chiếm quyền dễ dàng như vậy? Hãy nhìn vào code của Provider.

## File: `provider/src/index.js` (Endpoint `/auth`)

### ❌ Code Có Lỗi (Vulnerable Code)

```javascript
app.get('/auth', (req, res) => {
    const { client_id, redirect_uri } = req.query;

    // LỖI Ở ĐÂY:
    // Nhà phát triển hoàn toàn tin tưởng tham số 'redirect_uri'
    // Không hề có bước so sánh với whitelist trong Database.
    
    const authCode = generateAuthCode();

    // Chuyển hướng người dùng về bất cứ đâu họ yêu cầu
    return res.redirect(`${redirect_uri}?code=${authCode}`);
});
```

### ✅ Code An Toàn (Secure Code)

Để sửa lỗi này, chúng ta bắt buộc phải có whitelist.

```javascript
/* Database các Client hợp lệ */
const VALID_CLIENTS = {
    'photoapp': {
        // CHỈ cho phép redirect về đúng địa chỉ này
        allowed_redirect_uris: ['http://photoapp.local/callback']
    }
};

app.get('/auth', (req, res) => {
    const { client_id, redirect_uri } = req.query;
    
    // 1. Lấy thông tin Client
    const client = VALID_CLIENTS[client_id];

    // 2. So sánh CHÍNH XÁC (Strict Matching)
    if (!client.allowed_redirect_uris.includes(redirect_uri)) {
        return res.status(400).send("Lỗi: Redirect URI không hợp lệ!");
    }

    // Nếu khớp thì mới tiếp tục...
});
```

## Bài Học (Key Takeaway)
Trong OAuth 2.0, tham số `redirect_uri` giống như địa chỉ giao hàng. Nếu bưu điện (Provider) không kiểm tra xem địa chỉ đó có phải là nhà chủ xe (Client) hay không, kẻ gian có thể yêu cầu bưu điện giao chìa khóa xe về nhà hắn.
