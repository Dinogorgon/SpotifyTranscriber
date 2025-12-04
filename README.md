# Spotify Transcriber

A powerful tool to transcribe Spotify podcast episodes using Whisper AI. Available in two versions: a **Python GUI desktop application** and a **React web application**.

## Features

- 🎵 Extract audio from Spotify podcast links (RSS + iTunes fallback)
- 🎤 Transcribe audio locally via faster-whisper or openai-whisper (multiple model sizes)
- 📄 Export transcriptions in multiple formats (TXT, JSON, SRT, VTT)
- 📊 AI-generated summaries
- ⚡ Real-time progress tracking
- 🎨 Clean, modern interfaces

## Two Ways to Use

### Option 1: Python GUI (Desktop Application) 🖥️

A standalone desktop application built with CustomTkinter - no browser needed!

**Quick Start:**
```bash
# Install dependencies
pip install -r requirements.txt

# Run the GUI
python gui.py
```

**Features:**
- Three-panel layout (Episode Info, Transcript, Summary)
- Download MP3 files
- Copy/export transcripts
- Toggle timestamps
- All-in-one Python application

### Option 2: Web Application (React + Python Backend) 🌐

A modern web application with React frontend and FastAPI backend.

**Quick Start:**

**Windows (PowerShell):**
```powershell
.\start_all.ps1
```

**Windows (Command Prompt):**
```cmd
start_all.bat
```

**Manual Start:**
```bash
# Terminal 1 - Backend
cd backend
pip install -r requirements.txt
python main.py

# Terminal 2 - Frontend
cd frontend
npm install
npm run dev
```

The web app will be available at:
- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`

## Installation

### Prerequisites

- **Python 3.8+**
- **Node.js 18+** (for web version only)
- **FFmpeg** (for audio processing)

### Python Dependencies

**For GUI version:**
```bash
pip install -r requirements.txt
```

**For Web version backend:**
```bash
cd backend
pip install -r requirements.txt
```

**For Web version frontend:**
```bash
cd frontend
npm install
```

## Usage

### GUI Version

1. Run `python gui.py`
2. Paste a Spotify episode URL in the input field
3. Select transcription engine (Faster or Accurate) and model size
4. Click the submit button (→) or press Enter
5. View episode info, transcript, and summary in the three panels
6. Use buttons to copy, download, or export transcripts

### Web Version

1. Start both backend and frontend servers (use `start_all.bat` or `start_all.ps1`)
2. Open `http://localhost:5173` in your browser
3. Paste a Spotify episode URL
4. Select transcription engine and model size
5. Click submit to start transcription
6. View results in the web interface

## Architecture

### GUI Version
- **Frontend**: CustomTkinter (Python)
- **Backend**: Same Python modules (spotify_scraper, transcriber, etc.)
- **All-in-one**: Single Python application

### Web Version
- **Frontend**: React + Vite (JavaScript)
- **Backend**: FastAPI (Python)
- **API**: RESTful API at `http://localhost:8000`

Both versions use the same core Python modules:
- `spotify_scraper.py` - Extracts metadata and finds audio URLs
- `transcriber.py` - Handles Whisper transcription
- `audio_downloader.py` - Downloads audio from RSS feeds
- `summarizer.py` - Generates AI summaries
- `format_converters.py` - Exports in various formats

## API Endpoints (Web Version)

- `GET /api/metadata?spotify_url=...` - Get episode metadata
- `POST /api/transcribe` - Transcribe an episode
- `GET /api/download-audio?spotify_url=...` - Download audio as MP3
- `GET /api/proxy-image?image_url=...` - Proxy Spotify images (CORS)
- `POST /api/export` - Export transcription in various formats

## Supported Formats

- **TXT**: Plain text transcription
- **JSON**: Structured data with timestamps
- **SRT**: Subtitle format for video players
- **VTT**: WebVTT subtitle format

## Transcription Engines

### Faster (faster-whisper)
- ⚡ Faster processing
- Lower memory usage
- Good for quick transcriptions
- Model sizes: tiny, base, small, medium, large

### Accurate (openai-whisper)
- 🎯 Higher accuracy
- Better for complex audio
- More memory intensive
- Model sizes: tiny, base, small, medium, large

## Project Structure

```
Spotify Transcriber/
├── gui.py                 # GUI desktop application
├── spotify_scraper.py     # Spotify metadata extraction
├── transcriber.py         # Whisper transcription
├── audio_downloader.py    # Audio download from RSS
├── summarizer.py          # AI summarization
├── format_converters.py   # Export formats
├── requirements.txt       # Python dependencies (GUI)
├── backend/
│   ├── main.py           # FastAPI web server
│   └── requirements.txt  # Backend dependencies
├── frontend/
│   ├── src/              # React components
│   └── package.json      # Node.js dependencies
└── start_all.bat/ps1    # Start scripts for web version
```

## Development

### Backend Development (Web Version)

The FastAPI backend includes automatic API documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Frontend Development (Web Version)

The React frontend uses Vite for fast hot module replacement. Changes automatically reload in the browser.

## Notes

- First transcription may take longer as Whisper downloads the selected model
- Processing time depends on audio length and selected model size
- Works with Spotify **podcast episodes** (music tracks remain DRM-protected)
- Both versions produce identical results since they use the same backend code

## Troubleshooting

### GUI Version
- Ensure Python 3.8+ is installed
- Install all dependencies: `pip install -r requirements.txt`
- Check FFmpeg is available: `ffmpeg -version`

### Web Version
- Ensure both Python and Node.js are installed
- Backend must be running before frontend
- Check ports 8000 and 5173 are available
- Check browser console for errors

## License

This project is for educational purposes. Please respect Spotify's terms of service and copyright laws.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
