<?php
session_start();

$error = "";

date_default_timezone_set('Asia/Ho_Chi_Minh');
$email = getenv('EMAIL') ?: "admin@example.com";
$date = date('dmY');
$hash_flag = "FLAG{" . sha1($date . "_" . $email . "_image_extraction_user") . "}";
$random_key = getenv('RANDOM_KEY') ?: "default_random_key";
$flag_user = $hash_flag . ":"  . $random_key;

if ($_SERVER["REQUEST_METHOD"] == "POST") {
    $username = $_POST['username'] ?? '';
    $password = $_POST['password'] ?? '';

    if ($username === 'manh.dev' && $password === 'Summer2026!') {
        $_SESSION['loggedin'] = true;
        $_SESSION['username'] = $username;
    } else {
        $error = "Access Denied: Invalid credentials.";
    }
}

if (isset($_GET['logout'])) {
    session_destroy();
    header("Location: login.php");
    exit;
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Employee Portal | BlueMoon Fashion</title>
    <link rel="stylesheet" href="../style.css">
</head>
<body>
    <nav>
        <div class="logo">BLUEMOON FASHION</div>
        <div class="nav-links">
            <a href="../index.php">Home</a>
            <a href="../about.php">About</a>
            <a href="login.php" class="active">Portal</a>
        </div>
    </nav>

    <main>
        <div class="login-container">
            <?php if (isset($_SESSION['loggedin']) && $_SESSION['loggedin'] === true): ?>
                <div class="login-box" style="max-width: 600px;">
                    <div style="text-align: center; margin-bottom: 2rem;">
                        <span style="font-size: 4rem;">🔐</span>
                        <h2 style="margin-top: 1rem;">Authorized Access</h2>
                    </div>
                    <p style="text-align: center; color: var(--text-secondary); margin-bottom: 2rem;">
                        Welcome back, <strong><?php echo htmlspecialchars($_SESSION['username']); ?></strong>. 
                        You have successfully authenticated to the BlueMoon Internal Portal.
                    </p>
                    
                    <div style="background: rgba(34, 197, 94, 0.1); border: 1px solid #22c55e; padding: 2rem; border-radius: 20px; margin-bottom: 2rem;">
                        <span style="display: block; color: #4ade80; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 0.5rem;">Access Token</span>
                        <code style="font-family: monospace; color: #fff; font-size: 1.1rem; word-break: break-all;"><?php echo $flag_user; ?></code>
                    </div>

                    <div style="text-align: center;">
                        <a href="?logout=1" style="color: var(--text-secondary); text-decoration: none; font-size: 0.9rem;">Disconnect Session</a>
                    </div>
                </div>
            <?php else: ?>
                <div class="login-box">
                    <h2>BlueMoon Portal</h2>
                    <p style="text-align: center; color: var(--text-secondary); margin-bottom: 2rem; font-size: 0.9rem;">Internal Employee Access Only</p>
                    
                    <?php if ($error): ?>
                        <div class="error-msg"><?php echo $error; ?></div>
                    <?php endif; ?>

                    <form method="POST">
                        <div class="input-group">
                            <label>Username</label>
                            <input type="text" name="username" placeholder="e.g. john.doe" required autofocus>
                        </div>
                        <div class="input-group">
                            <label>Password</label>
                            <input type="password" name="password" placeholder="••••••••" required>
                        </div>
                        <button type="submit" class="btn" style="width: 100%;">Sign In</button>
                    </form>
                </div>
            <?php endif; ?>
        </div>
    </main>

    <footer>
        <p>&copy; 2026 BlueMoon Fashion International. All rights reserved.</p>
    </footer>
</body>
</html>
