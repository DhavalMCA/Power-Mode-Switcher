# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build definition for Power Mode Switch.

Build with:
    .\\build.ps1
or:
    .venv\\Scripts\\pyinstaller --noconfirm --clean PowerModeSwitch.spec
"""
from PyInstaller.utils.hooks import collect_data_files

# CustomTkinter ships theme JSON files and fonts that must be bundled.
datas = collect_data_files("customtkinter")
datas += [
    ("assets/icon.ico", "assets"),
    ("assets/icon-32.png", "assets"),
]

a = Analysis(
    ["power_mode.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["PIL", "numpy", "matplotlib", "scipy", "pytest"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="PowerModeSwitch",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="assets/icon.ico",
    version="version_info.txt",
    uac_admin=True,
)
