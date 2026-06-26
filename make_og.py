#!/usr/bin/env python3
"""Branded 1200x630 social-share card (og:image) for Research Lab Wiki.
Clinical white/teal palette, reuses the real flask logo. Re-runnable."""
import pathlib
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent
W, H = 1200, 630
BG=(246,249,251); INK=(31,42,55); TEAL=(13,148,136); TEALD=(15,118,110); MUTED=(90,106,123); LINE=(225,233,239)

def font(path, size):
    return ImageFont.truetype(path, size)
ARIAL  = "/System/Library/Fonts/Supplemental/Arial.ttf"
ARIALB = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
GEORGIA = "/System/Library/Fonts/Supplemental/Georgia.ttf"

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)

# white panel + teal top accent
m = 50
d.rounded_rectangle([m, m, W-m, H-m], radius=30, fill=(255,255,255), outline=LINE, width=2)
d.rounded_rectangle([m, m, W-m, m+12], radius=6, fill=TEAL)

# real flask logo (already rendered to PNG)
logo = Image.open(ROOT / "favicon-180.png").convert("RGBA").resize((150, 150))
img.paste(logo, (m+56, m+66), logo)

x = m + 240
d.text((x, m+82),  "RESEARCH LAB",        font=font(ARIALB, 30), fill=TEALD)
d.text((x, m+122), "Research Lab Wiki",    font=font(ARIALB, 86), fill=INK)

d.line([m+58, H-m-206, W-m-58, H-m-206], fill=LINE, width=2)
d.text((m+58, H-m-176), "Independent, fully-cited research.",                   font=font(GEORGIA, 42), fill=INK)
d.text((m+58, H-m-118), "Traced to primary studies, evidence-graded, weighed honestly.", font=font(GEORGIA, 33), fill=MUTED)
d.text((m+58, H-m-62),  "English  &  Ελληνικά      ·      patrykwajs.github.io/Research-Lab-Wiki",
       font=font(ARIALB, 27), fill=TEALD)

img.save(ROOT / "og-cover.png", "PNG")
print("wrote og-cover.png", img.size)
