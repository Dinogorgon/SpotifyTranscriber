"""Test description extraction with the specific episode URL"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from spotify_scraper import SpotifyScraper

url = "https://open.spotify.com/episode/5Xb6EpJLvelula9cHaUISg"

print("=" * 80)
print("Testing Description Extraction")
print("=" * 80)
print(f"URL: {url}\n")

scraper = SpotifyScraper()
info = scraper.get_spotify_info(url)

print("\n" + "=" * 80)
print("RESULTS:")
print("=" * 80)
print(f"Title: {info.get('title', 'NOT FOUND')}")
print(f"\nDescription Found: {'YES' if info.get('description') else 'NO'}")
if info.get('description'):
    desc = info.get('description')
    print(f"Description Length: {len(desc)} characters")
    print(f"\nDescription Content:")
    print("-" * 80)
    print(desc)
    print("-" * 80)
else:
    print("ERROR: Description was NOT found!")
    
print(f"\nCover Image: {info.get('cover_image', 'NOT FOUND')[:100] if info.get('cover_image') else 'NOT FOUND'}")

# Expected description (from web search):
expected_start = "Doing the thing that scared me most"
if info.get('description') and expected_start.lower() in info.get('description', '').lower():
    print("\n✓ SUCCESS: Description matches expected content!")
else:
    print("\n✗ FAILED: Description does not match expected content")

