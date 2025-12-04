"""Test RSS feed for description"""
from backend.spotify_rss import SpotifyRSSFetcher
import feedparser

url = "https://open.spotify.com/episode/5Xb6EpJLvelula9cHaUISg"
rss_fetcher = SpotifyRSSFetcher()

# Get show ID
show_id = rss_fetcher.get_show_id(url, {'id': '5Xb6EpJLvelula9cHaUISg'})
print(f"Show ID: {show_id}")

if show_id:
    # Fetch feed
    feed_url = rss_fetcher._fetch_feed_from_spotify(show_id) or rss_fetcher._fetch_feed_from_itunes(show_id)
    print(f"Feed URL: {feed_url}")
    
    if feed_url:
        feed = rss_fetcher._parse_feed(feed_url)
        print(f"Feed entries: {len(feed.entries) if feed else 0}")
        
        # Find our episode
        for i, entry in enumerate(feed.entries[:5]):
            print(f"\nEntry {i}:")
            print(f"  Title: {entry.get('title', '')[:80]}")
            print(f"  ID: {entry.get('id', '')[:50]}")
            print(f"  Summary length: {len(entry.get('summary', '') or '')}")
            if entry.get('summary'):
                print(f"  Summary: {entry.get('summary', '')[:200]}")

