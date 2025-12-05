"""
Standalone script to download audio from Spotify episode
Usage: python download_audio.py <spotify_url> <output_path>
"""
import sys
import json
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from spotify_scraper import SpotifyScraper
from audio_downloader import AudioDownloader

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(json.dumps({'error': 'Usage: python download_audio.py <spotify_url> <output_path>'}), file=sys.stderr)
        sys.exit(1)
    
    url = sys.argv[1]
    output_path = sys.argv[2]
    
    scraper = SpotifyScraper()
    info = scraper.get_spotify_info(url)
    
    if not info:
        print(json.dumps({'error': 'Could not extract metadata'}), file=sys.stderr)
        sys.exit(1)
    
    downloader = AudioDownloader()
    audio_path = downloader.download_from_spotify(url, spotify_info=info)
    
    # Copy to output path if different
    if audio_path != output_path:
        import shutil
        shutil.copy(audio_path, output_path)
    
    print(json.dumps({'path': output_path}))

