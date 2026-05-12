Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.Web

$file = "F:\FPT\do_an\Web-portal-labsystem\diagram he thong.drawio.xml"

# Read raw bytes, strip BOM
$bytes = [System.IO.File]::ReadAllBytes($file)
$bomLen = if ($bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) { 3 } else { 0 }
$b64 = [System.Text.Encoding]::ASCII.GetString($bytes, $bomLen, $bytes.Length - $bomLen).Trim()

# Strip ALL non-base64 chars
$clean = [regex]::Replace($b64, '[^A-Za-z0-9+/=]', '')

Write-Host "Cleaned base64: $($clean.Length) chars" -ForegroundColor Cyan

try {
    $raw = [Convert]::FromBase64String($clean)
    Write-Host "Decoded: $($raw.Length) bytes" -ForegroundColor Green

    # Decompress
    $msIn = New-Object System.IO.MemoryStream -ArgumentList @(,$raw)
    $msOut = New-Object System.IO.MemoryStream
    $deflate = New-Object System.IO.Compression.DeflateStream ($msIn, [System.IO.Compression.CompressionMode]::Decompress)
    $deflate.CopyTo($msOut)
    $deflate.Close(); $msIn.Close()
    $xmlDecoded = [System.Text.Encoding]::UTF8.GetString($msOut.ToArray())
    $msOut.Close()
    $xmlRaw = [System.Web.HttpUtility]::UrlDecode($xmlDecoded)

    Write-Host "Raw XML: $($xmlRaw.Length) chars" -ForegroundColor Green
    Write-Host "Starts with: $($xmlRaw.Substring(0, [Math]::Min(100, $xmlRaw.Length)))" -ForegroundColor Yellow

    # ===== APPLY MODIFICATIONS =====
    Write-Host "`n=== Applying modifications ===" -ForegroundColor Cyan

    # 1-2. Fix &amp;amp; -> &amp;
    $count1 = [regex]::Matches($xmlRaw, '&amp;amp;').Count
    $xmlRaw = $xmlRaw -replace 'Management &amp;amp; Execution Layer', 'Management &amp; Execution Layer'
    $xmlRaw = $xmlRaw -replace 'Management &amp;amp; Orchestration Module', 'Management &amp; Orchestration Module'
    Write-Host "  Double-encoded ampersands: $count1 -> replaced"

    # 3. Fix psuedo -> TTYD
    $xmlRaw = $xmlRaw -replace 'Sample lab web or psuedo terminal', 'TTYD web terminal proxy'
    Write-Host "  psuedo -> TTYD"

    # 4. Rename Management Backend -> Flask Application
    $xmlRaw = $xmlRaw -replace 'value="Management Backend"', 'value="Flask Application"'
    Write-Host "  Management Backend -> Flask Application"

    # 5. Add WAF note
    $wafNote = '<mxCell id="waf_note" parent="api_layer" style="text;html=1;whiteSpace=wrap;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;fontSize=10;fontColor=#FF0000;" value="Not implemented" vertex="1"><mxGeometry height="20" width="110" x="330" y="205" as="geometry"/></mxCell>'
    
    # 6. Add Third Party group
    $thirdPartyGroup = '<mxCell id="third_party_group" parent="1" style="swimlane;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;fontStyle=1;startSize=23;fontColor=#333333;" value="Third Party" vertex="1"><mxGeometry height="130" width="180" x="-320" y="580" as="geometry"/></mxCell>'
    
    # Insert before closing root
    $insertPoint = '</mxCell></root></mxGraphModel>'
    $insertContent = "$wafNote$thirdPartyGroup</mxCell></root></mxGraphModel>"
    $xmlRaw = $xmlRaw -replace [regex]::Escape($insertPoint), $insertContent
    Write-Host "  Inserted WAF note + Third Party group"
    
    # Reparent Third Party text
    $old = 'id="Imf7E-BpQb8dpRniBVNq-24" parent="1"'
    $new = 'id="Imf7E-BpQb8dpRniBVNq-24" parent="third_party_group"'
    $xmlRaw = $xmlRaw -replace [regex]::Escape($old), $new
    $xmlRaw = $xmlRaw -replace '(id="Imf7E-BpQb8dpRniBVNq-24".*?mxGeometry height="30" width="60" x=")-265"', '$155"'
    $xmlRaw = $xmlRaw -replace '(id="Imf7E-BpQb8dpRniBVNq-24".*?mxGeometry height="30" width="60" x="55" y=")600"', '$120"'
    Write-Host "  Reparented Third Party text"

    # Reparent OIDC
    $old2 = 'id="oidc" parent="1"'
    $new2 = 'id="oidc" parent="third_party_group"'
    $xmlRaw = $xmlRaw -replace [regex]::Escape($old2), $new2
    $xmlRaw = $xmlRaw -replace '(id="oidc".*?mxGeometry height="40" width="110" x=")-290"', '$130"'
    $xmlRaw = $xmlRaw -replace '(id="oidc".*?mxGeometry height="40" width="110" x="30" y=")640"', '$160"'
    Write-Host "  Reparented OIDC provider"

    # Fix API Gateway title
    $xmlRaw = $xmlRaw -replace 'API Gateway &amp;amp; Security Layer', 'API Gateway &amp; Security Layer'
    Write-Host "  Fixed API Gateway title"

    # ===== VERIFY =====
    Write-Host "`n=== Verification ===" -ForegroundColor Cyan
    $verify = @(
        @('Management &amp; Execution Layer', $xmlRaw.Contains('Management &amp; Execution Layer'))
        @('Management &amp; Orchestration Module', $xmlRaw.Contains('Management &amp; Orchestration Module'))
        @('TTYD web terminal proxy', $xmlRaw.Contains('TTYD web terminal proxy'))
        @('Flask Application', $xmlRaw.Contains('Flask Application'))
        @('WAF note (waf_note)', $xmlRaw.Contains('waf_note'))
        @('Third Party group', $xmlRaw.Contains('third_party_group'))
        @('OIDC reparented', $xmlRaw.Contains('oidc" parent="third_party_group"'))
        @('ThirdPartyText reparented', $xmlRaw.Contains('Imf7E-BpQb8dpRniBVNq-24" parent="third_party_group"'))
        @('API Gateway &amp; Security', $xmlRaw.Contains('API Gateway &amp; Security'))
        @('No double-encoded amp;amp;', -not $xmlRaw.Contains('&amp;amp;'))
        @('No psuedo', -not $xmlRaw.Contains('psuedo'))
        @('No Management Backend', -not $xmlRaw.Contains('Management Backend'))
    )
    foreach ($v in $verify) {
        $label = $v[0]
        $ok = $v[1]
        Write-Host "  $(if($ok){'[OK]'}else{'[FAIL]'}) $label" -ForegroundColor $(if($ok){'Green'}else{'Red'})
    }

    # ===== RE-ENCODE =====
    $urlEncoded = [System.Web.HttpUtility]::UrlEncode($xmlRaw)
    $encBytes = [System.Text.Encoding]::UTF8.GetBytes($urlEncoded)
    $msOut = New-Object System.IO.MemoryStream
    $deflate = New-Object System.IO.Compression.DeflateStream ($msOut, [System.IO.Compression.CompressionMode]::Compress)
    $deflate.Write($encBytes, 0, $encBytes.Length)
    $deflate.Close()
    $compressed = $msOut.ToArray()
    $msOut.Close()
    $newB64 = [Convert]::ToBase64String($compressed)

    # Wrap in XML
    $wrapped = '<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="app.diagrams.net"><diagram name="Page-1" id="nhEBWWJiJH7AQQz5EV65">' + $newB64 + '</diagram></mxfile>'

    Copy-Item $file "$file.bak2" -Force
    [System.IO.File]::WriteAllText($file, $wrapped, [System.Text.Encoding]::UTF8)
    Write-Host "`n[DONE] File saved with UTF-8 encoding" -ForegroundColor Green
}
catch {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
}
