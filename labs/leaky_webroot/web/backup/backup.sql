-- Database Backup for BlueMoon Fashion
-- Date: 2026-03-01

CREATE TABLE users (
    id INT PRIMARY KEY,
    username VARCHAR(50),
    password VARCHAR(100)
);

INSERT INTO users VALUES (1, 'admin', '5f4dcc3b5aa765d61d8327deb882cf99');
