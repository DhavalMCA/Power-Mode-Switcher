"""
Power Mode Switch — Windows power-plan manager.

Run from this folder:

    python power_mode.py            # modern GUI (default)
    python power_mode.py toggle     # CLI: flip Balanced <-> Ultimate
    python power_mode.py list       # CLI: list plans + active
    python power_mode.py diag       # CLI: diagnostic report

Requires Administrator privileges for any write (toggle / enable ultimate).
"""
from __future__ import annotations

import argparse
import ctypes
import os
import re
import subprocess
import sys
from dataclasses import dataclass

__version__ = "1.1.0"

APP_NAME = "Power Mode Switch"
APP_ID = "PowerModeSwitch.1"

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BALANCED_GUID = "381b4222-f694-41f0-9685-ff5bb260df2e"
ULTIMATE_SCHEMA = "e9a42b02-d5df-448d-aa00-03f14749eb61"
GUID_RE = re.compile(
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)
PLAN_LINE_RE = re.compile(
    r"Power Scheme GUID:\s*(?P<guid>[0-9a-fA-F-]{36})\s*(?:\((?P<name>[^)]*)\))?\s*(?P<active>\*)?",
    re.IGNORECASE,
)

# Hide the console window that would otherwise flash on every powercfg call
# when the app is packaged as a windowed executable.
_CREATE_NO_WINDOW = 0x08000000


class PowerModeError(RuntimeError):
    """Raised when a powercfg call fails or output cannot be parsed."""


@dataclass(frozen=True)
class Plan:
    """One Windows power scheme."""

    guid: str
    name: str
    active: bool = False

    @property
    def short_guid(self) -> str:
        return self.guid.lower()


# ---------------------------------------------------------------------------
# powercfg wrappers (pure stdlib, safe to import without tkinter)
# ---------------------------------------------------------------------------


def is_admin() -> bool:
    """True when the current process is running elevated."""
    if sys.platform != "win32":
        return False
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def is_frozen() -> bool:
    """True when running from a PyInstaller bundle."""
    return bool(getattr(sys, "frozen", False))


def _powercfg_exe() -> str:
    root = os.environ.get("SystemRoot", r"C:\Windows")
    candidate = os.path.join(root, "System32", "powercfg.exe")
    return candidate if os.path.isfile(candidate) else "powercfg"


def _run(*args: str) -> tuple[int, str, str]:
    """Run powercfg with the given arguments and capture its output."""
    flags = _CREATE_NO_WINDOW if sys.platform == "win32" else 0
    p = subprocess.run(
        [_powercfg_exe(), *args],
        capture_output=True,
        text=True,
        errors="replace",
        creationflags=flags,
    )
    return p.returncode, p.stdout, p.stderr


def list_plans() -> str:
    """Raw output of `powercfg /list`. Raises PowerModeError on failure."""
    rc, out, err = _run("/list")
    if rc != 0:
        raise PowerModeError(err.strip() or "powercfg /list failed")
    return out


def parse_plans(text: str) -> list[Plan]:
    """Parse `powercfg /list` output into Plan records."""
    plans: list[Plan] = []
    for line in text.splitlines():
        m = PLAN_LINE_RE.search(line)
        if not m:
            continue
        plans.append(
            Plan(
                guid=m.group("guid"),
                name=(m.group("name") or "Unnamed plan").strip(),
                active=bool(m.group("active")),
            )
        )
    return plans


def get_plans() -> list[Plan]:
    """Parsed list of power plans."""
    return parse_plans(list_plans())


def find_guid(fragment: str) -> str | None:
    """GUID of the first plan whose line contains `fragment` (case-insensitive)."""
    for line in list_plans().splitlines():
        if fragment.lower() in line.lower():
            m = GUID_RE.search(line)
            if m:
                return m.group(0)
    return None


