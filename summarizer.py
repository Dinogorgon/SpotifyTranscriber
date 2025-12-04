"""
Generate summaries from transcriptions using extractive summarization.
"""
import re
from collections import Counter


class Summarizer:
    """Extractive summarization for podcast transcripts."""
    
    @staticmethod
    def _split_into_sentences(text):
        """Split text into sentences."""
        # Simple sentence splitting on punctuation
        sentences = re.split(r'[.!?]+\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    @staticmethod
    def _calculate_sentence_scores(sentences, word_freq):
        """Calculate importance scores for sentences."""
        scores = {}
        for i, sentence in enumerate(sentences):
            words = re.findall(r'\b\w+\b', sentence.lower())
            score = sum(word_freq.get(word, 0) for word in words)
            # Normalize by sentence length
            if len(words) > 0:
                score = score / len(words)
            scores[i] = score
        return scores
    
    @staticmethod
    def _get_top_sentences(sentences, scores, num_sentences=5):
        """Get top N sentences by score."""
        sorted_indices = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_indices = [idx for idx, _ in sorted_indices[:num_sentences]]
        # Return in original order
        top_indices.sort()
        return [sentences[i] for i in top_indices]
    
    @staticmethod
    def summarize(transcription_result, max_sentences=5):
        """
        Generate an extractive summary from transcription.
        
        Args:
            transcription_result: Transcription result dict with 'text' or 'segments'
            max_sentences: Maximum number of sentences in summary
        
        Returns:
            Summary text string
        """
        # Get full text
        text = transcription_result.get('text', '').strip()
        if not text:
            segments = transcription_result.get('segments', [])
            if segments:
                text = ' '.join(seg.get('text', '').strip() for seg in segments)
        
        if not text:
            return "No transcript available for summarization."
        
        # Split into sentences
        sentences = Summarizer._split_into_sentences(text)
        if len(sentences) <= max_sentences:
            return text
        
        # Calculate word frequencies (excluding common stop words)
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 
                     'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were',
                     'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did',
                     'will', 'would', 'could', 'should', 'may', 'might', 'must',
                     'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she',
                     'it', 'we', 'they', 'what', 'which', 'who', 'when', 'where',
                     'why', 'how', 'all', 'each', 'every', 'some', 'any', 'no'}
        
        words = re.findall(r'\b\w+\b', text.lower())
        word_freq = Counter(word for word in words if word not in stop_words and len(word) > 3)
        
        # Calculate sentence scores
        scores = Summarizer._calculate_sentence_scores(sentences, word_freq)
        
        # Get top sentences
        top_sentences = Summarizer._get_top_sentences(sentences, scores, max_sentences)
        
        # Join with proper punctuation
        summary = '. '.join(top_sentences)
        if summary and not summary.endswith(('.', '!', '?')):
            summary += '.'
        
        return summary
    
    @staticmethod
    def summarize_with_timestamps(transcription_result, max_points=5):
        """
        Generate a summary with timestamps from segments.
        
        Args:
            transcription_result: Transcription result dict with 'segments'
            max_points: Maximum number of summary points
        
        Returns:
            List of dicts with 'timestamp', 'text', 'icon' keys
        """
        segments = transcription_result.get('segments', [])
        if not segments:
            return []
        
        # Group segments by topic (simple: by time gaps and sentence endings)
        summary_points = []
        current_group = []
        last_end = None
        
        for seg in segments:
            text = seg.get('text', '').strip()
            if not text:
                continue
            
            start = seg.get('start', 0)
            end = seg.get('end', start)
            gap = start - last_end if last_end is not None else 0
            
            # Start new point on significant gaps or sentence endings
            if (gap > 2.0 and current_group) or (text.endswith(('.', '!', '?')) and len(current_group) > 2):
                if current_group:
                    summary_points.append({
                        'timestamp': current_group[0].get('start', 0),
                        'text': ' '.join(s.get('text', '').strip() for s in current_group),
                        'icon': '📌'  # Default icon
                    })
                current_group = [seg]
            else:
                current_group.append(seg)
            
            last_end = end
            
            if len(summary_points) >= max_points:
                break
        
        # Add final group
        if current_group and len(summary_points) < max_points:
            summary_points.append({
                'timestamp': current_group[0].get('start', 0),
                'text': ' '.join(s.get('text', '').strip() for s in current_group),
                'icon': '📌'
            })
        
        return summary_points

