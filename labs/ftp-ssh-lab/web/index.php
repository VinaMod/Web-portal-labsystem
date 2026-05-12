<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Secure Admin Portal</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="container">
        <div class="login-box">
            <div class="logo">
                <svg width="60" height="60" viewBox="0 0 60 60" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <rect width="60" height="60" rx="12" fill="url(#gradient)"/>
                    <path d="M30 15L45 25V40L30 50L15 40V25L30 15Z" stroke="white" stroke-width="2" fill="none"/>
                    <circle cx="30" cy="30" r="5" fill="white"/>
                    <defs>
                        <linearGradient id="gradient" x1="0" y1="0" x2="60" y2="60">
                            <stop offset="0%" stop-color="#667eea"/>
                            <stop offset="100%" stop-color="#764ba2"/>
                        </linearGradient>
                    </defs>
                </svg>
            </div>
            <h1>Admin Portal</h1>
            <p class="subtitle">Secure Access Required</p>

<?php
session_start();

// Hard-coded credentials (intentionally difficult)
$valid_username = "admin";
$valid_password = "Sup3rS3cur3P@ssw0rd!2024#XYZ";

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $username = $_POST['username'] ?? '';
    $password = $_POST['password'] ?? '';
    
    if ($username === $valid_username && $password === $valid_password) {
        $_SESSION['logged_in'] = true;
        ?>
        <div class="success-message">
            <svg width="50" height="50" viewBox="0 0 50 50" fill="none">
                <circle cx="25" cy="25" r="24" stroke="#10b981" stroke-width="2"/>
                <path d="M15 25L22 32L35 18" stroke="#10b981" stroke-width="3" stroke-linecap="round"/>
            </svg>
            <h2>Access Granted</h2>
            <p>Welcome, Administrator!</p>
            <p class="info-text">You have successfully authenticated to the admin portal.</p>
            <p class="dead-end">However, this portal is currently under maintenance...</p>
        </div>
        <?php
    } else {
        ?>
        <div class="error-message">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="11" stroke="#ef4444" stroke-width="2"/>
                <path d="M12 7V13M12 16V17" stroke="#ef4444" stroke-width="2" stroke-linecap="round"/>
            </svg>
            <span>Invalid credentials. Access denied.</span>
        </div>
        <?php
        include 'login_form.php';
    }
} else {
    include 'login_form.php';
}
?>
        </div>
        
        <div class="footer">
            <p>Secure System v2.4.1 | © 2024</p>
        </div>
    </div>
</body>
</html>
