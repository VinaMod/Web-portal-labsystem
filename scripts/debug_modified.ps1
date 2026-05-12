Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.Web

$file = "F:\FPT\do_an\Web-portal-labsystem\diagram he thong.drawio.xml"
$content = Get-Content $file -Raw

if ($content -match '<diagram[^>]*>(.*?)</diagram>') {
    $b64 = $matches[1].Trim()
    $raw = [Convert]::FromBase64String($b64)
    $msIn = New-Object System.IO.MemoryStream -ArgumentList @(,$raw)
    $msOut = New-Object System.IO.MemoryStream
    $deflate = New-Object System.IO.Compression.DeflateStream ($msIn, [System.IO.Compression.CompressionMode]::Decompress)
    $deflate.CopyTo($msOut)
    $deflate.Close(); $msIn.Close()
    $xmlDecoded = [System.Text.Encoding]::UTF8.GetString($msOut.ToArray())
    $msOut.Close()
    $x = [System.Web.HttpUtility]::UrlDecode($xmlDecoded)

    Write-Host "=== MODIFIED FILE ===" -ForegroundColor Cyan

    $m1 = [regex]::Match($x, 'id="oidc" parent="([^"]+)"')
    Write-Host "OIDC parent = $($m1.Groups[1].Value)"

    $m2 = [regex]::Match($x, 'Imf7E-BpQb8dpRniBVNq-24" parent="([^"]+)"')
    Write-Host "ThirdPartyText parent = $($m2.Groups[1].Value)"

    Write-Host "Contains third_party_group: $($x.Contains('third_party_group'))"
    Write-Host "Contains waf_note: $($x.Contains('waf_note'))"
    Write-Host "Contains TTYD web terminal: $($x.Contains('TTYD web terminal proxy'))"
    Write-Host "Contains Flask Application: $($x.Contains('Flask Application'))"
    Write-Host "Management &amp; Execution: $($x.Contains('Management &amp; Execution Layer'))"
    Write-Host "Management &amp; Orchestration: $($x.Contains('Management &amp; Orchestration Module'))"

    $m3 = [regex]::Match($x, 'Sample lab web or psuedo terminal')
    Write-Host "Old psuedo text still present: $($m3.Success)"

    $m4 = [regex]::Match($x, '&amp;amp;')
    $count = 0
    $m4c = [regex]::Matches($x, '&amp;amp;')
    Write-Host "Double-encoded ampersands remaining: $($m4c.Count)"
}
