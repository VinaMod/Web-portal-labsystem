<?php
header('Content-Type: text/html; charset=UTF-8');
require_once 'config/database.php';
require_once 'config/session.php';
require_once 'config/xss_helper.php';

$database = new Database();
$db = $database->getConnection();

$product_id = isset($_GET['id']) ? (int)$_GET['id'] : 0;

// Lấy thông tin sản phẩm
$query = "SELECT * FROM products WHERE id = ?";
$stmt = $db->prepare($query);
$stmt->execute([$product_id]);
$product = $stmt->fetch(PDO::FETCH_ASSOC);

if (!$product) {
    header('Location: index.php');
    exit();
}

// Xử lý thêm bình luận (CÓ LỖ HỔNG XSS - KHÔNG ESCAPE INPUT)
if ($_POST && isset($_POST['comment']) && isLoggedIn()) {
    $display_name = $_POST['display_name'] ?? '';
    $display_email = $_POST['display_email'] ?? '';
    $title = $_POST['title'] ?? '';
    $comment = $_POST['comment']; // KHÔNG ESCAPE - ĐÂY LÀ LỖ HỔNG XSS
    $rating = isset($_POST['rating']) ? (int)$_POST['rating'] : 5;
    $user_id = $_SESSION['user_id'];
    
    $query = "INSERT INTO comments (product_id, user_id, display_name, display_email, title, comment, rating) VALUES (?, ?, ?, ?, ?, ?, ?)";
    $stmt = $db->prepare($query);
    $stmt->execute([$product_id, $user_id, $display_name, $display_email, $title, $comment, $rating]);
    
    header('Location: product.php?id=' . $product_id);
    exit();
}

// Lấy bình luận (CÓ LỖ HỔNG XSS - KHÔNG ESCAPE OUTPUT)
$query = "SELECT c.*, u.username, u.name, u.email FROM comments c 
          JOIN users u ON c.user_id = u.id 
          WHERE c.product_id = ? 
          ORDER BY c.created_at DESC";
$stmt = $db->prepare($query);
$stmt->execute([$product_id]);
$comments = $stmt->fetchAll(PDO::FETCH_ASSOC);
?>

