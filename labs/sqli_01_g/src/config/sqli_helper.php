<?php
/**
 * Helper function để kiểm tra xem field nào bị lỗ hổng SQLi
 * Dựa vào biến môi trường SQLI_VULN_FIELD
 * 
 * @param string $field Field cần kiểm tra: 'title', 'author', 'publisher', 'category', 'year', 'isbn', 'language'
 * @return bool true nếu field này bị SQLi, false nếu an toàn
 */
function isSqliVulnerable($field) {
    $vulnField = getenv('SQLI_VULN_FIELD') ?: 'title';
    
    // Hỗ trợ backward compatibility với các giá trị nhóm
    $fieldMapping = [
        'book_info' => ['title', 'isbn', 'language', 'year'],
        'people' => ['author'],
        'publisher_info' => ['publisher'],
        'categories' => ['category'],
        'search_all' => ['title', 'author', 'publisher', 'category', 'year', 'isbn', 'language']
    ];
    
    // Nếu là giá trị nhóm, map sang các field cụ thể
    if (isset($fieldMapping[strtolower($vulnField)])) {
        return in_array(strtolower($field), array_map('strtolower', $fieldMapping[strtolower($vulnField)]));
    }
    
    // Mapping cho các field tương đương
    $fieldAliases = [
        'book' => ['title', 'isbn'],
        'book_title' => ['title'],
        'author_name' => ['author'],
        'publisher_name' => ['publisher'],
        'category_name' => ['category'],
        'publication_year' => ['year'],
        'book_language' => ['language']
    ];
    
    // Kiểm tra alias mapping
    if (isset($fieldAliases[strtolower($vulnField)])) {
        return in_array(strtolower($field), array_map('strtolower', $fieldAliases[strtolower($vulnField)]));
    }
    
    // So sánh trực tiếp với field cụ thể
    return strtolower($vulnField) === strtolower($field);
}

/**
 * Xây dựng query với SQLi protection dựa vào field
 * 
 * @param string $baseQuery Query cơ bản
 * @param string $field Field type cụ thể
 * @param string $value Giá trị tìm kiếm
 * @param mysqli $connection Database connection
 * @return string Query đã xử lý
 */
function buildSearchQuery($baseQuery, $field, $value, $connection) {
    if (empty($value)) {
        return $baseQuery;
    }
    
    if (isSqliVulnerable($field)) {
        // Không escape - có lỗ hổng SQLi
        return $baseQuery . " AND " . getFieldColumn($field) . " LIKE '%" . $value . "%'";
    } else {
        // Escape để an toàn
        $escapedValue = mysqli_real_escape_string($connection, $value);
        return $baseQuery . " AND " . getFieldColumn($field) . " LIKE '%" . $escapedValue . "%'";
    }
}

/**
 * Map field name sang column name trong database
 */
function getFieldColumn($field) {
    $columnMapping = [
        'title' => 'b.title',
        'author' => 'a.name',
        'publisher' => 'p.name', 
        'category' => 'c.name',
        'year' => 'b.publication_year',
        'isbn' => 'b.isbn',
        'language' => 'b.language'
    ];
    
    return $columnMapping[strtolower($field)] ?? 'b.title';
}

/**
 * Debug function để xem field nào đang bị SQLi
 */
function getVulnerableField() {
    return getenv('SQLI_VULN_FIELD') ?: 'title';
}

/**
 * Kiểm tra xem có phải union-based SQLi không
 */
function isUnionBasedSqli($value) {
    $unionKeywords = ['union', 'select', 'from', 'where'];
    $value_lower = strtolower($value);
    
    foreach ($unionKeywords as $keyword) {
        if (strpos($value_lower, $keyword) !== false) {
            return true;
        }
    }
    
    return false;
}

/**
 * Log SQLi attempts
 */
function logSqliAttempt($field, $value, $isVulnerable) {
    $logFile = '/var/log/sqli_attempts.log';
    $timestamp = date('Y-m-d H:i:s');
    $ip = $_SERVER['REMOTE_ADDR'] ?? 'unknown';
    $userAgent = $_SERVER['HTTP_USER_AGENT'] ?? 'unknown';
    
    $logEntry = "[$timestamp] SQLi Attempt - Field: $field, Value: $value, Vulnerable: " . ($isVulnerable ? 'YES' : 'NO') . ", IP: $ip, User-Agent: $userAgent\n";
    
    // Thử ghi vào /var/log, nếu không được thì ghi vào thư mục web
    if (!@file_put_contents($logFile, $logEntry, FILE_APPEND | LOCK_EX)) {
        $fallbackLogFile = __DIR__ . '/../../sqli_attempts.log';
        @file_put_contents($fallbackLogFile, $logEntry, FILE_APPEND | LOCK_EX);
    }
}
