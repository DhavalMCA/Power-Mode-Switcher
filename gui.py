"""Modern Windows 11 Fluent interface for Power Mode Switch.

A clean, card-based interface inspired by Windows 11 Settings and PowerToys.
"""
from __future__ import annotations

import ctypes
import os
import queue
import sys
import threading
import tkinter as tk

# Auto-discover local virtual environment if running with global Python interpreter
_base_dir = os.path.dirname(os.path.abspath(__file__))
for _vname in (".venv", "venv"):
    _site_pkg = os.path.join(_base_dir, _vname, "Lib", "site-packages")
    if os.path.isdir(_site_pkg) and _site_pkg not in sys.path:
        sys.path.insert(0, _site_pkg)

# Suppress harmless CustomTkinter font warning on Windows systems where
# AddFontResourceExW is blocked for user-space OTF files.
_orig_stderr = sys.stderr
try:
    from io import StringIO
    sys.stderr = StringIO()
    import customtkinter as ctk
except ModuleNotFoundError:
    sys.stderr = _orig_stderr
    print(f"\n[ERROR] CustomTkinter is not installed in this Python environment ({sys.executable}).\n")
    print("To run Power Mode Switch, please use one of the following:")
    print(r"  1. Run with the local virtual environment directly:  .\.venv\Scripts\python.exe gui.py")
    print(r"  2. Or activate the virtual environment:             .\.venv\Scripts\activate; python gui.py")
    print(r"  3. Or install requirements into this interpreter:    pip install -r requirements.txt" + "\n")
    sys.exit(1)
finally:
    sys.stderr = _orig_stderr

import power_mode as core

# ---------------------------------------------------------------------------
# Theme & Palette (Windows 11 Fluent Dark)
# ---------------------------------------------------------------------------

BG = "#0D1117"
SURFACE = "#161B22"
SURFACE_ALT = "#1F242C"
SURFACE_HOVER = "#272E38"
BORDER = "#2A313C"
BORDER_LIGHT = "#353D4B"

TEXT = "#F0F3F6"
TEXT_MUTED = "#9AA2AE"
TEXT_DIM = "#656D76"

ACCENT = "#38BDF8"
SUCCESS = "#3FB950"
WARNING = "#D29922"
DANGER = "#F85149"

MODE_PROFILES = {
    "ultimate": {
        "icon": "⚡",
        "title": "Ultimate Performance",
        "desc": "Delivers unconstrained peak performance with zero power-saving limits.",
        "accent": "#F97316",
        "badge_bg": "#34180A",
    },
    "balanced": {
        "icon": "⚖",
        "title": "Balanced",
        "desc": "Automatically balances full performance with energy efficiency and low heat.",
        "accent": "#38BDF8",
        "badge_bg": "#0D2538",
    },
    "saver": {
        "icon": "🍃",
        "title": "Power Saver",
        "desc": "Reduces processor frequency to maximize battery life and minimize thermal output.",
        "accent": "#3FB950",
        "badge_bg": "#0E2916",
    },
    "high": {
        "icon": "🚀",
        "title": "High Performance",
        "desc": "Favors speed and performance, keeping clocks elevated for intensive workloads.",
        "accent": "#A855F7",
        "badge_bg": "#2A143D",
    },
    "unknown": {
        "icon": "⚙",
        "title": "Custom Scheme",
        "desc": "A custom or manufacturer-configured power plan on this system.",
        "accent": "#9AA2AE",
        "badge_bg": "#1F242C",
    },
}

FONT = "Segoe UI"
MONO = "Consolas"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def rgb_to_hex(r: float, g: float, b: float) -> str:
    def clamp(v: float) -> int:
        return max(0, min(255, int(round(v))))
    return f"#{clamp(r):02x}{clamp(g):02x}{clamp(b):02x}"


def blend(c1: str, c2: str, t: float) -> str:
    r1, g1, b1 = hex_to_rgb(c1)
    r2, g2, b2 = hex_to_rgb(c2)
    return rgb_to_hex(r1 + (r2 - r1) * t, g1 + (g2 - g1) * t, b1 + (b2 - b1) * t)


def resource_path(*parts: str) -> str:
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *parts)


