Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.Web

$src = @'
using System;
using System.IO;
using System.IO.Compression;
using System.Text;
using System.Collections.Generic;
using System.Net;

public class DrawioFixer {
    public static string CleanAndDecode(string filePath) {
        return CleanAndDecode(filePath, false);
    }
    public static string CleanAndDecode(string filePath, bool debug) {
        byte[] allBytes = File.ReadAllBytes(filePath);
        int start = 0;
        if (allBytes.Length >= 3 && allBytes[0] == 0xEF && allBytes[1] == 0xBB && allBytes[2] == 0xBF)
            start = 3;
        var valid = new List<byte>(allBytes.Length - start);
        int filtered = 0;
        for (int i = start; i < allBytes.Length; i++) {
            byte b = allBytes[i];
            if ((b >= 'A' && b <= 'Z') || (b >= 'a' && b <= 'z') || (b >= '0' && b <= '9') || b == '+' || b == '/' || b == '=')
                valid.Add(b);
            else if (debug && ++filtered <= 40)
                Console.Error.WriteLine($"Filtered byte 0x{b:X2} ('{(char)b}') at pos {i}");
        }
        string b64 = Encoding.ASCII.GetString(valid.ToArray());
        if (debug) {
            Console.Error.WriteLine($"Cleaned length: {b64.Length}, mod 4 = {b64.Length % 4}");
            var eqPositions = new System.Collections.ArrayList();
            for (int i = 0; i < b64.Length; i++) if (b64[i] == '=') eqPositions.Add(i);
            Console.Error.WriteLine($"'=' count: {eqPositions.Count}, positions: {string.Join(",", eqPositions.ToArray())}");
        }
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
            return Convert.ToBase64String(msOut.ToArray());
        }
    }
}
'@

Add-Type -TypeDefinition $src -ReferencedAssemblies "System.Web.dll"

$file = "F:\FPT\do_an\Web-portal-labsystem\diagram he thong.drawio.xml"

Write-Host "Decoding base64 from corrupted file..." -ForegroundColor Cyan
$xmlRaw = [DrawioFixer]::CleanAndDecode($file)
Write-Host "OK - $($xmlRaw.Length) chars decoded" -ForegroundColor Green
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

Write-Host "Modifications applied" -ForegroundColor Green

Write-Host "`nVerifying..." -ForegroundColor Cyan
$checks = @(
    @{l="Management & Execution Layer"; e={$xmlRaw.Contains('Management &amp; Execution Layer')}}
    @{l="Management & Orchestration Module"; e={$xmlRaw.Contains('Management &amp; Orchestration Module')}}
    @{l="TTYD web terminal proxy"; e={$xmlRaw.Contains('TTYD web terminal proxy')}}
    @{l="Flask Application"; e={$xmlRaw.Contains('Flask Application')}}
    @{l="WAF note (waf_note)"; e={$xmlRaw.Contains('waf_note')}}
    @{l="Third Party group"; e={$xmlRaw.Contains('third_party_group')}}
    @{l="OIDC reparented"; e={$xmlRaw.Contains('oidc" parent="third_party_group"')}}
    @{l="ThirdPartyText reparented"; e={$xmlRaw.Contains('Imf7E-BpQb8dpRniBVNq-24" parent="third_party_group"')}}
    @{l="API Gateway & Security"; e={$xmlRaw.Contains('API Gateway &amp; Security')}}
    @{l="No double-encoded &amp;amp;"; e={-not $xmlRaw.Contains('&amp;amp;')}}
    @{l="No psuedo"; e={-not $xmlRaw.Contains('psuedo')}}
    @{l="No Management Backend"; e={-not $xmlRaw.Contains('Management Backend')}}
)

$allPass = $true
foreach ($c in $checks) {
    $result = & $c.e
    if (-not $result) { $allPass = $false }
    Write-Host ("  " + $(if($result){"[OK]"}else{"[FAIL]"}) + " " + $c.l) -ForegroundColor $(if($result){"Green"}else{"Red"})
}

if (-not $allPass) { Write-Host "FIXES NEEDED" -ForegroundColor Red; exit 1 }

Write-Host "`nRe-encoding and saving..." -ForegroundColor Cyan
$newB64 = [DrawioFixer]::ReEncode($xmlRaw)
$wrapped = '<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="app.diagrams.net"><diagram name="Page-1" id="nhEBWWJiJH7AQQz5EV65">' + $newB64 + '</diagram></mxfile>'

[System.IO.File]::WriteAllText($file, $wrapped, [System.Text.Encoding]::UTF8)
Write-Host "[DONE] File saved!" -ForegroundColor Green
Write-Host "Size: $((Get-Item $file).Length) bytes" -ForegroundColor Gray
