"""Small, standalone self-check test suite for Power Mode Switch core logic.

Run with:
    python test_power_mode.py
"""
import sys

import power_mode as core
from gui import blend, hex_to_rgb, rgb_to_hex


def test_parse_plans():
    sample = """
Existing Power Schemes (* Active)
-----------------------------------
Power Scheme GUID: 381b4222-f694-41f0-9685-ff5bb260df2e  (Balanced) *
Power Scheme GUID: e9a42b02-d5df-448d-aa00-03f14749eb61  (Ultimate Performance)
Power Scheme GUID: 101f8372-9373-4a6f-a2f0-f8b4a0876e69  (Power saver)
Power Scheme GUID: 026f1f8c-69d0-40db-ac94-0e21f44ee2ea  (High performance)
Power Scheme GUID: eedf5c1c-aa61-4487-b509-3dc5da347281  (My Custom Plan 1)
"""
    plans = core.parse_plans(sample)
    assert len(plans) == 5, f"Expected 5 plans, got {len(plans)}"

    # Check active scheme
    balanced = plans[0]
    assert balanced.name == "Balanced"
    assert balanced.active is True
    assert balanced.guid == core.BALANCED_GUID

    # Check ultimate scheme
    ultimate = plans[1]
    assert ultimate.name == "Ultimate Performance"
    assert ultimate.active is False


def test_detect_plan_mode():
    assert core.detect_plan_mode(core.BALANCED_GUID, "Balanced") == "balanced"
    assert core.detect_plan_mode("some-other-guid", "Balanced Power Scheme") == "balanced"

    ult_guid = "0b3748d0-d611-4f8f-9929-6c4a683012c3"
    assert core.detect_plan_mode(ult_guid, "Ultimate Performance", ult_guid) == "ultimate"
    assert core.detect_plan_mode("another-guid", "Ultimate Performance") == "ultimate"

    assert core.detect_plan_mode("abc", "Power saver") == "saver"
    assert core.detect_plan_mode("xyz", "High performance") == "high"
    assert core.detect_plan_mode("123", "Custom Gaming Plan") == "unknown"


def test_color_blending():
    assert hex_to_rgb("#000000") == (0, 0, 0)
    assert hex_to_rgb("#FFFFFF") == (255, 255, 255)
    assert rgb_to_hex(255, 0, 128) == "#ff0080"
    mid = blend("#000000", "#FFFFFF", 0.5)
    assert mid == "#808080", f"Expected #808080, got {mid}"


def test_arg_parser():
    parser = core.build_parser()
    args = parser.parse_args(["toggle"])
    assert args.cmd == "toggle"

    args = parser.parse_args(["list"])
    assert args.cmd == "list"

    args = parser.parse_args(["diag"])
    assert args.cmd == "diag"


def main():
    test_parse_plans()
    test_detect_plan_mode()
    test_color_blending()
    test_arg_parser()
    print("All core tests passed successfully (4/4).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
