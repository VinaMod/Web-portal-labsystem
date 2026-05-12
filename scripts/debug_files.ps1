Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.Web

$file = "F:\FPT\do_an\Web-portal-labsystem\diagram he thong.drawio.xml"
$bak = "F:\FPT\do_an\Web-portal-labsystem\diagram he thong.drawio.xml.bak"

# Try reading both files
foreach ($f in @($file, $bak)) {
    Write-Host "`n=== $f ===" -ForegroundColor Cyan
    $info = Get-Item $f
    Write-Host "Size: $($info.Length)" -ForegroundColor Yellow
    
    $content = Get-Content $f -Raw -Encoding Byte
    if ($content -is [byte[]]) {
        Write-Host "Read as bytes: $($content.Length)" -ForegroundColor Yellow
        $str = [System.Text.Encoding]::UTF8.GetString($content[0..[Math]::Min(199, $content.Length-1)])
    } else {
        $str = $content.Substring(0, [Math]::Min(200, $content.Length))
    }
    Write-Host "First 200 chars: $str" -ForegroundColor Gray
    
    if ($f -eq $bak) {
        # Try to match diagram tag in backup
        $txt = if ($content -is [byte[]]) { [System.Text.Encoding]::UTF8.GetString($content) } else { $content }
        if ($txt -match '<diagram[^>]*>(.*?)</diagram>') {
            $b64 = $matches[1].Trim()
            Write-Host "MATCH! Base64 length: $($b64.Length)" -ForegroundColor Green
        } elseif ($txt -match '<mxfile') {
            Write-Host "Has mxfile tag but no diagram match" -ForegroundColor Yellow
        } else {
            Write-Host "No XML tags found" -ForegroundColor Red
        }
    }
}
