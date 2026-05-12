Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.Web

$file = "F:\FPT\do_an\Web-portal-labsystem\diagram he thong.drawio.xml"
$bak  = "F:\FPT\do_an\Web-portal-labsystem\diagram he thong.drawio.xml.bak"
$content = Get-Content $file -Raw

# The file IS the base64 content (no XML wrapper)
$b64 = $content.Trim()
$raw = [Convert]::FromBase64String($b64)

$msIn = New-Object System.IO.MemoryStream -ArgumentList @(,$raw)
$msOut = New-Object System.IO.MemoryStream
$deflate = New-Object System.IO.Compression.DeflateStream ($msIn, [System.IO.Compression.CompressionMode]::Decompress)
$deflate.CopyTo($msOut)
$deflate.Close(); $msIn.Close()
$xmlDecoded = [System.Text.Encoding]::UTF8.GetString($msOut.ToArray())
$msOut.Close()
$xmlRaw = [System.Web.HttpUtility]::UrlDecode($xmlDecoded)

Write-Host "=== VERIFICATION of FIXED DIAGRAM ===" -ForegroundColor Cyan

$checks = @(
    "Management &amp; Execution Layer"
    "Management &amp; Orchestration Module"
    "TTYD web terminal proxy"
    'value="Flask Application"'
    'id="waf_note"'
    'id="third_party_group"'
    'id="oidc" parent="third_party_group"'
    'id="Imf7E-BpQb8dpRniBVNq-24" parent="third_party_group"'
    "API Gateway &amp; Security"
)

foreach ($check in $checks) {
    $found = $xmlRaw.Contains($check)
    $symbol = if ($found) { "[OK]" } else { "[MISSING]" }
    $color = if ($found) { "Green" } else { "Red" }
    Write-Host "$symbol $check" -ForegroundColor $color
}
