-- Create database for Lab Management System
CREATE DATABASE IF NOT EXISTS lab_management 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

-- Use the database
USE lab_management;

-- Grant privileges (if needed)
GRANT ALL PRIVILEGES ON lab_management.* TO 'labtainer'@'localhost';
FLUSH PRIVILEGES;

-- Database is now ready for Flask-Migrate to create tables
