# Getting Started - Power Mode Toggle

## What You Have

You now have 4 files in your Power Mode Switch folder:

1. **PowerModeToggle.bat** - The main toggle script
2. **Diagnostics.bat** - Diagnostic tool to check your system
3. **README.md** - Full documentation
4. **QUICK_REFERENCE.txt** - Quick reference guide

---

## 5-Minute Setup

### Step 1: Run Diagnostics (Recommended First)
1. Right-click `Diagnostics.bat`
2. Select **"Run as administrator"**
3. Review the power plans shown
4. Close the window

**Why?** This shows you what power plans your system actually has.

---

### Step 2: Test the Toggle Script
1. Right-click `PowerModeToggle.bat`
2. Select **"Run as administrator"**
3. Watch it automatically toggle power modes
4. Press any key when done

**Expected**: You should see your power mode change from Balanced to Ultimate (or vice versa).

---

### Step 3: (Optional) Create an Easy-Access Shortcut

**Desktop Shortcut with Admin Privileges:**

1. Right-click on your desktop
2. Select **New → Shortcut**
3. For the location, paste:
   ```
   C:\Users\dhava\OneDrive\Desktop\Power Mode Switch\PowerModeToggle.bat
   ```
4. Click **Next**, name it: `Toggle Power Mode`
5. Click **Finish**
6. Right-click the new shortcut on desktop
7. Select **Properties**
8. Click **Advanced...**
9. ✓ Check **"Run as administrator"**
10. Click **OK** twice

**Now**: You can click the desktop shortcut to toggle instantly!

---

### Step 4: (Optional) Add Keyboard Shortcut to Shortcut

1. Right-click your desktop shortcut
2. Select **Properties**
3. In the "Shortcut key" field, press a key combination (e.g., `Ctrl+Alt+P`)
4. Click **Apply → OK**

**Result**: Press that key combo to toggle anytime!

---

## First-Time Troubleshooting

### Issue: "Run as administrator" option missing
**Solution**: 
1. Search for "Command Prompt" in Windows
2. Right-click it and select "Run as administrator"
3. Navigate to the script folder and run:
   ```
   PowerModeToggle.bat
   ```

### Issue: Nothing happens when I run it
**Solution**:
1. Make sure you're running it as Administrator
2. Run `Diagnostics.bat` first to check your power plans
3. Check if your Windows version has Ultimate Performance mode available

### Issue: I see an error but didn't catch it
**Solution**:
1. Open Command Prompt as Administrator
2. Navigate to the script folder:
   ```
   cd "C:\Users\dhava\OneDrive\Desktop\Power Mode Switch"
   ```
3. Run the script:
   ```
   PowerModeToggle.bat
   ```
4. Now you can read the error messages before the window closes

---

## How to Use - Daily

### Quick Toggle
- Double-click your desktop shortcut (if you created it), OR
- Press your keyboard shortcut (if you set one up)

### From Command Prompt
```bash
cd "C:\Users\dhava\OneDrive\Desktop\Power Mode Switch"
PowerModeToggle.bat
```

### Verify Current Mode
```bash
powercfg /getactivescheme
```

---

## Customization (For Advanced Users)

### If Your GUIDs Are Different

1. Run `Diagnostics.bat` to see your power plan GUIDs
2. Open `PowerModeToggle.bat` with Notepad
3. Find these lines (around line 26-28):
   ```batch
   set "BALANCED_GUID=381b4222-f694-41f0-9685-ff5bb260df2e"
   set "ULTIMATE_GUID=e9a42b02-d5df-448d-aa00-03f14749eb61"
   ```
4. Replace with your actual GUIDs from Diagnostics output
5. Save the file

---

## Script Features Overview

### What It Does
✓ Automatically detects your current power mode  
✓ Switches to the opposite mode  
✓ Enables Ultimate Performance if it's missing  
✓ Shows clear console output  
✓ Requires Administrator (for security)  

### What It Doesn't Do
✗ Require a system restart  
✗ Install anything  
✗ Modify registry permanently  
✗ Create any system files  

### Safe to Use
- Changes only active power scheme (no permanent modifications)
- Fully reversible (just run again to switch back)
- No malware or third-party dependencies
- Open-source and fully commented code

---

## Performance Notes

### Balanced Mode
- CPU/GPU scales based on demand
- Lower power consumption
- Good for everyday use

### Ultimate Performance Mode
- Maximum CPU/GPU performance clock speeds
- Higher power consumption (~20-30% more)
- Best for gaming and heavy workloads

---

## Next Steps

1. ✓ Review the **QUICK_REFERENCE.txt** for common commands
2. ✓ Check **README.md** for detailed documentation
3. ✓ Run **Diagnostics.bat** if you have any issues
4. ✓ Create a desktop shortcut for easy access

---

## Questions?

All documentation is included in this folder:
- **README.md** - Comprehensive guide
- **QUICK_REFERENCE.txt** - Quick commands
- **This file (SETUP.md)** - Getting started

---

## System Requirements

- Windows 10 (version 1903+) or Windows 11
- Administrator access
- Command Prompt or PowerShell

---

## Tips for Best Results

💡 **Create a keyboard shortcut** for one-click toggling  
💡 **Run Diagnostics.bat** before your first toggle  
💡 **Pin to Start Menu** for quick access  
💡 **Check README.md** for advanced usage  

---

**You're all set! Enjoy easy power mode toggling! 🚀**
