<?php
require_once 'db.php';

if (!isset($_SESSION['user_id'])) {
    header("Location: login.php");
    exit;
}

$user_id = $_SESSION['user_id'];

$stmt = $pdo->prepare("UPDATE orders SET total_price = 500000, coupon_applied = 0 WHERE user_id = ?");
$stmt->execute([$user_id]);

header("Location: index.php");
exit;
?>
