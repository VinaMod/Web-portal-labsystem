Add-Type -Path "F:\FPT\do_an\Web-portal-labsystem\scripts\DrawioFixer.cs" -ReferencedAssemblies "System.IO.Compression.dll"

$file = "F:\FPT\do_an\Web-portal-labsystem\diagram he thong.drawio.xml"

$xmlRaw = [DrawioFixer]::DecodeFileToString($file)

Write-Host "Raw XML: $($xmlRaw.Length) chars" -ForegroundColor Green
Write-Host "First 200: $($xmlRaw.Substring(0, 200))" -ForegroundColor Yellow

Write-Host "`nApplying modifications..." -ForegroundColor Cyan

# 1-2. Fix &amp;amp; -> &amp;
$xmlRaw = $xmlRaw -replace 'Management &amp;amp; Execution Layer', 'Management &amp; Execution Layer'
$xmlRaw = $xmlRaw -replace 'Management &amp;amp; Orchestration Module', 'Management &amp; Orchestration Module'
$xmlRaw = $xmlRaw -replace 'API Gateway &amp;amp; Security Layer', 'API Gateway &amp; Security Layer'

# 3. psuedo -> TTYD
$xmlRaw = $xmlRaw -replace 'Sample lab web or psuedo terminal', 'TTYD web terminal proxy'

# 4. Management Backend -> Flask Application
$xmlRaw = $xmlRaw -replace 'value="Management Backend"', 'value="Flask Application"'

# 5-6. Insert WAF note + Third Party group  
$wafNote = '<mxCell id="waf_note" parent="api_layer" style="text;html=1;whiteSpace=wrap;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;fontSize=10;fontColor=#FF0000;" value="Not implemented" vertex="1"><mxGeometry height="20" width="110" x="330" y="205" as="geometry"/></mxCell>'
$thirdPartyGroup = '<mxCell id="third_party_group" parent="1" style="swimlane;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;fontStyle=1;startSize=23;fontColor=#333333;" value="Third Party" vertex="1"><mxGeometry height="130" width="180" x="-320" y="580" as="geometry"/></mxCell>'
$xmlRaw = $xmlRaw -replace [regex]::Escape('</mxCell></root></mxGraphModel>'), "$wafNote$thirdPartyGroup</mxCell></root></mxGraphModel>"

# Reparent Third Party text
$xmlRaw = $xmlRaw -replace [regex]::Escape('id="Imf7E-BpQb8dpRniBVNq-24" parent="1"'), 'id="Imf7E-BpQb8dpRniBVNq-24" parent="third_party_group"'
$xmlRaw = $xmlRaw -replace '(id="Imf7E-BpQb8dpRniBVNq-24".*?mxGeometry height="30" width="60" x=")-265"', '$155"'
$xmlRaw = $xmlRaw -replace '(id="Imf7E-BpQb8dpRniBVNq-24".*?mxGeometry height="30" width="60" x="55" y=")600"', '$120"'

# Reparent OIDC
$xmlRaw = $xmlRaw -replace [regex]::Escape('id="oidc" parent="1"'), 'id="oidc" parent="third_party_group"'
$xmlRaw = $xmlRaw -replace '(id="oidc".*?mxGeometry height="40" width="110" x=")-290"', '$130"'
$xmlRaw = $xmlRaw -replace '(id="oidc".*?mxGeometry height="40" width="110" x="30" y=")640"', '$160"'

Write-Host "Done. Verifying..." -ForegroundColor Green

$allOk = $true
$checks = @(
    @("Management & Execution Layer", $xmlRaw.Contains('Management &amp; Execution Layer'))
    @("Management & Orchestration Module", $xmlRaw.Contains('Management &amp; Orchestration Module'))
    @("TTYD web terminal proxy", $xmlRaw.Contains('TTYD web terminal proxy'))
    @("Flask Application", $xmlRaw.Contains('Flask Application'))
    @("WAF note (waf_note)", $xmlRaw.Contains('waf_note'))
    @("Third Party group", $xmlRaw.Contains('third_party_group'))
    @("OIDC reparented", $xmlRaw.Contains('oidc" parent="third_party_group"'))
    @("ThirdPartyText reparented", $xmlRaw.Contains('Imf7E-BpQb8dpRniBVNq-24" parent="third_party_group"'))
    @("API Gateway & Security", $xmlRaw.Contains('API Gateway &amp; Security'))
    @("No double-encoded &amp;amp;", -not $xmlRaw.Contains('&amp;amp;'))
    @("No psuedo", -not $xmlRaw.Contains('psuedo'))
    @("No Management Backend", -not $xmlRaw.Contains('Management Backend'))
)
foreach ($c in $checks) {
    $label = $c[0]; $result = $c[1]
    if (-not $result) { $allOk = $false }
    Write-Host "  $(if($result){'[OK]'}else{'[FAIL]'}) $label" -ForegroundColor $(if($result){'Green'}else{'Red'})
}
if (-not $allOk) { Write-Host "FIXES NEEDED" -ForegroundColor Red; exit 1 }

# Re-encode
Write-Host "`nRe-encoding and saving..." -ForegroundColor Cyan
$newB64 = [DrawioFixer]::EncodeString($xmlRaw)

$wrapped = '<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="app.diagrams.net"><diagram name="Page-1" id="nhEBWWJiJH7AQQz5EV65">' + $newB64 + '</diagram></mxfile>'

[System.IO.File]::WriteAllText($file, $wrapped, [System.Text.Encoding]::UTF8)
Write-Host "[DONE] File saved!" -ForegroundColor Green
Write-Host "Size: $((Get-Item $file).Length) bytes" -ForegroundColor Gray
