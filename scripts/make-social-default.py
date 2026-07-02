#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pillow", "matplotlib"]
# ///
"""Generate the default social-preview card for the blog.

Run:  uv run scripts/make-social-default.py
Output: static/images/social-default.png (1280x630)

Design mirrors the site's CSS custom properties (assets/css/main.css):
  --bg #fdfdfc (paper)  --fg #1a1a1a (slate)  --accent #0a5ad6  --muted #666
Fonts are DejaVu Sans, sourced from matplotlib's bundled ttf set so the
render is reproducible on any machine without relying on system fonts.
"""
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import matplotlib

W, H = 1280, 630
BG = "#fdfdfc"
FG = "#1a1a1a"
ACCENT = "#0a5ad6"
MUTED = "#666666"

FONT_DIR = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
bold = lambda s: ImageFont.truetype(str(FONT_DIR / "DejaVuSans-Bold.ttf"), s)
reg = lambda s: ImageFont.truetype(str(FONT_DIR / "DejaVuSans.ttf"), s)

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)

MARGIN = 96
name_f = bold(96)
tag_f = reg(46)
url_f = reg(32)

# Vertically centered name + tagline block, left aligned.
name = "Shannon Bigelow"
tag = "Platform engineering, verified."

name_h = d.textbbox((0, 0), name, font=name_f)[3]
tag_h = d.textbbox((0, 0), tag, font=tag_f)[3]
rule_gap = 28
block_h = name_h + rule_gap + 3 + rule_gap + tag_h
top = (H - block_h) // 2

d.text((MARGIN, top), name, font=name_f, fill=FG)
rule_y = top + name_h + rule_gap
d.rectangle([MARGIN, rule_y, MARGIN + 200, rule_y + 3], fill=ACCENT)  # accent rule
d.text((MARGIN, rule_y + 3 + rule_gap), tag, font=tag_f, fill=FG)

# Site URL, small, bottom-left.
url = "bigelow.github.io"
url_h = d.textbbox((0, 0), url, font=url_f)[3]
d.text((MARGIN, H - MARGIN - url_h), url, font=url_f, fill=MUTED)

out = Path(__file__).resolve().parent.parent / "static" / "images" / "social-default.png"
out.parent.mkdir(parents=True, exist_ok=True)
img.save(out, "PNG")
print(f"wrote {out} ({img.size[0]}x{img.size[1]}, {os.path.getsize(out)} bytes)")
