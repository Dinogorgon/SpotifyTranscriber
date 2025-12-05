"""
Audio downloader that locates podcast audio via RSS feeds (legal workflow).
"""
import os
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlsplit

import requests

import ffmpeg_setup
from spotify_rss import SpotifyRSSFetcher
import sys
import os
# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Don't auto-install FFmpeg during import - it blocks the process
# FFmpeg is only needed for conversion, not RSS downloads
# We'll check/install it lazily when needed


class AudioDownloader:
    """Download Spotify podcast audio by resolving RSS enclosures."""

    def __init__(self, download_dir=None):
        if download_dir is None:
            download_dir = os.path.join(tempfile.gettempdir(), "spotify_transcriber")

        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)

        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            }
        )
        self.rss_fetcher = SpotifyRSSFetcher()

    def download_from_url(self, url, output_filename=None, extension=None, progress_callback=None):
        """Download audio from a direct URL with progress reporting and timeout."""
        if output_filename is None:
            output_filename = "spotify_audio"

        guessed_ext = extension or Path(urlsplit(url).path).suffix
        if not guessed_ext:
            guessed_ext = ".mp3"

        output_path = self.download_dir / f"{output_filename}{guessed_ext}"
        
        # Timeout for download: 10s connect, 60s read (RSS files should download quickly)
        try:
            response = self.session.get(url, stream=True, timeout=(10, 60))
            response.raise_for_status()
        except requests.exceptions.Timeout:
            raise RuntimeError("Download timeout: The server took too long to respond. The audio file may be very large or the server is slow.")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Download failed: {str(e)}")

        # Get content length if available
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        chunk_size = 8192
        last_progress = 0.0
        last_report_time = 0

        try:
            import time
            start_time = time.time()
            
            with open(output_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:  # filter out keep-alive new chunks
                        file.write(chunk)
                        downloaded += len(chunk)
                        
                        current_time = time.time()
                        
                        # Report progress every 1% OR every 1 second (whichever comes first)
                        if progress_callback and total_size > 0:
                            progress = downloaded / total_size
                            if progress - last_progress >= 0.01 or progress >= 1.0 or (current_time - last_report_time) >= 1.0:
                                progress_callback(progress)
                                last_progress = progress
                                last_report_time = current_time
                        elif progress_callback:
                            # If we don't know total size, report based on chunks and time
                            # Report every 1 second or every 500KB
                            if (current_time - last_report_time) >= 1.0 or downloaded % (512 * 1024) < chunk_size:
                                # Estimate progress based on typical podcast size (assume 50MB for 30min episode)
                                estimated_total = 50 * 1024 * 1024
                                progress = min(downloaded / estimated_total, 0.99)
                                progress_callback(progress)
                                last_report_time = current_time
        except Exception as e:
            # Clean up partial download on error
            if output_path.exists():
                try:
                    output_path.unlink()
                except:
                    pass
            raise RuntimeError(f"Download failed: {str(e)}")

        if not output_path.exists() or output_path.stat().st_size == 0:
            raise ValueError("Downloaded file is empty or missing")

        if progress_callback:
            progress_callback(1.0)

        return str(output_path)

    def convert_to_mp3(self, input_path, output_path):
        """Convert audio file to MP3 using FFmpeg."""
        try:
            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                str(input_path),
                "-codec:a",
                "libmp3lame",
                "-qscale:a",
                "2",
                str(output_path),
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            if not os.path.exists(output_path):
                raise ValueError("FFmpeg failed to create the output file")

            return str(output_path)
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(f"FFmpeg conversion failed: {exc.stderr.decode(errors='ignore')}") from exc

    def download_from_spotify(self, spotify_url, spotify_info=None, output_filename=None, progress_callback=None):
        """
        Download audio for a Spotify podcast episode by resolving its RSS enclosure.
        """
        if output_filename is None:
            output_filename = "spotify_audio"

        try:
            # Report progress for RSS lookup (maps to 20-30% of download stage)
            if progress_callback:
                progress_callback(0.3)  # RSS lookup started
            
            audio_meta = self.rss_fetcher.get_episode_audio(spotify_url, spotify_info or {})
            audio_url = audio_meta["audio_url"]
            extension = audio_meta.get("extension") or ".mp3"

            # Report progress for starting actual download (maps to 30-40% of download stage)
            if progress_callback:
                progress_callback(0.4)  # Starting download
            
            # Download with progress callback (maps to 40-100% of download stage)
            # We need to remap the callback to fit in the 40-100% range
            def remapped_callback(progress):
                # Map 0-1 from download_from_url to 0.4-1.0 overall
                if progress_callback:
                    progress_callback(0.4 + (progress * 0.6))
            
            return self.download_from_url(audio_url, output_filename, extension, remapped_callback)
        except Exception as e:
            raise RuntimeError(f"Failed to download Spotify audio: {str(e)}")

    def cleanup(self, file_path):
        """Remove downloaded file."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except OSError as exc:  # pragma: no cover
            print(f"Error cleaning up file: {exc}")
