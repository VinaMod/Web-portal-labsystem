<?php
require_once 'db.php';

if (!isset($_SESSION['user_id'])) {
    http_response_code(403);
    die("Unauthorized");
}
$user_id = $_SESSION['user_id'];
// CRITICAL: Close session writing to release the lock, otherwise requests are serialized!
session_write_close();

// 1. Fetch current order state
$stmt = $pdo->prepare("SELECT * FROM orders WHERE user_id = ?");
$stmt->execute([$user_id]);
$order = $stmt->fetch();

if (!$order) {
    die("Order not found");
}

// Check if coupon is already applied
if ($order['coupon_applied'] == 0) {
    
    // --- VULNERABILITY START ---
    // Extreme Mode: 2ms delay (Only scriptable)
    usleep(2000); 
    // --- VULNERABILITY END ---

    // Update DB with atomic subtraction
    // Use GREATEST to ensure price doesn't go below 0
    $update = $pdo->prepare("UPDATE orders SET total_price = GREATEST(total_price - 250000, 0), coupon_applied = 1 WHERE user_id = ?");
    $update->execute([$user_id]);

    echo "Coupon DC250 applied successfully!";
} else {
    http_response_code(400); // Bad Request
    echo "Coupon already used for this order!";
}
?>
