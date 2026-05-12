Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.Web

$file = "F:\FPT\do_an\Web-portal-labsystem\diagram he thong.drawio.xml"

$bytes = [System.IO.File]::ReadAllBytes($file)
$bomLen = if ($bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) { 3 } else { 0 }

# Get bytes as array of valid base64 chars only
$validBase64 = [System.Collections.Generic.List[byte]]::new()
for ($i = $bomLen; $i -lt $bytes.Length; $i++) {
    $c = $bytes[$i]
    # Valid base64: A-Z (65-90), a-z (97-122), 0-9 (48-57), + (43), / (47), = (61)
    if (($c -ge 65 -and $c -le 90) -or ($c -ge 97 -and $c -le 122) -or ($c -ge 48 -and $c -le 57) -or $c -eq 43 -or $c -eq 47 -or $c -eq 61) {
        $validBase64.Add($c)
    } else {
        Write-Host "Stripping byte $c ('$([char]$c)') at file offset $i" -ForegroundColor DarkYellow
    }
}

Write-Host "Valid base64 bytes: $($validBase64.Count)" -ForegroundColor Cyan

$b64 = [System.Text.Encoding]::ASCII.GetString($validBase64.ToArray())
Write-Host "String length: $($b64.Length)" -ForegroundColor Cyan

try {
    $raw = [Convert]::FromBase64String($b64)
    Write-Host "Base64 decoded SUCCESS. Raw bytes: $($raw.Length)" -ForegroundColor Green

    $msIn = New-Object System.IO.MemoryStream -ArgumentList @(,$raw)
    $msOut = New-Object System.IO.MemoryStream
    $deflate = New-Object System.IO.Compression.DeflateStream ($msIn, [System.IO.Compression.CompressionMode]::Decompress)
    $deflate.CopyTo($msOut)
    $deflate.Close(); $msIn.Close()
    $xmlDecoded = [System.Text.Encoding]::UTF8.GetString($msOut.ToArray())
    $msOut.Close()
    $xmlRaw = [System.Web.HttpUtility]::UrlDecode($xmlDecoded)

    Write-Host "Raw XML length: $($xmlRaw.Length)" -ForegroundColor Green
    Write-Host "Starts with: $($xmlRaw.Substring(0, [Math]::Min(200, $xmlRaw.Length)))" -ForegroundColor Yellow
}
catch {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
}
