#!/usr/bin/env python3
"""Generate flashcard quiz data from breed database."""

import json
import random
import sqlite3
from pathlib import Path

BASE_DIR = Path('/root/breed-scholar')
DB_PATH = BASE_DIR / 'dog_breeds.db'
OUTPUT_PATH = BASE_DIR / 'flashcards.json'

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute('''
    SELECT b.id, b.name, b.group_name, b.rank, b.country, b.size, b.fci_group, b.fact,
           GROUP_CONCAT(r.code, ',') as registries
    FROM breeds b
    LEFT JOIN breed_registries br ON b.id = br.breed_id
    LEFT JOIN registries r ON br.registry_id = r.id
    GROUP BY b.id
''')
breeds = [dict(row) for row in cur.fetchall()]
conn.close()

# Group breeds by attributes for better wrong answers
by_group = {}
by_country = {}
by_size = {}
for b in breeds:
    g = b['group_name'] or 'Unknown'
    c = b['country'] or 'Unknown'
    s = b['size'] or 'Unknown'
    by_group.setdefault(g, []).append(b['name'])
    by_country.setdefault(c, []).append(b['name'])
    by_size.setdefault(s, []).append(b['name'])

all_names = [b['name'] for b in breeds]

def pick_wrong(correct, pool, n=3):
    opts = [x for x in pool if x != correct]
    random.shuffle(opts)
    return opts[:n]

cards = []

for b in breeds:
    name = b['name']
    group = b['group_name'] or 'Unknown'
    country = b['country'] or 'Unknown'
    size = b['size'] or 'Unknown'
    registries = b['registries'] or ''
    fact = b['fact'] or ''
    rank = b['rank']

    # Card 1: breed name -> group
    wrong = pick_wrong(name, all_names, 3)
    cards.append({
        'id': f"{b['id']}-group",
        'question': f"What group is {name} in?",
        'answer': group,
        'choices': [group] + wrong,
        'type': 'breed-to-group'
    })

    # Card 2: breed name -> country
    wrong = pick_wrong(name, all_names, 3)
    cards.append({
        'id': f"{b['id']}-country",
        'question': f"Where does {name} originate?",
        'answer': country,
        'choices': [country] + wrong,
        'type': 'breed-to-country'
    })

    # Card 3: breed name -> size
    wrong = pick_wrong(name, all_names, 3)
    cards.append({
        'id': f"{b['id']}-size",
        'question': f"What size is {name}?",
        'answer': size,
        'choices': [size] + wrong,
        'type': 'breed-to-size'
    })

    # Card 4: group -> breed name
    if group in by_group and len(by_group[group]) >= 4:
        pool = by_group[group]
        wrong = pick_wrong(name, pool, 3)
        cards.append({
            'id': f"{b['id']}-breed-from-group",
            'question': f"Which breed is in the {group} group?",
            'answer': name,
            'choices': [name] + wrong,
            'type': 'group-to-breed'
        })

    # Card 5: fact/temperament question
    if fact:
        cards.append({
            'id': f"{b['id']}-fact",
            'question': f"Which breed matches this description: {fact[:120]}...",
            'answer': name,
            'choices': [name] + pick_wrong(name, all_names, 3),
            'type': 'fact-to-breed'
        })

# Shuffle all cards
random.seed(42)
random.shuffle(cards)

with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    json.dump({'cards': cards, 'total': len(cards)}, f, indent=2, ensure_ascii=False)

print(f'[*] Generated {len(cards)} flashcards')
print(f'[*] Saved to {OUTPUT_PATH}')
