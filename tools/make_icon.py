"""Generate the Power Mode Switch icon set (run at build time only).

    python tools/make_icon.py

Requires Pillow. Produces:
    assets/icon.ico       multi-resolution Windows icon
    assets/icon-256.png   large preview / store art
    assets/icon-32.png    in-app header logo
"""
from __future__ import annotations

import math
import os

from PIL import Image, ImageDraw, ImageFilter

S = 1024          # working resolution (downscaled with LANCZOS)
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")

BLUE = (59, 130, 246)
ORANGE = (255, 122, 24)
BG_TOP = (26, 34, 48)
BG_BOTTOM = (10, 13, 19)
BORDER = (44, 56, 76)
WHITE = (248, 250, 252)


def lerp(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def rounded_mask(size: int, radius: int) -> Image.Image:
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, size - 1, size - 1), radius=radius, fill=255
    )
    return mask


def vertical_gradient(size: int, top, bottom) -> Image.Image:
    grad = Image.new("RGB", (1, size))
    px = grad.load()
    for y in range(size):
        px[0, y] = lerp(top, bottom, y / (size - 1))
    return grad.resize((size, size), Image.BILINEAR)


def horizontal_gradient(size: int, left, right) -> Image.Image:
    grad = Image.new("RGB", (size, 1))
    px = grad.load()
    for x in range(size):
        px[x, 0] = lerp(left, right, x / (size - 1))
    return grad.resize((size, size), Image.BILINEAR)


def main() -> None:
    os.makedirs(OUT, exist_ok=True)

    # ---- background -------------------------------------------------
    base = vertical_gradient(S, BG_TOP, BG_BOTTOM).convert("RGBA")
    base.putalpha(rounded_mask(S, radius=222))

    border = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(border).rounded_rectangle(
        (6, 6, S - 7, S - 7), radius=216, outline=BORDER + (255,), width=5
    )
    base = Image.alpha_composite(base, border)

    # ---- ring -------------------------------------------------------
    cx = cy = S // 2
    outer_r = 352
    stroke = 104
    inner_r = outer_r - stroke
    center_r = (outer_r + inner_r) / 2

    ring_mask = Image.new("L", (S, S), 0)
    md = ImageDraw.Draw(ring_mask)
    md.ellipse((cx - outer_r, cy - outer_r, cx + outer_r, cy + outer_r), fill=255)
    md.ellipse((cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r), fill=0)
    # Keep a 270-degree sweep, leaving a gap at the bottom (90 deg).
    wedge = Image.new("L", (S, S), 0)
    ImageDraw.Draw(wedge).pieslice(
        (cx - outer_r, cy - outer_r, cx + outer_r, cy + outer_r),
        start=135, end=405, fill=255,
    )
    ring_mask = Image.composite(ring_mask, Image.new("L", (S, S), 0), wedge)

    # Rounded end caps.
    cap = ImageDraw.Draw(ring_mask)
    for angle in (135, 405):
        a = math.radians(angle)
        px = cx + center_r * math.cos(a)
        py = cy + center_r * math.sin(a)
        cap.ellipse((px - stroke / 2, py - stroke / 2,
                     px + stroke / 2, py + stroke / 2), fill=255)

    ring = horizontal_gradient(S, BLUE, ORANGE).convert("RGBA")
    ring.putalpha(ring_mask)

    # Soft glow underneath the ring.
    glow_mask = ring_mask.filter(ImageFilter.GaussianBlur(26))
    glow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    glow.paste(horizontal_gradient(S, BLUE, ORANGE).convert("RGBA"),
               (0, 0), glow_mask.point(lambda v: int(v * 0.45)))
    base = Image.alpha_composite(base, glow)
    base = Image.alpha_composite(base, ring)

    # ---- power glyph -------------------------------------------------
    glyph = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glyph)
    gr = 132
    gw = 46
    gd.arc(
        (cx - gr, cy - gr, cx + gr, cy + gr),
        start=-58, end=238, fill=WHITE + (255,), width=gw,
    )
    gd.line((cx, cy - gr - gw // 2 - 6, cx, cy + 8),
            fill=WHITE + (255,), width=gw)
    # Round the line ends.
    for yy in (cy - gr - gw // 2 - 6, cy + 8):
        gd.ellipse((cx - gw / 2, yy - gw / 2, cx + gw / 2, yy + gw / 2),
                   fill=WHITE + (255,))
    base = Image.alpha_composite(base, glyph)

    # ---- exports -----------------------------------------------------
    master = base.resize((1024, 1024), Image.LANCZOS)
    master.save(os.path.join(OUT, "icon-256.png"), format="PNG")

    sizes = [16, 24, 32, 48, 64, 128, 256]
    frames = [base.resize((n, n), Image.LANCZOS) for n in sizes]
    frames[-1].save(
        os.path.join(OUT, "icon.ico"),
        format="ICO",
        sizes=[(n, n) for n in sizes],
        append_images=frames[:-1],
    )
    base.resize((32, 32), Image.LANCZOS).save(
        os.path.join(OUT, "icon-32.png"), format="PNG"
    )
    base.resize((256, 256), Image.LANCZOS).save(
        os.path.join(OUT, "icon-256.png"), format="PNG"
    )
    print(f"Wrote icons to {OUT}")


if __name__ == "__main__":
    main()
