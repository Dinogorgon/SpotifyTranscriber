"""
Standalone script to get Spotify episode metadata
Usage: python get_metadata.py <spotify_url>
Output: JSON metadata
"""
import sys
import json
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from spotify_scraper import SpotifyScraper

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'No URL provided'}), file=sys.stderr)
        sys.exit(1)
    
    url = sys.argv[1]
    scraper = SpotifyScraper()
    info = scraper.get_spotify_info(url)
    
    if info:
        print(json.dumps(info, ensure_ascii=False))
    else:
        print(json.dumps({'error': 'Could not extract metadata'}), file=sys.stderr)
        sys.exit(1)

