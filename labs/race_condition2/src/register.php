<?php
require_once 'db.php';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $username = $_POST['username'];
    $password = $_POST['password'];

    // Check if user exists
    $stmt = $pdo->prepare("SELECT id FROM users WHERE username = ?");
    $stmt->execute([$username]);
    
    if ($stmt->fetch()) {
        $error = "Tên đăng nhập đã tồn tại!";
    } else {
        // Create User
        $hash = password_hash($password, PASSWORD_DEFAULT);
        $stmt = $pdo->prepare("INSERT INTO users (username, password) VALUES (?, ?)");
        $stmt->execute([$username, $hash]);
        $user_id = $pdo->lastInsertId();

        // Create Initial Order for this user
        $stmt = $pdo->prepare("INSERT INTO orders (user_id, total_price, coupon_applied) VALUES (?, 500000, 0)");
        $stmt->execute([$user_id]);

        header("Location: login.php");
        exit;
    }
}
?>
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Đăng Ký - Fashion Store</title>
    <link rel="stylesheet" href="style.css?v=6">
</head>
<body>
    <div class="auth-wrapper">
        <div class="auth-card">
            <h2 class="auth-title">Đăng Ký</h2>
            <?php if (isset($error)): ?>
                <div style="color: red; margin-bottom: 1rem; font-size: 0.9rem;"><?php echo $error; ?></div>
            <?php endif; ?>
            
            <form method="POST">
                <input type="text" name="username" required placeholder="Chọn tên đăng nhập">
                <input type="password" name="password" required placeholder="Chọn mật khẩu">
                <button type="submit" class="auth-btn">TẠO TÀI KHOẢN</button>
            </form>
            
            <div class="auth-links">
                Đã có tài khoản? <a href="login.php">Đăng nhập</a>
            </div>
        </div>
    </div>
</body>
</html>
