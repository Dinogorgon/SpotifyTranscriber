# Setup Instructions

## Prerequisites

1. **Python 3.8 or higher**
   - Download from https://www.python.org/downloads/
   - Make sure to check "Add Python to PATH" during installation

2. **FFmpeg** (Required for audio processing)
   - **Windows:**
     - Download from https://www.gyan.dev/ffmpeg/builds/
     - Extract and add `bin` folder to your system PATH
     - Or use: `winget install ffmpeg` (Windows 10/11)
   - **macOS:**
     ```bash
     brew install ffmpeg
     ```
   - **Linux:**
     ```bash
     sudo apt update
     sudo apt install ffmpeg
     ```

## Installation Steps

1. **Clone or navigate to the project directory**

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment:**
   - **Windows:**
     ```bash
     venv\Scripts\activate
     ```
   - **macOS/Linux:**
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Verify FFmpeg installation:**
   ```bash
   ffmpeg -version
   ```
   If this command fails, FFmpeg is not properly installed or not in your PATH.

## Running the Application

```bash
python main.py
```

## First Run Notes

- The first time you use a faster-whisper model, it will be downloaded automatically
- Model sizes:
  - **tiny**: Fastest, least accurate (~39 MB)
  - **base**: Good balance (~74 MB) - **Recommended**
  - **small**: Better accuracy (~244 MB)
  - **medium**: High accuracy (~769 MB)
  - **large**: Best accuracy, slowest (~1550 MB)

## Troubleshooting

### FFmpeg not found
- Make sure FFmpeg is installed and in your system PATH
- Restart your terminal/command prompt after adding FFmpeg to PATH

### RSS feed errors
- Some private or region-locked podcasts may not expose an RSS feed via Spotify
- The app uses Spotifeed to resolve RSS URLs. If Spotifeed is down, wait a bit and retry
- Ensure the link you paste points to a **podcast episode** (tracks/audiobooks are not supported)

### faster-whisper model download fails
- Check your internet connection
- Models are downloaded to: `~/.cache/whisper/` (or `%USERPROFILE%\.cache\whisper\` on Windows)

### Out of memory errors
- Use a smaller faster-whisper model (tiny or base)
- Close other applications
- Process shorter audio files

## Usage Tips

1. **Spotify Links**: Works with podcast episode URLs (show links are also accepted); music tracks are not supported
2. **Processing Time**: Depends on audio length and model size
   - 1 minute audio: ~10-30 seconds (base model)
   - 10 minute audio: ~2-5 minutes (base model)
3. **Export Formats**: All formats include timestamps where available
4. **Audio Files**: Downloaded audio is saved temporarily and can be reused
