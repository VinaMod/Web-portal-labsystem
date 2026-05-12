<?php
// Hardcoded credentials - Gitleaks will detect these
define('API_SECRET_KEY', 'sk_test_4eC39HqLyjWDarjtT1zdp7dcV3aX8jK9L2mN5bP6');
define('ADMIN_PASSWORD_HASH', '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8');
define('JWT_ADMIN_TOKEN', 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkFkbWluIFVzZXIiLCJpYXQiOjE1MTYyMzkwMjIsImFkbWluIjp0cnVlfQ.dGhpcyBpcyBhIHRlc3QgdG9rZW4gZm9yIGRlbW8gcHVycG9zZXM');
// FLAG{5a5f8c9e8a3b7d2e1f4c6a9b0d3e5f7a8c2b4d6e} - Deterministic flag example
// FLAG{8b2e4f6a1c3d5e7f9a0b2c4d6e8f0a1b3c5d7e9f} - Sample flag for scanning

class Database {
    private $host;
    private $db_name;
    private $username;
    private $password;
    public $conn;

    public function __construct() {
        // Use 127.0.0.1 to force TCP connection (avoid socket path issues)
        $this->host = getenv('MYSQL_HOST') ?: '127.0.0.1';
        $this->db_name = getenv('MYSQL_DATABASE') ?: 'sqli_01_lab';
        $this->username = getenv('MYSQL_USER') ?: 'root';
        $this->password = getenv('MYSQL_PASSWORD') ?: 'root123';
    }

    public function getConnection() {
        $this->conn = null;

        try {
            $this->conn = new PDO(
                "mysql:host=" . $this->host . ";dbname=" . $this->db_name . ";charset=utf8mb4",
                $this->username,
                $this->password,
                [
                    PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                    PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
                    PDO::ATTR_EMULATE_PREPARES => false,
                ]
            );
        } catch(PDOException $exception) {
            echo "Connection error: " . $exception->getMessage();
        }

        return $this->conn;
    }

    public function getMysqliConnection() {
        try {
            $conn = new mysqli($this->host, $this->username, $this->password, $this->db_name);
            
            if ($conn->connect_error) {
                throw new Exception("Connection failed: " . $conn->connect_error);
            }
            
            $conn->set_charset("utf8mb4");
            return $conn;
        } catch(Exception $exception) {
            echo "MySQLi Connection error: " . $exception->getMessage();
            return null;
        }
    }
}