def get_active() -> tuple[str, str]:
    """Return (active_guid, full_line) from `powercfg /getactivescheme`."""
    rc, out, err = _run("/getactivescheme")
    if rc != 0:
        raise PowerModeError(err.strip() or "powercfg /getactivescheme failed")
    full = out.strip()
    m = GUID_RE.search(full)
    if not m:
        raise PowerModeError(f"Could not parse GUID from: {full!r}")
    return m.group(0), full


def enable_ultimate() -> str:
    """Make the hidden Ultimate Performance scheme available; return its GUID.

    Idempotent: returns the existing scheme instead of duplicating it.
    """
    existing = find_guid("Ultimate")
    if existing:
        return existing

    rc, _, err = _run("-duplicatescheme", ULTIMATE_SCHEMA)
    if rc != 0:
        raise PowerModeError(err.strip() or "Failed to enable Ultimate Performance")
    g = find_guid("Ultimate")
    if not g:
        raise PowerModeError("Ultimate Performance enabled but GUID not found")
    return g


def set_active(guid: str) -> None:
    """Activate the plan with the given GUID."""
    rc, _, err = _run("/setactive", guid)
    if rc != 0:
        raise PowerModeError(err.strip() or f"setactive {guid} failed")


# ---------------------------------------------------------------------------
# Elevation
# ---------------------------------------------------------------------------


def detect_plan_mode(guid: str, name: str, ultimate_guid: str = "") -> str:
    """Categorize a plan into 'ultimate', 'balanced', 'saver', 'high', or 'unknown'."""
    g = (guid or "").lower()
    n = (name or "").lower()
    if (ultimate_guid and g == ultimate_guid.lower()) or "ultimate" in n:
        return "ultimate"
    if g == BALANCED_GUID.lower() or "balanced" in n:
        return "balanced"
    if "saver" in n:
        return "saver"
    if "high performance" in n:
        return "high"
    return "unknown"


def relaunch_as_admin() -> bool:
    """Re-launch this app elevated via UAC.

    Returns False when elevation was cancelled or failed (the caller keeps
    running). On success the current process exits.
    """
    if sys.platform != "win32":
        return False

    exe = sys.executable
    cwd = os.getcwd()
    if is_frozen():
        # sys.argv[0] is the exe itself; only forward real arguments.
        args = sys.argv[1:]
    else:
        # Pass absolute script path so elevation doesn't fail when cwd defaults to System32
        script = os.path.abspath(sys.argv[0])
        args = [script] + sys.argv[1:]
    params = " ".join(f'"{a}"' for a in args)

    try:
        rc = ctypes.windll.shell32.ShellExecuteW(None, "runas", exe, params, cwd, 1)
    except Exception:
        return False

    # ShellExecuteW returns a value > 32 on success.
    if int(rc) > 32:
        sys.exit(0)
    return False


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

# Exit codes match the legacy .bat scripts:
#   0 success, 1 not elevated, 2 ultimate enable failed,
#   3 setactive failed, 4 unknown current plan


def _print_header(text: str) -> None:
    bar = "=" * 60
    print(f"\n{bar}\n{text}\n{bar}")


def cmd_toggle(_args: argparse.Namespace) -> int:
    if not is_admin():
        _print_header("ERROR: Administrator privileges required")
        print("Re-run from an elevated (Run as administrator) terminal.")
        return 1

    _print_header("Detecting current power plan")
    active_guid, full = get_active()
    print(full)

    plans = get_plans()
    active_plan = next((p for p in plans if p.guid.lower() == active_guid.lower()), None)
    active_name = active_plan.name if active_plan else ""

    try:
        ultimate_guid = find_guid("Ultimate") or enable_ultimate()
    except PowerModeError as e:
        print(f"\nERROR: {e}")
        return 2
    print(f"\nUltimate Performance GUID: {ultimate_guid}\n")

    balanced_guid = next((p.guid for p in plans if "balanced" in p.name.lower()), BALANCED_GUID)

    mode = detect_plan_mode(active_guid, active_name, ultimate_guid)
    if mode == "balanced":
        print("Current: BALANCED -> switching to ULTIMATE PERFORMANCE")
        set_active(ultimate_guid)
    elif mode == "ultimate":
        print("Current: ULTIMATE PERFORMANCE -> switching to BALANCED")
        set_active(balanced_guid)
    else:
        print(f"Current: UNKNOWN ({active_guid} - {active_name or 'unnamed'})")
        print("Cannot identify as Balanced or Ultimate Performance.")
        return 4

    _, new_full = get_active()
    print(f"\nNow active: {new_full}")
    _print_header("SUCCESS: Power mode toggled")
    return 0


