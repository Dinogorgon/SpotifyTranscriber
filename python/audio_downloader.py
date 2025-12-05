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

# Ensure FFmpeg is available for optional conversions
if not ffmpeg_setup.check_ffmpeg():
    try:
        ffmpeg_setup.install_ffmpeg()
    except Exception as exc:  # pragma: no cover
        print(f"Warning: Could not install FFmpeg automatically: {exc}")


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

    def download_from_url(self, url, output_filename=None, extension=None):
        """Download audio from a direct URL."""
        if output_filename is None:
            output_filename = "spotify_audio"

        guessed_ext = extension or Path(urlsplit(url).path).suffix
        if not guessed_ext:
            guessed_ext = ".mp3"

        output_path = self.download_dir / f"{output_filename}{guessed_ext}"
        response = self.session.get(url, stream=True, timeout=60)
        response.raise_for_status()

        with open(output_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)

        if not output_path.exists() or output_path.stat().st_size == 0:
            raise ValueError("Downloaded file is empty or missing")

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

    def download_from_spotify(self, spotify_url, spotify_info=None, output_filename=None):
        """
        Download audio for a Spotify podcast episode by resolving its RSS enclosure.
        """
        if output_filename is None:
            output_filename = "spotify_audio"

        audio_meta = self.rss_fetcher.get_episode_audio(spotify_url, spotify_info or {})
        audio_url = audio_meta["audio_url"]
        extension = audio_meta.get("extension") or ".mp3"

        return self.download_from_url(audio_url, output_filename, extension)

    def cleanup(self, file_path):
        """Remove downloaded file."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except OSError as exc:  # pragma: no cover
            print(f"Error cleaning up file: {exc}")
