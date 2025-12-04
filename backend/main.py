"""
FastAPI backend for Spotify Transcriber
Handles audio processing, transcription, and metadata extraction
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse, Response
from pydantic import BaseModel
from typing import Optional
import os
import sys
import tempfile
import shutil
from pathlib import Path
import requests

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from audio_downloader import AudioDownloader
from format_converters import FormatConverter
from spotify_scraper import SpotifyScraper
from transcriber import Transcriber
from summarizer import Summarizer

app = FastAPI(title="Spotify Transcriber API")

# CORS middleware to allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
scraper = SpotifyScraper()
downloader = AudioDownloader()
transcriber_cache = {}

# Request/Response models
class TranscribeRequest(BaseModel):
    spotify_url: str
    backend: str = "faster"  # "faster" or "openai"
    model_size: str = "base"

class MetadataResponse(BaseModel):
    id: str
    title: str
    subtitle: Optional[str] = None
    description: Optional[str] = None
    cover_image: Optional[str] = None
    release_date: Optional[str] = None

class TranscriptionResponse(BaseModel):
    text: str
    segments: list
    language: str
    duration: float
    summary: str

@app.get("/")
async def root():
    return {"message": "Spotify Transcriber API", "status": "running"}

@app.get("/api/metadata")
async def get_metadata(spotify_url: str):
    """Get Spotify episode metadata"""
    try:
        info = scraper.get_spotify_info(spotify_url)
        if not info:
            raise HTTPException(status_code=404, detail="Could not extract metadata from Spotify URL")
        
        return MetadataResponse(
            id=info.get('id', ''),
            title=info.get('title', 'Unknown Episode'),
            subtitle=info.get('subtitle'),
            description=info.get('description'),
            cover_image=info.get('cover_image'),
            release_date=info.get('release_date')
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/transcribe")
async def transcribe_episode(request: TranscribeRequest, background_tasks: BackgroundTasks):
    """Transcribe a Spotify episode"""
    temp_path = None
    try:
        # Step 1: Get metadata
        info = scraper.get_spotify_info(request.spotify_url)
        if not info:
            raise HTTPException(status_code=404, detail="Could not extract metadata from Spotify URL")
        
        # Step 2: Download audio
        temp_path = downloader.download_from_spotify(request.spotify_url, spotify_info=info)
        
        # Step 3: Initialize transcriber
        cache_key = f"{request.backend}_{request.model_size}"
        if cache_key not in transcriber_cache:
            transcriber_cache[cache_key] = Transcriber(
                model_size=request.model_size,
                backend=request.backend
            )
        transcriber = transcriber_cache[cache_key]
        
        # Step 4: Transcribe
        transcription_result = transcriber.transcribe(temp_path)
        
        # Step 5: Generate comprehensive summary
        summary = Summarizer.summarize(transcription_result, max_sentences=15)
        
        # Cleanup temp file in background
        if temp_path and os.path.exists(temp_path):
            background_tasks.add_task(cleanup_file, temp_path)
        
        return TranscriptionResponse(
            text=transcription_result.get('text', ''),
            segments=transcription_result.get('segments', []),
            language=transcription_result.get('language', 'en'),
            duration=transcription_result.get('duration', 0),
            summary=summary
        )
    except Exception as e:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/proxy-image")
async def proxy_image(image_url: str):
    """Proxy Spotify images to avoid CORS issues"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://open.spotify.com/'
        }
        response = requests.get(image_url, headers=headers, timeout=10, stream=True)
        if response.status_code == 200:
            return Response(
                content=response.content,
                media_type=response.headers.get('Content-Type', 'image/jpeg')
            )
        else:
            raise HTTPException(status_code=404, detail="Image not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/download-audio")
async def download_audio(spotify_url: str):
    """Download audio file as MP3"""
    temp_path = None
    try:
        info = scraper.get_spotify_info(spotify_url)
        if not info:
            raise HTTPException(status_code=404, detail="Could not extract metadata")
        
        temp_path = downloader.download_from_spotify(spotify_url, spotify_info=info)
        
        # Convert to MP3 if needed
        temp_ext = Path(temp_path).suffix.lower()
        if temp_ext != ".mp3":
            mp3_path = temp_path.replace(temp_ext, ".mp3")
            downloader.convert_to_mp3(temp_path, mp3_path)
            os.remove(temp_path)
            temp_path = mp3_path
        
        # Generate filename
        filename = f"{info.get('title', 'episode').replace('/', '_')}.mp3"
        
        return FileResponse(
            temp_path,
            media_type="audio/mpeg",
            filename=filename,
            background=lambda: cleanup_file(temp_path) if os.path.exists(temp_path) else None
        )
    except Exception as e:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/export")
async def export_transcription(
    text: str,
    segments: list,
    format_type: str = "txt"
):
    """Export transcription in various formats"""
    try:
        transcription_result = {
            "text": text,
            "segments": segments
        }
        
        # Create temp file
        temp_dir = tempfile.mkdtemp()
        output_path = os.path.join(temp_dir, f"transcription.{format_type}")
        
        FormatConverter.export(transcription_result, output_path.replace(f".{format_type}", ""), format_type)
        
        if not os.path.exists(output_path):
            raise HTTPException(status_code=500, detail="Failed to create export file")
        
        media_types = {
            "txt": "text/plain",
            "json": "application/json",
            "srt": "text/plain",
            "vtt": "text/vtt"
        }
        
        return FileResponse(
            output_path,
            media_type=media_types.get(format_type, "text/plain"),
            filename=f"transcription.{format_type}",
            background=lambda: shutil.rmtree(temp_dir, ignore_errors=True)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def cleanup_file(file_path: str):
    """Background task to cleanup temporary files"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except:
        pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

