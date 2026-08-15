#!/usr/bin/env python3
"""
Crawl AKC dog breeds page and index into database.
Follows links up to 10 levels deep.
"""

import json
import re
import sqlite3
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

BASE_DIR = Path('/root/breed-scholar')
DB_PATH = BASE_DIR / 'dog_breeds.db'
AKC_BASE = 'https://www.akc.org/dog-breeds/'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; BreedScholar/1.0; +https://github.com/WickedYoda/breed-scholar)'
}


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
        if parsed.netloc == urlparse(AKC_BASE).netloc:
            links.add(full_url)
    return links


def is_breed_page(url):
    parsed = urlparse(url)
    path = parsed.path
    return '/dog-breeds/' in path and not path.rstrip('/').endswith('/dog-breeds')


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
    if not name:
        return None
    
    content_div = soup.find('div', class_=re.compile('breed-content|content|description|entry-content'))
    if not content_div:
        content_div = soup.find('article') or soup.find('main') or soup
    
    paragraphs = [p.get_text(strip=True) for p in content_div.find_all('p') if p.get_text(strip=True)]
    fact = ' '.join(paragraphs[:4]) if paragraphs else f'{name} is a dog breed recognized by the AKC.'
    fact = fact[:800]
    
    group = ''
    group_match = re.search(r'Group:\s*([^<\n]{2,50})', html)
    if not group_match:
        group_match = re.search(r'<h[23][^>]*>\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*</h[23]>', html)
    if group_match:
        group = group_match.group(1).strip()
    
    rank = None
    rank_match = re.search(r'Ranked\s+#?(\d+)|#(\d+)\s+most popular|Popularity\s+#?(\d+)', html, re.IGNORECASE)
    if rank_match:
        rank = int(next(g for g in rank_match.groups() if g))
    
    country = ''
    country_match = re.search(r'Origin:\s*([^<\n]{2,60})', html, re.IGNORECASE)
    if country_match:
        country = country_match.group(1).strip()
    
    size = ''
    size_match = re.search(r'Size:\s*([^<\n]{2,60})', html, re.IGNORECASE)
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


def crawl_akc(max_depth=10):
    print(f"[*] Starting AKC crawl with depth {max_depth}")
    
    visited = set()
    breed_pages = {}
    frontier = {AKC_BASE}
    
    for depth in range(max_depth):
        if not frontier:
            break
        
        current = frontier
        frontier = set()
        print(f"\n[*] Depth {depth + 1}/{max_depth}: {len(current)} URLs")
        
        for url in current:
            if url in visited:
                continue
            visited.add(url)
            
            html = fetch_page(url)
            if not html:
                continue
            
            if is_breed_page(url):
                breed = parse_breed_page(html, url)
                if breed:
                    breed_pages[breed['name']] = breed
                    print(f"  [+] Breed: {breed['name']}")
            
            links = extract_links(html, url)
            new_links = links - visited
            frontier.update(new_links)
            
            time.sleep(0.3)
    
    print(f"\n[*] Crawl complete: {len(breed_pages)} breeds found")
    return breed_pages


def init_db():
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
    
    conn.commit()
    conn.close()
    print("[*] Database initialized")


def index_breeds(breed_data):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    registry_map = {'akc': 1, 'fci': 2, 'non': 3}
    
    for breed in breed_data.values():
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
    
    print(f"[+] Indexed {total} breeds into database")
    return total


def main():
    print("=" * 60)
    print("AKC Breed Crawler & Database Builder")
    print("=" * 60)
    
    # Initialize database
    init_db()
    
    # Crawl AKC
    breed_data = crawl_akc(max_depth=10)
    
    if not breed_data:
        print("[!] No breeds found. Check network or AKC site structure.")
        return
    
    # Save raw crawl data
    output_json = BASE_DIR / 'akc_crawl_results.json'
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(breed_data, f, indent=2, ensure_ascii=False)
    print(f"[*] Saved crawl results to {output_json}")
    
    # Index into database
    total = index_breeds(breed_data)
    
    print("\n" + "=" * 60)
    print(f"[✓] Database ready at {DB_PATH}")
    print(f"[✓] Total breeds indexed: {total}")
    print("=" * 60)


if __name__ == '__main__':
    main()
