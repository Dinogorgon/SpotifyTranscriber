"""
Standalone script to download audio from Spotify episode
Usage: python download_audio.py <spotify_url> <output_path>
"""
import sys
import json
import os
import signal

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from spotify_scraper import SpotifyScraper
from audio_downloader import AudioDownloader

# Set up timeout handler
def timeout_handler(signum, frame):
    print(json.dumps({'error': 'Download timeout: Process took too long'}), file=sys.stderr)
    sys.exit(1)

if __name__ == '__main__':
    # Force unbuffered output for stderr
    sys.stderr.reconfigure(line_buffering=True)
    sys.stdout.reconfigure(line_buffering=True)
    
    if len(sys.argv) < 3:
        print(json.dumps({'error': 'Usage: python download_audio.py <spotify_url> <output_path>'}), file=sys.stderr)
        sys.exit(1)
    
    # Set timeout (15 minutes for large files)
    if hasattr(signal, 'SIGALRM'):
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(900)  # 15 minutes
    
    url = sys.argv[1]
    output_path = sys.argv[2]
    
    def progress_callback(progress):
        # Print progress as JSON for Next.js to parse
        # Use unbuffered write to ensure immediate output
        message = json.dumps({'progress': progress, 'stage': 'download'}) + '\n'
        sys.stderr.write(message)
        sys.stderr.flush()
    
    try:
        # Send initial progress - use unbuffered write
        sys.stderr.write(json.dumps({'progress': 0.0, 'stage': 'download'}) + '\n')
        sys.stderr.flush()
        
        # Note: Metadata is already fetched in the previous step, but we need it for RSS lookup
        # Send progress for RSS fetching phase
        sys.stderr.write(json.dumps({'progress': 0.1, 'stage': 'download', 'message': 'Finding audio source...'}) + '\n')
        sys.stderr.flush()
        
        scraper = SpotifyScraper()
        info = scraper.get_spotify_info(url)
        
        if not info:
            sys.stderr.write(json.dumps({'error': 'Could not extract metadata'}) + '\n')
            sys.stderr.flush()
            sys.exit(1)
        
        # Send progress for RSS lookup
        sys.stderr.write(json.dumps({'progress': 0.2, 'stage': 'download', 'message': 'Locating audio file...'}) + '\n')
        sys.stderr.flush()
        
        downloader = AudioDownloader()
        audio_path = downloader.download_from_spotify(url, spotify_info=info, progress_callback=progress_callback)
        
        # Copy to output path if different
        if audio_path != output_path:
            import shutil
            shutil.copy(audio_path, output_path)
        
        sys.stdout.write(json.dumps({'path': output_path}) + '\n')
        sys.stdout.flush()
    except Exception as e:
        sys.stderr.write(json.dumps({'error': str(e)}) + '\n')
        sys.stderr.flush()
        sys.exit(1)
    finally:
        # Cancel timeout
        if hasattr(signal, 'SIGALRM'):
            signal.alarm(0)

