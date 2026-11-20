# Launch a built exe, screenshot it, then close it. Dev/QA helper.
param([string]$Exe = "dist-test\PowerModeSwitchTest.exe")
Add-Type -AssemblyName System.Drawing

Add-Type @"
using System;
using System.Runtime.InteropServices;
public class Win32ExeCapture {
    [StructLayout(LayoutKind.Sequential)]
    public struct RECT { public int Left; public int Top; public int Right; public int Bottom; }
    [DllImport("user32.dll")]
    public static extern bool GetWindowRect(IntPtr hwnd, out RECT rect);
    [DllImport("user32.dll")]
    public static extern bool PrintWindow(IntPtr hwnd, IntPtr hdc, uint flags);
    [DllImport("user32.dll")]
    public static extern bool SetWindowPos(IntPtr hwnd, IntPtr after, int x, int y, int cx, int cy, uint flags);
    [DllImport("shcore.dll")]
    public static extern int SetProcessDpiAwareness(int value);
}
"@
[Win32ExeCapture]::SetProcessDpiAwareness(2) | Out-Null

$env:PMS_NO_PROMPT = "1"
$name = [System.IO.Path]::GetFileNameWithoutExtension($Exe)
Start-Process -FilePath $Exe | Out-Null

$win = $null
for ($i = 0; $i -lt 60; $i++) {
    Start-Sleep -Milliseconds 500
    $win = Get-Process -Name $name -ErrorAction SilentlyContinue |
        Where-Object { $_.MainWindowTitle -eq "Power Mode Switch" } |
        Select-Object -First 1
    if ($win) { break }
}

if (-not $win) {
    Write-Error "Exe window not found"
    Get-Process -Name $name -ErrorAction SilentlyContinue | Stop-Process -Force
    exit 1
}

$hwnd = $win.MainWindowHandle
[Win32ExeCapture]::SetWindowPos($hwnd, [IntPtr](-1), 0, 0, 0, 0, 0x0043) | Out-Null
Start-Sleep -Milliseconds 2500

$rect = New-Object Win32ExeCapture+RECT
[Win32ExeCapture]::GetWindowRect($hwnd, [ref]$rect) | Out-Null
$w = $rect.Right - $rect.Left
$h = $rect.Bottom - $rect.Top

$bmp = New-Object System.Drawing.Bitmap $w, $h
$gfx = [System.Drawing.Graphics]::FromImage($bmp)
$hdc = $gfx.GetHdc()
$ok = [Win32ExeCapture]::PrintWindow($hwnd, $hdc, 2)
$gfx.ReleaseHdc($hdc)
$bmp.Save("$PWD\exe_screenshot.png", [System.Drawing.Imaging.ImageFormat]::Png)
$gfx.Dispose(); $bmp.Dispose()

[Win32ExeCapture]::SetWindowPos($hwnd, [IntPtr](-2), 0, 0, 0, 0, 0x0043) | Out-Null
Get-Process -Name $name -ErrorAction SilentlyContinue | Stop-Process -Force
Write-Output "Captured ${w}x${h} -> exe_screenshot.png (printwindow=$ok)"
