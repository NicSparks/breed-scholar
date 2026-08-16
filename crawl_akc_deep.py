#!/usr/bin/env python3
"""
AKC breed crawler: crawl https://www.akc.org/dog-breeds/ up to 7 links deep,
extract breed info, deduplicate by normalized name, and index into SQLite.
"""

import json
import re
import sqlite3
import time
from collections import OrderedDict
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

BASE_DIR = Path('/root/breed-scholar')
DB_PATH = BASE_DIR / 'dog_breeds.db'
AKC_URL = 'https://www.akc.org/dog-breeds/'
MAX_DEPTH = 7
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; BreedScholar/1.0; +https://github.com/WickedYoda/breed-scholar)'
}


def normalize(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[^a-z0-9]+', '', text)
    return text


def fetch_page(url, retries=3):
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            return resp.text
        except requests.RequestException as e:
            print(f"  [!] Fetch error (attempt {attempt + 1}): {e}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
    return None


def extract_links(html, base_url):
    soup = BeautifulSoup(html, 'html.parser')
    links = set()
    for a in soup.find_all('a', href=True):
        href = a['href']
        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)
        if parsed.netloc not in {'', 'www.akc.org', 'akc.org'}:
            continue
        path = parsed.path
        if path.startswith('/dog-breeds/') and not path.rstrip('/').endswith('/dog-breeds') or path.startswith('/') and not path.startswith('/dog-breeds/'):
            links.add(full_url)
    return links


def parse_breed_page(html, url):
    soup = BeautifulSoup(html, 'html.parser')

    name = ''
    h1 = soup.find('h1')
    if h1:
        name = h1.get_text(strip=True)
    if not name:
        title = soup.find('title')
        if title:
            name = title.get_text(strip=True).split('|')[0].strip()
            name = name.replace(' Dog Breed Information', '').replace(' - American Kennel Club', '').strip()
    if not name:
        return None

    content_div = soup.find('div', class_=re.compile('breed-content|content|description|entry-content'))
    if not content_div:
        content_div = soup.find('article') or soup.find('main') or soup

    paragraphs = [p.get_text(strip=True) for p in content_div.find_all('p') if p.get_text(strip=True)]
    fact = ' '.join(paragraphs[:4]) if paragraphs else f'{name} is a dog breed recognized by the AKC.'
    fact = fact[:800]

    group = ''
    group_match = re.search(r'Group:\\s*([^<\n]{2,60})', html)
    if group_match:
        group = group_match.group(1).strip()

    rank = None
    rank_match = re.search(r'Ranked\\s+#?(\\d+)|#(\\d+)\\s+most popular|Popularity\\s+#?(\\d+)', html, re.IGNORECASE)
    if rank_match:
        rank = int(next(g for g in rank_match.groups() if g))

    country = ''
    country_match = re.search(r'Origin:\\s*([^<\n]{2,60})', html, re.IGNORECASE)
    if country_match:
        country = country_match.group(1).strip()

    size = ''
    size_match = re.search(r'Size:\\s*([^<\n]{2,60})', html, re.IGNORECASE)
    if size_match:
        size = size_match.group(1).strip()

    image_url = f'https://commons.wikimedia.org/wiki/Special:FilePath/{name.replace(" ", "_")}?width=400'

    return {
        'name': name,
        'group': group,
        'rank': rank,
        'country': country,
        'size': size,
        'fci_group': '',
        'fact': fact,
        'tips': f'Study {name}\'s distinctive features: coat type, build, and temperament.',
        'image_url': image_url,
        'registry': 'akc',
        'source_url': url
    }


def crawl(start_url, max_depth=MAX_DEPTH):
    print(f'[*] Crawling AKC from {start_url}')
    visited = OrderedDict()
    queue = [(start_url, 0)]
    seen = {start_url}

    while queue:
        url, depth = queue.pop(0)
        print(f'  [depth={depth}] {url}')
        html = fetch_page(url)
        if not html:
            continue

        # If this looks like a breed page, parse it
        if '/dog-breeds/' in url and not url.rstrip('/').endswith('/dog-breeds'):
            breed = parse_breed_page(html, url)
            if breed:
                norm = normalize(breed['name'])
                if norm not in visited:
                    visited[norm] = breed
                    print(f"    [+] Breed: {breed['name']}")

        # Only continue crawling if we have depth left
        if depth >= max_depth:
            continue

        for link in extract_links(html, url):
            if link not in seen:
                seen.add(link)
                queue.append((link, depth + 1))

        time.sleep(0.2)

    print(f'[*] Crawl complete: {len(visited)} unique breeds from {len(seen)} URLs')
    return list(visited.values())


def index_breeds(breeds):
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

    cur.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_breeds_name_unique ON breeds(LOWER(name))')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_breeds_rank ON breeds(rank)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_breeds_country ON breeds(country)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_breeds_group ON breeds(group_name)')

    registry_map = {'akc': 1, 'fci': 2, 'non': 3}
    cur.execute("INSERT OR IGNORE INTO registries (id, code, name) VALUES (1, 'akc', 'American Kennel Club')")
    cur.execute("INSERT OR IGNORE INTO registries (id, code, name) VALUES (2, 'fci', 'Fédération Cynologique Internationale')")
    cur.execute("INSERT OR IGNORE INTO registries (id, code, name) VALUES (3, 'non', 'Non-Recognized / Other')")

    for breed in breeds:
        cur.execute('''
            INSERT OR REPLACE INTO breeds
            (name, group_name, rank, country, size, fci_group, fact, tips, image_url, source_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            breed['name'],
            breed.get('group', ''),
            breed.get('rank'),
            breed.get('country', ''),
            breed.get('size', ''),
            breed.get('fci_group', ''),
            breed.get('fact', ''),
            breed.get('tips', ''),
            breed.get('image_url', ''),
            breed.get('source_url', '')
        ))

        breed_id = cur.lastrowid
        reg_id = registry_map.get(breed.get('registry', 'non'))
        if reg_id:
            cur.execute('INSERT OR IGNORE INTO breed_registries (breed_id, registry_id) VALUES (?, ?)',
                       (breed_id, reg_id))

    conn.commit()

    total = cur.execute('SELECT COUNT(*) FROM breeds').fetchone()[0]
    conn.close()
    return total


def main():
    print("=" * 60)
    print("AKC Breed Directory Crawler & Database Builder")
    print(f"Max depth: {MAX_DEPTH}")
    print("=" * 60)

    breeds = crawl(AKC_URL, max_depth=MAX_DEPTH)

    if not breeds:
        print("[!] No breeds found.")
        return

    output_json = BASE_DIR / 'akc_crawl_results.json'
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(breeds, f, indent=2, ensure_ascii=False)
    print(f"[*] Saved crawl results to {output_json}")

    total = index_breeds(breeds)

    print("\n" + "=" * 60)
    print(f"[✓] Database ready at {DB_PATH}")
    print(f"[✓] Total breeds indexed: {total}")
    print("=" * 60)


if __name__ == '__main__':
    main()
