"""
SpotScribe-inspired GUI for Spotify Transcriber with three-panel layout.
"""
import customtkinter as ctk
import threading
import os
import shutil
import textwrap
import re
from pathlib import Path
from datetime import datetime
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import requests
from io import BytesIO

from audio_downloader import AudioDownloader
from format_converters import FormatConverter
from spotify_scraper import SpotifyScraper
from transcriber import Transcriber
from summarizer import Summarizer

# Set theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")

class SpotifyTranscriberGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Spotify Transcriber")
        self.geometry("1400x900")
        self.resizable(True, True)
        
        # Initialize components
        self.scraper = SpotifyScraper()
        self.downloader = None
        self.transcriber = None
        self.transcription_result = None
        self.audio_path = None
        self.episode_info = None
        self.summary_points = []
        
        # Configure grid layout - three columns
        self.grid_columnconfigure(0, weight=0, minsize=320)  # Left panel (episode info)
        self.grid_columnconfigure(1, weight=1, minsize=400)  # Middle panel (transcript)
        self.grid_columnconfigure(2, weight=1, minsize=400)  # Right panel (summary)
        self.grid_rowconfigure(1, weight=1)  # Content area expands
        
        self.setup_ui()
        
    def setup_ui(self):
        # Top bar with URL input
        self.top_frame = ctk.CTkFrame(self, fg_color="transparent", height=80)
        self.top_frame.grid(row=0, column=0, columnspan=3, sticky="ew", padx=20, pady=10)
        self.top_frame.grid_columnconfigure(1, weight=1)
        
        # Logo/Title
        self.logo_label = ctk.CTkLabel(self.top_frame, text="Spotify Transcriber", 
                                      font=ctk.CTkFont(size=24, weight="bold"),
                                      text_color="#1DB954")
        self.logo_label.grid(row=0, column=0, padx=10, sticky="w")
        
        # URL Input
        self.url_entry = ctk.CTkEntry(self.top_frame, 
                                    placeholder_text="Paste a Spotify episode URL...",
                                    height=40,
                                    font=ctk.CTkFont(size=14))
        self.url_entry.grid(row=0, column=1, padx=10, sticky="ew")
        self.url_entry.bind("<Return>", lambda e: self.start_transcription())
        
        # Submit button
        self.submit_btn = ctk.CTkButton(self.top_frame, text="→", 
                                        command=self.start_transcription,
                                        width=50, height=40,
                                        fg_color="#1DB954", hover_color="#1ed760")
        self.submit_btn.grid(row=0, column=2, padx=10)
        
        # Progress bar (always visible)
        self.progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.progress_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=20, pady=10)
        self.progress_frame.grid_columnconfigure(1, weight=1)
        
        self.progress_label = ctk.CTkLabel(self.progress_frame, text="Ready", text_color="gray", 
                                          font=ctk.CTkFont(size=12))
        self.progress_label.grid(row=0, column=0, padx=10, sticky="w")
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, mode="determinate", height=20)
        self.progress_bar.grid(row=0, column=1, padx=10, sticky="ew")
        self.progress_bar.set(0)
        
        # Left Panel - Episode Info (no scrollbar)
        self.left_panel = ctk.CTkFrame(self)
        self.left_panel.grid(row=1, column=0, sticky="nsew", padx=(20, 10), pady=10)
        
        # Panel title
        panel_title = ctk.CTkLabel(self.left_panel, text="Episode Information", 
                                   font=ctk.CTkFont(size=16, weight="bold"))
        panel_title.pack(pady=10)
        
        # Episode info will be populated dynamically
        self.episode_image_label = ctk.CTkLabel(self.left_panel, text="No Image", width=280, height=280)
        self.episode_image_label.pack(pady=10)
        self.episode_image = None  # Keep reference to prevent garbage collection
        
        self.episode_title_label = ctk.CTkLabel(self.left_panel, text="", 
                                                font=ctk.CTkFont(size=16, weight="bold"),
                                                wraplength=280, justify="left",
                                                anchor="w")
        self.episode_title_label.pack(pady=5, padx=10, fill="x")
        
        self.episode_subtitle_label = ctk.CTkLabel(self.left_panel, text="", 
                                                  font=ctk.CTkFont(size=14),
                                                  text_color="gray",
                                                  wraplength=280, justify="left")
        self.episode_subtitle_label.pack(pady=2, padx=10)
        
        self.episode_date_label = ctk.CTkLabel(self.left_panel, text="", 
                                              font=ctk.CTkFont(size=12),
                                              text_color="gray")
        self.episode_date_label.pack(pady=5, padx=10)
        
        # Description
        self.description_label = ctk.CTkLabel(self.left_panel, text="", 
                                             font=ctk.CTkFont(size=12),
                                             wraplength=280, justify="left",
                                             anchor="w")
        self.description_label.pack(pady=10, padx=10, fill="x")
        
        # Transcription options
        self.options_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        self.options_frame.pack(pady=10, padx=10, fill="x")
        
        ctk.CTkLabel(self.options_frame, text="Transcription Engine:", 
                    font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=5)
        
        self.backend_var = ctk.StringVar(value="faster")
        self.faster_radio = ctk.CTkRadioButton(self.options_frame, text="Faster (faster-whisper)", 
                                              variable=self.backend_var, value="faster",
                                              font=ctk.CTkFont(size=11))
        self.faster_radio.pack(anchor="w", padx=20, pady=2)
        
        self.openai_radio = ctk.CTkRadioButton(self.options_frame, text="Accurate (openai-whisper)", 
                                               variable=self.backend_var, value="openai",
                                               font=ctk.CTkFont(size=11))
        self.openai_radio.pack(anchor="w", padx=20, pady=2)
        
        ctk.CTkLabel(self.options_frame, text="Model Size:", 
                    font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(10, 5))
        
        self.model_var = ctk.StringVar(value="base")
        self.model_option = ctk.CTkOptionMenu(self.options_frame, 
                                             values=['tiny', 'base', 'small', 'medium', 'large'],
                                             variable=self.model_var, width=200)
        self.model_option.pack(anchor="w", padx=20, pady=5)
        
        # Middle Panel - Transcript
        self.middle_panel = ctk.CTkFrame(self)
        self.middle_panel.grid(row=1, column=1, sticky="nsew", padx=5, pady=10)
        self.middle_panel.grid_columnconfigure(0, weight=1)
        self.middle_panel.grid_rowconfigure(1, weight=1)
        
        # Transcript header
        transcript_header = ctk.CTkFrame(self.middle_panel, fg_color="transparent")
        transcript_header.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        transcript_header.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(transcript_header, text="Transcript", 
                    font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, sticky="w")
        
        # Download and Copy buttons (with symbols)
        btn_frame = ctk.CTkFrame(transcript_header, fg_color="transparent")
        btn_frame.grid(row=0, column=1, sticky="e")
        
        self.download_mp3_btn = ctk.CTkButton(btn_frame, text="⬇", width=40, height=30,
                                             command=self.download_mp3,
                                             fg_color="transparent", border_width=1,
                                             font=ctk.CTkFont(size=16))
        self.download_mp3_btn.pack(side="left", padx=3)
        
        self.copy_btn = ctk.CTkButton(btn_frame, text="📋", width=40, height=30,
                                     command=self.copy_transcript,
                                     fg_color="transparent", border_width=1,
                                     font=ctk.CTkFont(size=16))
        self.copy_btn.pack(side="left", padx=3)
        
        self.download_btn = ctk.CTkButton(btn_frame, text="💾", width=40, height=30,
                                         command=self.download_transcript,
                                         fg_color="transparent", border_width=1,
                                         font=ctk.CTkFont(size=16))
        self.download_btn.pack(side="left", padx=3)
        
        # Timestamp toggle
        self.timestamp_var = ctk.BooleanVar(value=False)
        self.timestamp_toggle = ctk.CTkSwitch(transcript_header, text="Include timestamps",
                                             variable=self.timestamp_var,
                                             command=self.toggle_timestamps)
        self.timestamp_toggle.grid(row=1, column=0, sticky="w", pady=5)
        
        # Transcript text area (read-only)
        self.transcript_textbox = ctk.CTkTextbox(self.middle_panel, 
                                                font=ctk.CTkFont(size=13),
                                                wrap="word",
                                                corner_radius=10,
                                                state="disabled")  # Make read-only
        self.transcript_textbox.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        # Right Panel - Summary
        self.right_panel = ctk.CTkFrame(self)
        self.right_panel.grid(row=1, column=2, sticky="nsew", padx=(5, 20), pady=10)
        self.right_panel.grid_columnconfigure(0, weight=1)
        self.right_panel.grid_rowconfigure(1, weight=1)
        
        # Summary header
        summary_header = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        summary_header.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        summary_header.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(summary_header, text="Summary", 
                    font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, sticky="w")
        
        # Summary buttons (with symbols)
        summary_btn_frame = ctk.CTkFrame(summary_header, fg_color="transparent")
        summary_btn_frame.grid(row=0, column=1, sticky="e")
        
        self.copy_summary_btn = ctk.CTkButton(summary_btn_frame, text="📋", width=40, height=30,
                                             command=self.copy_summary,
                                             fg_color="transparent", border_width=1,
                                             font=ctk.CTkFont(size=16))
        self.copy_summary_btn.pack(side="left", padx=3)
        
        self.download_summary_btn = ctk.CTkButton(summary_btn_frame, text="💾", width=40, height=30,
                                                 command=self.download_summary,
                                                 fg_color="transparent", border_width=1,
                                                 font=ctk.CTkFont(size=16))
        self.download_summary_btn.pack(side="left", padx=3)
        
        # Summary text area (read-only)
        self.summary_textbox = ctk.CTkTextbox(self.right_panel,
                                             font=ctk.CTkFont(size=13),
                                             wrap="word",
                                             corner_radius=10,
                                             state="disabled")  # Make read-only
        self.summary_textbox.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
    def load_episode_image(self, image_url):
        """Load and display episode cover image at high quality."""
        if not image_url:
            print("GUI DEBUG: load_episode_image called with empty URL")
            self.episode_image_label.configure(text="No Image", image="")
            return
        
        print(f"GUI DEBUG: Attempting to load image from: {image_url[:100]}...")
        try:
            # Set headers to mimic a browser (helps with CORS/access issues)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://open.spotify.com/',
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            }
            
            # Try to get higher resolution version
            high_res_url = image_url
            # Spotify URLs often have size parameters - try to get larger version
            if 'spotify' in image_url.lower() or 'image' in image_url.lower():
                # Replace common small sizes with larger ones
                for small_size in ['64x64', '160x160', '300x300']:
                    if small_size in high_res_url:
                        high_res_url = high_res_url.replace(small_size, '640x640')
                        break
                # If no size found, try common high-res patterns
                if '640x640' not in high_res_url and '?' not in high_res_url:
                    # Try appending size parameter
                    if '/image/' in high_res_url:
                        high_res_url = high_res_url.replace('/image/', '/image/640x640/')
            
            # Try high-res URL first
            try:
                response = requests.get(high_res_url, headers=headers, timeout=15)
                print(f"GUI DEBUG: Image request status: {response.status_code} for {high_res_url[:80]}...")
                if response.status_code == 200:
                    img = Image.open(BytesIO(response.content))
                    print(f"GUI DEBUG: Image loaded successfully, size: {img.size}, format: {img.format}")
                    # Use high-quality resampling and maintain aspect ratio
                    # Resize to 280x280 but use better quality
                    img.thumbnail((280, 280), Image.Resampling.LANCZOS)
                    # Create a square image with the thumbnail centered
                    square_img = Image.new('RGB', (280, 280), (0, 0, 0))
                    x_offset = (280 - img.width) // 2
                    y_offset = (280 - img.height) // 2
                    square_img.paste(img, (x_offset, y_offset))
                    
                    photo = ImageTk.PhotoImage(square_img)
                    self.episode_image_label.configure(image=photo, text="")
                    self.episode_image = photo  # Keep a reference to prevent garbage collection
                    print("GUI DEBUG: Image displayed successfully")
                    return
            except Exception as e1:
                print(f"GUI DEBUG: High-res image failed: {e1}, trying original URL")
            
            # Fallback to original URL
            try:
                response = requests.get(image_url, headers=headers, timeout=15)
                print(f"GUI DEBUG: Fallback image request status: {response.status_code}")
                if response.status_code == 200:
                    img = Image.open(BytesIO(response.content))
                    print(f"GUI DEBUG: Fallback image loaded successfully, size: {img.size}, format: {img.format}")
                    img.thumbnail((280, 280), Image.Resampling.LANCZOS)
                    square_img = Image.new('RGB', (280, 280), (0, 0, 0))
                    x_offset = (280 - img.width) // 2
                    y_offset = (280 - img.height) // 2
                    square_img.paste(img, (x_offset, y_offset))
                    photo = ImageTk.PhotoImage(square_img)
                    self.episode_image_label.configure(image=photo, text="")
                    self.episode_image = photo
                    print("GUI DEBUG: Fallback image displayed successfully")
                    return
            except Exception as e2:
                print(f"GUI DEBUG: Fallback image also failed: {e2}")
            
            print(f"GUI DEBUG: Both image URLs failed")
            self.episode_image_label.configure(text="Image Load Failed", image="")
            self.episode_image = None
        except Exception as e:
            import traceback
            print(f"GUI DEBUG: Error loading image: {e}")
            traceback.print_exc()
            self.episode_image_label.configure(text="No Image", image="")
            self.episode_image = None
    
    def display_episode_info(self, info):
        """Display episode information in left panel."""
        self.episode_info = info
        
        # Debug output
        print(f"GUI DEBUG: Received episode info - Title: {info.get('title', 'N/A')}")
        print(f"GUI DEBUG: Description length: {len(info.get('description', ''))}")
        print(f"GUI DEBUG: Cover image: {info.get('cover_image', 'N/A')[:80] if info.get('cover_image') else 'None'}...")
        print(f"GUI DEBUG: Subtitle: {info.get('subtitle', 'N/A')}")
        print(f"GUI DEBUG: Release date: {info.get('release_date', 'N/A')}")
        
        # Title
        title = info.get('title', 'Unknown Episode')
        self.episode_title_label.configure(text=title)
        
        # Subtitle (show name)
        subtitle = info.get('subtitle', '')
        self.episode_subtitle_label.configure(text=subtitle if subtitle else "")
        
        # Date
        release_date = info.get('release_date', '')
        if release_date:
            try:
                dt = datetime.fromisoformat(release_date.replace('Z', '+00:00'))
                date_str = dt.strftime('%b %d, %Y')
                self.episode_date_label.configure(text=date_str)
            except:
                self.episode_date_label.configure(text=release_date[:10] if len(release_date) > 10 else release_date)
        else:
            self.episode_date_label.configure(text="")
        
        # Description
        description = info.get('description', '')
        if description:
            # Clean up description - remove HTML entities and extra whitespace
            description = description.strip()
            # Wrap text for display
            wrapped = '\n'.join(textwrap.wrap(description, width=40))
            self.description_label.configure(text=wrapped)
            print(f"GUI DEBUG: Displaying description (length: {len(description)})")
        else:
            self.description_label.configure(text="No description available.")
            print("GUI DEBUG: No description found in episode info")
        
        # Cover image - try multiple paths
        cover_image = info.get('cover_image')
        if not cover_image:
            visual_identity = info.get('visualIdentity', {})
            if visual_identity:
                images = visual_identity.get('image', [])
                if images and len(images) > 0:
                    # Get the largest image (usually last)
                    for img in reversed(images):
                        if isinstance(img, dict):
                            cover_image = img.get('url')
                            if cover_image:
                                break
                        elif isinstance(img, str):
                            cover_image = img
                            break
        
        # Also check other paths
        if not cover_image:
            cover_art = info.get('coverArt', {})
            if isinstance(cover_art, dict):
                sources = cover_art.get('sources', [])
                if sources and len(sources) > 0:
                    cover_image = sources[0].get('url') if isinstance(sources[0], dict) else sources[0]
        
        if cover_image:
            print(f"GUI DEBUG: Loading cover image from URL: {cover_image[:80]}...")
            # Load image in a thread to avoid blocking
            threading.Thread(target=self.load_episode_image, args=(cover_image,), daemon=True).start()
        else:
            print("GUI DEBUG: No cover image found in episode info")
            self.episode_image_label.configure(text="No Image", image="")
            self.episode_image = None
    
    def toggle_inputs(self, enable):
        """Enable/disable input controls."""
        state = "normal" if enable else "disabled"
        self.submit_btn.configure(state=state)
        self.url_entry.configure(state=state)
        self.faster_radio.configure(state=state)
        self.openai_radio.configure(state=state)
        self.model_option.configure(state=state)
        if enable:
            self.progress_bar.set(0)
            self.progress_label.configure(text="Ready", text_color="gray")
    
    def start_transcription(self):
        """Start the transcription process."""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a Spotify URL")
            return
        
        self.toggle_inputs(False)
        self.progress_label.configure(text="Starting...", text_color="white")
        self.transcript_textbox.delete("1.0", "end")
        self.summary_textbox.delete("1.0", "end")
        
        thread = threading.Thread(target=self.transcribe_worker, args=(url,), daemon=True)
        thread.start()
    
    def transcribe_worker(self, url):
        """Worker thread for transcription."""
        temp_path = None
        try:
            total_steps = 6

            # Step 1: Get Info
            self.update_phase("Fetching Spotify metadata...", 1, total_steps)
            info = self.scraper.get_spotify_info(url)
            if not info:
                raise ValueError("Could not extract information from Spotify URL")
            
            # Display episode info
            self.after(0, self.display_episode_info, info)
            
            # Step 2: Download audio
            self.update_phase("Resolving RSS feed and downloading audio...", 2, total_steps)
            if self.downloader is None:
                self.downloader = AudioDownloader()
            
            temp_path = self.downloader.download_from_spotify(url, spotify_info=info)
            
            # Step 3: Load Model
            backend = self.backend_var.get()
            self.update_phase(f"Loading {backend} Whisper model ({self.model_var.get()})...", 3, total_steps)
            self.transcriber = Transcriber(
                model_size=self.model_var.get(),
                backend=backend
            )
            
            # Step 4: Transcribe
            self.start_transcription_progress()
            self.transcription_result = self.transcriber.transcribe(
                temp_path,
                progress_callback=self.update_transcription_progress,
            )
            
            # Step 5: Generate Summary (AI-based, no timestamps)
            self.update_phase("Generating AI summary...", 5, total_steps)
            
            # Step 6: Display results
            self.update_phase("Complete!", total_steps, total_steps)
            
            # Format transcript with/without timestamps
            transcript_data = self.format_transcript(self.timestamp_var.get())
            summary_text = self.format_summary()
            
            self.after(0, self.display_results, transcript_data, summary_text)
            
        except Exception as e:
            self.after(0, self.show_error, str(e))
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
            self.after(0, lambda: self.toggle_inputs(True))
    
    def format_transcript(self, include_timestamps=False):
        """Format transcript for display with proper timestamp formatting."""
        if not self.transcription_result:
            return ""
        
        if include_timestamps:
            segments = self.transcription_result.get('segments', [])
            if not segments:
                return FormatConverter.to_display_text(self.transcription_result)
            
            # Group segments into chunks (similar to non-timestamp version)
            chunks = []
            current_chunk = []
            last_end = None
            
            for seg in segments:
                text = seg.get('text', '').strip()
                if not text:
                    continue
                
                start = seg.get('start', 0)
                end = seg.get('end', start)
                gap = start - last_end if (last_end is not None) else 0
                
                # Start new chunk on significant gaps or sentence endings
                if (gap > 1.5 and current_chunk) or (text.endswith(('.', '!', '?')) and len(current_chunk) > 2):
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = [seg]
                else:
                    current_chunk.append(seg)
                
                last_end = end
            
            if current_chunk:
                chunks.append(current_chunk)
            
            # Return chunks data for special formatting
            return {'chunks': chunks, 'format': 'timestamped'}
        else:
            return {'text': FormatConverter.to_display_text(self.transcription_result), 'format': 'plain'}
    
    def format_summary(self):
        """Format AI-generated summary for display (no timestamps)."""
        if not self.transcription_result:
            return "No summary available."
        
        # Use AI summarization (extractive, but can be enhanced)
        summary_text = Summarizer.summarize(self.transcription_result, max_sentences=8)
        
        # Format as readable paragraphs
        if summary_text:
            wrapped = '\n'.join(textwrap.wrap(summary_text, width=70))
            return wrapped
        
        return "No summary available."
    
    def toggle_timestamps(self):
        """Toggle timestamp display in transcript."""
        if self.transcription_result:
            transcript_data = self.format_transcript(self.timestamp_var.get())
            # Re-display with new format
            summary_text = self.summary_textbox.get("1.0", "end-1c")
            self.display_results(transcript_data, summary_text)
    
    def display_results(self, transcript_data, summary_text):
        """Display transcription and summary results with timestamp formatting."""
        self.transcript_textbox.configure(state="normal")
        self.transcript_textbox.delete("1.0", "end")
        
        if isinstance(transcript_data, dict) and transcript_data.get('format') == 'timestamped':
            # Format with timestamps in colored boxes (horizontally separated)
            chunks = transcript_data.get('chunks', [])
            
            for chunk in chunks:
                if not chunk:
                    continue
                
                first_seg = chunk[0]
                start_time = first_seg.get('start', 0)
                mins, secs = divmod(int(start_time), 60)
                timestamp = f"{mins:02d}:{secs:02d}"
                
                # Combine text from all segments in chunk
                chunk_text = ' '.join(seg.get('text', '').strip() for seg in chunk)
                
                # Format: [timestamp] text (with spacing for horizontal separation)
                # Use a special format that creates visual separation
                formatted_line = f"[{timestamp}]  {chunk_text}\n\n"
                
                # Insert with timestamp tag for red coloring
                start_pos = self.transcript_textbox.index("end-1c")
                self.transcript_textbox.insert("end", formatted_line)
                end_pos = self.transcript_textbox.index("end-1c")
                
                # Tag the timestamp portion (the [MM:SS] part)
                timestamp_start = formatted_line.find('[')
                timestamp_end = formatted_line.find(']') + 1
                if timestamp_start >= 0 and timestamp_end > timestamp_start:
                    # Calculate positions
                    line_start = self.transcript_textbox.index(f"{start_pos} linestart")
                    tag_start = f"{line_start}+{timestamp_start}c"
                    tag_end = f"{line_start}+{timestamp_end}c"
                    
                    # Apply red color to timestamp
                    self.transcript_textbox.tag_add("timestamp_red", tag_start, tag_end)
            
            # Configure timestamp tag (red text, bold)
            self.transcript_textbox.tag_config("timestamp_red", 
                                              foreground="#E22134",  # Red color
                                              font=ctk.CTkFont(size=13, weight="bold"))
        else:
            # Plain text format
            text = transcript_data.get('text', '') if isinstance(transcript_data, dict) else str(transcript_data)
            self.transcript_textbox.insert("1.0", text)
        
        self.transcript_textbox.configure(state="disabled")
        
        # Display summary
        self.summary_textbox.configure(state="normal")
        self.summary_textbox.delete("1.0", "end")
        self.summary_textbox.insert("1.0", summary_text)
        self.summary_textbox.configure(state="disabled")
    
    def copy_transcript(self):
        """Copy transcript to clipboard."""
        self.transcript_textbox.configure(state="normal")
        text = self.transcript_textbox.get("1.0", "end-1c")
        self.transcript_textbox.configure(state="disabled")
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            messagebox.showinfo("Copied", "Transcript copied to clipboard!")
        else:
            messagebox.showwarning("Empty", "No transcript to copy.")
    
    def copy_summary(self):
        """Copy summary to clipboard."""
        self.summary_textbox.configure(state="normal")
        text = self.summary_textbox.get("1.0", "end-1c")
        self.summary_textbox.configure(state="disabled")
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            messagebox.showinfo("Copied", "Summary copied to clipboard!")
        else:
            messagebox.showwarning("Empty", "No summary to copy.")
    
    def download_transcript(self):
        """Download transcript to file."""
        if not self.transcription_result:
            messagebox.showwarning("No Transcription", "Please transcribe audio first")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                self.transcript_textbox.configure(state="normal")
                text = self.transcript_textbox.get("1.0", "end-1c")
                self.transcript_textbox.configure(state="disabled")
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(text)
                messagebox.showinfo("Success", f"Saved to {filename}")
            except Exception as e:
                messagebox.showerror("Export Error", str(e))
    
    def download_summary(self):
        """Download summary to file."""
        self.summary_textbox.configure(state="normal")
        text = self.summary_textbox.get("1.0", "end-1c")
        self.summary_textbox.configure(state="disabled")
        if not text:
            messagebox.showwarning("No Summary", "No summary available to download")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(text)
                messagebox.showinfo("Success", f"Saved to {filename}")
            except Exception as e:
                messagebox.showerror("Export Error", str(e))
    
    def download_mp3(self):
        """Download the raw MP3 file."""
        if not self.episode_info:
            messagebox.showwarning("No Episode", "Please transcribe an episode first")
            return
        
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("No URL", "Please enter a Spotify URL")
            return
        
        save_path = filedialog.asksaveasfilename(
            defaultextension=".mp3",
            filetypes=[("MP3 Audio", "*.mp3"), ("All files", "*.*")]
        )
        if not save_path:
            return
        
        self.toggle_inputs(False)
        self.progress_label.configure(text="Downloading MP3...", text_color="white")
        
        thread = threading.Thread(target=self.download_mp3_worker, args=(url, save_path), daemon=True)
        thread.start()
    
    def download_mp3_worker(self, url, save_path):
        """Worker thread for MP3 download."""
        temp_path = None
        try:
            total_steps = 3
            
            self.update_phase("Fetching Spotify metadata...", 1, total_steps)
            info = self.scraper.get_spotify_info(url)
            
            self.update_phase("Downloading audio file...", 2, total_steps)
            if self.downloader is None:
                self.downloader = AudioDownloader()
            
            temp_path = self.downloader.download_from_spotify(url, spotify_info=info)
            
            self.update_phase("Preparing MP3 file...", 3, total_steps)
            temp_ext = Path(temp_path).suffix.lower()
            if temp_ext != ".mp3":
                self.downloader.convert_to_mp3(temp_path, save_path)
            else:
                shutil.copy(temp_path, save_path)
            
            self.update_phase("Download complete!", total_steps, total_steps)
            messagebox.showinfo("Success", f"Saved to {save_path}")
            
        except Exception as e:
            self.after(0, self.show_error, str(e))
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
            self.after(0, lambda: self.toggle_inputs(True))
    
    def update_phase(self, message, current_step, total_steps):
        """Update progress phase."""
        def _update():
            fraction = min(max(current_step / total_steps, 0), 1)
            self.progress_label.configure(text=message, text_color="white")
            self.progress_bar.set(fraction)
        self.after(0, _update)
    
    def start_transcription_progress(self):
        """Start transcription progress tracking."""
        def _start():
            self.progress_bar.set(0)
            self.progress_label.configure(text="Transcribing audio... 0%", text_color="white")
        self.after(0, _start)

    def update_transcription_progress(self, fraction):
        """Update transcription progress."""
        def _update():
            clamped = min(max(fraction, 0.0), 1.0)
            percent = int(clamped * 100)
            self.progress_bar.set(clamped)
            self.progress_label.configure(text=f"Transcribing audio... {percent}%", text_color="white")
        self.after(0, _update)
    
    def show_error(self, message):
        """Show error message."""
        self.progress_label.configure(text=f"Error: {message}", text_color="red")
        messagebox.showerror("Error", message)

def main():
    app = SpotifyTranscriberGUI()
    app.mainloop()

if __name__ == "__main__":
    main()
