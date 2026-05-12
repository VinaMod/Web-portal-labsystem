Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.Web

$file = "F:\FPT\do_an\Web-portal-labsystem\diagram he thong.drawio.xml"

# Read raw bytes
$bytes = [System.IO.File]::ReadAllBytes($file)
Write-Host "Total file size: $($bytes.Length) bytes" -ForegroundColor Cyan

# Check first bytes for BOM
$bomLength = 0
if ($bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
    Write-Host "UTF-8 BOM detected at start, stripping 3 bytes" -ForegroundColor Yellow
    $bomLength = 3
}

# Get content after BOM
$contentBytes = $bytes[$bomLength..($bytes.Length-1)]
$b64 = [System.Text.Encoding]::ASCII.GetString($contentBytes).Trim()

Write-Host "Base64 string length: $($b64.Length)" -ForegroundColor Cyan

# Check for invalid base64 chars
$invalid = [regex]::Matches($b64, '[^A-Za-z0-9+/=]')
if ($invalid.Count -gt 0) {
    Write-Host "Found $($invalid.Count) invalid base64 characters" -ForegroundColor Red
    $seen = @{}
    foreach ($m in $invalid) {
        $c = $m.Value
        if (-not $seen.ContainsKey($c)) {
            $seen[$c] = $true
            Write-Host "  Char 0x$([int][char]$c) = '$c' at position $($m.Index)"
        }
    }
    # Strip invalid chars
    $b64 = $b64 -replace '[^A-Za-z0-9+/=]', ''
    Write-Host "After stripping invalid chars: length = $($b64.Length)" -ForegroundColor Yellow
}

try {
    $raw = [Convert]::FromBase64String($b64)
    Write-Host "Base64 decoded successfully. $($raw.Length) bytes" -ForegroundColor Green

    $msIn = New-Object System.IO.MemoryStream -ArgumentList @(,$raw)
    $msOut = New-Object System.IO.MemoryStream
    $deflate = New-Object System.IO.Compression.DeflateStream ($msIn, [System.IO.Compression.CompressionMode]::Decompress)
    $deflate.CopyTo($msOut)
    $deflate.Close(); $msIn.Close()
    $xmlDecoded = [System.Text.Encoding]::UTF8.GetString($msOut.ToArray())
    $msOut.Close()
    $xmlRaw = [System.Web.HttpUtility]::UrlDecode($xmlDecoded)
    Write-Host "XML decoded. Length: $($xmlRaw.Length)" -ForegroundColor Green
    Write-Host "First 200 chars: $($xmlRaw.Substring(0, [Math]::Min(200, $xmlRaw.Length)))" -ForegroundColor Yellow

    # Wrap in XML
    $wrapped = '<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="app.diagrams.net"><diagram name="Page-1" id="nhEBWWJiJH7AQQz5EV65">' + $b64 + '</diagram></mxfile>'

    Copy-Item $file "$file.corrupted" -Force
    [System.IO.File]::WriteAllText($file, $wrapped, [System.Text.Encoding]::UTF8)
    Write-Host "[DONE] Reconstructed XML saved" -ForegroundColor Green
}
catch {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
}
