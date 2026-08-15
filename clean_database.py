#!/usr/bin/env python3
"""Clean up data quality issues in the breed database."""

import sqlite3
from pathlib import Path

DB_PATH = Path('/root/breed-scholar/dog_breeds.db')
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Remove suspicious entries
suspect_names = [
    'Dog Breeds', 'Dog Breed Information', 'Dog type',
    'Best Dogs For Apartment Dwellers', 'Best Dog Breeds for Kids',
    'Best Family Dogs', 'Best Guard Dogs', 'Foundation Stock Service',
    'Hairless Dog Breeds', 'Herding Group', 'Hound Group',
    'Hypoallergenic Dogs', 'Largest Dog Breeds', 'Medium Dog Breeds',
    'Miscellaneous Class', 'Non-Sporting Group', 'Smallest Dog Breeds',
    'Smartest Breeds of Dogs', 'Sporting Group', 'Terrier Group',
    'Toy Group', 'Working Group'
]

placeholders = ['Alderton, David']
remove_names = suspect_names + placeholders

cur.execute('SELECT id, name FROM breeds')
all_breeds = cur.fetchall()

removed = 0
for breed_id, name in all_breeds:
    if name in remove_names or name.endswith('Dog Breed Information'):
        cur.execute('DELETE FROM breeds WHERE id = ?', (breed_id,))
        cur.execute('DELETE FROM breed_registries WHERE breed_id = ?', (breed_id,))
        removed += 1
        print(f"  Removed: {name}")

print(f"\n[+] Removed {removed} non-breed entries")

# Clean up size and country fields
cur.execute('SELECT id, country, size FROM breeds WHERE country LIKE ".%" OR size LIKE ".%"')
dirty_rows = cur.fetchall()

cleaned = 0
for breed_id, country, size in dirty_rows:
    # Remove CSS-like content
    if country and ('.{' in country or country.startswith('.') or len(country) > 100):
        cur.execute('UPDATE breeds SET country = NULL WHERE id = ?', (breed_id,))
        cleaned += 1
    if size and ('.{' in size or size.startswith('.') or len(size) > 100):
        cur.execute('UPDATE breeds SET size = NULL WHERE id = ?', (breed_id,))
        cleaned += 1

print(f"[+] Cleaned {cleaned} dirty fields")

# Remove exact duplicates
cur.execute('''
    DELETE FROM breeds
    WHERE id NOT IN (
        SELECT MIN(id)
        FROM breeds
        GROUP BY LOWER(name)
    )
''')
dupes_removed = cur.rowcount
print(f"[+] Removed {dupes_removed} duplicate entries")

conn.commit()

# Final counts
total = cur.execute('SELECT COUNT(*) FROM breeds').fetchone()[0]
akc = cur.execute('''
    SELECT COUNT(DISTINCT b.id) FROM breeds b
    JOIN breed_registries br ON b.id = br.breed_id
    JOIN registries r ON br.registry_id = r.id WHERE r.code = 'akc'
''').fetchone()[0]
fci = cur.execute('''
    SELECT COUNT(DISTINCT b.id) FROM breeds b
    JOIN breed_registries br ON b.id = br.breed_id
    JOIN registries r ON br.registry_id = r.id WHERE r.code = 'fci'
''').fetchone()[0]
non = cur.execute('''
    SELECT COUNT(DISTINCT b.id) FROM breeds b
    JOIN breed_registries br ON b.id = br.breed_id
    JOIN registries r ON br.registry_id = r.id WHERE r.code = 'non'
''').fetchone()[0]

conn.close()

print("\n[✓] Database cleaned")
print(f"[✓] Total breeds: {total}")
print(f"[✓] AKC: {akc}, FCI: {fci}, Non-Recog: {non}")
