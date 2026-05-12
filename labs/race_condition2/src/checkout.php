<?php
require_once 'db.php';

if (!isset($_SESSION['user_id'])) {
    http_response_code(401);
    die("Unauthorized");
}

$user_id = $_SESSION['user_id'];

// 1. Get Current Order
$stmt = $pdo->prepare("SELECT * FROM orders WHERE user_id = ?");
$stmt->execute([$user_id]);
$order = $stmt->fetch();

if (!$order) {
    http_response_code(400);
    die("No active order");
}

$final_price = $order['total_price'];

// 2. Move to History (No Flag stored here)
$item_name = "Áo Khoác Hacker (Limited)";
$insert = $pdo->prepare("INSERT INTO order_history (user_id, item_name, amount, bonus_content) VALUES (?, ?, ?, NULL)");
$insert->execute([$user_id, $item_name, $final_price]);

// 4. Reset Current Order (New Cart)
$reset = $pdo->prepare("UPDATE orders SET total_price = 500000, coupon_applied = 0 WHERE user_id = ?");
$reset->execute([$user_id]);

echo "Thanh toán thành công!";
?>
