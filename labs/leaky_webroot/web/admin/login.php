<?php
session_start();

// Hardcoded for the lab
$admin_user = "admin";
$admin_pass_md5 = "5f4dcc3b5aa765d61d8327deb882cf99"; // md5('password')

$error = "";

if ($_SERVER["REQUEST_METHOD"] == "POST") {
    $username = $_POST['username'] ?? '';
    $password = $_POST['password'] ?? '';

    if ($username === $admin_user && md5($password) === $admin_pass_md5) {
        $_SESSION['loggedin'] = true;
        header("Location: dashboard.php");
        exit;
    } else {
        $error = "Invalid credentials. Please try again.";
    }
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Personnel Login | BlueMoon Fashion</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=Playfair+Display:wght@700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #1a1a1a;
            --accent: #c5a059;
            --bg: #0d0d0d;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), url('../assets/hero.jpg') center/cover no-repeat;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            color: white;
        }

        .login-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            padding: 50px;
            width: 100%;
            max-width: 450px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            text-align: center;
        }

        .logo {
            font-family: 'Playfair Display', serif;
            font-size: 2rem;
            letter-spacing: 5px;
            margin-bottom: 40px;
            display: block;
            text-decoration: none;
            color: white;
        }

        h2 { font-weight: 300; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 3px; margin-bottom: 30px; color: var(--accent); }

        .form-group { margin-bottom: 20px; text-align: left; }
        
        input {
            width: 100%;
            padding: 15px;
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            color: white;
            font-family: 'Inter', sans-serif;
            font-size: 0.9rem;
            outline: none;
            transition: border 0.3s;
        }

        input:focus { border-color: var(--accent); }

        button {
            width: 100%;
            padding: 15px;
            background: var(--accent);
            color: white;
            border: none;
            text-transform: uppercase;
            letter-spacing: 2px;
            font-weight: 600;
            cursor: pointer;
            margin-top: 10px;
            transition: background 0.3s, transform 0.2s;
        }

        button:hover { background: #b38e4a; transform: translateY(-2px); }
        button:active { transform: translateY(0); }

        .error {
            background: rgba(231, 76, 60, 0.2);
            color: #ff7675;
            padding: 10px;
            font-size: 0.8rem;
            margin-bottom: 20px;
            border-left: 3px solid #d63031;
        }

        .back-home {
            margin-top: 30px;
            display: block;
            font-size: 0.75rem;
            color: rgba(255,255,255,0.3);
            text-decoration: none;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .back-home:hover { color: white; }
    </style>
</head>
<body>
    <div class="login-card">
        <a href="../index.php" class="logo">BLUEMOON</a>
        <h2>Internal Portal</h2>
        
        <?php if ($error): ?>
            <div class="error"><?php echo $error; ?></div>
        <?php endif; ?>

        <form method="POST">
            <div class="form-group">
                <input type="text" name="username" placeholder="Username" required autocomplete="off">
            </div>
            <div class="form-group">
                <input type="password" name="password" placeholder="Password" required>
            </div>
            <button type="submit">Sign In</button>
        </form>

        <a href="../index.php" class="back-home">Return to Site</a>
    </div>
</body>
</html>
