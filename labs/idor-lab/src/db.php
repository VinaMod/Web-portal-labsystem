<?php
$host = 'db';
$db   = 'idor_lab';
$user = 'user';
$pass = 'password';
$charset = 'utf8mb4';

try {
    $dsn = "mysql:host=$host;dbname=$db;charset=$charset";
    $options = [
        PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        PDO::ATTR_EMULATE_PREPARES   => false,
    ];
    
    // Retry connection for up to 30 seconds
    $max_retries = 15;
    $retry_delay = 2; // seconds
    $connected = false;
    
    for ($i = 0; $i < $max_retries; $i++) {
        try {
            $pdo = new PDO($dsn, $user, $pass, $options);
            $connected = true;
            break;
        } catch (PDOException $e) {
            if ($i === $max_retries - 1) {
                throw $e; // Throw exception on last attempt
            }
            sleep($retry_delay);
        }
    }
} catch (\PDOException $e) {
    die("Database connection failed: " . $e->getMessage());
}
?>
