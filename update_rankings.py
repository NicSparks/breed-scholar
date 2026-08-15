#!/usr/bin/env python3
"""Crawl AKC popularity rankings page and update database."""

import json
import re
import sqlite3
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE_DIR = Path('/root/breed-scholar')
DB_PATH = BASE_DIR / 'dog_breeds.db'
POPULARITY_URL = 'https://www.akc.org/expert-advice/news/most-popular-dog-breeds-2025/'
HEADERS = {'User-Agent': 'Mozilla/5.0'}


def fetch_page(url, retries=3):
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            return resp.text
        except requests.RequestException as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
    return None


def parse_rankings(html):
    """Parse AKC popularity rankings."""
    soup = BeautifulSoup(html, 'html.parser')
    rankings = {}
    
    # Look for tables with rankings
    tables = soup.find_all('table')
    for table in tables:
        rows = table.find_all('tr')
        for row in rows[1:]:  # Skip header
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                rank_text = cells[0].get_text(strip=True)
                name_text = cells[1].get_text(strip=True)
                
                # Extract rank number
                rank_match = re.match(r'#?(\d+)', rank_text)
                if rank_match:
                    rank = int(rank_match.group(1))
                    name = name_text.replace(' Dog Breed', '').strip()
                    rankings[name] = rank
    
    # If no tables, try list items
    if not rankings:
        for item in soup.find_all(['li', 'div', 'p']):
            text = item.get_text(strip=True)
            match = re.match(r'#(\d+)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', text)
            if match:
                rank = int(match.group(1))
                name = match.group(2)
                rankings[name] = rank
    
    return rankings


def main():
    print("[*] Fetching AKC 2025 popularity rankings...")
    html = fetch_page(POPULARITY_URL)
    if not html:
        print("[!] Failed to fetch popularity rankings")
        return
    
    rankings = parse_rankings(html)
    print(f"[*] Found {len(rankings)} ranked breeds")
    
    if rankings:
        print("\nTop 10:")
        for name, rank in sorted(rankings.items(), key=lambda x: x[1])[:10]:
            print(f"  #{rank} {name}")
    
    # Update database
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    updated = 0
    for name, rank in rankings.items():
        cur.execute('UPDATE breeds SET rank = ? WHERE name LIKE ?', (rank, f'%{name}%'))
        if cur.rowcount > 0:
            updated += 1
    
    conn.commit()
    conn.close()
    
    print(f"\n[+] Updated {updated} breeds with rankings")


if __name__ == '__main__':
    main()
