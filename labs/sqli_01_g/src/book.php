<?php
header('Content-Type: text/html; charset=UTF-8');
require_once 'config/database.php';
require_once 'config/session.php';

$book_id = isset($_GET['id']) ? (int)$_GET['id'] : 0;

$database = new Database();
$db = $database->getConnection();

// Lấy thông tin sách
$query = "SELECT b.*, a.name as author_name, a.biography, a.birth_year, a.nationality,
                 p.name as publisher_name, p.address as publisher_address, 
                 c.name as category_name, c.description as category_description
          FROM books b 
          JOIN authors a ON b.author_id = a.id 
          JOIN publishers p ON b.publisher_id = p.id 
          JOIN categories c ON b.category_id = c.id 
          WHERE b.id = ?";
$stmt = $db->prepare($query);
$stmt->execute([$book_id]);
$book = $stmt->fetch(PDO::FETCH_ASSOC);

if (!$book) {
    header('Location: index.php?error=book_not_found');
    exit();
}

// Lấy reviews của sách
$reviews_query = "SELECT r.*, u.name as user_name, u.username 
                  FROM reviews r 
                  JOIN users u ON r.user_id = u.id 
                  WHERE r.book_id = ? 
                  ORDER BY r.created_at DESC";
$reviews_stmt = $db->prepare($reviews_query);
$reviews_stmt->execute([$book_id]);
$reviews = $reviews_stmt->fetchAll(PDO::FETCH_ASSOC);

// Tính rating trung bình
$avg_rating = 0;
if (!empty($reviews)) {
    $total_rating = array_sum(array_column($reviews, 'rating'));
    $avg_rating = round($total_rating / count($reviews), 1);
}
?>

