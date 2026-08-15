#!/usr/bin/env python3
import sqlite3
from pathlib import Path

conn = sqlite3.connect('/root/breed-scholar/dog_breeds.db')
cur = conn.cursor()

total = cur.execute('SELECT COUNT(*) FROM breeds').fetchone()[0]
akc = cur.execute('SELECT COUNT(DISTINCT b.id) FROM breeds b JOIN breed_registries br ON b.id=br.breed_id JOIN registries r ON br.registry_id=r.id WHERE r.code="akc"').fetchone()[0]
fci = cur.execute('SELECT COUNT(DISTINCT b.id) FROM breeds b JOIN breed_registries br ON b.id=br.breed_id JOIN registries r ON br.registry_id=r.id WHERE r.code="fci"').fetchone()[0]
non = cur.execute('SELECT COUNT(DISTINCT b.id) FROM breeds b JOIN breed_registries br ON b.id=br.breed_id JOIN registries r ON br.registry_id=r.id WHERE r.code="non"').fetchone()[0]

thumbs = len(list(Path('/root/breed-scholar/static/thumbs').glob('*.jpg')))
full = len(list(Path('/root/breed-scholar/static/full').glob('*.jpg')))

print(f'Database: {total} breeds')
print(f'  AKC: {akc}, FCI: {fci}, Non-Recog: {non}')
print(f'Thumbnails: {thumbs}')
print(f'Full images: {full}')

real_thumbs = 0
for p in Path('/root/breed-scholar/static/thumbs').glob('*.jpg'):
    if p.stat().st_size > 5000:
        real_thumbs += 1
print(f'Real thumbnails (>5KB): {real_thumbs}')
print(f'Placeholder thumbnails: {thumbs - real_thumbs}')

conn.close()
