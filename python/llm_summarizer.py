"""
LLM-based summarization for podcast transcripts using Ollama (free, local LLM).
"""
import os
import json
import sys
import requests

# Default to Ollama (free, local, no API key required)
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.2')  # llama3.2 is free, fast, and handles long contexts well

# System prompt for generating comprehensive summaries
SYSTEM_PROMPT = """You are an expert podcast transcription analyst and content summarizer. Your task is to create comprehensive, well-structured summaries of podcast episodes based on their full transcripts.

Your summaries should:

1. **Structure**: Organize the summary into clear sections:
   - **Overview**: A 2-3 sentence high-level summary of the entire episode
   - **Key Topics**: List the main topics, themes, or subjects discussed (3-5 bullet points)
   - **Main Points**: Detailed explanation of the most important ideas, insights, or arguments presented (2-4 paragraphs)
   - **Notable Quotes or Insights**: Extract particularly memorable, insightful, or quotable statements (2-3 quotes)
   - **Takeaways**: Actionable insights, lessons learned, or practical advice that listeners can apply (3-5 bullet points)

2. **Writing Style**:
   - Write in clear, professional, and engaging prose
   - Use proper paragraph breaks and formatting
   - Maintain the original meaning and context
   - Write in third person or neutral voice
   - Use markdown formatting for structure (headers, bullet points, bold for emphasis)
   - Ensure proper grammar, spelling, and language correctness

3. **Content Quality**:
   - Capture the essence and main narrative arc of the episode
   - Include specific details, examples, or anecdotes when they're important
   - Preserve the tone and style of the original content (serious, humorous, educational, etc.)
   - Highlight unique perspectives or novel ideas presented
   - Note any important context, background information, or setup that's crucial to understanding

4. **Length and Detail**:
   - Aim for a comprehensive summary that's approximately 15-25% of the original transcript length
   - For shorter episodes (< 10 minutes), provide a detailed summary
   - For longer episodes (> 60 minutes), focus on the most important themes and insights
   - Ensure the summary stands alone - someone who didn't listen should understand the key content

5. **Accuracy**:
   - Stay true to what was actually said in the transcript
   - Don't add information that wasn't in the original
   - Don't make assumptions beyond what's stated
   - If the transcript is unclear or has gaps, note that in your summary

6. **Formatting**:
   - Use markdown headers (##) for main sections
   - Use bullet points (-) for lists
   - Use **bold** for emphasis on key terms or concepts
   - Use proper paragraph spacing

Remember: Your goal is to create a summary that is both comprehensive and readable, giving readers a complete understanding of the episode's content, insights, and value. Write in proper, grammatically correct English."""

def check_ollama_available():
    """Check if Ollama is running and accessible."""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False

def ensure_model_installed():
    """Check if the required Ollama model is installed. Don't auto-install (too slow)."""
    try:
        # Check if model exists by listing models
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_names = [m.get('name', '') for m in models]
            # Check if our model (or a variant) exists
            for model_name in model_names:
                if OLLAMA_MODEL in model_name or model_name.startswith(OLLAMA_MODEL):
                    return True
        return False
    except Exception as e:
        return False

def summarize_with_llm(transcription_result, max_tokens=2000):
    """
    Generate a comprehensive summary using Ollama (free, local LLM).
    
    Args:
        transcription_result: Transcription result dict with 'text' or 'segments'
        max_tokens: Maximum tokens for the summary (default: 2000)
    
    Returns:
        Summary text string
    """
    # Get full text from transcription
    text = transcription_result.get('text', '').strip()
    if not text:
        segments = transcription_result.get('segments', [])
        if segments:
            text = ' '.join(seg.get('text', '').strip() for seg in segments)
    
    if not text:
        return "No transcript available for summarization."
    
    # Check if Ollama is available
    if not check_ollama_available():
        print("Ollama is not running. Falling back to extractive summarization.", file=sys.stderr)
        print("To use LLM summarization:", file=sys.stderr)
        print("  1. Install Ollama from https://ollama.ai", file=sys.stderr)
        print(f"  2. Run: ollama pull {OLLAMA_MODEL}", file=sys.stderr)
        from summarizer import Summarizer
        return Summarizer.summarize(transcription_result, max_sentences=15)
    
    # Check if model is installed (don't auto-install - too slow)
    if not ensure_model_installed():
        print(f"Model {OLLAMA_MODEL} is not installed. Falling back to extractive summarization.", file=sys.stderr)
        print(f"To install the model, run: ollama pull {OLLAMA_MODEL}", file=sys.stderr)
        from summarizer import Summarizer
        return Summarizer.summarize(transcription_result, max_sentences=15)
    
    # Truncate if too long (llama3.2 has 128k context, but we'll be conservative)
    # Keep up to 100k characters to handle very long transcripts (reduced for memory efficiency)
    original_length = len(text)
    if len(text) > 100000:
        # For very long transcripts, take beginning and end
        text = text[:50000] + "\n\n[... middle content truncated ...]\n\n" + text[-50000:]
    
    try:
        # Use Ollama API - format: system prompt + user prompt
        user_prompt = f"Please create a comprehensive summary of the following podcast transcript:\n\n{text}"
        
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": user_prompt,
                "system": SYSTEM_PROMPT,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": max_tokens,  # Maximum tokens to generate
                    "top_p": 0.9,
                    "top_k": 40,
                }
            },
            timeout=600  # 10 minutes timeout for long transcripts and model processing
        )
        
        if response.status_code == 200:
            result = response.json()
            summary = result.get('response', '').strip()
            
            if summary:
                return summary
            else:
                raise ValueError("Empty response from Ollama")
        else:
            raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
        
    except requests.exceptions.Timeout:
        print("Ollama request timed out. The transcript may be too long. Falling back to extractive summarization.", file=sys.stderr)
        from summarizer import Summarizer
        return Summarizer.summarize(transcription_result, max_sentences=15)
    except Exception as e:
        # Fallback to extractive summarization if LLM fails
        from summarizer import Summarizer
        error_msg = f"LLM summarization failed: {str(e)}. Falling back to extractive summarization."
        print(error_msg, file=sys.stderr)
        return Summarizer.summarize(transcription_result, max_sentences=15)

