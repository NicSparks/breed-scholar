#!/usr/bin/env python3
from pathlib import Path

from PIL import Image

for p in sorted(Path('/root/breed-scholar/static/thumbs').glob('*.jpg'))[:5]:
    img = Image.open(p)
    print(p.name, img.size, img.mode)
