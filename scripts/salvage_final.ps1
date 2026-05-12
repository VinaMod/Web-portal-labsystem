Add-Type @"
using System;
using System.IO;
using System.IO.Compression;
using System.Text;
using System.Text.RegularExpressions;
using System.Net;
using System.Collections.Generic;

public class DrawioFixer {
    public static string CleanAndDecode(string filePath) {
        byte[] allBytes = File.ReadAllBytes(filePath);
        
        // Skip BOM if present
        int start = 0;
        if (allBytes.Length >= 3 && allBytes[0] == 0xEF && allBytes[1] == 0xBB && allBytes[2] == 0xBF)
            start = 3;
        
        // Filter only valid base64 chars
        var valid = new List<byte>(allBytes.Length - start);
        for (int i = start; i < allBytes.Length; i++) {
            byte b = allBytes[i];
            if ((b >= 'A' && b <= 'Z') || (b >= 'a' && b <= 'z') || (b >= '0' && b <= '9') || b == '+' || b == '/' || b == '=')
                valid.Add(b);
        }
        
        string b64 = Encoding.ASCII.GetString(valid.ToArray());
        byte[] compressed = Convert.FromBase64String(b64);
        
        using (var msIn = new MemoryStream(compressed))
        using (var msOut = new MemoryStream()) {
            using (var deflate = new DeflateStream(msIn, CompressionMode.Decompress)) {
                deflate.CopyTo(msOut);
            }
            string urlEncoded = Encoding.UTF8.GetString(msOut.ToArray());
            return WebUtility.UrlDecode(urlEncoded);
        }
    }
    
    public static string ReEncode(string xmlRaw) {
            string urlEncoded = WebUtility.UrlEncode(xmlRaw);
        byte[] bytes = Encoding.UTF8.GetBytes(urlEncoded);
        
        using (var msOut = new MemoryStream()) {
            using (var deflate = new DeflateStream(msOut, CompressionMode.Compress)) {
                deflate.Write(bytes, 0, bytes.Length);
            }
            byte[] compressed = msOut.ToArray();
            return Convert.ToBase64String(compressed);
        }
    }
}

public static string CleanOnly(string filePath) {
    byte[] allBytes = File.ReadAllBytes(filePath);
    int start = 0;
    if (allBytes.Length >= 3 && allBytes[0] == 0xEF && allBytes[1] == 0xBB && allBytes[2] == 0xBF)
        start = 3;
    var valid = new List<byte>(allBytes.Length - start);
    for (int i = start; i < allBytes.Length; i++) {
        byte b = allBytes[i];
        if ((b >= 'A' && b <= 'Z') || (b >= 'a' && b <= 'z') || (b >= '0' && b <= '9') || b == '+' || b == '/' || b == '=')
            valid.Add(b);
    }
    return Encoding.ASCII.GetString(valid.ToArray());
}
"@

$file = "F:\FPT\do_an\Web-portal-labsystem\diagram he thong.drawio.xml"

Write-Host "=== Step 1: Decode base64 from corrupted file ===" -ForegroundColor Cyan
$cleaned = [DrawioFixer]::CleanOnly($file)
Write-Host "Cleaned base64 length: $($cleaned.Length)" -ForegroundColor Yellow
Write-Host "Clean ends with: ...$($cleaned.Substring([Math]::Max(0, $cleaned.Length - 20)))" -ForegroundColor Yellow
Write-Host "Clean length mod 4 = $($cleaned.Length % 4)" -ForegroundColor Yellow

# Check for padding issues
$lastEq = $cleaned.LastIndexOf('=')
$firstEq = $cleaned.IndexOf('=')
if ($lastEq -ge 0) {
    Write-Host "First '=' at $firstEq, last '=' at $lastEq" -ForegroundColor Yellow
}

$xmlRaw = [DrawioFixer]::CleanAndDecode($file)
Write-Host "Decoded XML length: $($xmlRaw.Length) chars" -ForegroundColor Green
if ($xmlRaw) { Write-Host "Starts with: $($xmlRaw.Substring(0, [Math]::Min(200, $xmlRaw.Length)))" -ForegroundColor Yellow }

Write-Host "`n=== Step 2: Apply modifications ===" -ForegroundColor Cyan

# 1-2. Fix &amp;amp; -> &amp;
$xmlRaw = $xmlRaw -replace 'Management &amp;amp; Execution Layer', 'Management &amp; Execution Layer'
$xmlRaw = $xmlRaw -replace 'Management &amp;amp; Orchestration Module', 'Management &amp; Orchestration Module'
Write-Host "  Fixed double-encoded ampersands"

# 3. Fix psuedo -> TTYD
$xmlRaw = $xmlRaw -replace 'Sample lab web or psuedo terminal', 'TTYD web terminal proxy'
Write-Host "  Fixed psuedo -> TTYD"

