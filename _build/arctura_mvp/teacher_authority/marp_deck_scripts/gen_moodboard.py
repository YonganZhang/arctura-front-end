#!/usr/bin/env python3
"""Generate a 6-swatch moodboard PNG from brief.json palette."""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

if len(sys.argv) < 2:
    print("usage: gen_moodboard.py <mvp-folder>")
    sys.exit(1)

mvp = Path(sys.argv[1])
brief = json.loads((mvp / 'brief.json').read_text())
palette = brief['style']['palette']  # dict of name → #hex
project = brief.get('project', mvp.name)
keywords = brief['style'].get('keywords', [])

W, H = 1600, 900
img = Image.new('RGB', (W, H), '#FAFAF7')
draw = ImageDraw.Draw(img)

# Try to find a Chinese-capable font
font_paths = [
    '/System/Library/Fonts/PingFang.ttc',
    '/System/Library/Fonts/STHeiti Medium.ttc',
    '/System/Library/Fonts/Hiragino Sans GB.ttc',
]
font_path = next((p for p in font_paths if Path(p).exists()), None)

def fnt(size):
    if font_path:
        try:
            return ImageFont.truetype(font_path, size)
        except Exception:
            pass
    return ImageFont.load_default()

title_font = fnt(48)
sub_font = fnt(22)
swatch_font = fnt(18)
swatch_hex_font = fnt(20)

# Header
draw.text((60, 50), project, fill='#2C2C2E', font=title_font)
sub_text = ' · '.join(keywords) if keywords else 'Mood Board'
draw.text((60, 120), sub_text, fill='#6B4E36', font=sub_font)

# Layout swatches: 2 rows × 3 cols (or N cols if more colors)
items = list(palette.items())
n = len(items)
cols = 3
rows = (n + cols - 1) // cols
sw_w = (W - 120 - (cols - 1) * 30) // cols
sw_h = (H - 220 - (rows - 1) * 30) // rows

for idx, (name, hex_color) in enumerate(items):
    r, c = divmod(idx, cols)
    x = 60 + c * (sw_w + 30)
    y = 200 + r * (sw_h + 30)
    # swatch
    draw.rectangle([x, y, x + sw_w, y + sw_h], fill=hex_color, outline='#2C2C2E', width=2)
    # name + hex bar at bottom
    bar_h = 60
    draw.rectangle([x, y + sw_h - bar_h, x + sw_w, y + sw_h], fill='#FAFAF7AA' if False else '#FFFFFF')
    # render text
    label = name.replace('_', ' ').title()
    draw.text((x + 12, y + sw_h - bar_h + 8),  label, fill='#2C2C2E', font=swatch_font)
    draw.text((x + 12, y + sw_h - bar_h + 32), hex_color.upper(), fill='#6B4E36', font=swatch_hex_font)

out = mvp / 'moodboard.png'
img.save(out, 'PNG')
print(f'[OK] {out} ({out.stat().st_size} bytes)')
