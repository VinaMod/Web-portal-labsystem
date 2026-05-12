<?php
header('Content-Type: text/html; charset=UTF-8');
require_once 'config/database.php';
require_once 'config/session.php';
require_once 'config/xss_helper.php';

function adminEscape($value) {
    return htmlspecialchars((string)$value, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

function adminEscapeWithBr($value) {
    return nl2br(adminEscape($value));
}

// Yêu cầu quyền admin
requireAdmin();

$database = new Database();
$db = $database->getConnection();

// Lấy tất cả bình luận với thông tin sản phẩm và user
$query = "SELECT c.*, u.username, u.name, u.email, p.name as product_name 
          FROM comments c 
          JOIN users u ON c.user_id = u.id 
          JOIN products p ON c.product_id = p.id 
          ORDER BY c.created_at DESC";
$stmt = $db->prepare($query);
$stmt->execute();
$comments = $stmt->fetchAll(PDO::FETCH_ASSOC);

// Lấy thống kê
$stats_query = "SELECT 
    COUNT(*) as total_comments,
    COUNT(DISTINCT user_id) as total_users,
    COUNT(DISTINCT product_id) as total_products
    FROM comments";
$stats_stmt = $db->prepare($stats_query);
$stats_stmt->execute();
$stats = $stats_stmt->fetch(PDO::FETCH_ASSOC);

// Đọc Flag động từ file
$dynamic_flag = "FLAG{LOADING...}";
$flag_file = "/var/www/html/flag.txt";
if (file_exists($flag_file)) {
    $dynamic_flag = trim(file_get_contents($flag_file));
}
?>

<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Panel - Shop XSS Lab</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .comment-item {
            border-left: 4px solid #007bff;
        }
        .comment-item:hover {
            background-color: #f8f9fa;
        }
        .flag-container {
            text-align: center;
        }
        .flag-content {
            animation: fadeIn 0.3s ease-in-out;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .flag-content .alert {
            background: linear-gradient(45deg, #2c3e50, #34495e);
            color: #f1c40f;
            border: 2px solid #f39c12;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="index.php">Shop XSS Lab</a>
            <div class="navbar-nav ms-auto">
                <span class="navbar-text me-3">Admin: <?php echo htmlspecialchars($_SESSION['username']); ?></span>
                <a class="nav-link" href="index.php">Trang chủ</a>
                <a class="nav-link" href="logout.php">Đăng xuất</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="row">
            <div class="col-12">
                <h1 class="mb-4">Admin Panel - Quản lý bình luận</h1>
                
                <!-- Thống kê -->
                <div class="row mb-4">
                    <div class="col-md-3">
                        <div class="card bg-primary text-white">
                            <div class="card-body">
                                <h5 class="card-title">Tổng bình luận</h5>
                                <h2><?php echo adminEscape($stats['total_comments']); ?></h2>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card bg-success text-white">
                            <div class="card-body">
                                <h5 class="card-title">Người dùng</h5>
                                <h2><?php echo adminEscape($stats['total_users']); ?></h2>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card bg-info text-white">
                            <div class="card-body">
                                <h5 class="card-title">Sản phẩm</h5>
                                <h2><?php echo adminEscape($stats['total_products']); ?></h2>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card bg-warning text-dark">
                            <div class="card-body">
                                <h5 class="card-title">
                                    <i class="fas fa-flag"></i> Admin Flag
                                </h5>
                                <div class="flag-container">
                                    <div id="flagContent" class="flag-content" style="display: none;">
                                        <div class="alert alert-dark mb-2" style="font-family: monospace; font-size: 12px; word-break: break-all;">
                                            <?php echo adminEscape($dynamic_flag); ?>
                                        </div>
                                        <div class="flag-info mt-2">
                                            <small class="text-muted">
                                                <i class="fas fa-calendar"></i> Generated: <?php 
                                                    $old_tz = date_default_timezone_get();
                                                    date_default_timezone_set('Asia/Ho_Chi_Minh');
                                                    echo date('d/m/Y H:i:s', filemtime($flag_file) ?: time());
                                                    date_default_timezone_set($old_tz);
                                                ?> (HCM)
                                            </small>
                                        </div>
                                    </div>
                                    <button id="toggleFlag" class="btn btn-dark btn-sm" onclick="toggleFlag()">
                                        <i class="fas fa-eye"></i> View Flag
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Danh sách bình luận -->
                <div class="card">
                    <div class="card-header">
                        <h4>Danh sách bình luận</h4>
                    </div>
                    <div class="card-body">
                        <?php if (empty($comments)): ?>
                        <p class="text-muted">Chưa có bình luận nào.</p>
                        <?php else: ?>
                        <div class="comments-list">
                            <?php foreach ($comments as $comment): ?>
                            <div class="comment-item card mb-3">
                                <div class="card-body">
                                    <div class="row">
                                        <div class="col-md-8">
                                            <div class="d-flex justify-content-between mb-2">
                                                <div>
                                                    <strong><?php 
                                                        $displayName = !empty($comment['display_name']) ? $comment['display_name'] : $comment['name'];
                                                        echo adminEscape($displayName); 
                                                    ?></strong>
                                                    <small class="text-muted ms-2">(@<?php echo adminEscape($comment['username']); ?>)</small>
                                                </div>
                                                <small class="text-muted"><?php echo adminEscape($comment['created_at']); ?></small>
                                            </div>
                                            <div class="mb-2">
                                                <small class="text-muted">
                                                    <strong>Email:</strong> <?php 
                                                        $displayEmail = !empty($comment['display_email']) ? $comment['display_email'] : $comment['email'];
                                                        echo adminEscape($displayEmail); 
                                                    ?>
                                                </small>
                                            </div>
                                            <p class="mb-1">
                                                <strong>Sản phẩm:</strong> 
                                                <a href="product.php?id=<?php echo (int)$comment['product_id']; ?>">
                                                    <?php echo adminEscape($comment['product_name']); ?>
                                                </a>
                                            </p>
                                            <?php if (!empty($comment['title'])): ?>
                                            <h6 class="mb-1">
                                                <strong>Tiêu đề:</strong> <?php echo adminEscape($comment['title']); ?>
                                            </h6>
                                            <?php endif; ?>
                                            <?php if (isset($comment['rating'])): ?>
                                            <div class="mb-2">
                                                <small class="text-warning">
                                                    <strong>Đánh giá:</strong> 
                                                    <?php for ($i = 0; $i < (int)$comment['rating']; $i++): ?>★<?php endfor; ?>
                                                    <?php for ($i = (int)$comment['rating']; $i < 5; $i++): ?>☆<?php endfor; ?>
                                                    (<?php echo adminEscape($comment['rating']); ?>/5)
                                                </small>
                                            </div>
                                            <?php endif; ?>
                                            <div class="comment-content">
                                                <strong>Nội dung:</strong>
                                                <?php echo adminEscapeWithBr($comment['comment']); ?>
                                            </div>
                                        </div>
                                        <div class="col-md-4">
                                            <div class="text-end">
                                                <a href="product.php?id=<?php echo $comment['product_id']; ?>" 
                                                   class="btn btn-sm btn-outline-primary">Xem sản phẩm</a>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <?php endforeach; ?>
                        </div>
                        <?php endif; ?>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/js/all.min.js"></script>
    <script>
        function toggleFlag() {
            const flagContent = document.getElementById('flagContent');
            const toggleButton = document.getElementById('toggleFlag');
            
            if (flagContent.style.display === 'none' || flagContent.style.display === '') {
                // Show flag
                flagContent.style.display = 'block';
                toggleButton.innerHTML = '<i class="fas fa-eye-slash"></i> Hide Flag';
                toggleButton.classList.remove('btn-dark');
                toggleButton.classList.add('btn-secondary');
            } else {
                // Hide flag
                flagContent.style.display = 'none';
                toggleButton.innerHTML = '<i class="fas fa-eye"></i> View Flag';
                toggleButton.classList.remove('btn-secondary');
                toggleButton.classList.add('btn-dark');
            }
        }
    </script>
</body>
</html>
