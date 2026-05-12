<?php
session_start();
session_destroy();
$provider_url = getenv('PROVIDER_URL');
// In a real scenario, the client URL might be dynamic or configured differently.
// For this lab, we derive it or hardcode the return path.
// Since PROVIDER_URL is internal (http://oauth-provider:3000) or external depending on context,
// we need the browser-accessible URL for the redirect. 
// However, the PHP script runs in the container, so getenv('PROVIDER_URL') might be the internal one.
// Let's assume the browser-accessible provider URL is on port 3000 of the host.

// FIX: To make this robust for the lab, we'll try to use a relative path if they are on same origin, 
// but they are on different ports. 
// We will construct the provider URL based on the current request's host but port 3000, 
// OR we can rely on an environment variable for EXTERNAL_PROVIDER_URL if we had one.
// For simplicity in this specific lab setup (localhost), we can assume the user accesses both via localhost.
// Getting the Protocol
$protocol = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off' || $_SERVER['SERVER_PORT'] == 443) ? "https://" : "http://";
$host = $_SERVER['HTTP_HOST']; // e.g. localhost:8083
$host_parts = explode(':', $host);
$hostname = $host_parts[0];

// The Provider is expected to be on port 3000
$provider_logout_url = "$protocol$hostname:" . getenv('PROVIDER_PORT') . "/logout";
$client_return_url = "$protocol$host/";

header("Location: $provider_logout_url?next=" . urlencode($client_return_url));
?>
