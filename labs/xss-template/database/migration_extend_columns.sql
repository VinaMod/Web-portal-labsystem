-- Migration script: Tăng độ dài các cột display_name, display_email, title
-- Chạy script này để tăng độ dài các cột đã tồn tại trong database

USE xss_02_lab;

-- Tăng độ dài cột display_name từ VARCHAR(100) lên VARCHAR(255)
ALTER TABLE comments MODIFY COLUMN display_name VARCHAR(255);

-- Tăng độ dài cột display_email từ VARCHAR(100) lên VARCHAR(255)
ALTER TABLE comments MODIFY COLUMN display_email VARCHAR(255);

-- Tăng độ dài cột title từ VARCHAR(200) lên VARCHAR(500)
ALTER TABLE comments MODIFY COLUMN title VARCHAR(500);

