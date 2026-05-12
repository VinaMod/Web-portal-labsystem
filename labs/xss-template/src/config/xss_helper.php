<?php
/**
 * Helper function để kiểm tra xem field nào bị lỗ hổng XSS
 * Dựa vào biến môi trường XSS_VULN_FIELD
 * 
 * @param string $field Field cần kiểm tra: 'display_name', 'display_email', 'title', 'comment', 'rating', 'name', 'username', 'email', 'product_name', 'description'
 * @return bool true nếu field này bị XSS, false nếu an toàn
 */
function isXssVulnerable($field) {
    $vulnField = getenv('XSS_VULN_FIELD') ?: 'comment';
    
    // Hỗ trợ backward compatibility với các giá trị cũ
    $fieldMapping = [
        'users' => ['name', 'username', 'email', 'display_name', 'display_email'],
        'products' => ['product_name', 'description'],
        'comments' => ['title', 'comment']
    ];
    
    // Nếu là giá trị cũ (users/products/comments), map sang các field cụ thể
    if (isset($fieldMapping[strtolower($vulnField)])) {
        return in_array(strtolower($field), array_map('strtolower', $fieldMapping[strtolower($vulnField)]));
    }
    
    // Mapping cho các field tương đương
    $fieldAliases = [
        'email' => ['email', 'display_email'],  // ENV=email sẽ match cả 'email' và 'display_email'
        'display_email' => ['email', 'display_email'],
        'name' => ['name', 'display_name'],
        'display_name' => ['name', 'display_name']
    ];
    
    // Kiểm tra alias mapping
    if (isset($fieldAliases[strtolower($vulnField)])) {
        return in_array(strtolower($field), array_map('strtolower', $fieldAliases[strtolower($vulnField)]));
    }
    
    // So sánh trực tiếp với field cụ thể
    return strtolower($vulnField) === strtolower($field);
}

/**
 * Output với XSS protection dựa vào field
 * 
 * @param string $value Giá trị cần output
 * @param string $field Field type cụ thể: 'display_name', 'display_email', 'title', 'comment', 'rating', etc.
 * @return string Output đã escape hoặc chưa escape
 */
function safeOutput($value, $field) {
    if (isXssVulnerable($field)) {
        // Không escape - có lỗ hổng XSS
        return $value;
    } else {
        // Escape để an toàn
        return htmlspecialchars($value, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
    }
}

/**
 * Output với nl2br và XSS protection
 */
function safeOutputWithBr($value, $field) {
    if (isXssVulnerable($field)) {
        // Không escape - có lỗ hổng XSS
        return nl2br($value);
    } else {
        // Escape để an toàn
        return nl2br(htmlspecialchars($value, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8'));
    }
}
