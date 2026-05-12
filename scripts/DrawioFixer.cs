using System;
using System.IO;
using System.IO.Compression;
using System.Text;
using System.Collections.Generic;
using System.Net;

public class DrawioFixer
{
    public static string DecodeFileToString(string filePath)
    {
        byte[] allBytes = File.ReadAllBytes(filePath);
        int start = 0;
        if (allBytes.Length >= 3 && allBytes[0] == 0xEF && allBytes[1] == 0xBB && allBytes[2] == 0xBF)
            start = 3;
        
        var valid = new List<byte>(allBytes.Length - start);
        for (int i = start; i < allBytes.Length; i++)
        {
            byte b = allBytes[i];
            if ((b >= 'A' && b <= 'Z') || (b >= 'a' && b <= 'z') || (b >= '0' && b <= '9') || b == '+' || b == '/' || b == '=')
                valid.Add(b);
        }
        
        string b64 = Encoding.ASCII.GetString(valid.ToArray());
        
        // Fix padding
        int mod4 = b64.Length % 4;
        if (mod4 != 0)
            b64 = b64.PadRight(b64.Length + (4 - mod4), '=');
        
        // Remove = not at end
        int lastNonEq = b64.Length - 1;
        while (lastNonEq >= 0 && b64[lastNonEq] == '=') lastNonEq--;
        int firstEq = b64.IndexOf('=');
        if (firstEq >= 0 && firstEq < lastNonEq)
            b64 = b64.Substring(0, firstEq).PadRight(((b64.Substring(0, firstEq).Length + 3) / 4) * 4, '=');
        
        byte[] compressed = Convert.FromBase64String(b64);
        
        using (var msIn = new MemoryStream(compressed))
        using (var msOut = new MemoryStream())
        {
            using (var deflate = new DeflateStream(msIn, CompressionMode.Decompress))
                deflate.CopyTo(msOut);
            string urlEncoded = Encoding.UTF8.GetString(msOut.ToArray());
            return WebUtility.UrlDecode(urlEncoded);
        }
    }
    
    public static string EncodeString(string xmlRaw)
    {
        string urlEncoded = WebUtility.UrlEncode(xmlRaw);
        byte[] bytes = Encoding.UTF8.GetBytes(urlEncoded);
        using (var msOut = new MemoryStream())
        {
            using (var deflate = new DeflateStream(msOut, CompressionMode.Compress))
                deflate.Write(bytes, 0, bytes.Length);
            return Convert.ToBase64String(msOut.ToArray());
        }
    }
}
