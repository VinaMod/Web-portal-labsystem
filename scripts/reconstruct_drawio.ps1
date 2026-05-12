Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.Web

# The corrupted file still has the base64 content (with BOM prefix)
$file = "F:\FPT\do_an\Web-portal-labsystem\diagram he thong.drawio.xml"
$content = [System.IO.File]::ReadAllText($file)

# Strip BOM if present, then trim
$b64 = $content.Trim().TrimStart([char]0xFEFF, [char]0xEF, [char]0xBB, [char]0xBF).Trim()

# Verify it's valid base64 by decoding
try {
    $raw = [Convert]::FromBase64String($b64)
    Write-Host "Base64 decoded successfully. Length: $($raw.Length) bytes" -ForegroundColor Green

    # Decompress and URL-decode to verify
    $msIn = New-Object System.IO.MemoryStream -ArgumentList @(,$raw)
    $msOut = New-Object System.IO.MemoryStream
    $deflate = New-Object System.IO.Compression.DeflateStream ($msIn, [System.IO.Compression.CompressionMode]::Decompress)
    $deflate.CopyTo($msOut)
    $deflate.Close(); $msIn.Close()
    $xmlDecoded = [System.Text.Encoding]::UTF8.GetString($msOut.ToArray())
    $msOut.Close()
    $xmlRaw = [System.Web.HttpUtility]::UrlDecode($xmlDecoded)
    Write-Host "XML decoded successfully. Length: $($xmlRaw.Length) chars" -ForegroundColor Green
    Write-Host "First 100 chars: $($xmlRaw.Substring(0, 100))" -ForegroundColor Yellow

    # Wrap in XML
    $wrapped = '<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="app.diagrams.net"><diagram name="Page-1" id="nhEBWWJiJH7AQQz5EV65">' + $b64 + '</diagram></mxfile>'

    # Save backup of corrupted file
    Copy-Item $file "$file.corrupted" -Force
    Write-Host "Saved corrupted version as .corrupted" -ForegroundColor Gray

    # Save reconstructed XML with UTF-8 encoding
    [System.IO.File]::WriteAllText($file, $wrapped, [System.Text.Encoding]::UTF8)
    Write-Host "[DONE] File reconstructed with XML wrapper" -ForegroundColor Green
}
catch {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
}
