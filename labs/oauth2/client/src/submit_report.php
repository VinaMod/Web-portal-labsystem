<?php
$bot_url = "http://" . getenv('BOT_HOST') . ":" . getenv('BOT_PORT') . "/visit"; // Internal Docker URL for the bot

if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['url'])) {
    $target_url = $_POST['url'];
    
    // Call the bot
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $bot_url);
    curl_setopt($ch, CURLOPT_POST, 1);
    curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode(['url' => $target_url]));
    curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_TIMEOUT, 10); // Wait max 10s
    
    $response = curl_exec($ch);
    $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    
    if ($http_code == 200) {
        echo "Admin has visited your link!";
    } else {
        echo "Failed to contact admin bot. (Debug: $response)";
    }
} else {
    echo "Invalid request.";
}
?>
