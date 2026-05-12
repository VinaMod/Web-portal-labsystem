<?php
require_once 'db.php';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $username = $_POST['username'];
    $password = $_POST['password'];

    $stmt = $pdo->prepare("SELECT * FROM users WHERE username = ?");
    $stmt->execute([$username]);
    $user = $stmt->fetch();

    if ($user && password_verify($password, $user['password'])) {
        $_SESSION['user_id'] = $user['id'];
        $_SESSION['username'] = $user['username'];
        header("Location: index.php");
        exit;
    } else {
        $error = "Sai tên đăng nhập hoặc mật khẩu!";
    }
}
?>
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Đăng Nhập - Fashion Store</title>
    <link rel="stylesheet" href="style.css?v=6">
</head>
<body>
    <div class="auth-wrapper">
        <div class="auth-card">
            <h2 class="auth-title">Đăng Nhập</h2>
            <?php if (isset($error)): ?>
                <div style="color: red; margin-bottom: 1rem; font-size: 0.9rem;"><?php echo $error; ?></div>
            <?php endif; ?>
            
            <form method="POST">
                <input type="text" name="username" required placeholder="Tên đăng nhập" autofocus>
                <input type="password" name="password" required placeholder="Mật khẩu">
                <button type="submit" class="auth-btn">ĐĂNG NHẬP</button>
            </form>
            
            <div class="auth-links">
                Chưa có tài khoản? <a href="register.php">Đăng ký ngay</a>
            </div>
        </div>
    </div>
</body>
</html>
