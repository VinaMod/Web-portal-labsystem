<?php
require_once 'db.php';

$username = 'demo';
$password = 'demo123';

// Check if user exists
$stmt = $pdo->prepare("SELECT id FROM users WHERE username = ?");
$stmt->execute([$username]);
$user = $stmt->fetch();

if (!$user) {
    // Create User
    $hash = password_hash($password, PASSWORD_DEFAULT);
    $stmt = $pdo->prepare("INSERT INTO users (username, password) VALUES (?, ?)");
    $stmt->execute([$username, $hash]);
    $user_id = $pdo->lastInsertId();

    // Create Initial Order for this user
    $stmt = $pdo->prepare("INSERT INTO orders (user_id, total_price, coupon_applied) VALUES (?, 500000, 0)");
    $stmt->execute([$user_id]);

    echo "Demo user created successfully.\n";
} else {
    echo "Demo user already exists.\n";
}
?>
