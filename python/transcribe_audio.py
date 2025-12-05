"""
Standalone script to transcribe audio file
Usage: python transcribe_audio.py <audio_path> <backend> <model_size> [progress_callback_url]
Output: JSON transcription result
"""
import sys
import json
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from transcriber import Transcriber

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print(json.dumps({'error': 'Usage: python transcribe_audio.py <audio_path> <backend> <model_size>'}), file=sys.stderr)
        sys.exit(1)
    
    audio_path = sys.argv[1]
    backend = sys.argv[2]
    model_size = sys.argv[3]
    
    if not os.path.exists(audio_path):
        print(json.dumps({'error': f'Audio file not found: {audio_path}'}), file=sys.stderr)
        sys.exit(1)
    
    transcriber = Transcriber(model_size=model_size, backend=backend)
    
    def progress_callback(fraction):
        # Print progress as JSON for Next.js to parse
        print(json.dumps({'progress': fraction}), file=sys.stderr)
    
    try:
        result = transcriber.transcribe(audio_path, progress_callback=progress_callback)
        print(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({'error': str(e)}), file=sys.stderr)
        sys.exit(1)

