<?php
session_start();

if (!isset($_SESSION['user']) || $_SESSION['user']['role'] !== 'admin') {
    die("Access Denied. Admins only.");
}

// Generate Dynamic Flag
// Formula: SHA1(ddmmyyyy_email_oauth_account_takeover)
$timezone = 'Asia/Ho_Chi_Minh';
date_default_timezone_set($timezone);
$date_component = date('dmY'); 
$email = getenv('EMAIL') ?: 'carl@techvision.com';
$suffix = 'oauth_account_takeover';

$raw_string = "{$date_component}_{$email}_{$suffix}";
$flag_hash = sha1($raw_string);
$randomKey = getenv('RANDOM_KEY') ?: bin2hex(random_bytes(16)); // Add some randomness to the flag to make it unique per session
$flag = "FLAG{" . $flag_hash . "}:" . $randomKey;

?>
<!DOCTYPE html>
<html>
<head>
    <title>Admin Dashboard</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="container">
        <h1>Admin Dashboard</h1>
        <div class="alert success">
            <p>Welcome, Admin!</p>
            <p>Here is your secret flag:</p>
            <h2 class="flag"><?php echo $flag; ?></h2>
        </div>
        <a href="index.php">Back to Home</a>
    </div>
</body>
</html>
