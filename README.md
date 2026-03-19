# Power Mode Switcher

A Windows Batch script that toggles between **Balanced** and **Ultimate Performance** power modes with a single click.

> **Version**: 1.0 | **Updated**: March 2026 | **Tested**: Windows 10, Windows 11

---

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Setup Instructions](#setup-instructions)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Power Plans](#power-plans)
- [Customization](#customization)
- [Troubleshooting](#troubleshooting)
- [Verification](#verification)
- [Exit Codes](#exit-codes)
- [Advanced Usage](#advanced-usage)
- [Tips & Tricks](#tips--tricks)
- [System Impact](#system-impact)
- [Repository](#repository)
- [License](#license)

---

## Quick Start

**Get started in 30 seconds:**

```bash
Right-click PowerModeToggle.bat → Run as administrator
```

That's it! The script will automatically detect and toggle your power mode.

---

## ⚙️ Setup Instructions

**First-time setup? Follow these steps in order (run each as Administrator):**

### Step 1: Run Diagnostics
```bash
Right-click Diagnostics.bat → Run as administrator
```
This detects your system's power plans and auto-configures PowerModeToggle.bat

### Step 2: List Available Power Plans
```bash
Right-click ListPowerPlans.bat → Run as administrator
```
This shows all available power plans on your system

### Step 3: Start Toggling Power Modes
```bash
Right-click PowerModeToggle.bat → Run as administrator
```
Now you can toggle between power modes!

---

## Features

- 🎯 **Auto-Detection** — Detects currently active power plan
- ⚡ **Smart Toggle** — Switches modes with a single click
- 🔒 **Admin Check** — Verifies Administrator privileges
- 🚀 **Auto-Enable** — Automatically enables Ultimate Performance if missing
- 📊 **Clear Feedback** — Shows current and target modes
- ✨ **Well-Documented** — Code comments explain everything
- 🔧 **Customizable** — Easy to modify power plan GUIDs

---

## Requirements

| Item | Details |
|------|---------|
| **OS** | Windows 10 or Windows 11 |
| **Privileges** | Administrator rights (required) |
| **Shell** | Command Prompt or PowerShell |
| **Dependencies** | None |

---

## Installation

### Option 1: Simple (Recommended)
1. Save `PowerModeToggle.bat` to any folder
2. Right-click the file → "Run as administrator"

### Option 2: Desktop Shortcut with Admin
1. Right-click `PowerModeToggle.bat` → Send to → Desktop (create shortcut)
2. Right-click the shortcut → Properties → Advanced
3. Check "Run as administrator" → OK

### Option 3: Quick Shell Access
Add to PowerShell profile:
```powershell
function Toggle-PowerMode { & 'C:\path\to\PowerModeToggle.bat' }
```

---

## Usage

### Basic Execution
```bash
Right-click PowerModeToggle.bat → Run as administrator
```

### From Command Line
```bash
# Run from Command Prompt or PowerShell (as Administrator)
PowerModeToggle.bat
```

### Automated with Task Scheduler
1. Open Task Scheduler
2. Create New Task with Administrator privileges
3. Set action to run `PowerModeToggle.bat`
4. Configure schedule (e.g., 8 AM daily)

---

## Power Plans

### Balanced Mode
- **GUID**: `381b4222-f694-41f0-9685-ff5bb260df2e`
- **Use When**: General daily use, web browsing, office work
- **Power**: Moderate consumption
- **Performance**: Adequate for most tasks

### Ultimate Performance Mode
- **GUID**: `e9a42b02-d5df-448d-aa00-03f14749eb61`
- **Use When**: Gaming, video editing, intensive tasks
- **Power**: High consumption
- **Performance**: Maximum (no power-saving)

---

## Customization

If your Ultimate Performance GUID differs from default:

```batch
REM Find this line:
set "ULTIMATE_GUID=e9a42b02-d5df-448d-aa00-03f14749eb61"

REM Replace with your GUID:
set "ULTIMATE_GUID=YOUR-GUID-HERE"
```

### Find Your Power Plan GUIDs

Run this command:
```bash
powercfg /list
```

Output example:
```
Existing Power Schemes (* Active)
-----------------------------------
Power Scheme GUID: 381b4222-f694-41f0-9685-ff5bb260df2e  (Balanced) *
Power Scheme GUID: 8c5e7fda-e8bf-45a7-a48b-0b6f8a3e9c1e  (Power saver)
Power Scheme GUID: e9a42b02-d5df-448d-aa00-03f14749eb61  (Ultimate Performance)
```

---

## Troubleshooting

### ❌ Admin Privileges Required
**Error**: "This script requires Administrator privileges!"  
**Fix**: Right-click file → "Run as administrator"

### ❌ Ultimate Performance Not Found
**Error**: "Ultimate Performance mode not found!"  
**Fixes**:
- Script auto-enables it (if fails, check Windows updates)
- Verify Windows edition (Pro/Enterprise needed)
- Manual enable: Settings > System > Power & sleep > Additional power settings

### ❌ Failed to Switch Modes
**Error**: "Failed to switch modes"  
**Checks**:
1. Verify running as Administrator
2. Install latest Windows updates
3. Test GUID: `powercfg /query YOUR-GUID`

### ❌ No Error Message Shown
**Error**: Script pauses without showing error  
**Fix**: Run from Command Prompt; check exit code before pause

---

## Verification

### Check Current Power Plan
```bash
powercfg /getactivescheme
```

### List All Available Plans
```bash
powercfg /list
```

### View Power Plan Details
```bash
powercfg /query e9a42b02-d5df-448d-aa00-03f14749eb61
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | ✓ Successfully toggled power mode |
| 1 | ✗ Not running as Administrator |
| 2 | ✗ Failed to enable Ultimate Performance |
| 3 | ✗ Failed to switch power plan |
| 4 | ✗ Unknown power plan detected |

---

## Advanced Usage

### Call from Another Batch Script
```batch
call PowerModeToggle.bat
if %errorlevel% equ 0 (
    echo Power mode changed successfully
) else (
    echo Failed (error: %errorlevel%)
)
```

---

## Tips & Tricks

💡 **Desktop Shortcut with Hotkey** — Create shortcut, enable admin, assign Win+Alt+P in Properties

💡 **Task Scheduler Automation** — Schedule toggles at work/home times

💡 **Windows Terminal Function** — Add alias to PowerShell profile for quick access

💡 **Monitor Power Usage** — Track which mode you use most for optimization

---

## System Impact

| Aspect | Details |
|--------|---------|
| **Speed** | Switching takes ~1-2 seconds |
| **Restart** | Not required |
| **Scope** | Affects CPU, GPU, monitor power settings |
| **Duration** | Changes persist until manually changed |

---

## Important Notes

- ✅ Compatible with Windows 10 & Windows 11
- ⚠️ Ultimate Performance requires Pro/Enterprise edition
- ⚠️ Administrator privileges required (Windows security)
- ℹ️ No system restart needed for changes

---

## License

This script is provided as-is for personal and professional use.

---

## Repository

**GitHub**: [DhavalMCA/Power-Mode-Switcher](https://github.com/DhavalMCA/Power-Mode-Switcher)

Clone the repository:
```bash
git clone https://github.com/DhavalMCA/Power-Mode-Switcher.git
```

---

**Version 1.0** | **March 2026** | Tested on Windows 10 & 11
