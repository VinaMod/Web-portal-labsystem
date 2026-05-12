<?php
header('Content-Type: text/html; charset=UTF-8');
require_once 'config/database.php';
require_once 'config/session.php';
require_once 'config/sqli_helper.php';

$database = new Database();
$db = $database->getConnection();
$mysqli = $database->getMysqliConnection();

// Lấy tham số tìm kiếm
$searchTitle = $_GET['title'] ?? '';
$searchAuthor = $_GET['author'] ?? '';
$searchPublisher = $_GET['publisher'] ?? '';
$searchCategory = $_GET['category'] ?? '';
$searchYear = $_GET['year'] ?? '';
$searchIsbn = $_GET['isbn'] ?? '';
$searchLanguage = $_GET['language'] ?? '';

// Base query - Chỉ SELECT các cột cần thiết để giảm số cột cho SQLi (7 cột thay vì 17)
$baseQuery = "SELECT b.id, b.title, b.isbn, b.publication_year, b.language, b.price, b.description,
              a.name as author_name, p.name as publisher_name, c.name as category_name 
              FROM books b 
              JOIN authors a ON b.author_id = a.id 
              JOIN publishers p ON b.publisher_id = p.id 
              JOIN categories c ON b.category_id = c.id 
              WHERE 1=1";

// Xây dựng query với SQLi vulnerability
$query = $baseQuery;

