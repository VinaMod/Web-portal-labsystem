<?php
session_start();

// Hàm kiểm tra đăng nhập
function isLoggedIn() {
    return isset($_SESSION['user_id']);
}

// Hàm kiểm tra quyền admin
function isAdmin() {
    return isset($_SESSION['role']) && $_SESSION['role'] === 'admin';
}

// Hàm đăng xuất
function logout() {
    session_destroy();
    header('Location: index.php');
    exit();
}

// Hàm bảo vệ trang (yêu cầu đăng nhập)
function requireLogin() {
    if (!isLoggedIn()) {
        header('Location: login.php');
        exit();
    }
}

// Hàm bảo vệ trang admin
function requireAdmin() {
    requireLogin();
    if (!isAdmin()) {
        header('Location: index.php');
        exit();
    }
}
?>
