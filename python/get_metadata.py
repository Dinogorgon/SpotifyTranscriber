"""
Standalone script to get Spotify episode metadata
Usage: python get_metadata.py <spotify_url>
Output: JSON metadata
"""
import sys
import json
import os
import contextlib
import io

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from spotify_scraper import SpotifyScraper

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'No URL provided'}), file=sys.stderr)
        sys.exit(1)
    
    url = sys.argv[1]
    
    # Suppress debug output by redirecting stdout temporarily
    # We'll capture it but only output the final JSON
    scraper = SpotifyScraper()
    
    # Capture stdout to filter out debug messages
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    
    try:
        # Redirect stdout/stderr temporarily to capture debug output
        with contextlib.redirect_stdout(stdout_capture), contextlib.redirect_stderr(stderr_capture):
            info = scraper.get_spotify_info(url)
        
        if info:
            # Output only the JSON result
            print(json.dumps(info, ensure_ascii=False))
        else:
            print(json.dumps({'error': 'Could not extract metadata'}), file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(json.dumps({'error': str(e)}), file=sys.stderr)
        sys.exit(1)

