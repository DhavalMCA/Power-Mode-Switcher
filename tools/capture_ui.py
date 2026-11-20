"""Helper to launch GUI, wait for render, and capture a clean screenshot."""
import os
import sys
import time
import ctypes
from ctypes import wintypes

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["PMS_NO_PROMPT"] = "1"

import customtkinter as ctk
import gui
from PIL import ImageGrab


def capture(out_path="screenshot.png", ultimate=False):
    if ultimate:
        from power_mode import Plan, BALANCED_GUID
        ult_guid = "e9a42b02-d5df-448d-aa00-03f14749eb61"
        gui.core.is_admin = lambda: True
        gui.core.get_plans = lambda: [
            Plan(BALANCED_GUID, "Balanced", False),
            Plan("eedf5c1c-aa61-4487-b509-30c5da347281", "My Custom Plan 1", False),
            Plan(ult_guid, "Ultimate Performance", True),
        ]
        gui.core.get_active = lambda: (ult_guid, f"Power Scheme GUID: {ult_guid}  (Ultimate Performance) *")

    ctk.set_appearance_mode("dark")
    app = gui.App()
    for _ in range(25):
        app.update_idletasks()
        app.update()
        time.sleep(0.04)

    hwnd = ctypes.windll.user32.GetParent(app.winfo_id()) or app.winfo_id()
    rect = wintypes.RECT()
    ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
    img = ImageGrab.grab(bbox=(rect.left, rect.top, rect.right, rect.bottom), all_screens=True)
    img.save(out_path)
    print(f"Captured {img.size} to {out_path}")
    app.destroy()


if __name__ == "__main__":
    is_ult = "--ultimate" in sys.argv
    capture("screenshot.png", ultimate=is_ult)
