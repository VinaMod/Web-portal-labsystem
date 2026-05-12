<?php
require_once 'db.php';

try {
    $sql = "CREATE TABLE IF NOT EXISTS order_history (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        item_name VARCHAR(100) NOT NULL,
        amount INT NOT NULL,
        status VARCHAR(20) DEFAULT 'Paid',
        bonus_content TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )";
    
    $pdo->exec($sql);
    echo "Table 'order_history' created successfully.";
} catch (PDOException $e) {
    echo "Error: " . $e->getMessage();
}
?>
