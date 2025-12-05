"""
Transcription with support for both faster-whisper (fast) and openai-whisper (accurate).
"""
import os
import subprocess
import shutil

try:
    from mutagen import File as MutagenFile
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False

# Import ffmpeg_setup for FFmpeg path resolution
try:
    import ffmpeg_setup
except ImportError:
    # If ffmpeg_setup is not available, we'll use 'ffmpeg' directly
    ffmpeg_setup = None

# Global model cache to avoid reloading models
_model_cache = {}


def convert_to_mp3(input_path, output_path=None):
    """
    Convert audio/video file (MP4, M4A) to MP3 using FFmpeg.
    
    Args:
        input_path: Path to input file (MP4 or M4A)
        output_path: Path to output MP3 file (optional, defaults to same name with .mp3 extension)
    
    Returns:
        Path to converted MP3 file
    """
    if output_path is None:
        output_path = input_path.rsplit('.', 1)[0] + '.mp3'
    
    # Check if FFmpeg is available and get path
    ffmpeg_cmd = None
    
    # First, check system PATH
    ffmpeg_cmd = shutil.which("ffmpeg")
    
    # If not in PATH, check local bin directory using multiple strategies
    if not ffmpeg_cmd:
        from pathlib import Path
        
        # Strategy 1: Relative to this file (python/transcriber.py -> ../bin/ffmpeg.exe)
        python_dir = Path(__file__).parent.resolve()
        bin_dir = python_dir.parent / "bin"
        ffmpeg_exe = bin_dir / "ffmpeg.exe"
        
        if ffmpeg_exe.exists():
            ffmpeg_cmd = str(ffmpeg_exe.resolve())
        else:
            # Strategy 2: Check current working directory
            cwd_bin = Path.cwd() / "bin" / "ffmpeg.exe"
            if cwd_bin.exists():
                ffmpeg_cmd = str(cwd_bin.resolve())
            else:
                # Strategy 3: Check parent of current working directory
                parent_bin = Path.cwd().parent / "bin" / "ffmpeg.exe"
                if parent_bin.exists():
                    ffmpeg_cmd = str(parent_bin.resolve())
                else:
                    # Strategy 4: Try to find bin directory by searching up from __file__
                    current = Path(__file__).resolve()
                    for _ in range(5):  # Search up to 5 levels
                        potential_bin = current.parent / "bin" / "ffmpeg.exe"
                        if potential_bin.exists():
                            ffmpeg_cmd = str(potential_bin.resolve())
                            break
                        current = current.parent
                        if current == current.parent:  # Reached root
                            break
    
    # Try using ffmpeg_setup if still not found
    if not ffmpeg_cmd and ffmpeg_setup:
        try:
            # Add to PATH and check again
            if hasattr(ffmpeg_setup, 'add_to_path'):
                ffmpeg_setup.add_to_path()
            ffmpeg_cmd = shutil.which("ffmpeg")
            if not ffmpeg_cmd:
                # Try get_ffmpeg_path if available
                if hasattr(ffmpeg_setup, 'get_ffmpeg_path'):
                    try:
                        potential_cmd = ffmpeg_setup.get_ffmpeg_path()
                        if potential_cmd and (os.path.exists(potential_cmd) or potential_cmd == "ffmpeg"):
                            ffmpeg_cmd = potential_cmd
                    except Exception:
                        pass
        except Exception:
            pass
    
    # Final check - if still not found, raise error with helpful message
    if not ffmpeg_cmd:
        # Provide helpful error message with checked paths
        checked_paths = [
            str(Path(__file__).parent.parent / "bin" / "ffmpeg.exe"),
            str(Path.cwd() / "bin" / "ffmpeg.exe"),
        ]
        error_msg = (
            "FFmpeg is not installed or not found. "
            f"Checked paths: {', '.join(checked_paths)}. "
            "Please ensure FFmpeg is installed and available in your system PATH or in the bin/ directory."
        )
        raise Exception(error_msg)
    
    # Verify the command exists (unless it's just 'ffmpeg' which will be checked by subprocess)
    if ffmpeg_cmd != "ffmpeg" and not os.path.exists(ffmpeg_cmd):
        raise Exception(f"FFmpeg executable not found at: {ffmpeg_cmd}. Please verify FFmpeg installation.")
    
    try:
        cmd = [
            ffmpeg_cmd,
            '-i', input_path,
            '-vn',  # No video
            '-acodec', 'libmp3lame',  # MP3 codec
            '-ar', '44100',  # Sample rate
            '-ac', '2',  # Stereo
            '-b:a', '192k',  # Audio bitrate
            '-y',  # Overwrite output file
            output_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        if result.returncode != 0:
            error_msg = result.stderr or result.stdout or "Unknown FFmpeg error"
            raise Exception(f"FFmpeg conversion failed: {error_msg}")
        
        if not os.path.exists(output_path):
            raise Exception("Converted file not found")
        
        return output_path
    except subprocess.TimeoutExpired:
        raise Exception("FFmpeg conversion timed out (10 minutes)")
    except FileNotFoundError:
        raise Exception(f"FFmpeg executable not found at: {ffmpeg_cmd}")
    except Exception as e:
        raise Exception(f"Failed to convert to MP3: {str(e)}")


class Transcriber:
    def __init__(self, model_size="base", backend="faster", device="auto", compute_type="int8_float32"):
        """
        Initialize transcriber with selected backend.
        Uses model caching to avoid reloading models on subsequent requests.
        
        Args:
            model_size: tiny, base, small, medium, large
            backend: 'faster' for faster-whisper (fast) or 'openai' for openai-whisper (accurate)
            device: 'auto', 'cpu', or 'cuda'
            compute_type: For faster-whisper: 'int8', 'int8_float32', 'float16', 'float32'
        """
        self.model_size = model_size
        self.backend = backend.lower()
        self.device = device
        self.compute_type = compute_type
        
        # Create cache key
        cache_key = f"{self.backend}_{self.model_size}_{self.device}_{self.compute_type}"
        
        # Check if model is already cached
        if cache_key in _model_cache:
            self.model = _model_cache[cache_key]
            print(f"Using cached model: {cache_key}")
        else:
            self.model = None
            self._load_model()
            # Cache the model
            _model_cache[cache_key] = self.model
            print(f"Cached model: {cache_key}")

    def _load_model(self):
        """Load Whisper model based on selected backend."""
        if self.model is None:
            if self.backend == "faster":
                from faster_whisper import WhisperModel
                print(f"Loading faster-whisper model: {self.model_size} ({self.compute_type})...")
                self.model = WhisperModel(
                    self.model_size,
                    device=self.device,
                    compute_type=self.compute_type,
                )
            else:  # openai-whisper
                import whisper
                print(f"Loading openai-whisper model: {self.model_size}...")
                self.model = whisper.load_model(self.model_size)
            print("Model loaded successfully!")

    @staticmethod
    def _get_duration(audio_path):
        """Get audio duration in seconds."""
        if MUTAGEN_AVAILABLE:
            try:
                audio_file = MutagenFile(audio_path)
                if audio_file is not None:
                    duration = audio_file.info.length
                    if duration:
                        return duration
            except Exception:
                pass
        
        # Fallback to ffprobe if mutagen fails or isn't available
        try:
            cmd = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                audio_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                duration = float(result.stdout.strip())
                if duration > 0:
                    return duration
        except Exception:
            pass
        
        # If all else fails, return 0 (progress won't be accurate but transcription will work)
        return 0

    def transcribe(self, audio_path, language=None, task="transcribe", progress_callback=None):
        """
        Transcribe audio file with optional progress callback.
        Automatically converts MP4 and M4A files to MP3 before transcription.

        Args:
            audio_path: Path to audio file (MP3, MP4, or M4A)
            language: Language code (None for auto-detect)
            task: 'transcribe' or 'translate'
            progress_callback: callable accepting float 0-1 to report progress
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # Convert MP4 or M4A to MP3 if needed
        original_path = audio_path
        converted_path = None
        file_ext = os.path.splitext(audio_path)[1].lower()
        if file_ext in ['.mp4', '.m4a']:
            print(f"Converting {file_ext.upper()} to MP3: {audio_path}")
            converted_path = convert_to_mp3(audio_path)
            audio_path = converted_path
            print(f"Conversion complete: {audio_path}")

        print(f"Transcribing audio: {audio_path} (backend: {self.backend})")
        duration = self._get_duration(audio_path)

        try:
            if self.backend == "faster":
                result = self._transcribe_faster(audio_path, language, task, duration, progress_callback)
            else:
                result = self._transcribe_openai(audio_path, language, task, duration, progress_callback)
            
            # Clean up converted MP3 file if it was created
            if converted_path and os.path.exists(converted_path) and converted_path != original_path:
                try:
                    os.remove(converted_path)
                    print(f"Cleaned up converted file: {converted_path}")
                except Exception as e:
                    print(f"Warning: Could not delete converted file: {e}")
            
            return result
        except Exception as e:
            # Clean up converted file on error
            if converted_path and os.path.exists(converted_path) and converted_path != original_path:
                try:
                    os.remove(converted_path)
                except:
                    pass
            raise Exception(f"Transcription failed: {str(e)}") from e
    
    def _transcribe_faster(self, audio_path, language, task, duration, progress_callback):
        """Transcribe using faster-whisper with optimized settings for speed."""
        segments_iter, info = self.model.transcribe(
            audio_path,
            language=language,
            task=task,
            beam_size=1,  # Reduced from 5 for speed
            vad_filter=True,
            condition_on_previous_text=False,  # Faster
            compression_ratio_threshold=2.4,  # Default
            log_prob_threshold=-1.0,  # Default
            no_speech_threshold=0.6,  # Default
        )

        segments = []
        text_parts = []
        last_report = 0.0

        for segment in segments_iter:
            seg_text = segment.text.strip()
            segments.append(
                {
                    "id": segment.id,
                    "start": segment.start,
                    "end": segment.end,
                    "text": seg_text,
                    "words": [
                        {
                            "start": w.start,
                            "end": w.end,
                            "text": w.word.strip(),
                            "probability": w.probability,
                        }
                        for w in (segment.words or [])
                    ],
                }
            )
            if seg_text:
                text_parts.append(seg_text)

            if progress_callback and duration:
                progress = min(max(segment.end / duration, 0), 1)
                if progress - last_report >= 0.01 or progress >= 1.0:
                    progress_callback(progress)
                    last_report = progress
                    # Flush stdout/stderr to ensure progress is sent immediately
                    import sys
                    sys.stderr.flush()

        full_text = " ".join(text_parts).strip()

        result = {
            "text": full_text,
            "segments": segments,
            "language": info.language,
            "duration": duration,
        }

        if progress_callback:
            progress_callback(1.0)

        return result
    
    def _transcribe_openai(self, audio_path, language, task, duration, progress_callback):
        """Transcribe using openai-whisper (slower but more accurate)."""
        result_dict = self.model.transcribe(
            audio_path,
            language=language,
            task=task,
            verbose=False
        )
        
        # Convert to consistent format
        segments = []
        for i, seg in enumerate(result_dict.get('segments', [])):
            segments.append({
                "id": i,
                "start": seg.get('start', 0),
                "end": seg.get('end', 0),
                "text": seg.get('text', '').strip(),
                "words": seg.get('words', [])
            })
            
            # Update progress
            if progress_callback and duration:
                progress = min(max(seg.get('end', 0) / duration, 0), 1)
                progress_callback(progress)

        result = {
            "text": result_dict.get('text', '').strip(),
            "segments": segments,
            "language": result_dict.get('language', 'en'),
            "duration": duration,
        }

        if progress_callback:
            progress_callback(1.0)

        return result

    def get_text(self, transcription_result):
        """Extract plain text from transcription result."""
        return transcription_result.get("text", "").strip()

    def get_segments(self, transcription_result):
        """Get segments with timestamps."""
        return transcription_result.get("segments", [])
