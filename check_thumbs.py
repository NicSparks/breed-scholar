#!/usr/bin/env python3
from PIL import Image
from pathlib import Path

for p in sorted(Path('/root/breed-scholar/static/thumbs').glob('*.jpg'))[:5]:
    img = Image.open(p)
    print(p.name, img.size, img.mode)
