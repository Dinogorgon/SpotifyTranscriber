"""Test scraper with specific episode URL"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from spotify_scraper import SpotifyScraper
import requests
from bs4 import BeautifulSoup
import json
import re

url = "https://open.spotify.com/episode/5Xb6EpJLvelula9cHaUISg"

print("=" * 80)
print("Testing Spotify Episode Scraper")
print("=" * 80)
print(f"URL: {url}")
print()

# Test the scraper
scraper = SpotifyScraper()
info = scraper.get_spotify_info(url)

print("\n" + "=" * 80)
print("SCRAPER RESULTS:")
print("=" * 80)
print(f"Title: {info.get('title', 'NOT FOUND')}")
print(f"Subtitle: {info.get('subtitle', 'NOT FOUND')}")
print(f"Description: {info.get('description', 'NOT FOUND')[:500] if info.get('description') else 'NOT FOUND'}")
print(f"Description Length: {len(info.get('description', ''))}")
print(f"Cover Image: {info.get('cover_image', 'NOT FOUND')[:100] if info.get('cover_image') else 'NOT FOUND'}")
print(f"Release Date: {info.get('release_date', 'NOT FOUND')}")

# Now manually check the page
print("\n" + "=" * 80)
print("MANUAL PAGE INSPECTION:")
print("=" * 80)

response = scraper.session.get(url, timeout=15)
soup = BeautifulSoup(response.text, 'html.parser')

# Check meta tags
print("\n--- Meta Tags ---")
meta_desc = soup.find('meta', property='og:description')
if meta_desc:
    print(f"og:description: {meta_desc.get('content', '')[:200]}")
else:
    print("og:description: NOT FOUND")

# Check all meta tags with description
all_meta = soup.find_all('meta')
for meta in all_meta:
    prop = meta.get('property', '') or meta.get('name', '')
    if 'description' in prop.lower():
        print(f"{prop}: {meta.get('content', '')[:200]}")

# Check __NEXT_DATA__
print("\n--- __NEXT_DATA__ Check ---")
next_data = soup.find('script', id='__NEXT_DATA__')
if next_data:
    try:
        data = json.loads(next_data.string)
        # Navigate to entity
        if 'props' in data:
            page_props = data['props'].get('pageProps', {})
            if 'state' in page_props:
                state = page_props['state']
                if 'data' in state:
                    data_obj = state['data']
                    if 'entity' in data_obj:
                        entity = data_obj['entity']
                        print(f"Found entity with keys: {list(entity.keys())[:20]}")
                        
                        # Check for description in various places
                        desc_paths = [
                            ('description', entity.get('description')),
                            ('htmlDescription', entity.get('htmlDescription')),
                            ('content.description', entity.get('content', {}).get('description') if isinstance(entity.get('content'), dict) else None),
                            ('content.htmlDescription', entity.get('content', {}).get('htmlDescription') if isinstance(entity.get('content'), dict) else None),
                        ]
                        
                        for path, value in desc_paths:
                            if value:
                                print(f"  {path}: {str(value)[:200]}")
    except Exception as e:
        print(f"Error parsing __NEXT_DATA__: {e}")

# Check visible text content
print("\n--- Visible Text Content ---")
# Look for paragraph tags with long text
paragraphs = soup.find_all('p')
for i, p in enumerate(paragraphs[:10]):
    text = p.get_text(strip=True)
    if len(text) > 100:
        print(f"Paragraph {i+1} ({len(text)} chars): {text[:200]}")

