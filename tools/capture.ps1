# Capture the running app window to a PNG for visual review.
param([string]$Script = "power_mode.py")
Add-Type -AssemblyName System.Drawing

Add-Type @"
using System;
using System.Runtime.InteropServices;
public class Win32Capture {
    [StructLayout(LayoutKind.Sequential)]
    public struct RECT { public int Left; public int Top; public int Right; public int Bottom; }
    [DllImport("user32.dll")]
    public static extern bool SetForegroundWindow(IntPtr hwnd);
    [DllImport("user32.dll")]
    public static extern bool ShowWindow(IntPtr hwnd, int cmd);
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

# Make this script DPI-aware so window rects are in real pixels.
[Win32Capture]::SetProcessDpiAwareness(2) | Out-Null

$env:PMS_NO_PROMPT = "1"
$launcher = Start-Process -FilePath ".\.venv\Scripts\pythonw.exe" `
    -ArgumentList $Script -PassThru

$win = $null
for ($i = 0; $i -lt 40; $i++) {
    Start-Sleep -Milliseconds 500
    $win = Get-Process pythonw -ErrorAction SilentlyContinue |
        Where-Object { $_.MainWindowTitle -eq "Power Mode Switch" } |
        Select-Object -First 1
    if ($win) { break }
}

if (-not $win) {
    Write-Error "Window not found"
    Get-Process pythonw -ErrorAction SilentlyContinue | Stop-Process -Force
    exit 1
}

$hwnd = $win.MainWindowHandle
[Win32Capture]::ShowWindow($hwnd, 9) | Out-Null
[Win32Capture]::SetWindowPos($hwnd, [IntPtr](-1), 0, 0, 0, 0, 0x0043) | Out-Null
[Win32Capture]::SetForegroundWindow($hwnd) | Out-Null
Start-Sleep -Milliseconds 2200

$rect = New-Object Win32Capture+RECT
[Win32Capture]::GetWindowRect($hwnd, [ref]$rect) | Out-Null
$w = $rect.Right - $rect.Left
$h = $rect.Bottom - $rect.Top

$bmp = New-Object System.Drawing.Bitmap $w, $h
$gfx = [System.Drawing.Graphics]::FromImage($bmp)
$hdc = $gfx.GetHdc()
$ok = [Win32Capture]::PrintWindow($hwnd, $hdc, 2)
$gfx.ReleaseHdc($hdc)
$bmp.Save("$PWD\screenshot.png", [System.Drawing.Imaging.ImageFormat]::Png)
$gfx.Dispose()
$bmp.Dispose()

# Real screen grab (shows the actual title bar / DWM styling).
$bmp2 = New-Object System.Drawing.Bitmap $w, $h
$gfx2 = [System.Drawing.Graphics]::FromImage($bmp2)
$gfx2.CopyFromScreen($rect.Left, $rect.Top, 0, 0, $bmp2.Size)
$bmp2.Save("$PWD\screenshot_screen.png", [System.Drawing.Imaging.ImageFormat]::Png)
$gfx2.Dispose()
$bmp2.Dispose()

[Win32Capture]::SetWindowPos($hwnd, [IntPtr](-2), 0, 0, 0, 0, 0x0043) | Out-Null
Get-Process pythonw -ErrorAction SilentlyContinue | Stop-Process -Force
Write-Output "Captured ${w}x${h} -> screenshot.png / screenshot_screen.png"