def apply_dark_titlebar(window: tk.Misc) -> None:
    """Ask DWM to draw a dark title bar (Windows 10 1903+)."""
    if sys.platform != "win32":
        return
    try:
        window.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id()) or window.winfo_id()
        enabled = ctypes.c_int(1)
        for attr in (20, 19):  # DWMWA_USE_IMMERSIVE_DARK_MODE (+ legacy)
            if ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, attr, ctypes.byref(enabled), ctypes.sizeof(enabled)
            ) == 0:
                break
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Power Plan Row (Fluent Card)
# ---------------------------------------------------------------------------


class PlanCard(ctk.CTkFrame):
    """Fluent card representing one Windows power plan."""

    def __init__(self, master: tk.Misc, plan: core.Plan, selected: bool,
                 on_select, on_activate) -> None:
        super().__init__(
            master,
            fg_color=SURFACE_ALT if not selected else "#232A34",
            corner_radius=10,
            border_width=2 if selected else 1,
            border_color=ACCENT if selected else BORDER,
            height=60,
        )
        self.grid_propagate(False)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.plan = plan
        self._selected = selected
        self._hover = False
        self._on_select = on_select
        self._on_activate = on_activate

        # Mode status indicator dot
        dot_color = SUCCESS if plan.active else (ACCENT if selected else TEXT_DIM)
        self._dot = ctk.CTkLabel(
            self, text="●", width=20, font=(FONT, 12), text_color=dot_color
        )
        self._dot.grid(row=0, column=0, rowspan=2, padx=(14, 10))

        # Plan Name
        self._name = ctk.CTkLabel(
            self, text=plan.name, anchor="w", font=(FONT, 12, "bold"), text_color=TEXT
        )
        self._name.grid(row=0, column=1, sticky="sw", pady=(4, 0))

        # Monospace GUID
        self._guid = ctk.CTkLabel(
            self, text=plan.guid, anchor="w", font=(MONO, 9), text_color=TEXT_MUTED
        )
        self._guid.grid(row=1, column=1, sticky="nw", pady=(0, 4))

        # Right-side action: either ACTIVE chip or Activate button
        if plan.active:
            self._chip = ctk.CTkLabel(
                self, text="ACTIVE", width=62, height=24,
                corner_radius=6, fg_color="#12351E", text_color=SUCCESS,
                font=(FONT, 9, "bold")
            )
            self._chip.grid(row=0, column=2, rowspan=2, padx=(8, 14))
        else:
            self._btn_apply = ctk.CTkButton(
                self, text="Activate", width=74, height=26, corner_radius=6,
                fg_color=SURFACE, hover_color=SURFACE_HOVER,
                border_width=1, border_color=BORDER_LIGHT, text_color=TEXT,
                font=(FONT, 10, "bold"),
                command=lambda: self._on_activate(self.plan.guid)
            )
            self._btn_apply.grid(row=0, column=2, rowspan=2, padx=(8, 14))

        self._bind_tree(self)

    def _bind_tree(self, widget: tk.Misc) -> None:
        # Do not bind row clicks onto the Activate button to prevent double triggering
        if getattr(self, "_btn_apply", None) is widget:
            return
        widget.bind("<Button-1>", lambda _e: self._on_select(self.plan.guid))
        widget.bind("<Double-Button-1>", lambda _e: self._on_activate(self.plan.guid))
        widget.bind("<Enter>", self._on_enter)
        widget.bind("<Leave>", self._on_leave)
        for child in widget.winfo_children():
            if getattr(self, "_btn_apply", None) is not child:
                self._bind_tree(child)

    def _on_enter(self, _event: tk.Event) -> None:
        if not self._selected:
            self.configure(fg_color=SURFACE_HOVER, border_color=BORDER_LIGHT)

    def _on_leave(self, _event: tk.Event) -> None:
        if not self._selected:
            self.configure(fg_color=SURFACE_ALT, border_color=BORDER)


# ---------------------------------------------------------------------------
# Modal Dialog
# ---------------------------------------------------------------------------


