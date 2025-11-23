-- Ensure connection uses UTF-8 during import
SET NAMES utf8mb4;

-- Tạo database
CREATE DATABASE IF NOT EXISTS xss_02_lab CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE xss_02_lab;

-- Đảm bảo database dùng utf8mb4
ALTER DATABASE xss_02_lab CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;



-- Bảng users
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('user', 'admin') DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Bảng products
CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    image VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Bảng comments (có lỗ hổng XSS)
CREATE TABLE comments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    user_id INT NOT NULL,
    display_name VARCHAR(255),
    display_email VARCHAR(255),
    title VARCHAR(500),
    comment TEXT NOT NULL,
    rating INT DEFAULT 5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
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

-- Đảm bảo các bảng hiện có (nếu tồn tại từ trước) được chuyển sang utf8mb4
ALTER TABLE users CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE products CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE comments CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE sessions CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Thêm cột name vào bảng users nếu chưa có (migration)
SET @dbname = DATABASE();
SET @tablename = 'users';
SET @columnname = 'name';
SET @preparedStatement = (SELECT IF(
  (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE
      (TABLE_SCHEMA = @dbname)
      AND (TABLE_NAME = @tablename)
      AND (COLUMN_NAME = @columnname)
  ) > 0,
  'SELECT 1',
  CONCAT('ALTER TABLE ', @tablename, ' ADD COLUMN ', @columnname, ' VARCHAR(100) NOT NULL DEFAULT "" AFTER username')
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

-- Thêm cột display_name và display_email vào bảng comments nếu chưa có (migration)
SET @tablename = 'comments';
SET @columnname = 'display_name';
SET @preparedStatement = (SELECT IF(
  (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE
      (TABLE_SCHEMA = @dbname)
      AND (TABLE_NAME = @tablename)
      AND (COLUMN_NAME = @columnname)
  ) > 0,
  'SELECT 1',
  CONCAT('ALTER TABLE ', @tablename, ' ADD COLUMN ', @columnname, ' VARCHAR(255) AFTER user_id')
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

SET @columnname = 'display_email';
SET @preparedStatement = (SELECT IF(
  (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE
      (TABLE_SCHEMA = @dbname)
      AND (TABLE_NAME = @tablename)
      AND (COLUMN_NAME = @columnname)
  ) > 0,
  'SELECT 1',
  CONCAT('ALTER TABLE ', @tablename, ' ADD COLUMN ', @columnname, ' VARCHAR(255) AFTER display_name')
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

-- Thêm cột title và rating vào bảng comments nếu chưa có (migration)
SET @columnname = 'title';
SET @preparedStatement = (SELECT IF(
  (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE
      (TABLE_SCHEMA = @dbname)
      AND (TABLE_NAME = @tablename)
      AND (COLUMN_NAME = @columnname)
  ) > 0,
  'SELECT 1',
  CONCAT('ALTER TABLE ', @tablename, ' ADD COLUMN ', @columnname, ' VARCHAR(500) AFTER display_email')
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

SET @columnname = 'rating';
SET @preparedStatement = (SELECT IF(
  (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE
      (TABLE_SCHEMA = @dbname)
      AND (TABLE_NAME = @tablename)
      AND (COLUMN_NAME = @columnname)
  ) > 0,
  'SELECT 1',
  CONCAT('ALTER TABLE ', @tablename, ' ADD COLUMN ', @columnname, ' INT DEFAULT 5 AFTER comment')
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

-- Insert dữ liệu mẫu
INSERT INTO users (username, name, email, password, role) VALUES 
('admin', 'Quản trị viên', 'admin@example.com', MD5('qwertyuiop'), 'admin'),
('user1', 'Nguyễn Văn A', 'user1@example.com', MD5('user123'), 'user'),
('user2', 'Trần Thị B', 'user2@example.com', MD5('user123'), 'user');

INSERT INTO products (name, description, price, image) VALUES 
('iPhone 15 Pro', 'Apple iPhone 15 Pro với camera 48MP và chip A17 Pro', 999.99, 'iphone15.jpg'),
('Samsung Galaxy S24', 'Samsung Galaxy S24 với màn hình Dynamic AMOLED 2X', 899.99, 'galaxy_s24.jpg'),
('MacBook Pro M3', 'Apple MacBook Pro 14 inch với chip M3 Pro', 1999.99, 'macbook_pro.jpg'),
('Dell XPS 13', 'Dell XPS 13 với Intel Core i7 và màn hình 13.4 inch', 1299.99, 'dell_xps13.jpg');

INSERT INTO comments (product_id, user_id, display_name, display_email, title, comment, rating) VALUES 
(1, 2, 'Nguyễn Văn A', 'user1@example.com', 'Rất hài lòng', 'Sản phẩm rất tốt, camera chụp ảnh đẹp!', 5),
(1, 3, 'Trần Thị B', 'user2@example.com', 'Chất lượng tốt', 'Giá hơi cao nhưng chất lượng xứng đáng', 4),
(2, 2, 'Nguyễn Văn A', 'user1@example.com', 'Màn hình đẹp', 'Màn hình rất đẹp, pin trâu', 5),
(3, 3, 'Trần Thị B', 'user2@example.com', 'Hiệu năng mạnh', 'Hiệu năng mạnh mẽ, phù hợp cho công việc', 5);