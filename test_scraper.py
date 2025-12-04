"""Test the scraper"""
from backend.spotify_scraper import SpotifyScraper
import json

s = SpotifyScraper()
info = s.get_spotify_info('https://open.spotify.com/episode/5Xb6EpJLvelula9cHaUISg')

print('\n=== RESULTS ===')
print(f'Title: {info.get("title")}')
print(f'Description: {"YES" if info.get("description") else "NO"} (length: {len(info.get("description", "") or "")})')
print(f'Cover Image: {"YES" if info.get("cover_image") else "NO"}')
if info.get("cover_image"):
    print(f'Cover URL: {info.get("cover_image")[:100]}')
if info.get("description"):
    print(f'Description preview: {info.get("description")[:200]}')

