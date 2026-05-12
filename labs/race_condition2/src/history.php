<?php
require_once 'db.php';

if (!isset($_SESSION['user_id'])) {
    header("Location: login.php");
    exit;
}

$user_id = $_SESSION['user_id'];
$username = $_SESSION['username'];

// Get History
$stmt = $pdo->prepare("SELECT * FROM order_history WHERE user_id = ? ORDER BY created_at DESC");
$stmt->execute([$user_id]);
$history = $stmt->fetchAll();
?>
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lịch Sử Đơn Hàng - Fashion Store</title>
    <link rel="stylesheet" href="style.css?v=6">
    <style>
        .history-table {
            width: 100%;
            border-collapse: collapse;
            background: #fff;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .history-table th, .history-table td {
            text-align: left;
            padding: 1rem;
            border-bottom: 1px solid #eee;
        }
        .history-table th { background: #f9f9f9; font-weight: 600; }
        .bonus-box {
            background: #000;
            color: #0f0;
            font-family: monospace;
            padding: 5px 10px;
            border-radius: 4px;
            font-size: 0.9rem;
            display: inline-block;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <a href="index.php" class="brand">FASHION.</a>
        <div class="nav-right">
            <a href="index.php">Trang Chủ</a>
            <span style="margin: 0 10px; color: #ccc;">|</span>
            <span>Chào, <b><?php echo htmlspecialchars($username); ?></b></span>
            <a href="logout.php">Đăng Xuất</a>
        </div>
    </nav>

    <div class="container" style="margin-top: 2rem;">
        <h2 class="section-title">Lịch Sử Mua Hàng</h2>
        
        <?php if (count($history) > 0): ?>
            <table class="history-table">
                <thead>
                    <tr>
                        <th>Mã đơn</th>
                        <th>Sản phẩm</th>
                        <th>Thời gian</th>
                        <th>Thành tiền</th>
                        <th>Trạng thái</th>
                    </tr>
                </thead>
                <tbody>
                    <?php foreach ($history as $row): ?>
                        <tr>
                            <td>#<?php echo $row['id']; ?></td>
                            <td>
                                <div><?php echo htmlspecialchars($row['item_name']); ?></div>
                            </td>
                            <td><?php echo $row['created_at']; ?></td>
                            <td><?php echo number_format($row['amount'], 0, ',', '.'); ?>₫</td>
                            <td><span style="color: green; font-weight: bold;">Đã thanh toán</span></td>
                        </tr>
                    <?php endforeach; ?>
                </tbody>
            </table>
        <?php else: ?>
            <div style="text-align: center; color: #666; padding: 2rem;">
                Bạn chưa có đơn hàng nào. <a href="index.php" style="color: blue;">Mua sắm ngay</a>
            </div>
        <?php endif; ?>
    </div>
</body>
</html>