# 4. Rename
$xmlRaw = $xmlRaw -replace 'value="Management Backend"', 'value="Flask Application"'
Write-Host "  Renamed Management Backend"

# 5. WAF note
$wafNote = '<mxCell id="waf_note" parent="api_layer" style="text;html=1;whiteSpace=wrap;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;fontSize=10;fontColor=#FF0000;" value="Not implemented" vertex="1"><mxGeometry height="20" width="110" x="330" y="205" as="geometry"/></mxCell>'

# 6. Third Party group
$thirdPartyGroup = '<mxCell id="third_party_group" parent="1" style="swimlane;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;fontStyle=1;startSize=23;fontColor=#333333;" value="Third Party" vertex="1"><mxGeometry height="130" width="180" x="-320" y="580" as="geometry"/></mxCell>'

$insertPoint = '</mxCell></root></mxGraphModel>'
$insertContent = "$wafNote$thirdPartyGroup</mxCell></root></mxGraphModel>"
$xmlRaw = $xmlRaw -replace [regex]::Escape($insertPoint), $insertContent
Write-Host "  Inserted WAF note + Third Party group"

# Reparent Third Party text
$xmlRaw = $xmlRaw -replace [regex]::Escape('id="Imf7E-BpQb8dpRniBVNq-24" parent="1"'), 'id="Imf7E-BpQb8dpRniBVNq-24" parent="third_party_group"'
$xmlRaw = $xmlRaw -replace '(id="Imf7E-BpQb8dpRniBVNq-24".*?mxGeometry height="30" width="60" x=")-265"', '$155"'
$xmlRaw = $xmlRaw -replace '(id="Imf7E-BpQb8dpRniBVNq-24".*?mxGeometry height="30" width="60" x="55" y=")600"', '$120"'
Write-Host "  Reparented Third Party text"

# Reparent OIDC
$xmlRaw = $xmlRaw -replace [regex]::Escape('id="oidc" parent="1"'), 'id="oidc" parent="third_party_group"'
$xmlRaw = $xmlRaw -replace '(id="oidc".*?mxGeometry height="40" width="110" x=")-290"', '$130"'
$xmlRaw = $xmlRaw -replace '(id="oidc".*?mxGeometry height="40" width="110" x="30" y=")640"', '$160"'
Write-Host "  Reparented OIDC provider"

# 7. API Gateway
$xmlRaw = $xmlRaw -replace 'API Gateway &amp;amp; Security Layer', 'API Gateway &amp; Security Layer'
Write-Host "  Fixed API Gateway title"

Write-Host "`n=== Step 3: Verify ===" -ForegroundColor Cyan
$verify = @(
    @('Management & Execution Layer', $xmlRaw.Contains('Management &amp; Execution Layer'))
    @('Management & Orchestration Module', $xmlRaw.Contains('Management &amp; Orchestration Module'))
    @('TTYD web terminal proxy', $xmlRaw.Contains('TTYD web terminal proxy'))
    @('Flask Application', $xmlRaw.Contains('Flask Application'))
    @('WAF note', $xmlRaw.Contains('waf_note'))
    @('Third Party group', $xmlRaw.Contains('third_party_group'))
    @('OIDC reparented', $xmlRaw.Contains('oidc" parent="third_party_group"'))
    @('ThirdPartyText reparented', $xmlRaw.Contains('Imf7E-BpQb8dpRniBVNq-24" parent="third_party_group"'))
    @('API Gateway & Security', $xmlRaw.Contains('API Gateway &amp; Security'))
    @('No double amp;amp;', -not $xmlRaw.Contains('&amp;amp;'))
    @('No psuedo', -not $xmlRaw.Contains('psuedo'))
    @('No Management Backend', -not $xmlRaw.Contains('Management Backend'))
)
$allOk = $true
foreach ($v in $verify) {
    $label = $v[0]
    $ok = $v[1]
    if (-not $ok) { $allOk = $false }
    Write-Host "  $(if($ok){'[OK]'}else{'[FAIL]'}) $label" -ForegroundColor $(if($ok){'Green'}else{'Red'})
}

if (-not $allOk) {
    Write-Host "`nFIXES NEEDED before re-encoding" -ForegroundColor Red
    exit 1
}

Write-Host "`n=== Step 4: Re-encode and save ===" -ForegroundColor Cyan
$newB64 = [DrawioFixer]::ReEncode($xmlRaw)

$wrapped = '<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="app.diagrams.net"><diagram name="Page-1" id="nhEBWWJiJH7AQQz5EV65">' + $newB64 + '</diagram></mxfile>'

[System.IO.File]::WriteAllText($file, $wrapped, [System.Text.Encoding]::UTF8)
Write-Host "[DONE] File saved successfully!" -ForegroundColor Green
Write-Host "File size: $([System.IO.FileInfo]::new($file).Length) bytes" -ForegroundColor Gray
