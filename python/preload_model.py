"""
Pre-load the faster/base Whisper model on application startup.
This script is called when the server starts to cache the model in memory.
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from transcriber import Transcriber

if __name__ == '__main__':
    print("Pre-loading faster/base Whisper model...")
    try:
        # Pre-load the default model (faster/base)
        transcriber = Transcriber(model_size="base", backend="faster")
        print("Model pre-loaded successfully!")
    except Exception as e:
        print(f"Warning: Could not pre-load model: {e}")
        sys.exit(0)  # Don't fail startup if pre-load fails

