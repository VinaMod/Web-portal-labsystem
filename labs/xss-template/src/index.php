<?php
header('Content-Type: text/html; charset=UTF-8');
require_once 'config/database.php';
require_once 'config/session.php';
require_once 'config/xss_helper.php';

$database = new Database();
$db = $database->getConnection();

// Lấy danh sách sản phẩm
$query = "SELECT * FROM products ORDER BY created_at DESC";
$stmt = $db->prepare($query);
$stmt->execute();
$products = $stmt->fetchAll(PDO::FETCH_ASSOC);
?>

<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Shop XSS Lab</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .product-card {
            transition: transform 0.3s;
        }
        .product-card:hover {
            transform: translateY(-5px);
        }
        .navbar-brand {
            font-weight: bold;
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="index.php">Shop XSS Lab</a>
            <div class="navbar-nav ms-auto">
                <?php if (isLoggedIn()): ?>
                    <span class="navbar-text me-3">Xin chào, <?php echo htmlspecialchars($_SESSION['username']); ?>!</span>
                    <?php if (isAdmin()): ?>
                        <a class="nav-link" href="admin.php">Admin Panel</a>
                    <?php endif; ?>
                    <a class="nav-link" href="logout.php">Đăng xuất</a>
                <?php else: ?>
                    <a class="nav-link" href="login.php">Đăng nhập</a>
                    <a class="nav-link" href="register.php">Đăng ký</a>
                <?php endif; ?>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="row">
            <div class="col-12">
                <h1 class="mb-4">Cửa hàng điện tử</h1>
                <p class="text-muted">Chào mừng đến với cửa hàng điện tử của chúng tôi!</p>
            </div>
        </div>

        <div class="row">
            <?php foreach ($products as $product): ?>
            <div class="col-md-6 col-lg-4 mb-4">
                <div class="card product-card h-100">
                    <div class="card-body">
                        <h5 class="card-title"><?php echo safeOutput($product['name'], 'product_name'); ?></h5>
                        <p class="card-text"><?php echo safeOutput($product['description'], 'description'); ?></p>
                        <p class="card-text">
                            <strong class="text-danger">$<?php echo number_format($product['price'], 2); ?></strong>
                        </p>
                        <a href="product.php?id=<?php echo $product['id']; ?>" class="btn btn-primary">Xem chi tiết</a>
                    </div>
                </div>
            </div>
            <?php endforeach; ?>
        </div>

        <?php if (!isLoggedIn()): ?>
        <?php endif; ?>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
