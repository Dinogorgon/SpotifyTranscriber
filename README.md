# Spotify Transcriber

A Next.js application that transcribes Spotify podcast episodes using OpenAI Whisper AI. Extract metadata, download audio, transcribe, and generate summaries - all from a single command.

## Features

- 🎙️ **Spotify Integration**: Extract episode metadata and cover images from Spotify URLs
- 🎵 **Audio Download**: Download podcast audio via RSS feeds (legal workflow)
- 🤖 **AI Transcription**: Use faster-whisper (fast) or openai-whisper (accurate) for transcription
- 📝 **AI Summarization**: Generate comprehensive summaries using LLM (OpenAI API or compatible endpoints)
- 💾 **Multiple Formats**: Export transcripts as TXT, JSON, SRT, or VTT
- 🎨 **Modern UI**: Beautiful dark-themed interface built with Next.js

## Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.8+
- **FFmpeg** (for audio processing)

### Installing FFmpeg

**Windows:**
- Download from [ffmpeg.org](https://ffmpeg.org/download.html)
- Add to PATH, or place `ffmpeg.exe` and `ffprobe.exe` in the `bin/` directory

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt-get install ffmpeg
```

## Installation

1. **Clone the repository:**
```bash
git clone https://github.com/Dinogorgon/SpotifyTranscriber.git
cd SpotifyTranscriber
```

2. **Install Node.js dependencies:**
```bash
npm install
```

3. **Install Python dependencies:**
```bash
pip install -r python-requirements.txt
```

4. **Install Ollama (for free LLM summarization - recommended):**
   - Download and install from [ollama.ai](https://ollama.ai)
   - After installation, pull a model (choose based on your system):
     ```bash
     # Recommended: llama3.2 (3B) - Fast, efficient, handles long contexts
     ollama pull llama3.2
     
     # Better quality (requires 8GB+ RAM): llama3.1:8b
     ollama pull llama3.1:8b
     
     # Alternative: mistral (good balance)
     ollama pull mistral
     ```
   - **Model Recommendations:**
     - **llama3.2** (default): Fast, ~2GB RAM, handles 128k context, good for most users
     - **llama3.1:8b**: Better quality, ~5GB RAM, handles 128k context, recommended if you have RAM
     - **mistral**: Alternative option, ~4GB RAM, good performance
   - **Why Ollama?**
     - ✅ Completely free and open source
     - ✅ No API keys required
     - ✅ Runs entirely locally (privacy-friendly)
     - ✅ Handles very long transcripts (128k+ tokens)
     - ✅ Good language quality and grammar
   - Set custom model (optional):
     ```bash
     # Windows PowerShell
     $env:OLLAMA_MODEL="llama3.1:8b"
     
     # macOS/Linux
     export OLLAMA_MODEL="llama3.1:8b"
     ```
   - **Note**: If Ollama is not installed or not running, the app will automatically fall back to extractive summarization (no setup required)

## Usage

### Start the Application

Simply run:
```bash
npm run dev
```

The application will start at `http://localhost:3000`. Everything runs from a single command - no need to start separate frontend/backend servers!

### Using the Application

1. **Enter a Spotify URL**: Paste any Spotify episode URL in the input field
2. **Choose Settings**: 
   - **Engine**: Faster (faster-whisper) or Accurate (openai-whisper)
   - **Model**: tiny, base, small, medium, or large
3. **Click the arrow button** to start transcription
4. **View Results**: 
   - Episode info (metadata, cover image, description)
   - Full transcript with optional timestamps
   - AI-generated summary
5. **Download**: Export transcript as TXT or download the MP3 audio file

## Architecture

- **Frontend**: Next.js 14+ static export deployed to Netlify
- **Backend**: FastAPI Python service deployed to Render
- **Python Modules**: Heavy processing (scraping, audio, transcription) handled by Python
- **Integration**: Frontend communicates with backend via REST API and Server-Sent Events (SSE)

## Project Structure

```
spotify-transcriber/
├── app/
│   ├── page.tsx          # Main application page
│   ├── layout.tsx        # Root layout
│   └── globals.css      # Global styles
├── backend/
│   ├── main.py          # FastAPI backend application
│   ├── requirements.txt # Backend Python dependencies
│   └── render.yaml      # Render deployment configuration
├── components/          # React components
├── lib/                 # TypeScript utilities
│   ├── apiClient.ts     # Backend API client
│   ├── formatConverters.ts  # Format conversion
│   └── types.ts         # TypeScript types
├── python/             # Python modules
│   ├── spotify_scraper.py
│   ├── audio_downloader.py
│   ├── transcriber.py
│   └── llm_summarizer.py
├── .github/
│   └── workflows/
│       └── keep-alive.yml  # GitHub Actions to keep Render warm
├── package.json
├── python-requirements.txt     # Python dependencies (for local dev)
├── netlify.toml         # Netlify deployment configuration
└── README.md
```

## Development

### Local Development Setup

1. **Start the backend** (in one terminal):
```bash
cd backend
pip install -r requirements.txt
python main.py
```
The backend will run on `http://localhost:8000`

2. **Start the frontend** (in another terminal):
```bash
npm install
npm run dev
```
The frontend will run on `http://localhost:3000` and connect to the backend automatically.

### Build for Production

```bash
npm run build
```
This creates a static export in the `out/` directory ready for Netlify deployment.

### Run Linter

```bash
npm run lint
```

## Deployment

### Deploy Backend to Render

1. **Create a Render account** at [render.com](https://render.com)
2. **Create a new Web Service**:
   - Connect your GitHub repository
   - Select the `backend/` directory as the root
   - Build command: `pip install -r requirements.txt`
   - Start command: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Environment: Python 3
3. **Get your Render backend URL** (e.g., `https://your-app.onrender.com`)
4. **Set environment variables** (if needed):
   - `FRONTEND_URL`: Your Netlify frontend URL (for CORS)

### Deploy Frontend to Netlify

1. **Create a Netlify account** at [netlify.com](https://netlify.com)
2. **Create a new site**:
   - Connect your GitHub repository
   - Build command: `npm run build`
   - Publish directory: `out`
3. **Set environment variable**:
   - `NEXT_PUBLIC_BACKEND_URL`: Your Render backend URL (e.g., `https://your-app.onrender.com`)
4. **Deploy**: Netlify will automatically deploy on every push to your main branch

### Set Up GitHub Actions Keep-Alive

1. **Add GitHub Secret** (optional):
   - Go to your repository Settings → Secrets and variables → Actions
   - Add a secret named `RENDER_URL` with your Render backend URL
   - Or edit `.github/workflows/keep-alive.yml` and replace `your-backend.onrender.com` with your actual URL
2. **Enable GitHub Actions**:
   - The workflow will automatically run every 10 minutes to keep Render warm
   - You can also manually trigger it from the Actions tab

### Custom Domain Setup

**Netlify:**
- Go to Site settings → Domain management
- Add your custom domain (e.g., `spotifytranscriber.name.me`)
- Follow DNS instructions
- SSL is automatic

**Render:**
- Go to your service settings → Custom Domains
- Add your custom domain
- Follow DNS instructions
- SSL is automatic

## Troubleshooting

### Python Not Found
Ensure Python is in your PATH. Test with:
```bash
python --version
```

### FFmpeg Not Found
- Windows: Place `ffmpeg.exe` and `ffprobe.exe` in the `bin/` directory
- macOS/Linux: Install via package manager

### Transcription Fails
- Check that the Spotify URL is valid
- Ensure audio download completes (check network connection)
- Try a smaller model size if memory issues occur

### Image Not Loading
- Images are proxied through `/api/proxy-image` to handle CORS
- Check browser console for errors

## License

See [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Acknowledgments

- OpenAI Whisper for transcription
- faster-whisper for fast inference
- Spotify for podcast content
