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
    $xmlRaw = [System.Web.HttpUtility]::UrlDecode($xmlDecoded)

    # ===== MODIFICATIONS =====

    # 1-2. Fix &amp;amp; -> &amp;
    $xmlRaw = $xmlRaw -replace 'Management &amp;amp; Execution Layer', 'Management &amp; Execution Layer'
    $xmlRaw = $xmlRaw -replace 'Management &amp;amp; Orchestration Module', 'Management &amp; Orchestration Module'
    
    # 3. Fix psuedo -> TTYD
    $xmlRaw = $xmlRaw -replace 'Sample lab web or psuedo terminal', 'TTYD web terminal proxy'
    
    # 4. Rename
    $xmlRaw = $xmlRaw -replace 'value="Management Backend"', 'value="Flask Application"'
    
    # 5. WAF note below WAF (x=330 y=200, same parent api_layer)
    $wafNote = '<mxCell id="waf_note" parent="api_layer" style="text;html=1;whiteSpace=wrap;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;fontSize=10;fontColor=#FF0000;" value="Not implemented" vertex="1"><mxGeometry height="20" width="110" x="330" y="205" as="geometry"/></mxCell>'
    
    # 6. Third Party group swimlane
    $thirdPartyGroup = '<mxCell id="third_party_group" parent="1" style="swimlane;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;fontStyle=1;startSize=23;fontColor=#333333;" value="Third Party" vertex="1"><mxGeometry height="130" width="180" x="-320" y="580" as="geometry"/></mxCell>'
    
    # Insert before closing root tags, BEFORE the last </root></mxGraphModel>
    $insertPoint = '</mxCell></root></mxGraphModel>'
    $insertContent = "$wafNote$thirdPartyGroup</mxCell></root></mxGraphModel>"
    $xmlRaw = $xmlRaw -replace [regex]::Escape($insertPoint), $insertContent
    
    # Reparent Third Party text label + update coords (relative to group at x=-320,y=580)
    # Old: parent="1" x="-265" y="600" -> new: parent="third_party_group" x="55" y="20"
    $old = 'id="Imf7E-BpQb8dpRniBVNq-24" parent="1"'
    $new = 'id="Imf7E-BpQb8dpRniBVNq-24" parent="third_party_group"'
    $xmlRaw = $xmlRaw -replace [regex]::Escape($old), $new
    # Update x: -265 -(-320) = 55
    $xmlRaw = $xmlRaw -replace '(id="Imf7E-BpQb8dpRniBVNq-24".*?mxGeometry height="30" width="60" x=")-265"', '$155"'
    # Update y: 600 - 580 = 20
    $xmlRaw = $xmlRaw -replace '(id="Imf7E-BpQb8dpRniBVNq-24".*?mxGeometry height="30" width="60" x="55" y=")600"', '$120"'
    
    # Reparent OIDC provider + update coords (relative to group at x=-320,y=580)
    # Old: parent="1" x="-290" y="640" -> new: parent="third_party_group" x="30" y="60"
    $old2 = 'id="oidc" parent="1"'
    $new2 = 'id="oidc" parent="third_party_group"'
    $xmlRaw = $xmlRaw -replace [regex]::Escape($old2), $new2
    # Update x: -290 - (-320) = 30
    $xmlRaw = $xmlRaw -replace '(id="oidc".*?mxGeometry height="40" width="110" x=")-290"', '$130"'
    # Update y: 640 - 580 = 60
    $xmlRaw = $xmlRaw -replace '(id="oidc".*?mxGeometry height="40" width="110" x="30" y=")640"', '$160"'
    
    # Remove old freestanding "Third Party" text (now redundant with group title)
    # Actually keep it - it shows "Third Party" inside the group
    
    # 7. Fix API Gateway title if needed
    $xmlRaw = $xmlRaw -replace 'API Gateway &amp;amp; Security Layer', 'API Gateway &amp; Security Layer'

    # ===== VERIFY CHANGES =====
    Write-Host "=== Changes made ===" -ForegroundColor Cyan
    @("Management &amp; Execution", "Management &amp; Orchestration", "TTYD web terminal", 'Flask Application', 'Not implemented', 'third_party_group', 'parent="third_party_group"') | ForEach-Object {
        $found = $xmlRaw -match $_
        Write-Host "  $_ : $(if($found){'OK'}else{'MISSING'})" -ForegroundColor $(if($found){'Green'}else{'Red'})
    }

    # ===== RE-ENCODE =====
    $urlEncoded = [System.Web.HttpUtility]::UrlEncode($xmlRaw)
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($urlEncoded)
    $msOut = New-Object System.IO.MemoryStream
    $deflate = New-Object System.IO.Compression.DeflateStream ($msOut, [System.IO.Compression.CompressionMode]::Compress)
    $deflate.Write($bytes, 0, $bytes.Length)
    $deflate.Close()
    $compressed = $msOut.ToArray()
    $msOut.Close()
    $newB64 = [Convert]::ToBase64String($compressed)
    
    # Write file
    Copy-Item $file "$file.bak" -Force
    $newContent = $content -replace [regex]::Escape($matches[1]), $newB64
    [System.IO.File]::WriteAllText($file, $newContent, [System.Text.Encoding]::UTF8)
    
    Write-Host "`n[DONE] File updated. Backup saved as .bak" -ForegroundColor Green
}
