"""
Transcription with support for both faster-whisper (fast) and openai-whisper (accurate).
"""
import os
import subprocess

try:
    from mutagen import File as MutagenFile
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False


class Transcriber:
    def __init__(self, model_size="base", backend="faster", device="auto", compute_type="int8_float32"):
        """
        Initialize transcriber with selected backend.
        
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
        self.model = None
        self._load_model()

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

        Args:
            audio_path: Path to audio file
            language: Language code (None for auto-detect)
            task: 'transcribe' or 'translate'
            progress_callback: callable accepting float 0-1 to report progress
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        print(f"Transcribing audio: {audio_path} (backend: {self.backend})")
        duration = self._get_duration(audio_path)

        try:
            if self.backend == "faster":
                return self._transcribe_faster(audio_path, language, task, duration, progress_callback)
            else:
                return self._transcribe_openai(audio_path, language, task, duration, progress_callback)
        except Exception as e:
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