class MessageDialog(ctk.CTkToplevel):
    """Fluent dialog replacement for tkinter's messagebox."""

    def __init__(self, master: tk.Misc, title: str, message: str,
                 kind: str = "info", buttons=None) -> None:
        super().__init__(master, fg_color=BG)
        try:
            self.config(background=BG)
        except Exception:
            pass
        self.withdraw()
        self.title(title)
        self.resizable(False, False)
        self.transient(master)
        self.result = None

        accent = SUCCESS if kind == "success" else (WARNING if kind == "warning" else (DANGER if kind == "error" else ACCENT))
        buttons = buttons or [("OK", True, "primary")]
        buttons = [
            (b[0], b[1], b[2]) if len(b) >= 3 else (b[0], b[1], "secondary")
            for b in buttons
        ]

        wrap = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=12,
                            border_width=1, border_color=BORDER)
        wrap.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(wrap, text=title, anchor="w", justify="left",
                     font=(FONT, 14, "bold"), text_color=TEXT,
                     wraplength=360).pack(fill="x", padx=18, pady=(18, 0))

        ctk.CTkLabel(wrap, text=message, anchor="w", justify="left",
                     font=(FONT, 11), text_color=TEXT_MUTED,
                     wraplength=360).pack(fill="x", padx=18, pady=(10, 0))

        row = ctk.CTkFrame(wrap, fg_color="transparent")
        row.pack(fill="x", padx=18, pady=(20, 18))

        cancel_val = buttons[0][1]
        for label, value, style in reversed(buttons):
            if style == "primary":
                btn = ctk.CTkButton(row, text=label, height=34, width=96,
                                    corner_radius=8, fg_color=accent,
                                    text_color="#0D1117", font=(FONT, 11, "bold"),
                                    command=lambda v=value: self._close(v))
            else:
                btn = ctk.CTkButton(row, text=label, height=34, width=96,
                                    corner_radius=8, fg_color=SURFACE_ALT,
                                    hover_color=SURFACE_HOVER, border_width=1,
                                    border_color=BORDER, text_color=TEXT,
                                    font=(FONT, 11, "bold"),
                                    command=lambda v=value: self._close(v))
            btn.pack(side="right", padx=(8, 0))

        self.protocol("WM_DELETE_WINDOW", lambda: self._close(cancel_val))
        self.bind("<Escape>", lambda _e: self._close(cancel_val))

    def _close(self, value) -> None:
        self.result = value
        self.grab_release()
        self.destroy()

    def show(self):
        self.deiconify()
        self.update_idletasks()
        apply_dark_titlebar(self)

        width = 420
        height = max(180, self.winfo_reqheight())
        try:
            px = self.master.winfo_rootx()
            py = self.master.winfo_rooty()
            pw = self.master.winfo_width()
            ph = self.master.winfo_height()
        except tk.TclError:
            px = py = pw = ph = 0
        x = max(0, px + (pw - width) // 2)
        y = max(0, py + (ph - height) // 3)
        self.geometry(f"{width}x{height}+{x}+{y}")

        self.lift()
        self.focus_force()
        self.grab_set()
        self.wait_window(self)
        return self.result


# ---------------------------------------------------------------------------
# Main Application
# ---------------------------------------------------------------------------


class App(ctk.CTk):
    def __init__(self) -> None:
        super().__init__(fg_color=BG)
        try:
            self.config(background=BG)
        except Exception:
            pass

        self.title(core.APP_NAME)
        # Scaled window geometry designed to fit comfortably on all displays
        self.geometry("880x560")
        self.minsize(820, 520)

        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(core.APP_ID)
        except Exception:
            pass

        icon = resource_path("assets", "icon.ico")
        if os.path.isfile(icon):
            try:
                self.iconbitmap(icon)
            except tk.TclError:
                pass

        self._plans: list[core.Plan] = []
        self._active_guid = ""
        self._ultimate_guid = ""
        self._selected_guid = ""
        self._is_admin = core.is_admin()
        self._busy = False
        self._building = True
        self._prompted = False
        self._results: queue.Queue = queue.Queue()

        self._build()
        self._building = False
        self._sync_controls()

        self.bind("<F5>", lambda _e: self.refresh(announce=True))
        self.bind("<Control-q>", lambda _e: self.destroy())

        self.after(100, lambda: apply_dark_titlebar(self))
        self.after(700, lambda: apply_dark_titlebar(self))
        self.bind("<Map>", lambda e: apply_dark_titlebar(self) if e.widget is self else None)

        self.after(50, self._drain_results)
        self.after(150, lambda: self.refresh(announce=True))
        self.after(700, self._maybe_prompt_admin)

    # ----- layout -------------------------------------------------------

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)  # Schemes list area expands

        self._build_header()
        self._build_hero()
        self._build_schemes_section()
        self._build_footer()

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(16, 10))
        header.grid_columnconfigure(1, weight=1)

        # App Icon & Title block
        logo = self._make_logo(header)
        logo.grid(row=0, column=0, rowspan=2, padx=(0, 12), sticky="w")

        ctk.CTkLabel(
            header, text=core.APP_NAME, anchor="w",
            font=(FONT, 17, "bold"), text_color=TEXT
        ).grid(row=0, column=1, sticky="sw")
        ctk.CTkLabel(
            header, text="Windows Power Plan & Performance Manager", anchor="w",
            font=(FONT, 11), text_color=TEXT_MUTED
        ).grid(row=1, column=1, sticky="nw", pady=(1, 0))

        # Right header controls: Admin Badge + Refresh
        ctrls = ctk.CTkFrame(header, fg_color="transparent")
        ctrls.grid(row=0, column=2, rowspan=2, sticky="e")

        pill_color = "#12281D" if self._is_admin else "#2A2012"
        pill_text = SUCCESS if self._is_admin else WARNING
        pill = ctk.CTkFrame(ctrls, fg_color=pill_color, corner_radius=14,
                            border_width=1, border_color=pill_text)
        pill.pack(side="left", padx=(0, 10))

        dot = ctk.CTkLabel(pill, text="●", font=(FONT, 8), text_color=pill_text)
        dot.pack(side="left", padx=(10, 4), pady=5)
        lbl_text = "Administrator" if self._is_admin else "Standard user · Click to elevate"
        lbl = ctk.CTkLabel(pill, text=lbl_text, font=(FONT, 10, "bold"), text_color=pill_text)
        lbl.pack(side="left", padx=(0, 10), pady=5)

        if not self._is_admin:
            for w in (pill, dot, lbl):
                w.configure(cursor="hand2")
                w.bind("<Button-1>", lambda _e: self._on_elevate())

        self.btn_refresh = ctk.CTkButton(
            ctrls, text="↻ Refresh", width=82, height=28, corner_radius=8,
            fg_color=SURFACE, hover_color=SURFACE_HOVER,
            border_width=1, border_color=BORDER, text_color=TEXT_MUTED,
            font=(FONT, 10, "bold"), command=lambda: self.refresh(announce=True),
        )
        self.btn_refresh.pack(side="left")

    def _make_logo(self, parent: tk.Misc) -> tk.Misc:
        png = resource_path("assets", "icon-32.png")
        if os.path.isfile(png):
            try:
                self._logo_image = tk.PhotoImage(file=png)
                return tk.Label(parent, image=self._logo_image, bg=BG, bd=0, highlightthickness=0)
            except tk.TclError:
                pass
        canvas = tk.Canvas(parent, width=32, height=32, bg=BG, highlightthickness=0, bd=0)
        canvas.create_oval(2, 2, 30, 30, fill=SURFACE, outline=ACCENT, width=2)
        canvas.create_line(16, 8, 16, 17, fill=ACCENT, width=2.5, capstyle="round")
        return canvas

    def _build_hero(self) -> None:
        """Top active power mode card with instant segmented switcher."""
        hero = ctk.CTkFrame(
            self, fg_color=SURFACE, corner_radius=14,
            border_width=1, border_color=BORDER
        )
        self.hero_card = hero
        hero.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 14))
        hero.grid_columnconfigure(1, weight=1)

        # Left: Mode Icon Badge
        self.hero_icon_frame = ctk.CTkFrame(
            hero, width=54, height=54, corner_radius=12,
            fg_color="#0D2538", border_width=1, border_color="#1E3A8A"
        )
        self.hero_icon_frame.grid(row=0, column=0, rowspan=3, padx=(18, 14), pady=16)
        self.hero_icon_frame.pack_propagate(False)

        self.hero_icon_lbl = ctk.CTkLabel(
            self.hero_icon_frame, text="⚖", font=(FONT, 22), text_color=ACCENT
        )
        self.hero_icon_lbl.place(relx=0.5, rely=0.5, anchor="center")

        # Center: Active Mode Details
        meta_row = ctk.CTkFrame(hero, fg_color="transparent")
        meta_row.grid(row=0, column=1, sticky="w", pady=(16, 0))

        ctk.CTkLabel(
            meta_row, text="ACTIVE POWER MODE", font=(FONT, 9, "bold"), text_color=TEXT_DIM
        ).pack(side="left", padx=(0, 8))

        self.hero_status_chip = ctk.CTkLabel(
            meta_row, text="ACTIVE", width=52, height=18,
            corner_radius=4, fg_color="#12351E", text_color=SUCCESS,
            font=(FONT, 8, "bold")
        )
        self.hero_status_chip.pack(side="left")

        self.hero_title = ctk.CTkLabel(
            hero, text="Detecting active plan…", anchor="w",
            font=(FONT, 16, "bold"), text_color=TEXT
        )
        self.hero_title.grid(row=1, column=1, sticky="w", pady=(1, 0))

        self.hero_desc = ctk.CTkLabel(
            hero, text="Reading Windows active power scheme configuration…",
            anchor="w", font=(FONT, 11), text_color=TEXT_MUTED
        )
        self.hero_desc.grid(row=2, column=1, sticky="w", pady=(2, 16))

        # Right: Segmented Quick-Switch Control
        switch_box = ctk.CTkFrame(hero, fg_color="transparent")
        switch_box.grid(row=0, column=2, rowspan=3, padx=(14, 18), pady=16, sticky="e")

        ctk.CTkLabel(
            switch_box, text="QUICK SWITCH", font=(FONT, 9, "bold"), text_color=TEXT_DIM
        ).pack(anchor="e", pady=(0, 6))

        self.seg_container = ctk.CTkFrame(
            switch_box, fg_color=BG, corner_radius=10, border_width=1, border_color=BORDER
        )
        self.seg_container.pack()

        self.btn_seg_balanced = ctk.CTkButton(
            self.seg_container, text="⚖ Balanced", width=110, height=34, corner_radius=8,
            font=(FONT, 11, "bold"), command=lambda: self._on_switch_target("balanced")
        )
        self.btn_seg_balanced.pack(side="left", padx=3, pady=3)

        self.btn_seg_ultimate = ctk.CTkButton(
            self.seg_container, text="⚡ Ultimate", width=110, height=34, corner_radius=8,
            font=(FONT, 11, "bold"), command=lambda: self._on_switch_target("ultimate")
        )
        self.btn_seg_ultimate.pack(side="left", padx=(0, 3), pady=3)

    def _build_schemes_section(self) -> None:
        """Lower card holding the complete list of system power plans."""
        section = ctk.CTkFrame(
            self, fg_color=SURFACE, corner_radius=14,
            border_width=1, border_color=BORDER
        )
        section.grid(row=2, column=0, sticky="nsew", padx=24, pady=(0, 12))
        section.grid_columnconfigure(0, weight=1)
        section.grid_rowconfigure(2, weight=1)

        # Header of Schemes Card
        head = ctk.CTkFrame(section, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", padx=18, pady=(14, 8))
        head.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            head, text="All Available Power Schemes", anchor="w",
            font=(FONT, 13, "bold"), text_color=TEXT
        ).grid(row=0, column=0, sticky="w")

        self.count_chip = ctk.CTkLabel(
            head, text="—", width=62, height=22, corner_radius=6,
            fg_color=SURFACE_ALT, text_color=TEXT_MUTED, font=(FONT, 9, "bold")
        )
        self.count_chip.grid(row=0, column=1, sticky="e")

        # Contextual banner: enable Ultimate if hidden
        self.ultimate_banner = ctk.CTkFrame(
            section, fg_color="#182234", corner_radius=8,
            border_width=1, border_color="#1E3A8A"
        )
        self.ultimate_banner.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 8))
        self.ultimate_banner.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            self.ultimate_banner, text="⚡", font=(FONT, 12), text_color=ACCENT
        ).grid(row=0, column=0, padx=(12, 6), pady=7)
        ctk.CTkLabel(
            self.ultimate_banner,
            text="Ultimate Performance is currently hidden by Windows. Unlock it for maximum speed.",
            anchor="w", font=(FONT, 10), text_color=TEXT_MUTED
        ).grid(row=0, column=1, sticky="w", pady=7)

        self.btn_enable_banner = ctk.CTkButton(
            self.ultimate_banner, text="Unlock Scheme", width=108, height=26, corner_radius=6,
            fg_color=ACCENT, hover_color="#0284C7", text_color="#0D1117",
            font=(FONT, 10, "bold"), command=self._on_enable_ultimate
        )
        self.btn_enable_banner.grid(row=0, column=2, padx=(8, 12), pady=7)

        # Scrollable container for scheme cards
        self.plans_host = ctk.CTkScrollableFrame(
            section, fg_color="transparent",
            scrollbar_button_color=SURFACE_ALT,
            scrollbar_button_hover_color=SURFACE_HOVER,
        )
        self.plans_host.grid(row=2, column=0, sticky="nsew", padx=14, pady=(0, 12))
        self.plans_host.grid_columnconfigure(0, weight=1)

        self.plan_empty = ctk.CTkLabel(
            self.plans_host, text="No power plans found.\nTry running as Administrator.",
            font=(FONT, 11), text_color=TEXT_DIM, justify="center"
        )
        self.plan_empty.grid(row=0, column=0, pady=40)
        self.plan_empty.grid_remove()

    def _build_footer(self) -> None:
        footer = ctk.CTkFrame(
            self, fg_color=SURFACE, corner_radius=8,
            border_width=1, border_color=BORDER, height=34
        )
        footer.grid(row=3, column=0, sticky="ew", padx=24, pady=(0, 14))
        footer.grid_columnconfigure(1, weight=1)

        self.status_dot = ctk.CTkLabel(
            footer, text="●", width=12, font=(FONT, 9), text_color=TEXT_DIM
        )
        self.status_dot.grid(row=0, column=0, padx=(14, 6), pady=6)
        self.status_text = ctk.CTkLabel(
            footer, text="Starting up…", anchor="w",
            font=(FONT, 10), text_color=TEXT_MUTED
        )
        self.status_text.grid(row=0, column=1, sticky="w", pady=6)

        ctk.CTkLabel(
            footer, text=f"v{core.__version__}   ·   F5 refresh   ·   Ctrl+Q quit",
            font=(FONT, 9), text_color=TEXT_DIM
        ).grid(row=0, column=2, sticky="e", padx=(0, 16))

    # ----- state --------------------------------------------------------

    def _state(self) -> str:
        active = self._active_guid.lower()
        if not active:
            return "unknown"
        active_name = next(
            (p.name for p in self._plans if p.guid.lower() == active), ""
        )
        return core.detect_plan_mode(active, active_name, self._ultimate_guid)

    def _set_status(self, text: str, tone: str = "info") -> None:
        colors = {
            "info": TEXT_MUTED,
            "ok": SUCCESS,
            "warn": WARNING,
            "error": DANGER,
            "busy": ACCENT,
        }
        self.status_dot.configure(text_color=colors.get(tone, TEXT_MUTED))
        self.status_text.configure(text=text)

    def _set_busy(self, busy: bool, message: str | None = None) -> None:
        self._busy = busy
        if message:
            self._set_status(message, "busy")
        self._sync_controls()

    def _sync_controls(self) -> None:
        if self._building:
            return
        busy = self._busy
        self.btn_refresh.configure(state="disabled" if busy else "normal")
        self.btn_seg_balanced.configure(state="disabled" if busy else "normal")
        self.btn_seg_ultimate.configure(state="disabled" if busy else "normal")

        ultimate_ready = bool(self._ultimate_guid)
        if ultimate_ready:
            self.ultimate_banner.grid_remove()
        else:
            self.ultimate_banner.grid()
            self.btn_enable_banner.configure(state="disabled" if busy else "normal")

    # ----- async plumbing ----------------------------------------------

    def _run_async(self, fn, on_done, busy_message: str) -> None:
        if self._busy:
            return
        self._set_busy(True, busy_message)

        def worker() -> None:
            try:
                result = fn()
            except Exception as exc:  # noqa: BLE001
                result = exc
            self._results.put((on_done, result))

        threading.Thread(target=worker, daemon=True).start()

    def _drain_results(self) -> None:
        try:
            while True:
                on_done, result = self._results.get_nowait()
                self._set_busy(False)
                try:
                    on_done(result)
                except Exception as exc:  # noqa: BLE001
                    self._set_status(f"Unexpected error: {exc}", "error")
        except queue.Empty:
            pass
        self.after(50, self._drain_results)

    # ----- actions ------------------------------------------------------

    def _maybe_prompt_admin(self) -> None:
        if self._is_admin or self._prompted or os.environ.get("PMS_NO_PROMPT"):
            return
        self._prompted = True
        choice = MessageDialog(
            self,
            "Administrator Required",
            "Power Mode Switch requires administrator privileges to activate power plans.\n\n"
            "Restart with elevated rights now?",
            kind="warning",
            buttons=[("Not now", False), ("Elevate", True, "primary")],
        ).show()
        if choice:
            core.relaunch_as_admin()

    def _on_elevate(self) -> None:
        if not core.relaunch_as_admin():
            self._set_status("Elevation was cancelled.", "warn")

    def _require_admin(self) -> bool:
        if self._is_admin:
            return True
        choice = MessageDialog(
            self,
            "Administrator Required",
            "Activating power plans requires administrator rights.\n\n"
            "Restart Power Mode Switch as Administrator?",
            kind="warning",
            buttons=[("Not now", False), ("Elevate", True, "primary")],
        ).show()
        if choice:
            core.relaunch_as_admin()
        return False

    def refresh(self, announce: bool = False) -> None:
        if self._busy or self._building:
            return

        def work():
            plans = core.get_plans()
            active_guid, _full = core.get_active()
            ultimate = next(
                (p.guid for p in plans if "ultimate" in p.name.lower()), ""
            )
            return plans, active_guid, ultimate

        def done(result) -> None:
            if isinstance(result, Exception):
                self._set_status(f"Could not read power plans: {result}", "error")
                MessageDialog(self, "Error reading plans", str(result), kind="error").show()
                return
            plans, active_guid, ultimate = result
            self._plans = plans
            self._active_guid = active_guid
            self._ultimate_guid = ultimate

            guids = {p.guid.lower() for p in plans}
            if self._selected_guid.lower() not in guids:
                self._selected_guid = active_guid
            self._render_plans()
            self._render_hero()
            self._set_status("Ready" if announce else "Power plans refreshed", "ok")
            self._sync_controls()

        self._run_async(work, done, "Refreshing power plans…")

    def _render_plans(self) -> None:
        for child in self.plans_host.winfo_children():
            if child is not self.plan_empty:
                child.destroy()

        self.count_chip.configure(
            text=f"{len(self._plans)} plan{'s' if len(self._plans) != 1 else ''}"
        )

        if not self._plans:
            self.plan_empty.grid()
            return
        self.plan_empty.grid_remove()

        # Sort: active plan is always first, followed by standard and custom plans
        def plan_sort_key(p: core.Plan):
            mode_rank = {"balanced": 1, "ultimate": 2, "high": 3, "saver": 4}
            mode = core.detect_plan_mode(p.guid, p.name, self._ultimate_guid)
            return (not p.active, mode_rank.get(mode, 5), p.name.lower(), p.guid)

        sorted_plans = sorted(self._plans, key=plan_sort_key)

        for i, plan in enumerate(sorted_plans):
            card = PlanCard(
                self.plans_host,
                plan,
                selected=plan.guid.lower() == self._selected_guid.lower(),
                on_select=self._select_plan,
                on_activate=self._activate_plan,
            )
            card.grid(row=i, column=0, sticky="ew", pady=(0, 8), padx=(0, 4))

    def _render_hero(self) -> None:
        state = self._state()
        profile = MODE_PROFILES.get(state, MODE_PROFILES["unknown"])

        active_plan = next(
            (p for p in self._plans if p.guid.lower() == self._active_guid.lower()), None
        )
        display_name = active_plan.name if active_plan else profile["title"]

        self.hero_icon_lbl.configure(text=profile["icon"], text_color=profile["accent"])
        self.hero_icon_frame.configure(
            fg_color=profile["badge_bg"],
            border_color=profile["accent"]
        )

        self.hero_title.configure(text=display_name)
        self.hero_desc.configure(text=profile["desc"])

        # Update segmented quick switch highlights
        if state == "balanced":
            self.btn_seg_balanced.configure(
                fg_color="#1E3A8A", text_color="#60A5FA",
                hover_color="#1E40AF"
            )
            self.btn_seg_ultimate.configure(
                fg_color="transparent", text_color=TEXT_MUTED,
                hover_color=SURFACE_HOVER
            )
        elif state == "ultimate":
            self.btn_seg_ultimate.configure(
                fg_color="#7C2D12", text_color="#FB923C",
                hover_color="#9A3412"
            )
            self.btn_seg_balanced.configure(
                fg_color="transparent", text_color=TEXT_MUTED,
                hover_color=SURFACE_HOVER
            )
        else:
            self.btn_seg_balanced.configure(
                fg_color="transparent", text_color=TEXT_MUTED, hover_color=SURFACE_HOVER
            )
            self.btn_seg_ultimate.configure(
                fg_color="transparent", text_color=TEXT_MUTED, hover_color=SURFACE_HOVER
            )

    def _select_plan(self, guid: str) -> None:
        if self._busy:
            return
        self._selected_guid = guid
        self._render_plans()

    def _activate_plan(self, guid: str) -> None:
        self._select_plan(guid)
        if not guid or guid.lower() == self._active_guid.lower():
            return
        if not self._require_admin():
            return

        def work():
            core.set_active(guid)
            active_guid, _full = core.get_active()
            return active_guid, core.get_plans()

        def done(result) -> None:
            if isinstance(result, Exception):
                self._switch_failed(result)
                return
            active_guid, plans = result
            self._active_guid = active_guid
            self._plans = plans
            self._ultimate_guid = next(
                (p.guid for p in plans if "ultimate" in p.name.lower()),
                self._ultimate_guid,
            )
            self._selected_guid = active_guid
            self._render_plans()
            self._render_hero()
            self._set_status("Active power plan changed", "ok")
            self._sync_controls()

        self._run_async(work, done, "Activating power plan…")

    def _on_switch_target(self, target: str) -> None:
        if self._busy or self._building:
            return
        if not self._require_admin():
            return

        def work():
            plans = core.get_plans()
            if target == "ultimate":
                target_guid = self._ultimate_guid or core.find_guid("Ultimate") or core.enable_ultimate()
            else:
                target_guid = next((p.guid for p in plans if "balanced" in p.name.lower()), core.BALANCED_GUID)
            core.set_active(target_guid)
            active_guid, _full = core.get_active()
            return active_guid, core.get_plans()

        def done(result) -> None:
            if isinstance(result, Exception):
                self._switch_failed(result)
                return
            active_guid, plans = result
            self._active_guid = active_guid
            self._plans = plans
            self._ultimate_guid = next(
                (p.guid for p in plans if "ultimate" in p.name.lower()),
                self._ultimate_guid,
            )
            self._selected_guid = active_guid
            self._render_plans()
            self._render_hero()
            self._set_status(f"Switched to {target.title()}", "ok")
            self._sync_controls()

        self._run_async(work, done, f"Switching to {target.title()}…")

    def _switch_failed(self, exc: Exception) -> None:
        self._set_status(f"Switch failed: {exc}", "error")
        self._render_hero()
        MessageDialog(self, "Could not switch power mode", str(exc), kind="error").show()

    def _on_enable_ultimate(self) -> None:
        if self._busy or not self._require_admin():
            return

        def work():
            return core.enable_ultimate()

        def done(result) -> None:
            if isinstance(result, Exception):
                self._set_status(f"Could not enable Ultimate Performance: {result}", "error")
                MessageDialog(self, "Enable Failed", str(result), kind="error").show()
                return
            self._ultimate_guid = result
            self._set_status("Ultimate Performance is available", "ok")
            self.refresh(announce=True)

        self._run_async(work, done, "Enabling Ultimate Performance…")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def launch() -> int:
    ctk.set_appearance_mode("dark")
    app = App()
    app.mainloop()
    return 0
