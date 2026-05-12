-- Ensure connection uses UTF-8 during import
SET NAMES utf8mb4;

-- Tạo database
CREATE DATABASE IF NOT EXISTS sqli_01_lab CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE sqli_01_lab;

-- Đảm bảo database dùng utf8mb4
ALTER DATABASE sqli_01_lab CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Bảng flags (chứa FLAG cho SQLi challenge)
CREATE TABLE flags (
    id INT AUTO_INCREMENT PRIMARY KEY,
    flag_name VARCHAR(50) NOT NULL,
    flag_value VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Bảng users
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('user', 'admin', 'librarian') DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Bảng categories (thể loại sách)
CREATE TABLE categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Bảng publishers (nhà xuất bản)
CREATE TABLE publishers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    address TEXT,
    phone VARCHAR(20),
    email VARCHAR(100),
    website VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Bảng authors (tác giả)
CREATE TABLE authors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    biography TEXT,
    birth_year INT,
    nationality VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Bảng books (sách)
CREATE TABLE books (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    isbn VARCHAR(20) UNIQUE,
    author_id INT NOT NULL,
    publisher_id INT NOT NULL,
    category_id INT NOT NULL,
    publication_year INT,
    pages INT,
    price DECIMAL(10,2),
    stock_quantity INT DEFAULT 0,
    description TEXT,
    cover_image VARCHAR(255),
    language VARCHAR(50) DEFAULT 'Vietnamese',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (author_id) REFERENCES authors(id) ON DELETE CASCADE,
    FOREIGN KEY (publisher_id) REFERENCES publishers(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Bảng reviews (đánh giá sách)
CREATE TABLE reviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    book_id INT NOT NULL,
    user_id INT NOT NULL,
    rating INT CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Bảng sessions
CREATE TABLE sessions (
    id VARCHAR(128) PRIMARY KEY,
    user_id INT NOT NULL,
    data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert dữ liệu mẫu

-- FLAGS sẽ được insert động bởi docker-entrypoint.sh
-- FLAG1: Dynamic SQLi Challenge Flag
-- FLAG2: Dynamic RCE Challenge Flag (trong /var/www/html/flag.txt)


INSERT INTO users (username, name, email, password, role) VALUES 
('admin', 'Quản trị viên', 'admin@bookstore.com', MD5('admin123'), 'admin'),
('librarian', 'Thủ thư', 'librarian@bookstore.com', MD5('lib123'), 'librarian'),
('user1', 'Nguyễn Văn A', 'user1@example.com', MD5('user123'), 'user'),
('user2', 'Trần Thị B', 'user2@example.com', MD5('user123'), 'user'),
('user3', 'Lê Hoàng C', 'user3@example.com', MD5('user123'), 'user');

INSERT INTO categories (name, description) VALUES 
('Văn học', 'Sách văn học trong và ngoài nước'),
('Khoa học', 'Sách khoa học và công nghệ'),
('Lịch sử', 'Sách lịch sử và nhân vật lịch sử'),
('Kinh tế', 'Sách về kinh tế và quản lý'),
('Giáo dục', 'Sách giáo khoa và tham khảo'),
('Thiếu nhi', 'Sách dành cho trẻ em'),
('Tâm lý', 'Sách tâm lý học và phát triển bản thân'),
('Công nghệ', 'Sách về công nghệ thông tin');

INSERT INTO publishers (name, address, phone, email, website) VALUES 
('NXB Trẻ', '161B Lý Chính Thắng, Q.3, TP.HCM', '028-39316211', 'info@nxbtre.com.vn', 'https://www.nxbtre.com.vn'),
('NXB Kim Đồng', '55 Quang Trung, Hai Bà Trưng, Hà Nội', '024-39434730', 'kimdong@nxbkimdong.com.vn', 'https://nxbkimdong.com.vn'),
('NXB Giáo dục', '81 Trần Hưng Đạo, Hoàn Kiếm, Hà Nội', '024-38220801', 'nxbgd@moet.gov.vn', 'https://nxbgiaoduc.vn'),
('NXB Lao động', '175 Giảng Võ, Ba Đình, Hà Nội', '024-38515380', 'nxblaodong@gmail.com', 'https://nxblaodong.vn'),
('NXB Thanh niên', '64 Bà Triệu, Hoàn Kiếm, Hà Nội', '024-39434167', 'nxbthanhnien@hn.vnn.vn', 'https://nxbthanhnien.vn'),
('Penguin Random House', 'New York, USA', '+1-212-782-9000', 'info@penguinrandomhouse.com', 'https://www.penguinrandomhouse.com'),
('O\'Reilly Media', 'Sebastopol, CA, USA', '+1-707-827-7000', 'info@oreilly.com', 'https://www.oreilly.com');

INSERT INTO authors (name, biography, birth_year, nationality) VALUES 
('Nguyễn Nhật Ánh', 'Nhà văn nổi tiếng của Việt Nam, tác giả nhiều tác phẩm văn học thiếu nhi', 1955, 'Việt Nam'),
('Tô Hoài', 'Nhà văn Việt Nam, tác giả "Dế Mèn phiêu lưu ký"', 1920, 'Việt Nam'),
('Nam Cao', 'Nhà văn hiện thực Việt Nam', 1915, 'Việt Nam'),
('J.K. Rowling', 'Tác giả series Harry Potter', 1965, 'Anh'),
('Stephen King', 'Nhà văn kinh dị nổi tiếng', 1947, 'Mỹ'),
('Haruki Murakami', 'Nhà văn Nhật Bản đương đại', 1949, 'Nhật Bản'),
('Robert C. Martin', 'Kỹ sư phần mềm và tác giả sách lập trình', 1952, 'Mỹ'),
('Douglas Crockford', 'Nhà phát triển JavaScript', 1955, 'Mỹ'),
('Dale Carnegie', 'Tác giả sách self-help nổi tiếng', 1888, 'Mỹ'),
('Paulo Coelho', 'Nhà văn Brazil', 1947, 'Brazil');

INSERT INTO books (title, isbn, author_id, publisher_id, category_id, publication_year, pages, price, stock_quantity, description, language) VALUES 
('Mắt Biếc', '978-604-1-00001-1', 1, 1, 1, 2019, 280, 89000, 50, 'Tiểu thuyết nổi tiếng của Nguyễn Nhật Ánh', 'Vietnamese'),
('Tôi Thấy Hoa Vàng Trên Cỏ Xanh', '978-604-1-00002-2', 1, 1, 1, 2018, 320, 95000, 35, 'Câu chuyện tuổi thơ đầy cảm động', 'Vietnamese'),
('Dế Mèn Phiêu Lưu Ký', '978-604-1-00003-3', 2, 2, 6, 2020, 200, 65000, 80, 'Tác phẩm kinh điển văn học thiếu nhi Việt Nam', 'Vietnamese'),
('Chí Phèo', '978-604-1-00004-4', 3, 3, 1, 2021, 150, 45000, 60, 'Truyện ngắn nổi tiếng của Nam Cao', 'Vietnamese'),
('Harry Potter và Hòn đá Phù thủy', '978-604-1-00005-5', 4, 1, 6, 2020, 350, 120000, 40, 'Cuốn sách đầu tiên trong series Harry Potter', 'Vietnamese'),
('The Shining', '978-604-1-00006-6', 5, 6, 1, 2019, 450, 180000, 25, 'Tiểu thuyết kinh dị nổi tiếng của Stephen King', 'English'),
('Norwegian Wood', '978-604-1-00007-7', 6, 1, 1, 2021, 380, 150000, 30, 'Tiểu thuyết lãng mạn của Haruki Murakami', 'Vietnamese'),
('Clean Code', '978-604-1-00008-8', 7, 7, 8, 2020, 464, 450000, 20, 'Sách hướng dẫn viết code sạch', 'English'),
('JavaScript: The Good Parts', '978-604-1-00009-9', 8, 7, 8, 2018, 176, 350000, 15, 'Sách về JavaScript căn bản', 'English'),
('How to Win Friends and Influence People', '978-604-1-00010-0', 9, 6, 7, 2019, 288, 200000, 45, 'Sách kỹ năng giao tiếp nổi tiếng', 'English'),
('The Alchemist', '978-604-1-00011-1', 10, 6, 1, 2020, 163, 120000, 55, 'Tiểu thuyết triết học của Paulo Coelho', 'English'),
('Toán học cao cấp', '978-604-1-00012-2', 3, 3, 5, 2021, 500, 180000, 100, 'Sách giáo khoa toán học đại học', 'Vietnamese'),
('Lịch sử Việt Nam', '978-604-1-00013-3', 2, 3, 3, 2020, 600, 220000, 75, 'Sách lịch sử Việt Nam từ cổ đại đến hiện đại', 'Vietnamese'),
('Kinh tế học vi mô', '978-604-1-00014-4', 1, 4, 4, 2019, 400, 280000, 40, 'Giáo trình kinh tế học cơ bản', 'Vietnamese'),
('Tâm lý học đại cương', '978-604-1-00015-5', 4, 5, 7, 2021, 350, 190000, 65, 'Sách giáo khoa tâm lý học', 'Vietnamese');

INSERT INTO reviews (book_id, user_id, rating, comment) VALUES 
(1, 3, 5, 'Cuốn sách rất hay, cảm động và ý nghĩa'),
(1, 4, 4, 'Văn phong Nguyễn Nhật Ánh luôn cuốn hút'),
(2, 3, 5, 'Hồi ức tuổi thơ đẹp đẽ'),
(3, 4, 5, 'Sách thiếu nhi kinh điển, con em rất thích'),
(5, 3, 5, 'Harry Potter là series tuyệt vời nhất'),
(8, 4, 4, 'Sách rất hữu ích cho lập trình viên'),
(9, 3, 3, 'Hơi khó hiểu với người mới bắt đầu'),
(10, 4, 5, 'Sách kỹ năng sống rất thiết thực');
