Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.Web

$file = "F:\FPT\do_an\Web-portal-labsystem\diagram he thong.drawio.xml.bak"
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

    Write-Host "OIDC element:"
    $m1 = [regex]::Match($x, 'id="oidc" parent="([^"]+)"')
    if ($m1.Success) { Write-Host "  parent=$($m1.Groups[1].Value)" } else { Write-Host "  NOT FOUND" }

    Write-Host "ThirdParty text element:"
    $m2 = [regex]::Match($x, 'Imf7E-BpQb8dpRniBVNq-24" parent="([^"]+)"')
    if ($m2.Success) { Write-Host "  parent=$($m2.Groups[1].Value)" } else { Write-Host "  NOT FOUND" }

    Write-Host "ThirdParty text coords:"
    $m3 = [regex]::Match($x, 'Imf7E-BpQb8dpRniBVNq-24".*?mxGeometry[^>]*?x="([^"]+)" y="([^"]+)"')
    if ($m3.Success) { Write-Host "  x=$($m3.Groups[1].Value) y=$($m3.Groups[2].Value)" } else { Write-Host "  NOT FOUND" }

    $m4 = [regex]::Match($x, 'API Gateway')
    Write-Host "API Gateway title: $(if($m4.Success){'FOUND'}else{'NOT FOUND'})"

    Write-Host "WAF box:"
    $m5 = [regex]::Match($x, 'value="WAF"')
    Write-Host "  FOUND at index $($m5.Index)"

    Write-Host "psuedo mentions:"
    $m6 = [regex]::Matches($x, 'psuedo')
    Write-Host "  count = $($m6.Count)"
} else {
    Write-Host "ERROR: <diagram> tag not found in file"
    Write-Host "First 100 chars:"
    Write-Host $content.Substring(0, [Math]::Min(100, $content.Length))
}
