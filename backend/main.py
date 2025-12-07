"""
FastAPI backend for Spotify Transcriber
Handles all Python processing: metadata fetching, audio download, transcription, and summarization
"""
import os
import sys
import json
import subprocess
import tempfile
import shutil
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse, Response
from pydantic import BaseModel
import requests

# Add python directory to path so we can import modules
PROJECT_ROOT = Path(__file__).parent.parent
PYTHON_DIR = PROJECT_ROOT / "python"
sys.path.insert(0, str(PYTHON_DIR))

app = FastAPI(title="Spotify Transcriber API")

# CORS configuration - allow Netlify and localhost
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        os.getenv("FRONTEND_URL", "http://localhost:3000"),
        "https://spotifytranscriber.name.me",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request models
class TranscribeRequest(BaseModel):
    spotify_url: Optional[str] = None
    file_path: Optional[str] = None
    backend: str = "faster"
    model_size: str = "base"


@app.get("/health")
def health_check():
    """Health check endpoint for keep-alive"""
    return {
        "status": "ok",
        "service": "spotify-transcriber-backend",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/metadata")
async def get_metadata(spotify_url: str):
    """Get Spotify episode metadata"""
    if not spotify_url:
        raise HTTPException(status_code=400, detail="spotify_url parameter is required")
    
    try:
        result = subprocess.run(
            ["python", str(PYTHON_DIR / "get_metadata.py"), spotify_url],
            cwd=str(PYTHON_DIR),
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            # Filter out debug messages
            lines = result.stdout.strip().split('\n')
            json_lines = [line for line in lines if line.strip().startswith('{') or line.strip().startswith('[')]
            json_output = json_lines[0] if json_lines else result.stdout.strip()
            
            try:
                return json.loads(json_output)
            except json.JSONDecodeError as e:
                raise HTTPException(status_code=500, detail=f"Failed to parse metadata: {str(e)}")
        else:
            # Filter out debug messages from stderr
            error_lines = result.stderr.strip().split('\n')
            error_lines = [line for line in error_lines if not line.startswith('DEBUG:') and line.strip()]
            error_message = '\n'.join(error_lines) if error_lines else result.stderr or f"Process exited with code {result.returncode}"
            raise HTTPException(status_code=500, detail=error_message)
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Metadata fetch timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch metadata: {str(e)}")


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Handle file uploads"""
    MAX_FILE_SIZE = 1610612736  # 1.5 GB
    ALLOWED_TYPES = ['audio/mpeg', 'audio/mp3', 'audio/mp4', 'video/mp4', 'audio/x-m4a', 'audio/m4a']
    ALLOWED_EXTENSIONS = ['.mp3', '.mp4', '.m4a']
    
    # Validate file type
    file_extension = '.' + file.filename.split('.')[-1].lower() if '.' in file.filename else ''
    is_valid_type = file.content_type in ALLOWED_TYPES or file_extension in ALLOWED_EXTENSIONS
    
    if not is_valid_type:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload an MP3, MP4, or M4A file."
        )
    
    # Read file content
    content = await file.read()
    
    # Validate file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds maximum of 1.5 GB. File size: {len(content) / 1024 / 1024:.2f} MB"
        )
    
    # Create temporary directory and save file
    temp_dir = tempfile.mkdtemp(prefix='spotify-transcriber-upload-')
    file_path = os.path.join(temp_dir, file.filename)
    
    try:
        with open(file_path, 'wb') as f:
            f.write(content)
        
        return {
            "file_path": file_path,
            "file_name": file.filename,
            "file_size": len(content),
        }
    except Exception as e:
        # Cleanup on error
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except:
            pass
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")


@app.get("/api/download-audio")
async def download_audio(spotify_url: str):
    """Download audio file from Spotify and return as MP3"""
    if not spotify_url:
        raise HTTPException(status_code=400, detail="spotify_url parameter is required")
    
    temp_dir = None
    audio_path = None
    
    try:
        # Step 1: Get metadata for filename
        metadata_result = subprocess.run(
            ["python", str(PYTHON_DIR / "get_metadata.py"), spotify_url],
            cwd=str(PYTHON_DIR),
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if metadata_result.returncode != 0:
            error_lines = metadata_result.stderr.strip().split('\n')
            error_lines = [line for line in error_lines if not line.startswith('DEBUG:') and line.strip()]
            error_message = '\n'.join(error_lines) if error_lines else "Failed to get metadata"
            raise HTTPException(status_code=500, detail=error_message)
        
        # Parse metadata
        lines = metadata_result.stdout.strip().split('\n')
        json_lines = [line for line in lines if line.strip().startswith('{') or line.strip().startswith('[')]
        json_output = json_lines[0] if json_lines else metadata_result.stdout.strip()
        
        try:
            metadata = json.loads(json_output)
            title = metadata.get('title', 'episode')
        except json.JSONDecodeError:
            title = 'episode'
        
        # Step 2: Download audio
        temp_dir = tempfile.mkdtemp(prefix='spotify-transcriber-download-')
        audio_path = os.path.join(temp_dir, 'audio.mp3')
        
        download_result = subprocess.run(
            ["python", str(PYTHON_DIR / "download_audio.py"), spotify_url, audio_path],
            cwd=str(PYTHON_DIR),
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if download_result.returncode != 0:
            error_lines = download_result.stderr.strip().split('\n')
            error_json = None
            for line in error_lines:
                try:
                    parsed = json.loads(line.strip())
                    if parsed.get('error'):
                        error_json = parsed['error']
                        break
                except:
                    continue
            
            error_message = error_json if error_json else (download_result.stderr or "Failed to download audio")
            raise HTTPException(status_code=500, detail=error_message)
        
        # Step 3: Generate filename
        filename = f"{title.replace('/', '_').replace('\\', '_')[:100]}.mp3"
        # Remove any invalid filename characters
        filename = ''.join(c for c in filename if c.isalnum() or c in '._- ')
        
        # Step 4: Return file
        return FileResponse(
            audio_path,
            media_type='audio/mpeg',
            filename=filename,
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"'
            }
        )
        
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Download timeout")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download audio: {str(e)}")
    finally:
        # Note: FileResponse will handle file cleanup after sending
        # But we should still clean up if there was an error
        if temp_dir and os.path.exists(temp_dir) and (not audio_path or not os.path.exists(audio_path)):
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except:
                pass


@app.get("/api/proxy-image")
async def proxy_image(image_url: str):
    """Proxy image from external URL to avoid CORS issues"""
    if not image_url:
        raise HTTPException(status_code=400, detail="image_url parameter is required")
    
    try:
        response = requests.get(
            image_url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://open.spotify.com/',
            },
            timeout=10
        )
        
        response.raise_for_status()
        
        content_type = response.headers.get('Content-Type', 'image/jpeg')
        
        return Response(
            content=response.content,
            media_type=content_type,
            headers={
                'Cache-Control': 'public, max-age=31536000, immutable',
            }
        )
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch image: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image proxy error: {str(e)}")


async def read_subprocess_output(process, queue):
    """Read subprocess output and put lines in queue"""
    for line in iter(process.stderr.readline, ''):
        if not line:
            break
        await queue.put(line)
    await queue.put(None)  # Signal end


@app.post("/api/transcribe-stream")
async def transcribe_stream(request: TranscribeRequest):
    """Stream transcription progress using Server-Sent Events"""
    
    if not request.spotify_url and not request.file_path:
        async def error_stream():
            yield f"data: {json.dumps({'type': 'error', 'error': 'Either spotify_url or file_path is required'})}\n\n"
        return StreamingResponse(error_stream(), media_type="text/event-stream")
    
    async def generate_stream():
        temp_dir = None
        
        def send_progress(message: str, percent: float):
            data = json.dumps({"type": "progress", "message": message, "percent": percent})
            return f"data: {data}\n\n"
        
        def send_error(error: str):
            data = json.dumps({"type": "error", "error": error})
            return f"data: {data}\n\n"
        
        try:
            audio_path = None
            
            if request.file_path:
                # Verify file exists
                if not os.path.exists(request.file_path):
                    yield send_error(f"Uploaded file not found: {request.file_path}")
                    return
                
                audio_path = request.file_path
                # Extract temp directory from file path
                path_parts = request.file_path.replace('\\', '/').split('/')
                temp_dir_index = next((i for i, part in enumerate(path_parts) if part.startswith('spotify-transcriber-upload-')), -1)
                if temp_dir_index != -1:
                    temp_dir = '/'.join(path_parts[:temp_dir_index + 1])
                else:
                    temp_dir = os.path.dirname(request.file_path)
            
            elif request.spotify_url:
                # Step 1: Get metadata
                yield send_progress("Fetching Spotify metadata...", 10)
                metadata_result = subprocess.run(
                    ["python", str(PYTHON_DIR / "get_metadata.py"), request.spotify_url],
                    cwd=str(PYTHON_DIR),
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if metadata_result.returncode != 0:
                    error_lines = metadata_result.stderr.strip().split('\n')
                    error_lines = [line for line in error_lines if not line.startswith('DEBUG:') and line.strip()]
                    error_message = '\n'.join(error_lines) if error_lines else "Failed to get metadata"
                    yield send_error(error_message)
                    return
                
                # Step 2: Download audio with real-time progress
                yield send_progress("Downloading audio...", 20)
                temp_dir = tempfile.mkdtemp(prefix='spotify-transcriber-')
                audio_path = os.path.join(temp_dir, "audio.mp3")
                
                download_process = subprocess.Popen(
                    ["python", "-u", str(PYTHON_DIR / "download_audio.py"), request.spotify_url, audio_path],
                    cwd=str(PYTHON_DIR),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1
                )
                
                download_stderr = ""
                for line in iter(download_process.stderr.readline, ''):
                    if not line:
                        break
                    download_stderr += line
                    line = line.strip()
                    if line:
                        try:
                            parsed = json.loads(line)
                            if parsed.get('progress') is not None and parsed.get('stage') == 'download':
                                progress = parsed['progress']
                                download_percent = 20 + (progress * 10)
                                progress_percent = int(progress * 100)
                                message = parsed.get('message', f"Downloading audio... {progress_percent}%")
                                yield send_progress(message, download_percent)
                            elif parsed.get('error'):
                                download_process.kill()
                                yield send_error(parsed['error'])
                                return
                        except:
                            pass
                
                download_process.wait(timeout=300)
                
                if download_process.returncode != 0:
                    # Try to parse error from stderr
                    error_json = None
                    for line in download_stderr.split('\n'):
                        try:
                            parsed = json.loads(line.strip())
                            if parsed.get('error'):
                                error_json = parsed['error']
                                break
                        except:
                            continue
                    
                    if error_json:
                        yield send_error(error_json)
                    else:
                        yield send_error(download_stderr or "Failed to download audio")
                    return
                
                yield send_progress("Download complete", 30)
            
            # Step 3: Transcribe with real-time progress
            yield send_progress("Starting transcription...", 30)
            
            env = os.environ.copy()
            env['PYTHONWARNINGS'] = 'ignore::DeprecationWarning:pkg_resources'
            
            transcribe_process = subprocess.Popen(
                ["python", "-u", str(PYTHON_DIR / "transcribe_audio.py"), audio_path, request.backend, request.model_size],
                cwd=str(PROJECT_ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                bufsize=1
            )
            
            stdout_data = ""
            last_progress_time = datetime.now()
            
            # Read stderr for progress updates
            for line in iter(transcribe_process.stderr.readline, ''):
                if not line:
                    break
                line = line.strip()
                if line:
                    try:
                        parsed = json.loads(line)
                        if parsed.get('progress') is not None:
                            progress = parsed['progress']
                            transcription_percent = 30 + (progress * 65)
                            progress_msg = f"Transcribing with {request.backend} Whisper ({request.model_size})... {int(progress * 100)}%"
                            yield send_progress(progress_msg, transcription_percent)
                            last_progress_time = datetime.now()
                        elif parsed.get('error'):
                            transcribe_process.kill()
                            yield send_error(parsed['error'])
                            return
                    except:
                        pass
            
            # Read stdout for result
            for line in iter(transcribe_process.stdout.readline, ''):
                if not line:
                    break
                stdout_data += line
            
            return_code = transcribe_process.wait(timeout=1800)
            
            if return_code != 0:
                error_message = "Transcription failed"
                yield send_error(error_message)
                return
            
            # Parse transcription result
            try:
                lines = stdout_data.strip().split('\n')
                json_lines = [line for line in lines if line.strip().startswith('{') or line.strip().startswith('[')]
                json_output = json_lines[0] if json_lines else stdout_data.strip()
                transcription_result = json.loads(json_output)
            except json.JSONDecodeError as e:
                yield send_error(f"Failed to parse transcription: {str(e)}")
                return
            
            # Step 4: Summarize
            yield send_progress("Generating AI summary...", 95)
            
            summarize_process = subprocess.Popen(
                ["python", str(PYTHON_DIR / "summarize_transcript.py")],
                cwd=str(PYTHON_DIR),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            summarize_process.stdin.write(json.dumps(transcription_result))
            summarize_process.stdin.close()
            
            summary_stdout, summary_stderr = summarize_process.communicate(timeout=300)
            
            if summarize_process.returncode != 0:
                yield send_error(summary_stderr or "Failed to summarize")
                return
            
            summary_text = summary_stdout.strip()
            
            # Send final result
            final_result = {
                **transcription_result,
                "summary": summary_text
            }
            
            yield send_progress("Complete!", 100)
            result_data = json.dumps({"type": "result", "data": final_result})
            yield f"data: {result_data}\n\n"
            
        except subprocess.TimeoutExpired:
            yield send_error("Process timeout: The operation took too long")
        except Exception as e:
            yield send_error(f"Transcription failed: {str(e)}")
        finally:
            # Cleanup temporary directory
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                except:
                    pass
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
