<?php
session_start();

$provider_url = getenv('PROVIDER_URL');
$client_id = getenv('CLIENT_ID');
$client_secret = getenv('CLIENT_SECRET');
$redirect_uri = getenv('REDIRECT_URI');

if (isset($_GET['code'])) {
    $code = $_GET['code'];
    
    // Exchange code for token
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, "$provider_url/token");
    curl_setopt($ch, CURLOPT_POST, 1);
    curl_setopt($ch, CURLOPT_POSTFIELDS, http_build_query([
        'code' => $code,
        'client_id' => $client_id,
        'client_secret' => $client_secret,
        'redirect_uri' => $redirect_uri,
        'grant_type' => 'authorization_code'
    ]));
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    $response = curl_exec($ch);
    curl_close($ch);
    
    $data = json_decode($response, true);
    
    if (isset($data['access_token'])) {
        // Get User Info
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, "$provider_url/userinfo");
        curl_setopt($ch, CURLOPT_HTTPHEADER, [
            "Authorization: Bearer " . $data['access_token']
        ]);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        $user_response = curl_exec($ch);
        curl_close($ch);
        
        $user = json_decode($user_response, true);
        
        if ($user) {
            $_SESSION['user'] = $user;
            header('Location: index.php');
            exit;
        }
    }
    
    echo "Login Failed: " . htmlspecialchars($response);
} else {
    echo "No code provided.";
}
?>
