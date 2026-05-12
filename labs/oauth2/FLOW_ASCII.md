# 🔄 OAuth 2.0 Attack Flow (Simplified)

Mô hình trực quan quá trình chiếm quyền.

```text
    [Admin Bot]                 [SocialID Provider]              [Attacker Server]
         |                              |                                |
         | 1. Bấm vào Link Độc (Do Attacker gửi)                         |
         | (Link có redirect_uri=Attacker)                               |
         |                              |                                |
         |----------------------------->|                                |
         |                              |                                |
         |                              | 2. Kiểm tra redirect_uri?      |
         |                              |    [BỎ QUA / KHÔNG CHECK]      |
         |                              |                                |
         |                              | 3. Sinh Code đăng nhập         |
         |                              |                                |
         |                              | 4. Redirect về Attacker!       |
         |                              |    (Kèm theo Code)             |
         |                              |                                |
         |<-----------------------------|                                |
         |                              |                                |
         | 5. GET /callback?code=SECRET |                                |
         |-------------------------------------------------------------->|
                                                                         |
                                                                    [HIỆN LOG LÊN MÀN HÌNH]
                                                                    "Received: code=SECRET"
                                                                         |
    [Attacker] ----------------------------------------------------------+
         |
         | 6. Copy Code -> Tự đăng nhập
         v
    [PhotoApp Client] --> "Welcome Admin!"
```
