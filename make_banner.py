#!/usr/bin/env python3
"""Generate a clean linkedin-autopilot banner (1200x630) with PIL."""
from PIL import Image, ImageDraw, ImageFont
import os

W, H = 1200, 630
BG = "#0d1117"
GRID = "#161b22"
GOLD = "#d4af37"
WHITE = "#f0f6fc"
GRAY = "#8b949e"
GREEN = "#3fb950"

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)

# subtle grid
for x in range(0, W, 40):
    d.line([(x, 0), (x, H)], fill=GRID, width=1)
for y in range(0, H, 40):
    d.line([(0, y), (W, y)], fill=GRID, width=1)

# gold accents
d.rectangle([0, 0, 10, H], fill=GOLD)
d.rectangle([0, H - 8, W, H], fill=GOLD)


def font(size, bold=True, mono=False):
    if mono:
        paths = ["C:/Windows/Fonts/consolab.ttf", "C:/Windows/Fonts/consola.ttf",
                 "C:/Windows/Fonts/courbd.ttf", "C:/Windows/Fonts/cour.ttf"]
    else:
        paths = ["C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/arial.ttf",
                 "C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/segoeui.ttf"]
    if bold:
        paths = ["C:/Windows/Fonts/consolab.ttf", "C:/Windows/Fonts/courbd.ttf"] if mono else ["C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/segoeuib.ttf"]
    for p in paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


# top-left label
d.text((60, 48), "OPEN SOURCE  •  PYTHON  •  NO SaaS FEES", font=font(26, mono=True), fill=GOLD)

# title
d.text((60, 150), "linkedin-autopilot", font=font(84), fill=WHITE)

# tagline
d.text((60, 300), "AI writes. You approve. It posts.", font=font(44), fill=GRAY)

# terminal line
d.rounded_rectangle([60, 430, 900, 500], radius=12, outline="#30363d", width=2)
d.text((90, 450), "$ python post.py --personal --image banner.png", font=font(28, mono=True), fill=GREEN)

# bottom-right URL
d.text((60, 560), "github.com/Amz34/linkedin-autopilot", font=font(30, mono=True), fill=GRAY)

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "banner.png")
img.save(out, "PNG")
print("Banner saved:", out, os.path.getsize(out), "bytes")
