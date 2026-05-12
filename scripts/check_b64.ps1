Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.Web

$file = "F:\FPT\do_an\Web-portal-labsystem\diagram he thong.drawio.xml"

# Use .NET's Convert.TryFromBase64String to check validity
Add-Type @'
using System;
using System.IO;
using System.Text;
using System.Collections.Generic;
using System.Text.RegularExpressions;

public class B64Check {
    public static void Analyze(string path) {
        byte[] allBytes = File.ReadAllBytes(path);
        int start = (allBytes.Length >= 3 && allBytes[0] == 0xEF && allBytes[1] == 0xBB && allBytes[2] == 0xBF) ? 3 : 0;
        
        var valid = new List<byte>(allBytes.Length - start);
        int filterCount = 0;
        for (int i = start; i < allBytes.Length; i++) {
            byte b = allBytes[i];
            if ((b >= 'A' && b <= 'Z') || (b >= 'a' && b <= 'z') || (b >= '0' && b <= '9') || b == '+' || b == '/' || b == '=') {
                valid.Add(b);
            } else {
                filterCount++;
                if (filterCount <= 40) {
                    char c = (char)b;
                    Console.Error.WriteLine($"  Filtered: byte={b} char='{c}' (0x{b:X2}) at offset {i}");
                }
            }
        }
        Console.Error.WriteLine($"Total filtered: {filterCount}");
        
        string b64 = Encoding.ASCII.GetString(valid.ToArray());
        Console.Error.WriteLine($"Clean length: {b64.Length}, mod 4 = {b64.Length % 4}");
        
        // Check = positions
        int firstEq = -1, lastEq = -1, eqCount = 0;
        for (int i = 0; i < b64.Length; i++) {
            if (b64[i] == '=') {
                if (firstEq == -1) firstEq = i;
                lastEq = i;
                eqCount++;
            }
        }
        Console.Error.WriteLine($"= count: {eqCount}, first at: {firstEq}, last at: {lastEq}");
        
        // Show first/last 100 chars
        Console.Error.WriteLine($"First 80: {b64.Substring(0, Math.Min(80, b64.Length))}");
        Console.Error.WriteLine($"Last 80:  {b64.Substring(Math.Max(0, b64.Length - 80))}");
        
        // Try decoding
        Span<byte> buffer = new byte[b64.Length * 3 / 4 + 10];
        if (Convert.TryFromBase64String(b64, buffer, out int written)) {
            Console.Error.WriteLine($"DECODE SUCCESS: {written} bytes");
            // Now try deflate
            try {
                using (var msIn = new MemoryStream(buffer.ToArray(), 0, written)) {
                    using (var msOut = new MemoryStream()) {
                        using (var deflate = new System.IO.Compression.DeflateStream(msIn, System.IO.Compression.CompressionMode.Decompress)) {
                            deflate.CopyTo(msOut);
                        }
                        Console.Error.WriteLine($"Deflate success: {msOut.Length} bytes");
                    }
                }
            } catch (Exception ex) {
                Console.Error.WriteLine($"Deflate error: {ex.Message}");
            }
        } else {
            Console.Error.WriteLine("DECODE FAILED");
            // Try to find the problem area
            if (firstEq >= 0 && lastEq >= 0 && lastEq != b64.Length - 1 && lastEq != b64.Length - 2) {
                Console.Error.WriteLine($"ISSUE: = not at end (last = at {lastEq}, total len {b64.Length})");
            }
        }
    }
}
'@

[B64Check]::Analyze($file)
