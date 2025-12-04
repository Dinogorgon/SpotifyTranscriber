# Setup Instructions

Complete setup guide for Spotify Transcriber (both GUI and Web versions).

## Prerequisites

### Required Software

1. **Python 3.8 or higher**
   - Download from [python.org](https://www.python.org/downloads/)
   - During installation, check "Add Python to PATH"

2. **FFmpeg** (for audio processing)
   - **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html) or use the included binaries in `bin/` folder
   - **macOS**: `brew install ffmpeg`
   - **Linux**: `sudo apt-get install ffmpeg` (Ubuntu/Debian) or `sudo yum install ffmpeg` (RHEL/CentOS)

3. **Node.js 18+** (for Web version only)
   - Download from [nodejs.org](https://nodejs.org/)
   - Includes npm (Node Package Manager)

### Verify Installation

```bash
# Check Python
python --version

# Check Node.js (Web version only)
node --version
npm --version

# Check FFmpeg
ffmpeg -version
```

## GUI Version Setup

### Step 1: Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Run the Application

```bash
python gui.py
```

Or use the convenience script:
```bash
python main.py
```

That's it! The GUI will open in a new window.

## Web Version Setup

### Step 1: Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### Step 2: Install Frontend Dependencies

```bash
cd frontend
npm install
```

### Step 3: Start the Application

**Option A: Use the start script (Recommended)**

**Windows PowerShell:**
```powershell
.\start_all.ps1
```

**Windows Command Prompt:**
```cmd
start_all.bat
```

**Option B: Manual Start**

**Terminal 1 - Backend:**
```bash
cd backend
python main.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### Step 4: Access the Application

- Frontend: Open `http://localhost:5173` in your browser
- Backend API: Available at `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`

## Troubleshooting

### Python Issues

**Problem**: `python` command not found
- **Solution**: Use `python3` instead, or add Python to your PATH

**Problem**: `pip` command not found
- **Solution**: Use `python -m pip` instead

**Problem**: Permission errors during installation
- **Solution**: Use `pip install --user -r requirements.txt` to install for current user only

### FFmpeg Issues

**Problem**: FFmpeg not found
- **Solution**: 
  - Windows: Ensure `bin/ffmpeg.exe` exists or add FFmpeg to PATH
  - macOS/Linux: Install via package manager

**Problem**: Audio processing fails
- **Solution**: Verify FFmpeg installation: `ffmpeg -version`

### Node.js Issues

**Problem**: `npm` command not found
- **Solution**: Reinstall Node.js and ensure it's added to PATH

**Problem**: Port already in use
- **Solution**: 
  - Backend (8000): Change port in `backend/main.py`
  - Frontend (5173): Change port in `frontend/vite.config.js` or use `npm run dev -- --port 3001`

### Whisper Model Issues

**Problem**: First transcription is very slow
- **Solution**: This is normal - Whisper downloads the model on first use (can be 100MB-3GB depending on model size)

**Problem**: Out of memory errors
- **Solution**: Use a smaller model (tiny or base) or increase system RAM

### Network Issues

**Problem**: Cannot fetch Spotify metadata
- **Solution**: 
  - Check internet connection
  - Verify Spotify URL is correct
  - Some episodes may not be publicly available

**Problem**: CORS errors in browser
- **Solution**: Ensure backend is running and CORS is properly configured (already set up in `backend/main.py`)

## Platform-Specific Notes

### Windows

- Use PowerShell or Command Prompt
- FFmpeg binaries are included in `bin/` folder
- Use `.\start_all.ps1` or `start_all.bat` for web version

### macOS

- Use Terminal
- Install FFmpeg via Homebrew: `brew install ffmpeg`
- May need to allow Python/Node.js in Security & Privacy settings

### Linux

- Use terminal
- Install FFmpeg via package manager
- May need `sudo` for system-wide Python package installation

## Development Setup

### For Contributors

1. Clone the repository
2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   cd backend && pip install -r requirements.txt
   ```
4. Install frontend dependencies:
   ```bash
   cd frontend && npm install
   ```

### Running Tests

Test files are located in the root directory:
- `test_scraper.py` - Test Spotify scraper
- `test_rss.py` - Test RSS feed parsing
- `test_network.py` - Test network connectivity

Run tests with:
```bash
python test_scraper.py
```

## Additional Resources

- [Python Documentation](https://docs.python.org/3/)
- [Node.js Documentation](https://nodejs.org/docs/)
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)

## Getting Help

If you encounter issues:
1. Check the Troubleshooting section above
2. Review error messages carefully
3. Check that all prerequisites are installed correctly
4. Ensure you're using the correct Python/Node.js versions
5. Check GitHub Issues for similar problems
