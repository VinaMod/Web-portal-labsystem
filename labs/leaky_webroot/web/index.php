<?php session_start(); ?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BlueMoon Fashion | Premium Men's Collection</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&family=Playfair+Display:wght@700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #1a1a1a;
            --accent: #c5a059;
            --text-light: #f4f4f4;
            --text-dark: #333;
            --bg-light: #ffffff;
            --bg-gray: #f8f8f8;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', sans-serif; background-color: var(--bg-light); color: var(--text-dark); line-height: 1.6; overflow-x: hidden; }

        header {
            position: absolute;
            top: 0;
            width: 100%;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 2rem 5%;
            z-index: 100;
            background: linear-gradient(to bottom, rgba(0,0,0,0.5), transparent);
        }

        .logo {
            font-family: 'Playfair Display', serif;
            font-size: 1.8rem;
            color: white;
            letter-spacing: 2px;
            text-transform: uppercase;
        }

        nav a {
            color: white;
            margin-left: 2rem;
            text-decoration: none;
            font-weight: 500;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            transition: color 0.3s;
        }

        nav a:hover { color: var(--accent); }

        .hero {
            height: 100vh;
            background: linear-gradient(rgba(0,0,0,0.4), rgba(0,0,0,0.4)), url('assets/hero.jpg') center/cover no-repeat;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            color: white;
        }

        .hero h2 {
            font-family: 'Playfair Display', serif;
            font-size: 4rem;
            margin-bottom: 1rem;
            opacity: 0;
            transform: translateY(30px);
            animation: fadeIn 1s forwards 0.5s;
        }

        .hero p {
            font-size: 1.2rem;
            max-width: 600px;
            margin-bottom: 2rem;
            font-weight: 300;
            opacity: 0;
            transform: translateY(30px);
            animation: fadeIn 1s forwards 0.7s;
        }

        .cta-btn {
            padding: 1rem 2.5rem;
            background-color: var(--accent);
            color: white;
            text-decoration: none;
            text-transform: uppercase;
            letter-spacing: 2px;
            font-weight: 600;
            transition: transform 0.3s, background 0.3s;
            opacity: 0;
            animation: fadeIn 1s forwards 0.9s;
        }

        .cta-btn:hover {
            transform: scale(1.05);
            background-color: #b38e4a;
        }

        .featured {
            padding: 100px 5%;
            background-color: var(--bg-gray);
            text-align: center;
        }

        .featured h3 {
            font-family: 'Playfair Display', serif;
            font-size: 2.5rem;
            margin-bottom: 3rem;
        }

        .product-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 2rem;
        }

        .product-card {
            background: white;
            padding: 20px;
            border-radius: 0;
            box-shadow: 0 10px 30px rgba(0,0,0,0.05);
            transition: transform 0.3s;
        }

        .product-card:hover { transform: translateY(-10px); }

        .product-card h4 { margin: 15px 0 5px; font-weight: 600; }
        .product-card p { color: #888; font-size: 0.9rem; }

        footer {
            background: var(--primary);
            color: rgba(255,255,255,0.5);
            padding: 50px 5%;
            text-align: center;
            font-size: 0.8rem;
            letter-spacing: 1px;
        }

        @keyframes fadeIn {
            to { opacity: 1; transform: translateY(0); }
        }

        @media (max-width: 768px) {
            .hero h2 { font-size: 2.5rem; }
            header { flex-direction: column; gap: 1rem; }
            nav a { margin: 0 0.5rem; font-size: 0.7rem; }
        }
    </style>
</head>
<body>
    <header>
        <div class="logo">BlueMoon</div>
        <nav>
            <a href="index.php">Home</a>
            <a href="products.php">Collection</a>
            <a href="#">Stories</a>
        </nav>
    </header>

    <div class="hero">
        <h2>Elegance in Every Stitch</h2>
        <p>Curated premium menswear for the modern gentleman who values sophistication and quality above all else.</p>
        <a href="products.php" class="cta-btn">Explore Collection</a>
    </div>

    <section class="featured">
        <h3>Season's Essentials</h3>
        <div class="product-grid">
            <div class="product-card">
                <img src="assets/1.jpg" alt="Tailored Evening Blazer" style="width:100%; height:300px; object-fit:cover; margin-bottom:15px;">
                <h4>Tailored Evening Blazer</h4>
                <p>Starting from $299</p>
            </div>
            <div class="product-card">
                <img src="assets/2.jpg" alt="Classic Oxford Footwear" style="width:100%; height:300px; object-fit:cover; margin-bottom:15px;">
                <h4>Classic Oxford Footwear</h4>
                <p>Premium Leather - $189</p>
            </div>
            <div class="product-card">
                <img src="assets/3.jpg" alt="Minimalist Tech Bag" style="width:100%; height:300px; object-fit:cover; margin-bottom:15px;">
                <h4>Minimalist Tech Bag</h4>
                <p>Limited Edition - $245</p>
            </div>
        </div>
    </section>

    <footer>
        <p>&copy; 2026 BLUEMOON FASHION. ALL RIGHTS RESERVED.</p>
        <p style="margin-top: 10px;">PRIVACY POLICY | TERMS OF SERVICE</p>
    </footer>
</body>
</html>