def cmd_list(_args: argparse.Namespace) -> int:
    _print_header("ALL AVAILABLE POWER PLANS")
    print(list_plans())
    _print_header("CURRENT ACTIVE POWER PLAN")
    _, full = get_active()
    print(full)
    return 0


def cmd_diag(_args: argparse.Namespace) -> int:
    elevated = is_admin()
    _print_header("POWER MODE TOGGLE — DIAGNOSTIC REPORT")
    print(f"Privileges: {'Administrator (elevated)' if elevated else 'Standard user (read-only)'}")
    print("\n[1/3] Listing power plans:")
    print(list_plans())
    print("[2/3] Active plan:")
    _, full = get_active()
    print(f"  {full}\n")
    print("[3/3] Ultimate Performance availability:")
    ult = find_guid("Ultimate")
    if not ult and elevated:
        try:
            ult = enable_ultimate()
        except PowerModeError as e:
            print(f"  FAILED to enable: {e}")
            return 2
    if ult:
        print(f"  Available. GUID: {ult}")
    else:
        print("  Not currently enabled. Run with Administrator rights to enable it.")
    print(f"\nBalanced GUID:        {BALANCED_GUID}")
    print(f"Ultimate Performance: {ult or 'Not enabled'}")
    print("\nDiagnostics complete.")
    return 0
    _, full = get_active()
    print(f"  {full}\n")
    print("[3/3] Ultimate Performance availability:")
    try:
        ult = find_guid("Ultimate") or enable_ultimate()
    except PowerModeError as e:
        print(f"  FAILED: {e}")
        return 2
    print(f"  Available. GUID: {ult}")
    print(f"\nBalanced GUID:        {BALANCED_GUID}")
    print(f"Ultimate Performance: {ult}")
    print("\nDiagnostics complete.")
    return 0


def _cmd_relaunch_admin(_args: argparse.Namespace) -> int:
    relaunch_as_admin()
    return 0


# Handlers are looked up by name at call time so tests can monkey-patch them.
_HANDLER_NAMES = {
    "toggle": "cmd_toggle",
    "list":   "cmd_list",
    "diag":   "cmd_diag",
}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="power_mode",
        description="Toggle Windows power plans between Balanced and Ultimate Performance.",
    )
    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("toggle", help="Toggle between Balanced and Ultimate Performance")
    sub.add_parser("list", help="List all power plans and the active one")
    sub.add_parser("diag", help="Run a full diagnostic report")
    sub.add_parser("gui", help="Launch the animated GUI")
    sub.add_parser("relaunch-admin", help="Re-launch as Administrator and exit")
    return p


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    # No command (or `-h`/`--help`) → either GUI or help
    if not argv or argv[0].startswith("-"):
        if argv and argv[0] in ("-h", "--help"):
            build_parser().print_help()
            return 0
        return run_gui()

    args = build_parser().parse_args(argv)
    if args.cmd == "gui":
        return run_gui()
    if args.cmd == "relaunch-admin":
        return _cmd_relaunch_admin(args)

    name = _HANDLER_NAMES.get(args.cmd)
    if name is None:
        build_parser().print_help()
        return 0
    handler = getattr(sys.modules[__name__], name)
    return handler(args)


def run_gui() -> int:
    """Entry point for the GUI (imported lazily so the CLI stays tkinter-free)."""
    from gui import launch

    return launch()


if __name__ == "__main__":
    sys.exit(main())
