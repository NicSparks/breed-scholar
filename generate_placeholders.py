#!/usr/bin/env python3
"""Generate placeholder thumbnails for all breeds without real images."""

import sqlite3
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path('/root/breed-scholar')
THUMBS_DIR = BASE_DIR / 'static' / 'thumbs'
FULL_DIR = BASE_DIR / 'static' / 'full'
DB_PATH = BASE_DIR / 'dog_breeds.db'

# Create directories
THUMBS_DIR.mkdir(parents=True, exist_ok=True)
FULL_DIR.mkdir(parents=True, exist_ok=True)

def create_placeholder_thumb(breed_id, breed_name):
    """Create a placeholder thumbnail with breed initials."""
    thumb_path = THUMBS_DIR / f'{breed_id}.jpg'
    if thumb_path.exists():
        return False
    
    # Create 200x200 image
    img = Image.new('RGB', (200, 200), (30, 30, 40))
    draw = ImageDraw.Draw(img)
    
    # Get initials
    words = breed_name.split()
    if len(words) >= 2:
        initials = words[0][0] + words[-1][0]
    else:
        initials = breed_name[:2]
    
    initials = initials.upper()
    
    # Try to use a font, fallback to default
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
    except:
        font = ImageFont.load_default()
    
    # Center text
    bbox = draw.textbbox((0, 0), initials, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (200 - text_width) // 2
    y = (200 - text_height) // 2
    
    # Draw text
    draw.text((x, y), initials, fill=(80, 80, 100), font=font)
    
    # Save thumbnail
    img.save(thumb_path, 'JPEG', quality=80)
    return True


def create_placeholder_full(breed_id, breed_name):
    """Create a placeholder full-size image."""
    full_path = FULL_DIR / f'{breed_id}.jpg'
    if full_path.exists():
        return False
    
    # Create 800x600 image
    img = Image.new('RGB', (800, 600), (30, 30, 40))
    draw = ImageDraw.Draw(img)
    
    # Get initials
    words = breed_name.split()
    if len(words) >= 2:
        initials = words[0][0] + words[-1][0]
    else:
        initials = breed_name[:2]
    
    initials = initials.upper()
    
    # Try to use a font
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 120)
    except:
        font = ImageFont.load_default()
    
    # Center text
    bbox = draw.textbbox((0, 0), initials, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (800 - text_width) // 2
    y = (600 - text_height) // 2
    
    # Draw text
    draw.text((x, y), initials, fill=(80, 80, 100), font=font)
    
    # Save full image
    img.save(full_path, 'JPEG', quality=85)
    return True


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Get all breeds
    cur.execute('SELECT id, name FROM breeds ORDER BY id')
    breeds = cur.fetchall()
    conn.close()
    
    print(f"[*] Processing {len(breeds)} breeds...")
    
    thumbs_created = 0
    full_created = 0
    skipped = 0
    
    for breed_id, breed_name in breeds:
        if create_placeholder_thumb(breed_id, breed_name):
            thumbs_created += 1
        else:
            skipped += 1
        
        if create_placeholder_full(breed_id, breed_name):
            full_created += 1
    
    print(f"\n[+] Thumbnails created: {thumbs_created}")
    print(f"[+] Full images created: {full_created}")
    print(f"[+] Skipped (already exists): {skipped}")
    print(f"[+] Total: {len(breeds)} breeds")
    
    # Verify
    thumb_count = len(list(THUMBS_DIR.glob('*.jpg')))
    full_count = len(list(FULL_DIR.glob('*.jpg')))
    print(f"\n[✓] Thumbs directory: {thumb_count} images")
    print(f"[✓] Full directory: {full_count} images")


if __name__ == '__main__':
    main()
