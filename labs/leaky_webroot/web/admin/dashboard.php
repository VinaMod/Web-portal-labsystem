<?php
session_start();
if (!isset($_SESSION['loggedin']) || $_SESSION['loggedin'] !== true) {
    header("Location: login.php");
    exit;
}

$flag = file_get_contents("flag.txt");
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Admin Dashboard - BlueMoon Fashion</title>
    <style>
        body { font-family: sans-serif; background: #f8f9fa; margin: 2rem; }
        .dashboard { background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
        .flag { background: #d4edda; color: #155724; padding: 1rem; border-radius: 4px; border: 1px solid #c3e6cb; font-family: monospace; font-size: 1.2rem; }
        .logout { margin-top: 1rem; display: inline-block; color: #007bff; text-decoration: none; }
    </style>
</head>
<body>
    <div class="dashboard">
        <h1>Welcome Admin</h1>
        <p>You have successfully accessed the internal admin panel.</p>
        <div class="flag">
            <?php echo htmlspecialchars($flag); ?>
        </div>
        <a href="logout.php" class="logout">Logout</a>
    </div>
</body>
</html>
