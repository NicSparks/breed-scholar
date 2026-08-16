#!/usr/bin/env python3
"""Generate iOS/PWA app icons."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path('/root/breed-scholar/static')
BASE_DIR.mkdir(parents=True, exist_ok=True)

def create_icon(size, path):
    img = Image.new('RGBA', (size, size), (10, 10, 15, 255))
    draw = ImageDraw.Draw(img)
    padding = size // 10
    draw.rounded_rectangle(
        [padding, padding, size - padding, size - padding],
        radius=size // 5,
        fill=(20, 20, 35, 255),
        outline=(241, 196, 15, 255),
        width=max(2, size // 32)
    )
    try:
        font_size = size // 3
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except OSError:
        font = ImageFont.load_default()
    text = "B"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (size - text_width) // 2
    y = (size - text_height) // 2
    draw.text((x, y), text, fill=(241, 196, 15, 255), font=font)
    img.save(str(path), 'PNG')
    print(f"[+] Created {path} ({size}x{size})")

def main():
    create_icon(192, BASE_DIR / 'icon-192.png')
    create_icon(512, BASE_DIR / 'icon-512.png')
    create_icon(32, BASE_DIR / 'favicon.ico')
    print(f"\n[✓] Icons created in {BASE_DIR}")

if __name__ == '__main__':
    main()