<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title><?php echo htmlspecialchars($book['title']); ?> - Book Management</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="index.php">
                <i class="fas fa-book"></i> Book Management
            </a>
            <div class="navbar-nav ms-auto">
                <span class="navbar-text me-3">
                    <i class="fas fa-flag"></i> Challenge: Tìm FLAGS trong database!
                </span>
                <span class="navbar-text">
                    <i class="fas fa-database"></i> BookStore
                </span>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <nav aria-label="breadcrumb">
            <ol class="breadcrumb">
                <li class="breadcrumb-item"><a href="index.php">Trang chủ</a></li>
                <li class="breadcrumb-item active"><?php echo htmlspecialchars($book['title']); ?></li>
            </ol>
        </nav>

        <div class="row">
            <div class="col-md-8">
                <div class="card">
                    <div class="card-body">
                        <h1><?php echo htmlspecialchars($book['title']); ?></h1>
                        
                        <div class="row mb-3">
                            <div class="col-md-6">
                                <p><strong><i class="fas fa-user"></i> Tác giả:</strong> <?php echo htmlspecialchars($book['author_name']); ?></p>
                                <p><strong><i class="fas fa-building"></i> Nhà xuất bản:</strong> <?php echo htmlspecialchars($book['publisher_name']); ?></p>
                                <p><strong><i class="fas fa-tags"></i> Thể loại:</strong> <?php echo htmlspecialchars($book['category_name']); ?></p>
                                <p><strong><i class="fas fa-calendar"></i> Năm xuất bản:</strong> <?php echo htmlspecialchars($book['publication_year']); ?></p>
                            </div>
                            <div class="col-md-6">
                                <p><strong><i class="fas fa-barcode"></i> ISBN:</strong> <?php echo htmlspecialchars($book['isbn']); ?></p>
                                <p><strong><i class="fas fa-language"></i> Ngôn ngữ:</strong> <?php echo htmlspecialchars($book['language']); ?></p>
                                <p><strong><i class="fas fa-file-alt"></i> Số trang:</strong> <?php echo htmlspecialchars($book['pages']); ?></p>
                                <?php if ($book['price']): ?>
                                <p><strong class="text-danger"><i class="fas fa-dollar-sign"></i> Giá: <?php echo number_format($book['price']); ?> VND</strong></p>
                                <?php endif; ?>
                            </div>
                        </div>

                        <?php if ($book['description']): ?>
                        <div class="mb-3">
                            <h5>Mô tả:</h5>
                            <p><?php echo nl2br(htmlspecialchars($book['description'])); ?></p>
                        </div>
                        <?php endif; ?>

                        <div class="mb-3">
                            <h5>Đánh giá: 
                                <span class="text-warning">
                                    <?php for ($i = 1; $i <= 5; $i++): ?>
                                        <?php if ($i <= $avg_rating): ?>
                                            <i class="fas fa-star"></i>
                                        <?php else: ?>
                                            <i class="far fa-star"></i>
                                        <?php endif; ?>
                                    <?php endfor; ?>
                                    (<?php echo $avg_rating; ?>/5 - <?php echo count($reviews); ?> đánh giá)
                                </span>
                            </h5>
                        </div>
                    </div>
                </div>

                <!-- Reviews Section -->
                <div class="card mt-4">
                    <div class="card-header">
                        <h5><i class="fas fa-comments"></i> Đánh giá từ độc giả</h5>
                    </div>
                    <div class="card-body">
                        <?php if (empty($reviews)): ?>
                        <p class="text-muted">Chưa có đánh giá nào cho cuốn sách này.</p>
                        <?php else: ?>
                            <?php foreach ($reviews as $review): ?>
                            <div class="border-bottom pb-3 mb-3">
                                <div class="d-flex justify-content-between">
                                    <div>
                                        <strong><?php echo htmlspecialchars($review['user_name']); ?></strong>
                                        <small class="text-muted">(@<?php echo htmlspecialchars($review['username']); ?>)</small>
                                    </div>
                                    <small class="text-muted"><?php echo $review['created_at']; ?></small>
                                </div>
                                <div class="mt-1">
                                    <span class="text-warning">
                                        <?php for ($i = 1; $i <= 5; $i++): ?>
                                            <?php if ($i <= $review['rating']): ?>
                                                <i class="fas fa-star"></i>
                                            <?php else: ?>
                                                <i class="far fa-star"></i>
                                            <?php endif; ?>
                                        <?php endfor; ?>
                                    </span>
                                </div>
                                <?php if ($review['comment']): ?>
                                <p class="mt-2 mb-0"><?php echo nl2br(htmlspecialchars($review['comment'])); ?></p>
                                <?php endif; ?>
                            </div>
                            <?php endforeach; ?>
                        <?php endif; ?>
                    </div>
                </div>
            </div>

            <div class="col-md-4">
                <!-- Author Info -->
                <div class="card">
                    <div class="card-header">
                        <h6><i class="fas fa-user-edit"></i> Thông tin tác giả</h6>
                    </div>
                    <div class="card-body">
                        <h6><?php echo htmlspecialchars($book['author_name']); ?></h6>
                        <?php if ($book['nationality']): ?>
                        <p><strong>Quốc tịch:</strong> <?php echo htmlspecialchars($book['nationality']); ?></p>
                        <?php endif; ?>
                        <?php if ($book['birth_year']): ?>
                        <p><strong>Năm sinh:</strong> <?php echo htmlspecialchars($book['birth_year']); ?></p>
                        <?php endif; ?>
                        <?php if ($book['biography']): ?>
                        <p><?php echo nl2br(htmlspecialchars($book['biography'])); ?></p>
                        <?php endif; ?>
                    </div>
                </div>

                <!-- Publisher Info -->
                <div class="card mt-3">
                    <div class="card-header">
                        <h6><i class="fas fa-building"></i> Nhà xuất bản</h6>
                    </div>
                    <div class="card-body">
                        <h6><?php echo htmlspecialchars($book['publisher_name']); ?></h6>
                        <?php if ($book['publisher_address']): ?>
                        <p><strong>Địa chỉ:</strong> <?php echo htmlspecialchars($book['publisher_address']); ?></p>
                        <?php endif; ?>
                    </div>
                </div>

                <!-- Back to Search -->
                <div class="card mt-3">
                    <div class="card-body text-center">
                        <a href="index.php" class="btn btn-primary">
                            <i class="fas fa-search"></i> Tìm sách khác
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <footer class="bg-dark text-light text-center py-3 mt-5">
        <div class="container">
            <p>&copy; 2025 Book Management System. </p>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
