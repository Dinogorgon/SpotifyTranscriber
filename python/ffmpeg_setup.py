"""
FFmpeg setup utility
Checks for FFmpeg and downloads it if missing.
"""
import os
import sys
import zipfile
import shutil
import subprocess
import requests
from pathlib import Path

FFMPEG_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
INSTALL_DIR = Path(os.path.dirname(os.path.abspath(__file__))) / "bin"

def check_ffmpeg():
    """Check if ffmpeg is available in PATH or local bin"""
    # Check system PATH
    if shutil.which("ffmpeg"):
        return True
    
    # Check local bin
    ffmpeg_exe = INSTALL_DIR / "ffmpeg.exe"
    if ffmpeg_exe.exists():
        add_to_path()
        return True
        
    return False

def add_to_path():
    """Add local bin to PATH for this session"""
    if str(INSTALL_DIR) not in os.environ["PATH"]:
        os.environ["PATH"] += os.pathsep + str(INSTALL_DIR)
        print(f"Added {INSTALL_DIR} to PATH")

def get_ffmpeg_path():
    """Get the path to ffmpeg executable"""
    # Check system PATH first
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        return ffmpeg_path
    
    # Check local bin
    ffmpeg_exe = INSTALL_DIR / "ffmpeg.exe"
    if ffmpeg_exe.exists():
        add_to_path()
        return str(ffmpeg_exe)
    
    # Fallback to just 'ffmpeg' (might work if in PATH)
    return "ffmpeg"

def install_ffmpeg():
    """Download and install FFmpeg"""
    print("FFmpeg not found. Downloading...")
    INSTALL_DIR.mkdir(exist_ok=True)
    
    zip_path = INSTALL_DIR / "ffmpeg.zip"
    
    try:
        # Download
        response = requests.get(FFMPEG_URL, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        block_size = 8192
        downloaded = 0
        
        with open(zip_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=block_size):
                f.write(chunk)
                downloaded += len(chunk)
                if total_size:
                    percent = int((downloaded / total_size) * 100)
                    print(f"Downloading FFmpeg: {percent}%", end='\r')
        
        print("\nExtracting FFmpeg...")
        
        # Extract
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Find the bin folder inside the zip
            bin_path_in_zip = None
            for name in zip_ref.namelist():
                if name.endswith('bin/ffmpeg.exe'):
                    bin_path_in_zip = os.path.dirname(name)
                    break
            
            if not bin_path_in_zip:
                raise Exception("Could not find ffmpeg.exe in zip")
                
            # Extract only the bin files we need
            for file in ['ffmpeg.exe', 'ffprobe.exe']:
                source = f"{bin_path_in_zip}/{file}"
                target = INSTALL_DIR / file
                with zip_ref.open(source) as source_f, open(target, 'wb') as target_f:
                    shutil.copyfileobj(source_f, target_f)
                    
        print("FFmpeg installed successfully!")
        add_to_path()
        
    except Exception as e:
        print(f"Failed to install FFmpeg: {e}")
        raise
    finally:
        # Cleanup zip
        if zip_path.exists():
            os.remove(zip_path)

if __name__ == "__main__":
    if not check_ffmpeg():
        install_ffmpeg()
    else:
        print("FFmpeg is already available.")
