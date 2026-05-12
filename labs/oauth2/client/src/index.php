<?php
session_start();
$provider_url = getenv('PROVIDER_URL');
$client_id = getenv('CLIENT_ID');
$redirect_uri = getenv('REDIRECT_URI');

// Build Login URL
$login_url = "$provider_url/auth?response_type=code&client_id=$client_id&redirect_uri=$redirect_uri&scope=profile";

// Dummy Data for Gallery
$public_photos = [
    ['url' => 'https://picsum.photos/id/101/400/300', 'title' => 'Mountain View', 'user' => 'nature_lover'],
    ['url' => 'https://picsum.photos/id/102/400/300', 'title' => 'Summer Vibes', 'user' => 'sunny_girl'],
    ['url' => 'https://picsum.photos/id/103/400/300', 'title' => 'Urban Life', 'user' => 'city_walker'],
    ['url' => 'https://picsum.photos/id/104/400/300', 'title' => 'Morning Coffee', 'user' => 'barista_daily'],
];

$private_photos = [
    ['url' => 'https://picsum.photos/id/201/400/300', 'title' => 'Secret Project A', 'tag' => 'Private'],
    ['url' => 'https://picsum.photos/id/202/400/300', 'title' => 'Family Trip 2024', 'tag' => 'Private'],
    ['url' => 'https://picsum.photos/id/203/400/300', 'title' => 'Draft Designs', 'tag' => 'Work'],
];
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PhotoApp - Share Your World</title>
    <link rel="stylesheet" href="style.css">
    <!-- FontAwesome for Icons -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body>

    <!-- Navbar -->
    <nav class="navbar">
        <a href="/" class="logo"><i class="fas fa-camera-retro"></i> PhotoApp</a>
        <div class="nav-links">
            <a href="#" class="nav-item">Explore</a>
            <a href="#" class="nav-item">Creators</a>
            <?php if (isset($_SESSION['user'])): ?>
                <a href="logout.php" class="btn btn-outline btn-sm">Sign Out</a>
            <?php else: ?>
                <a href="<?php echo $login_url; ?>" class="btn btn-primary">Login with SocialID</a>
            <?php endif; ?>
        </div>
    </nav>

    <!-- Main Content -->
    <div class="container">
        
        <?php if (!isset($_SESSION['user'])): ?>
            <!-- Hero Section (Visitor) -->
            <section class="hero">
                <h1>Capture & Share Your Moments</h1>
                <p>Join millions of creators sharing their visual stories with the world. Fast, secure, and beautiful.</p>
                <div style="margin-top: 2rem;">
                    <a href="<?php echo $login_url; ?>" class="btn btn-primary btn-lg">
                        <i class="fab fa-connectdevelop"></i> Connect with SocialID
                    </a>
                    <a href="#" class="btn btn-outline btn-lg" style="margin-left: 1rem;">Learn More</a>
                </div>
            </section>
        <?php endif; ?>

        <?php if (isset($_SESSION['user'])): ?>
            <!-- User Dashboard (Logged In) -->
            <div class="profile-section">
                <div class="profile-info">
                    <h2>Welcome back, <?php echo htmlspecialchars($_SESSION['user']['name']); ?>!</h2>
                    <p style="color: var(--text-muted); margin-bottom: 0.5rem;">
                        <i class="fas fa-user-circle"></i> <?php echo htmlspecialchars($_SESSION['user']['role']); ?> Account
                        <span class="profile-role-badge"><?php echo htmlspecialchars(strtoupper($_SESSION['user']['role'])); ?></span>
                    </p>
                    <p style="font-size: 0.9rem; color: #64748b;">Member since 2023</p>
                </div>
                <div class="profile-actions">
                    <?php if ($_SESSION['user']['role'] === 'admin'): ?>
                        <a href="admin.php" class="btn btn-danger">
                            <i class="fas fa-shield-alt"></i> Admin Dashboard
                        </a>
                    <?php endif; ?>
                    <button class="btn btn-primary">
                        <i class="fas fa-cloud-upload-alt"></i> Upload Photo
                    </button>
                </div>
            </div>

            <!-- Private Gallery -->
            <h3 style="border-bottom: 1px solid var(--border); padding-bottom: 1rem; margin-top: 3rem;">
                <i class="fas fa-lock"></i> Your Private Gallery
            </h3>
            <div class="gallery-grid">
                <?php foreach ($private_photos as $photo): ?>
                    <div class="photo-card">
                        <img src="<?php echo $photo['url']; ?>" alt="Photo" class="photo-img">
                        <div class="photo-info">
                            <span class="photo-title"><?php echo $photo['title']; ?></span>
                            <div class="photo-meta">
                                <span><i class="fas fa-tag"></i> <?php echo $photo['tag']; ?></span>
                                <span>Just now</span>
                            </div>
                        </div>
                    </div>
                <?php endforeach; ?>
                <!-- Add placeholder for "Add New" -->
                 <div class="photo-card" style="display: flex; align-items: center; justify-content: center; background: rgba(255,255,255,0.02); border: 2px dashed var(--border); cursor: pointer;">
                    <div style="text-align: center; color: var(--text-muted);">
                        <i class="fas fa-plus-circle" style="font-size: 2rem; margin-bottom: 0.5rem;"></i>
                        <p>Add New</p>
                    </div>
                </div>
            </div>
        <?php endif; ?>

        <!-- Public Showcase (Always Visible) -->
        <h3 style="border-bottom: 1px solid var(--border); padding-bottom: 1rem; margin-top: 4rem;">
            <i class="fas fa-globe-americas"></i> Trending Now
        </h3>
        <div class="gallery-grid">
            <?php foreach ($public_photos as $photo): ?>
                <div class="photo-card">
                    <img src="<?php echo $photo['url']; ?>" alt="Photo" class="photo-img">
                    <div class="photo-info">
                        <span class="photo-title"><?php echo $photo['title']; ?></span>
                        <div class="photo-meta">
                            <span>by @<?php echo $photo['user']; ?></span>
                            <span><i class="fas fa-heart" style="color: #ef4444;"></i> <?php echo rand(100, 999); ?></span>
                        </div>
                    </div>
                </div>
            <?php endforeach; ?>
        </div>
    </div>

    <!-- Footer -->
    <footer class="footer">
        <p style="font-size: 0.9rem;">
            Found a vulnerability? <a href="report.php"><i class="fas fa-bug"></i> Report a Bug</a> to our security team.
        </p>
    </footer>

</body>
</html>
