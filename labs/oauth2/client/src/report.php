<?php
session_start();
?>
<!DOCTYPE html>
<html>
<head>
    <title>Report Bug</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="container">
        <h1>Report a Bug</h1>
        <p>Found a vulnerability? Send the link to the admin.</p>
        <form id="reportForm">
            <input type="text" id="url" name="url" placeholder="http://..." required>
            <button type="submit" class="btn btn-primary">Send to Admin</button>
        </form>
        <div id="message"></div>
        <a href="index.php">Back</a>
    </div>

    <script>
        document.getElementById('reportForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const url = document.getElementById('url').value;
            const msgDiv = document.getElementById('message');
            
            msgDiv.innerText = "Sending to admin bot...";
            
            try {
                // In a real scenario, this would call the bot service directly or via an API
                // For this lab, we'll assume the bot is listening on a specific endpoint or we just simulate the call.
                // Since the bot is in a separate container, we can't easily trigger it from client-side JS unless we expose an endpoint.
                // Let's make a PHP proxy or just assume the user will run the bot manually?
                // No, the plan said "Admin Bot".
                // Let's add a PHP endpoint `submit_report.php` that calls the bot container.
                
                const response = await fetch('submit_report.php', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: 'url=' + encodeURIComponent(url)
                });
                
                const text = await response.text();
                msgDiv.innerText = text;
            } catch (err) {
                msgDiv.innerText = "Error sending report.";
            }
        });
    </script>
</body>
</html>