<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title><?php echo safeOutput($product['name'], 'product_name'); ?> - Shop XSS Lab</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
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
            <div class="col-md-8">
                <div class="card">
                    <div class="card-body">
                        <h2><?php echo safeOutput($product['name'], 'product_name'); ?></h2>
                        <p class="text-muted">Giá: <strong class="text-danger">$<?php echo number_format($product['price'], 2); ?></strong></p>
                        <p><?php echo safeOutput($product['description'], 'description'); ?></p>
                    </div>
                </div>

                <!-- Phần bình luận -->
                <div class="mt-4">
                    <h4>Bình luận</h4>
                    
                    <?php if (isLoggedIn()): ?>
                    <div class="card mb-3">
                        <div class="card-body">
                            <form method="POST">
                                <div class="mb-3">
                                    <label for="display_name" class="form-label">Tên hiển thị:</label>
                                    <input type="text" class="form-control" id="display_name" name="display_name" placeholder="Nhập tên của bạn" value="<?php 
                                        $user_query = "SELECT name FROM users WHERE id = ?";
                                        $user_stmt = $db->prepare($user_query);
                                        $user_stmt->execute([$_SESSION['user_id']]);
                                        $user_data = $user_stmt->fetch(PDO::FETCH_ASSOC);
                                        echo htmlspecialchars($user_data['name'] ?? '');
                                    ?>">
                                </div>
                                <div class="mb-3">
                                    <label for="display_email" class="form-label">Email:</label>
                                    <input type="email" class="form-control" id="display_email" name="display_email" placeholder="Nhập email của bạn" value="<?php 
                                        $user_query = "SELECT email FROM users WHERE id = ?";
                                        $user_stmt = $db->prepare($user_query);
                                        $user_stmt->execute([$_SESSION['user_id']]);
                                        $user_data = $user_stmt->fetch(PDO::FETCH_ASSOC);
                                        echo htmlspecialchars($user_data['email'] ?? '');
                                    ?>">
                                </div>
                                <div class="mb-3">
                                    <label for="title" class="form-label">Tiêu đề bình luận:</label>
                                    <input type="text" class="form-control" id="title" name="title" placeholder="Nhập tiêu đề bình luận">
                                </div>
                                <div class="mb-3">
                                    <label for="comment" class="form-label">Nội dung bình luận:</label>
                                    <textarea class="form-control" id="comment" name="comment" rows="3" required></textarea>
                                </div>
                                <div class="mb-3">
                                    <label for="rating" class="form-label">Đánh giá (1-5 sao):</label>
                                    <select class="form-control" id="rating" name="rating">
                                        <option value="5" selected>5 sao - Tuyệt vời</option>
                                        <option value="4">4 sao - Tốt</option>
                                        <option value="3">3 sao - Bình thường</option>
                                        <option value="2">2 sao - Không tốt</option>
                                        <option value="1">1 sao - Rất tệ</option>
                                    </select>
                                </div>
                                <button type="submit" class="btn btn-primary">Gửi bình luận</button>
                            </form>
                        </div>
                    </div>
                    <?php else: ?>
                    <div class="alert alert-info">
                        <a href="login.php">Đăng nhập</a> để bình luận
                    </div>
                    <?php endif; ?>

                    <!-- Hiển thị bình luận - CÓ LỖ HỔNG XSS -->
                    <div class="comments">
                        <?php foreach ($comments as $comment): ?>
                        <div class="card mb-2">
                            <div class="card-body">
                                <div class="d-flex justify-content-between">
                                    <div>
                                        <strong><?php 
                                            $displayName = !empty($comment['display_name']) ? $comment['display_name'] : $comment['name'];
                                            echo safeOutput($displayName, 'display_name'); 
                                        ?></strong>
                                        <small class="text-muted ms-2">(@<?php echo safeOutput($comment['username'], 'username'); ?>)</small>
                                    </div>
                                    <small class="text-muted"><?php echo $comment['created_at']; ?></small>
                                </div>
                                <div class="mt-2">
                                    <small class="text-muted">Email: <?php 
                                        $displayEmail = !empty($comment['display_email']) ? $comment['display_email'] : $comment['email'];
                                        echo safeOutput($displayEmail, 'display_email'); 
                                    ?></small>
                                </div>
                                <?php if (!empty($comment['title'])): ?>
                                <h6 class="mt-2 mb-1">
                                    <?php echo safeOutput($comment['title'], 'title'); ?>
                                </h6>
                                <?php endif; ?>
                                <?php if (isset($comment['rating'])): ?>
                                <div class="mb-2">
                                    <small class="text-warning">
                                        <?php for ($i = 0; $i < $comment['rating']; $i++): ?>★<?php endfor; ?>
                                        <?php for ($i = $comment['rating']; $i < 5; $i++): ?>☆<?php endfor; ?>
                                        (<?php echo safeOutput($comment['rating'], 'rating'); ?>/5)
                                    </small>
                                </div>
                                <?php endif; ?>
                                <p class="mt-2 mb-0">
                                    <?php echo safeOutputWithBr($comment['comment'], 'comment'); ?>
                                </p>
                            </div>
                        </div>
                        <?php endforeach; ?>
                    </div>
                </div>
            </div>

            <div class="col-md-4">
                <div class="card">
                    <div class="card-body">
                        <h5>Payload XSS mẫu:</h5>
                        <div class="alert alert-warning">
                            <small>
                                <code>&lt;script&gt;alert('XSS')&lt;/script&gt;</code><br>
                                <code>&lt;img src=x onerror=alert('XSS')&gt;</code><br>
                                <code>&lt;svg onload=alert('XSS')&gt;</code>
                            </small>
                        </div>
                        <p class="text-muted small">
                            Thử copy các payload trên vào ô bình luận để test XSS
                        </p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
