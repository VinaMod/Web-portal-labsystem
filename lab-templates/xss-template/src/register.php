<?php
header('Content-Type: text/html; charset=UTF-8');
require_once 'config/database.php';
require_once 'config/session.php';

// Nếu đã đăng nhập, chuyển về trang chủ
if (isLoggedIn()) {
    header('Location: index.php');
    exit();
}

$error = '';
$success = '';

if ($_POST) {
    $username = $_POST['username'] ?? '';
    $name = $_POST['name'] ?? '';
    $email = $_POST['email'] ?? '';
    $password = $_POST['password'] ?? '';
    $confirm_password = $_POST['confirm_password'] ?? '';
    
    if ($username && $name && $email && $password && $confirm_password) {
        if ($password !== $confirm_password) {
            $error = 'Mật khẩu xác nhận không khớp!';
        } else {
            $database = new Database();
            $db = $database->getConnection();
            
            // Kiểm tra username đã tồn tại
            $query = "SELECT id FROM users WHERE username = ? OR email = ?";
            $stmt = $db->prepare($query);
            $stmt->execute([$username, $email]);
            
            if ($stmt->fetch()) {
                $error = 'Tên đăng nhập hoặc email đã tồn tại!';
            } else {
                // Tạo tài khoản mới
                $query = "INSERT INTO users (username, name, email, password) VALUES (?, ?, ?, ?)";
                $stmt = $db->prepare($query);
                $stmt->execute([$username, $name, $email, md5($password)]);
                
                $success = 'Đăng ký thành công! <a href="login.php">Đăng nhập ngay</a>';
            }
        }
    } else {
        $error = 'Vui lòng nhập đầy đủ thông tin!';
    }
}
?>

<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Đăng ký - Shop XSS Lab</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="index.php">Shop XSS Lab</a>
        </div>
    </nav>

    <div class="container mt-5">
        <div class="row justify-content-center">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h3 class="text-center">Đăng ký tài khoản</h3>
                    </div>
                    <div class="card-body">
                        <?php if ($error): ?>
                        <div class="alert alert-danger"><?php echo htmlspecialchars($error); ?></div>
                        <?php endif; ?>
                        
                        <?php if ($success): ?>
                        <div class="alert alert-success"><?php echo $success; ?></div>
                        <?php endif; ?>
                        
                        <form method="POST">
                            <div class="mb-3">
                                <label for="name" class="form-label">Họ và tên:</label>
                                <input type="text" class="form-control" id="name" name="name" required>
                            </div>
                            <div class="mb-3">
                                <label for="username" class="form-label">Tên đăng nhập:</label>
                                <input type="text" class="form-control" id="username" name="username" required>
                            </div>
                            <div class="mb-3">
                                <label for="email" class="form-label">Email:</label>
                                <input type="email" class="form-control" id="email" name="email" required>
                            </div>
                            <div class="mb-3">
                                <label for="password" class="form-label">Mật khẩu:</label>
                                <input type="password" class="form-control" id="password" name="password" required>
                            </div>
                            <div class="mb-3">
                                <label for="confirm_password" class="form-label">Xác nhận mật khẩu:</label>
                                <input type="password" class="form-control" id="confirm_password" name="confirm_password" required>
                            </div>
                            <button type="submit" class="btn btn-primary w-100">Đăng ký</button>
                        </form>
                        
                        <div class="mt-3 text-center">
                            <a href="login.php">Đã có tài khoản? Đăng nhập ngay</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
