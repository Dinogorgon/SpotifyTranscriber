# Contributing to Spotify Transcriber

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Code Structure

### Core Modules (Root Directory)
- `spotify_scraper.py` - Extracts metadata from Spotify pages
- `transcriber.py` - Handles Whisper transcription
- `audio_downloader.py` - Downloads audio from RSS feeds
- `summarizer.py` - Generates AI summaries
- `format_converters.py` - Exports transcripts in various formats
- `spotify_rss.py` - RSS feed utilities
- `gui.py` - Desktop GUI application

### Backend (Web Version)
- `backend/main.py` - FastAPI server (imports from root modules)

### Frontend (Web Version)
- `frontend/src/` - React components and services

## Development Guidelines

### Code Style
- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions focused and small

### Debug Output
- Debug print statements are acceptable for troubleshooting
- Consider using Python's `logging` module for production code
- Debug output helps users troubleshoot issues

### Testing
- Test files are in the root directory (`test_*.py`)
- Run tests before submitting PRs
- Add tests for new features

### Pull Requests
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test thoroughly
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Reporting Issues
- Use GitHub Issues to report bugs
- Include steps to reproduce
- Include error messages and logs
- Specify which version (GUI or Web) you're using

## Areas for Contribution

- Improving transcription accuracy
- Adding new export formats
- UI/UX improvements
- Performance optimizations
- Documentation improvements
- Bug fixes
- Feature requests

## Questions?

Feel free to open an issue for questions or discussions!

