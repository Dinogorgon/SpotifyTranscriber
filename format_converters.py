"""
Convert transcription to various formats (TXT, JSON, SRT, VTT)
"""
import json
import textwrap
from datetime import timedelta


class FormatConverter:
    @staticmethod
    def to_txt(transcription_result):
        """Convert to plain text"""
        return transcription_result.get('text', '').strip()
    
    @staticmethod
    def to_json(transcription_result, pretty=True):
        """Convert to JSON format"""
        if pretty:
            return json.dumps(transcription_result, indent=2, ensure_ascii=False)
        return json.dumps(transcription_result, ensure_ascii=False)
    
    @staticmethod
    def _format_timestamp(seconds):
        """Format seconds to SRT/VTT timestamp (HH:MM:SS,mmm)"""
        td = timedelta(seconds=seconds)
        total_seconds = int(td.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        milliseconds = int((td.total_seconds() - total_seconds) * 1000)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
    
    @staticmethod
    def _format_timestamp_vtt(seconds):
        """Format seconds to VTT timestamp (HH:MM:SS.mmm)"""
        td = timedelta(seconds=seconds)
        total_seconds = int(td.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        milliseconds = int((td.total_seconds() - total_seconds) * 1000)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"
    
    @staticmethod
    def to_srt(transcription_result):
        """Convert to SRT subtitle format"""
        segments = transcription_result.get('segments', [])
        
        if not segments:
            # If no segments, create one from full text
            text = transcription_result.get('text', '').strip()
            if text:
                return f"1\n00:00:00,000 --> 00:00:10,000\n{text}\n\n"
            return ""
        
        srt_lines = []
        for i, segment in enumerate(segments, 1):
            start = segment.get('start', 0)
            end = segment.get('end', start + 1)
            text = segment.get('text', '').strip()
            
            start_time = FormatConverter._format_timestamp(start)
            end_time = FormatConverter._format_timestamp(end)
            
            srt_lines.append(f"{i}\n{start_time} --> {end_time}\n{text}\n\n")
        
        return ''.join(srt_lines)
    
    @staticmethod
    def to_vtt(transcription_result):
        """Convert to WebVTT subtitle format"""
        segments = transcription_result.get('segments', [])
        
        vtt_lines = ["WEBVTT\n"]
        
        if not segments:
            # If no segments, create one from full text
            text = transcription_result.get('text', '').strip()
            if text:
                vtt_lines.append("00:00:00.000 --> 00:00:10.000\n")
                vtt_lines.append(f"{text}\n\n")
            return ''.join(vtt_lines)
        
        for segment in segments:
            start = segment.get('start', 0)
            end = segment.get('end', start + 1)
            text = segment.get('text', '').strip()
            
            start_time = FormatConverter._format_timestamp_vtt(start)
            end_time = FormatConverter._format_timestamp_vtt(end)
            
            vtt_lines.append(f"{start_time} --> {end_time}\n")
            vtt_lines.append(f"{text}\n\n")
        
        return ''.join(vtt_lines)
    
    @staticmethod
    def save_to_file(content, filepath, format_type):
        """Save content to file based on format"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    
    @staticmethod
    def export(transcription_result, output_path, format_type):
        """
        Export transcription to file in specified format
        
        Args:
            transcription_result: Whisper transcription result
            output_path: Output file path (without extension)
            format_type: 'txt', 'json', 'srt', or 'vtt'
        """
        format_type = format_type.lower()
        
        if format_type == 'txt':
            content = FormatConverter.to_txt(transcription_result)
            filepath = f"{output_path}.txt"
        elif format_type == 'json':
            content = FormatConverter.to_json(transcription_result)
            filepath = f"{output_path}.json"
        elif format_type == 'srt':
            content = FormatConverter.to_srt(transcription_result)
            filepath = f"{output_path}.srt"
        elif format_type == 'vtt':
            content = FormatConverter.to_vtt(transcription_result)
            filepath = f"{output_path}.vtt"
        else:
            raise ValueError(f"Unsupported format: {format_type}")
        
        FormatConverter.save_to_file(content, filepath, format_type)
        return filepath

    @staticmethod
    def to_display_text(transcription_result, width=96, gap_threshold=1.5):
        """
        Create a reader-friendly paragraph layout for GUI display.
        """
        segments = transcription_result.get('segments', [])
        if not segments:
            text = transcription_result.get('text', '').strip()
            return "\n\n".join(textwrap.wrap(text, width=width)) if text else ""

        paragraphs = []
        current = []
        last_end = None

        for segment in segments:
            text = (segment.get('text') or '').strip()
            if not text:
                continue

            start = segment.get('start', 0.0)
            end = segment.get('end', start)
            gap = start - last_end if (last_end is not None) else 0

            if (gap > gap_threshold and current) or len(" ".join(current)) > 320:
                paragraphs.append(" ".join(current).strip())
                current = [text]
            else:
                current.append(text)

            last_end = end

            if text.endswith(('.', '!', '?')) and len(" ".join(current)) > 200:
                paragraphs.append(" ".join(current).strip())
                current = []

        if current:
            paragraphs.append(" ".join(current).strip())

        wrapped = ["\n".join(textwrap.wrap(p, width=width)) for p in paragraphs if p]
        return "\n\n".join(wrapped).strip()
