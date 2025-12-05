"""
Standalone script to summarize transcription using LLM
Usage: python summarize_transcript.py <transcription_json>
Input: JSON transcription result from stdin
Output: Summary text
"""
import sys
import json
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from llm_summarizer import summarize_with_llm

if __name__ == '__main__':
    try:
        # Read transcription from stdin
        input_data = sys.stdin.read()
        transcription = json.loads(input_data)
        
        # Use LLM-based summarization
        summary = summarize_with_llm(transcription, max_tokens=1500)
        print(summary)
    except Exception as e:
        print(f'Error: {str(e)}', file=sys.stderr)
        sys.exit(1)

