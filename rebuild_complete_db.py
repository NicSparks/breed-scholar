#!/usr/bin/env python3
"""Merge AKC crawl results into master catalog and rebuild database."""

import json
import sqlite3
from pathlib import Path

BASE_DIR = Path('/root/breed-scholar')
DB_PATH = BASE_DIR / 'dog_breeds.db'

# Load master catalog
with open(BASE_DIR / 'breeds_final.json', 'r') as f:
    master = json.load(f)

# Load AKC crawl results
akc_crawl_path = BASE_DIR / 'akc_crawl_results.json'
if akc_crawl_path.exists():
    with open(akc_crawl_path, 'r') as f:
        akc_data = json.load(f)
else:
    akc_data = {}

print(f"Master catalog: {len(master)} breeds")
print(f"AKC crawl results: {len(akc_data)} breeds")

# Merge: update master catalog with AKC source URLs and better data
master_by_name = {b['name'].lower(): b for b in master}

updated = 0
for akc_name, akc_breed in akc_data.items():
    key = akc_name.lower()
    if key in master_by_name:
        # Update existing breed with AKC data
        breed = master_by_name[key]
        if akc_breed.get('source_url'):
            breed['source_url'] = akc_breed['source_url']
        if akc_breed.get('group') and not breed.get('group'):
            breed['group'] = akc_breed['group']
        if akc_breed.get('rank') and not breed.get('rank'):
            breed['rank'] = akc_breed['rank']
        if akc_breed.get('country') and not breed.get('country'):
            breed['country'] = akc_breed['country']
        if akc_breed.get('size') and not breed.get('size'):
            breed['size'] = akc_breed['size']
        if akc_breed.get('fact') and len(akc_breed['fact']) > len(breed.get('fact', '')):
            breed['fact'] = akc_breed['fact']
        updated += 1

print(f"Updated {updated} breeds with AKC data")

# Rebuild database with merged data
if DB_PATH.exists():
    DB_PATH.unlink()

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute('''
    CREATE TABLE IF NOT EXISTS registries (
        id INTEGER PRIMARY KEY,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL
    )
''')

cur.execute('''
    CREATE TABLE IF NOT EXISTS breeds (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        group_name TEXT,
        rank INTEGER,
        country TEXT,
        size TEXT,
        fci_group TEXT,
        fact TEXT,
        tips TEXT,
        image_url TEXT,
        source_url TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

cur.execute('''
    CREATE TABLE IF NOT EXISTS breed_registries (
        breed_id INTEGER NOT NULL,
        registry_id INTEGER NOT NULL,
        PRIMARY KEY (breed_id, registry_id),
        FOREIGN KEY (breed_id) REFERENCES breeds(id),
        FOREIGN KEY (registry_id) REFERENCES registries(id)
    )
''')

cur.execute('CREATE INDEX IF NOT EXISTS idx_breeds_name ON breeds(name)')
cur.execute('CREATE INDEX IF NOT EXISTS idx_breeds_rank ON breeds(rank)')
cur.execute('CREATE INDEX IF NOT EXISTS idx_breeds_country ON breeds(country)')
cur.execute('CREATE INDEX IF NOT EXISTS idx_breeds_group ON breeds(group_name)')

cur.execute("INSERT OR IGNORE INTO registries (id, code, name) VALUES (1, 'akc', 'American Kennel Club')")
cur.execute("INSERT OR IGNORE INTO registries (id, code, name) VALUES (2, 'fci', 'Fédération Cynologique Internationale')")
cur.execute("INSERT OR IGNORE INTO registries (id, code, name) VALUES (3, 'non', 'Non-Recognized / Other')")

registry_map = {'akc': 1, 'fci': 2, 'non': 3}

for breed in master:
    cur.execute('''
        INSERT OR REPLACE INTO breeds 
        (name, group_name, rank, country, size, fci_group, fact, tips, image_url, source_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        breed['name'],
        breed.get('group') or '',
        breed.get('rank'),
        breed.get('country') or '',
        breed.get('size') or '',
        breed.get('fciGroup') or '',
        breed.get('fact') or '',
        breed.get('tips') or '',
        breed.get('image') or '',
        breed.get('source_url', '')
    ))
    
    breed_id = cur.lastrowid
    reg_id = registry_map.get(breed.get('registry', 'non'))
    if reg_id:
        cur.execute('INSERT OR IGNORE INTO breed_registries (breed_id, registry_id) VALUES (?, ?)',
                   (breed_id, reg_id))

conn.commit()

total = cur.execute('SELECT COUNT(*) FROM breeds').fetchone()[0]
akc_count = cur.execute('''
    SELECT COUNT(DISTINCT b.id) FROM breeds b
    JOIN breed_registries br ON b.id = br.breed_id
    JOIN registries r ON br.registry_id = r.id WHERE r.code = 'akc'
''').fetchone()[0]
fci_count = cur.execute('''
    SELECT COUNT(DISTINCT b.id) FROM breeds b
    JOIN breed_registries br ON b.id = br.registry_id
    JOIN registries r ON br.registry_id = r.id WHERE r.code = 'fci'
''').fetchone()[0]
non_count = cur.execute('''
    SELECT COUNT(DISTINCT b.id) FROM breeds b
    JOIN breed_registries br ON b.id = br.breed_id
    JOIN registries r ON br.registry_id = r.id WHERE r.code = 'non'
''').fetchone()[0]

conn.close()

print(f"\n[✓] Database rebuilt: {DB_PATH}")
print(f"[✓] Total breeds: {total}")
print(f"[✓] AKC: {akc_count}, FCI: {fci_count}, Non-Recog: {non_count}")