if (!empty($searchTitle)) {
    if (isSqliVulnerable('title')) {
        $query .= " AND b.title LIKE '%" . $searchTitle . "%'";
        logSqliAttempt('title', $searchTitle, true);
    } else {
        $stmt_title = $db->prepare("SELECT b.*, a.name as author_name, p.name as publisher_name, c.name as category_name 
                                   FROM books b 
                                   JOIN authors a ON b.author_id = a.id 
                                   JOIN publishers p ON b.publisher_id = p.id 
                                   JOIN categories c ON b.category_id = c.id 
                                   WHERE b.title LIKE ?");
        $searchTitleParam = "%$searchTitle%";
        logSqliAttempt('title', $searchTitle, false);
    }
}

if (!empty($searchAuthor)) {
    if (isSqliVulnerable('author')) {
        $query .= " AND a.name LIKE '%" . $searchAuthor . "%'";
        logSqliAttempt('author', $searchAuthor, true);
    } else {
        $escapedAuthor = mysqli_real_escape_string($mysqli, $searchAuthor);
        $query .= " AND a.name LIKE '%" . $escapedAuthor . "%'";
        logSqliAttempt('author', $searchAuthor, false);
    }
}

if (!empty($searchPublisher)) {
    if (isSqliVulnerable('publisher')) {
        $query .= " AND p.name LIKE '%" . $searchPublisher . "%'";
        logSqliAttempt('publisher', $searchPublisher, true);
    } else {
        $escapedPublisher = mysqli_real_escape_string($mysqli, $searchPublisher);
        $query .= " AND p.name LIKE '%" . $escapedPublisher . "%'";
        logSqliAttempt('publisher', $searchPublisher, false);
    }
}

if (!empty($searchCategory)) {
    if (isSqliVulnerable('category')) {
        $query .= " AND c.name LIKE '%" . $searchCategory . "%'";
        logSqliAttempt('category', $searchCategory, true);
    } else {
        $escapedCategory = mysqli_real_escape_string($mysqli, $searchCategory);
        $query .= " AND c.name LIKE '%" . $escapedCategory . "%'";
        logSqliAttempt('category', $searchCategory, false);
    }
}

if (!empty($searchYear)) {
    if (isSqliVulnerable('year')) {
        $query .= " AND b.publication_year = " . $searchYear;
        logSqliAttempt('year', $searchYear, true);
    } else {
        $escapedYear = mysqli_real_escape_string($mysqli, $searchYear);
        $query .= " AND b.publication_year = '" . $escapedYear . "'";
        logSqliAttempt('year', $searchYear, false);
    }
}

if (!empty($searchIsbn)) {
    if (isSqliVulnerable('isbn')) {
        $query .= " AND b.isbn LIKE '%" . $searchIsbn . "%'";
        logSqliAttempt('isbn', $searchIsbn, true);
    } else {
        $escapedIsbn = mysqli_real_escape_string($mysqli, $searchIsbn);
        $query .= " AND b.isbn LIKE '%" . $escapedIsbn . "%'";
        logSqliAttempt('isbn', $searchIsbn, false);
    }
}

if (!empty($searchLanguage)) {
    if (isSqliVulnerable('language')) {
        $query .= " AND b.language LIKE '%" . $searchLanguage . "%'";
        logSqliAttempt('language', $searchLanguage, true);
    } else {
        $escapedLanguage = mysqli_real_escape_string($mysqli, $searchLanguage);
        $query .= " AND b.language LIKE '%" . $escapedLanguage . "%'";
        logSqliAttempt('language', $searchLanguage, false);
    }
}

$query .= " ORDER BY b.created_at DESC LIMIT 50";

// Thực thi query
try {
    $result = $mysqli->query($query);
    $books = [];
    if ($result) {
        while ($row = $result->fetch_assoc()) {
            $books[] = $row;
        }
    }
} catch (Exception $e) {
    $books = [];
    $error_message = "Lỗi tìm kiếm: " . $e->getMessage();
}

// Lấy danh sách categories cho dropdown
$categories_query = "SELECT * FROM categories ORDER BY name";
$categories_result = $mysqli->query($categories_query);
$categories = [];
if ($categories_result) {
    while ($row = $categories_result->fetch_assoc()) {
        $categories[] = $row;
    }
}
?>

<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Book Management - Hệ thống quản lý sách</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .book-card {
            transition: transform 0.2s;
            height: 100%;
        }
        .book-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        .vulnerable-field {
            border: 2px solid #dc3545 !important;
            background-color: #fff5f5 !important;
        }
        .safe-field {
            border: 2px solid #28a745 !important;
            background-color: #f8fff8 !important;
        }
        .sqli-info {
            background: linear-gradient(45deg, #ff6b6b, #ee5a24);
            color: white;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="index.php">
                <i class="fas fa-book"></i> Book Management
            </a>
            <div class="navbar-nav ms-auto">
                <span class="navbar-text me-3">
                    <i class="fas fa-server text-success"></i> <strong>Book Management System</strong>
                </span>
                <span class="navbar-text">
                    <i class="fas fa-database"></i> Find the FLAG!
                </span>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <!-- SQLi Challenge Info removed -->

        <!-- Search Form -->
        <div class="card mb-4">
            <div class="card-header">
                <h4><i class="fas fa-search"></i> Tìm kiếm sách</h4>
            </div>
            <div class="card-body">
                <form method="GET" action="">
                    <div class="row">
                        <div class="col-md-4 mb-3">
                            <label for="title" class="form-label">Tên sách:</label>
                            <input type="text" class="form-control" 
                                   id="title" name="title" value="<?php echo htmlspecialchars($searchTitle); ?>" 
                                   placeholder="Nhập tên sách...">

                        </div>
                        
                        <div class="col-md-4 mb-3">
                            <label for="author" class="form-label">Tác giả:</label>
                            <input type="text" class="form-control" 
                                   id="author" name="author" value="<?php echo htmlspecialchars($searchAuthor); ?>" 
                                   placeholder="Nhập tên tác giả...">

                        </div>
                        
                        <div class="col-md-4 mb-3">
                            <label for="publisher" class="form-label">Nhà xuất bản:</label>
                            <input type="text" class="form-control" 
                                   id="publisher" name="publisher" value="<?php echo htmlspecialchars($searchPublisher); ?>" 
                                   placeholder="Nhập nhà xuất bản...">

                        </div>
                    </div>
                    
                    <div class="row">
                        <div class="col-md-3 mb-3">
                            <label for="category" class="form-label">Thể loại:</label>
                            <select class="form-control" 
                                    id="category" name="category">
                                <option value="">-- Chọn thể loại --</option>
                                <?php foreach ($categories as $cat): ?>
                                    <option value="<?php echo htmlspecialchars($cat['name']); ?>" 
                                            <?php echo ($searchCategory === $cat['name']) ? 'selected' : ''; ?>>
                                        <?php echo htmlspecialchars($cat['name']); ?>
                                    </option>
                                <?php endforeach; ?>
                            </select>

                        </div>
                        
                        <div class="col-md-3 mb-3">
                            <label for="year" class="form-label">Năm xuất bản:</label>
                            <input type="number" class="form-control" 
                                   id="year" name="year" value="<?php echo htmlspecialchars($searchYear); ?>" 
                                   placeholder="2020" min="1900" max="2030">

                        </div>
                        
                        <div class="col-md-3 mb-3">
                            <label for="isbn" class="form-label">ISBN:</label>
                            <input type="text" class="form-control" 
                                   id="isbn" name="isbn" value="<?php echo htmlspecialchars($searchIsbn); ?>" 
                                   placeholder="978-604-1-00001-1">

                        </div>
                        
                        <div class="col-md-3 mb-3">
                            <label for="language" class="form-label">Ngôn ngữ:</label>
                            <select class="form-control" 
                                    id="language" name="language">
                                <option value="">-- Chọn ngôn ngữ --</option>
                                <option value="Vietnamese" <?php echo ($searchLanguage === 'Vietnamese') ? 'selected' : ''; ?>>Tiếng Việt</option>
                                <option value="English" <?php echo ($searchLanguage === 'English') ? 'selected' : ''; ?>>English</option>
                                <option value="French" <?php echo ($searchLanguage === 'French') ? 'selected' : ''; ?>>Français</option>
                                <option value="Japanese" <?php echo ($searchLanguage === 'Japanese') ? 'selected' : ''; ?>>日本語</option>
                            </select>

                        </div>
                    </div>
                    
                    <div class="d-flex gap-2">
                        <button type="submit" class="btn btn-primary">
                            <i class="fas fa-search"></i> Tìm kiếm
                        </button>
                        <a href="index.php" class="btn btn-secondary">
                            <i class="fas fa-redo"></i> Làm mới
                        </a>
                    </div>
                </form>
            </div>
        </div>

        <!-- Error Message -->
        <?php if (isset($error_message)): ?>
        <div class="alert alert-danger">
            <i class="fas fa-exclamation-triangle"></i> <?php echo htmlspecialchars($error_message); ?>
        </div>
        <?php endif; ?>

        <!-- Results -->
        <div class="row">
            <?php if (empty($books)): ?>
                <div class="col-12">
                    <div class="alert alert-info text-center">
                        <i class="fas fa-info-circle"></i> 
                        <?php echo empty(array_filter([$searchTitle, $searchAuthor, $searchPublisher, $searchCategory, $searchYear, $searchIsbn, $searchLanguage])) 
                            ? 'Sử dụng form tìm kiếm ở trên để tìm sách.' 
                            : 'Không tìm thấy sách nào phù hợp với tiêu chí tìm kiếm.'; ?>
                    </div>
                </div>
            <?php else: ?>
                <?php foreach ($books as $book): ?>
                <div class="col-md-4 mb-4">
                    <div class="card book-card">
                        <div class="card-body">
                            <h5 class="card-title"><?php echo htmlspecialchars($book['title']); ?></h5>
                            <p class="card-text">
                                <strong><i class="fas fa-user"></i> Tác giả:</strong> <?php echo htmlspecialchars($book['author_name']); ?><br>
                                <strong><i class="fas fa-building"></i> NXB:</strong> <?php echo htmlspecialchars($book['publisher_name']); ?><br>
                                <strong><i class="fas fa-tags"></i> Thể loại:</strong> <?php echo htmlspecialchars($book['category_name']); ?><br>
                                <strong><i class="fas fa-calendar"></i> Năm:</strong> <?php echo htmlspecialchars($book['publication_year']); ?><br>
                                <strong><i class="fas fa-barcode"></i> ISBN:</strong> <?php echo htmlspecialchars($book['isbn']); ?><br>
                                <strong><i class="fas fa-language"></i> Ngôn ngữ:</strong> <?php echo htmlspecialchars($book['language']); ?>
                            </p>
                            <?php if ($book['price']): ?>
                            <p class="card-text">
                                <strong class="text-danger"><i class="fas fa-dollar-sign"></i> Giá: <?php echo number_format($book['price']); ?> VND</strong>
                            </p>
                            <?php endif; ?>
                            <a href="book.php?id=<?php echo $book['id']; ?>" class="btn btn-primary">
                                <i class="fas fa-eye"></i> Xem chi tiết
                            </a>
                        </div>
                    </div>
                </div>
                <?php endforeach; ?>
            <?php endif; ?>
        </div>

        <!-- SQLi Examples removed -->
    </div>

    <footer class="bg-dark text-light text-center py-3 mt-5">
        <div class="container">
            <p>&copy; 2025 Book Management System.</p>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
