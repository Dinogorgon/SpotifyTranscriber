# Spotify Transcriber

A Next.js application that transcribes Spotify podcast episodes using OpenAI Whisper AI. Extract metadata, download audio, transcribe, and generate summaries - all from a single command.

## Features

- 🎙️ **Spotify Integration**: Extract episode metadata and cover images from Spotify URLs
- 🎵 **Audio Download**: Download podcast audio via RSS feeds (legal workflow)
- 🤖 **AI Transcription**: Use faster-whisper (fast) or openai-whisper (accurate) for transcription
- 📝 **AI Summarization**: Generate extractive summaries from transcripts
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
pip install -r requirements.txt
```

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

- **Frontend**: Next.js 14+ with TypeScript and App Router
- **Backend**: Next.js API Routes that orchestrate Python scripts
- **Python Modules**: Heavy processing (scraping, audio, transcription) handled by Python
- **Integration**: Python scripts called via child processes from Next.js API routes

## Project Structure

```
spotify-transcriber/
├── app/
│   ├── api/              # Next.js API routes
│   ├── page.tsx          # Main application page
│   ├── layout.tsx        # Root layout
│   └── globals.css      # Global styles
├── components/          # React components
├── lib/                 # TypeScript utilities
│   ├── pythonRunner.ts  # Python execution utility
│   ├── formatConverters.ts  # Format conversion
│   └── types.ts         # TypeScript types
├── python/             # Python modules
│   ├── spotify_scraper.py
│   ├── audio_downloader.py
│   ├── transcriber.py
│   └── summarizer.py
├── package.json
├── requirements.txt
└── README.md
```

## Development

### Build for Production

```bash
npm run build
npm start
```

### Run Linter

```bash
npm run lint
```

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
