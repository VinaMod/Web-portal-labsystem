<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Our Collection | BlueMoon Fashion</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=Playfair+Display:wght@700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #1a1a1a;
            --accent: #c5a059;
            --bg-gray: #f8f8f8;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', sans-serif; background-color: var(--bg-gray); color: #333; }

        header {
            background-color: var(--primary);
            padding: 1.5rem 5%;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .logo {
            font-family: 'Playfair Display', serif;
            font-size: 1.5rem;
            color: white;
            text-decoration: none;
            letter-spacing: 2px;
        }

        nav a {
            color: rgba(255,255,255,0.7);
            margin-left: 20px;
            text-decoration: none;
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            transition: color 0.3s;
        }

        nav a:hover { color: var(--accent); }

        .container {
            max-width: 1200px;
            margin: 80px auto;
            padding: 0 5%;
        }

        .page-title {
            font-family: 'Playfair Display', serif;
            font-size: 3rem;
            margin-bottom: 50px;
            text-align: center;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 40px;
        }

        .product-card {
            background: white;
            padding: 0;
            border-radius: 0;
            overflow: hidden;
            transition: transform 0.4s ease;
        }

        .product-card:hover { transform: translateY(-5px); }

        .img-placeholder {
            height: 380px;
            background: #eee;
            position: relative;
        }

        .img-placeholder::after {
            content: 'PREVIEW';
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: #ccc;
            letter-spacing: 5px;
            font-size: 0.7rem;
        }

        .details { padding: 25px; text-align: left; }
        .details h4 { font-family: 'Playfair Display', serif; font-size: 1.3rem; margin-bottom: 10px; }
        .price { color: var(--accent); font-weight: 600; font-size: 1.1rem; }

        footer {
            background: var(--primary);
            color: rgba(255,255,255,0.4);
            padding: 40px 5%;
            text-align: center;
            font-size: 0.75rem;
            margin-top: 100px;
        }
    </style>
</head>
<body>
    <header>
        <a href="index.php" class="logo">BlueMoon</a>
        <nav>
            <a href="index.php">Home</a>
            <a href="products.php">Collection</a>
        </nav>
    </header>

    <div class="container">
        <h2 class="page-title">The Essentials</h2>
        <div class="grid">
            <div class="product-card">
                <img src="assets/1.jpg" alt="Tailored Evening Blazer" style="width:100%; height:380px; object-fit:cover;">
                <div class="details">
                    <h4>Tailored Evening Blazer</h4>
                    <p class="price">$299.00</p>
                </div>
            </div>
            <div class="product-card">
                <img src="assets/2.jpg" alt="Navy Wool Chinos" style="width:100%; height:380px; object-fit:cover;">
                <div class="details">
                    <h4>Navy Wool Chinos</h4>
                    <p class="price">$145.00</p>
                </div>
            </div>
            <div class="product-card">
                <img src="assets/3.jpg" alt="Limited Edition Cashmere Scarf" style="width:100%; height:380px; object-fit:cover;">
                <div class="details">
                    <h4>Limited Edition Cashmere Scarf</h4>
                    <p class="price">$85.00</p>
                </div>
            </div>
            <div class="product-card">
                <div class="img-placeholder" style="background:#d9d9d9"></div>
                <div class="details">
                    <h4>Leather Chelsea Boots</h4>
                    <p class="price">$220.00</p>
                </div>
            </div>
        </div>
    </div>

    <footer>
        <p>&copy; 2026 BLUEMOON FASHION. ALL RIGHTS RESERVED.</p>
    </footer>
</body>
</html>
