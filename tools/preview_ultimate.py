"""Dev-only preview: render the app in the Ultimate Performance state."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import customtkinter as ctk

import gui
from power_mode import BALANCED_GUID, Plan

ULTIMATE_GUID = "e9a42b02-d5df-448d-aa00-03f14749eb61"

gui.core.is_admin = lambda: True
gui.core.get_plans = lambda: [
    Plan(BALANCED_GUID, "Balanced"),
    Plan("eedf5c1c-aa61-4487-b509-30c5da347281", "My Custom Plan 1"),
    Plan(ULTIMATE_GUID, "Ultimate Performance", True),
]
gui.core.get_active = lambda: (
    ULTIMATE_GUID,
    f"Power Scheme GUID: {ULTIMATE_GUID}  (Ultimate Performance) *",
)
gui.App._maybe_prompt_admin = lambda self: None

ctk.set_appearance_mode("dark")
gui.App().mainloop()
