"""
Spotify RSS utilities for fetching direct podcast audio URLs.
"""
import os
import re
from urllib.parse import urlparse

import feedparser
import requests


class SpotifyRSSFetcher:
    """Resolve Spotify podcast episodes to their RSS audio URLs."""

    SPOTIFEED_TEMPLATE = "https://spotifeed.timdorr.com/show/{show_id}"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            }
        )
        # Set default timeout for all requests (30 seconds connect, 60 seconds read)
        self.session.timeout = (30, 60)

    def _extract_show_name(self, spotify_info):
        if not spotify_info:
            return None

        candidates = [
            spotify_info.get("showName"),
            spotify_info.get("subtitle"),
            spotify_info.get("title"),
        ]

        nested_paths = [
            ("show", "name"),
            ("podcastShow", "name"),
            ("linkedEntity", "name"),
        ]

        for path in nested_paths:
            data = spotify_info
            for key in path:
                if isinstance(data, dict):
                    data = data.get(key)
                else:
                    data = None
                    break
            if isinstance(data, str):
                candidates.append(data)

        for candidate in candidates:
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
        return None

    def _extract_show_id_from_info(self, spotify_info):
        if not spotify_info:
            return None

        # Possible places where the show ID/URI appears
        candidate_paths = [
            ("show", "uri"),
            ("show", "id"),
            ("podcastShow", "uri"),
            ("podcastShow", "id"),
            ("linkedEntity", "uri"),
        ]

        for path in candidate_paths:
            data = spotify_info
            for key in path:
                if isinstance(data, dict) and key in data:
                    data = data[key]
                else:
                    data = None
                    break
            if isinstance(data, str):
                return self._normalize_show_id(data)

        # Flat keys and metadata fields
        flat_keys = [
            "showUri",
            "show_id",
            "showId",
            "podcastShowUri",
            "relatedEntityUri",
            "relatedEntityId",
            "parentShowUri",
        ]

        for key in flat_keys:
            value = spotify_info.get(key)
            if isinstance(value, str):
                return self._normalize_show_id(value)

        # Deep search through nested structures for any spotify:show reference
        deep_uri = self._deep_find_show_reference(spotify_info)
        if deep_uri:
            return deep_uri

        return None

    @staticmethod
    def _normalize_show_id(value):
        if not value:
            return None
        if value.startswith("spotify:show:"):
            return value.split(":")[-1]
        if "open.spotify.com/show/" in value:
            match = re.search(r"open\.spotify\.com/show/([a-zA-Z0-9]+)", value)
            if match:
                return match.group(1)
        return value

    def _deep_find_show_reference(self, payload):
        """Search recursively for the first spotify:show reference."""
        if isinstance(payload, dict):
            for _, val in payload.items():
                found = self._deep_find_show_reference(val)
                if found:
                    return found
        elif isinstance(payload, (list, tuple)):
            for item in payload:
                found = self._deep_find_show_reference(item)
                if found:
                    return found
        elif isinstance(payload, str):
            if "spotify:show:" in payload or "open.spotify.com/show/" in payload:
                return self._normalize_show_id(payload)
        return None

    def _extract_show_id_from_url(self, spotify_url):
        match = re.search(r"spotify\.com/show/([a-zA-Z0-9]+)", spotify_url)
        if match:
            return match.group(1)
        return None

    def _extract_show_id_from_page(self, spotify_url):
        try:
            response = self.session.get(spotify_url, timeout=10)
            response.raise_for_status()
            patterns = [
                r"spotify:show:([a-zA-Z0-9]+)",
                r"open\.spotify\.com/show/([a-zA-Z0-9]+)",
            ]
            for pattern in patterns:
                match = re.search(pattern, response.text)
                if match:
                    return match.group(1)
        except requests.RequestException:
            return None
        return None

    def get_show_id(self, spotify_url, spotify_info):
        show_id = self._extract_show_id_from_info(spotify_info)
        if show_id:
            return show_id

        show_id = self._extract_show_id_from_url(spotify_url)
        if show_id:
            return show_id

        return self._extract_show_id_from_page(spotify_url)

    def _fetch_feed_from_spotify(self, show_id):
        if not show_id:
            raise ValueError("Unable to resolve Spotify show ID")

        feed_url = self.SPOTIFEED_TEMPLATE.format(show_id=show_id)
        
        # Retry logic with exponential backoff - shorter timeout for faster failure
        max_retries = 2  # Reduced retries for faster failure
        for attempt in range(max_retries):
            try:
                # Shorter timeout: 5s connect, 15s read
                response = self.session.get(feed_url, timeout=(5, 15))
                response.raise_for_status()
                return self._parse_feed(response.content)
            except requests.exceptions.HTTPError as http_error:
                # Check for 404 specifically - this means the show isn't in spotifeed
                if http_error.response is not None and http_error.response.status_code == 404:
                    # Re-raise as HTTPError so caller can catch it
                    raise http_error
                if attempt == max_retries - 1:
                    raise RuntimeError(f"Failed to fetch RSS feed from Spotify: {str(http_error)}")
                import time
                time.sleep(1)  # Shorter backoff
            except requests.exceptions.Timeout:
                if attempt == max_retries - 1:
                    raise RuntimeError(f"Timeout fetching RSS feed from Spotify after {max_retries} attempts")
                import time
                time.sleep(1)  # Shorter backoff
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    raise RuntimeError(f"Failed to fetch RSS feed from Spotify: {str(e)}")
                import time
                time.sleep(1)

    def _fetch_feed_from_itunes(self, show_name):
        if not show_name:
            raise ValueError("Show name is required for iTunes fallback")

        params = {
            "media": "podcast",
            "term": show_name,
            "limit": 5,
        }
        
        # Retry logic with exponential backoff
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.session.get("https://itunes.apple.com/search", params=params, timeout=(10, 30))
                response.raise_for_status()
                data = response.json()
                break
            except requests.exceptions.Timeout:
                if attempt == max_retries - 1:
                    raise RuntimeError(f"Timeout fetching iTunes search results after {max_retries} attempts")
                import time
                time.sleep(2 ** attempt)
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    raise RuntimeError(f"Failed to fetch iTunes search results: {str(e)}")
                import time
                time.sleep(2 ** attempt)

        results = data.get("results", [])
        if not results:
            raise ValueError("Unable to locate podcast via iTunes search")

        target = self._normalize_text(show_name)
        feed_url = None

        for result in results:
            candidate_feed = result.get("feedUrl")
            candidate_name = result.get("collectionName") or ""
            if not candidate_feed:
                continue
            normalized_candidate = self._normalize_text(candidate_name)

            if (
                normalized_candidate
                and target
                and (target in normalized_candidate or normalized_candidate in target)
            ):
                feed_url = candidate_feed
                break

        if not feed_url:
            feed_url = next((r.get("feedUrl") for r in results if r.get("feedUrl")), None)

        if not feed_url:
            raise ValueError("iTunes fallback did not return a usable feed URL")

        feed_response = self.session.get(feed_url, timeout=30)
        feed_response.raise_for_status()
        return self._parse_feed(feed_response.content)

    @staticmethod
    def _normalize_text(value):
        if not value:
            return ""
        return re.sub(r"[^a-z0-9]+", "", value.lower())

    @staticmethod
    def _parse_feed(content):
        feed = feedparser.parse(content)
        if feed.bozo:
            raise ValueError("Invalid RSS feed received")
        if not feed.entries:
            raise ValueError("RSS feed is empty or unavailable")
        return feed

    def _match_episode_entry(self, feed, episode_id=None, episode_title=None):
        if not episode_id and not episode_title:
            return None

        # Try matching by episode ID first (most reliable)
        if episode_id:
            episode_id_lower = episode_id.lower()
            # Also try without case sensitivity and with different separators
            episode_id_variants = [episode_id_lower, episode_id.upper(), episode_id]
            
            for entry in feed.entries:
                candidates = [
                    entry.get("id"),
                    entry.get("guid"),
                    entry.get("link"),
                ]
                # Also check all links
                if hasattr(entry, 'links'):
                    candidates.extend(
                        link.get("href") if isinstance(link, dict) else str(link)
                        for link in entry.links
                    )
                elif isinstance(entry.get("links"), list):
                    candidates.extend(
                        link.get("href") if isinstance(link, dict) else str(link)
                        for link in entry.get("links", [])
                    )

                for candidate in filter(None, candidates):
                    candidate_str = str(candidate).lower()
                    # Check if episode ID appears anywhere in the candidate
                    for variant in episode_id_variants:
                        if variant.lower() in candidate_str:
                            return entry
                    # Also check if it's a Spotify URL with the episode ID
                    if "spotify.com/episode/" in candidate_str:
                        # Extract ID from URL and compare
                        import re
                        url_id_match = re.search(r'episode/([a-zA-Z0-9]+)', candidate_str)
                        if url_id_match and url_id_match.group(1).lower() == episode_id_lower:
                            return entry

        # Try matching by title with improved normalization
        if episode_title:
            target_title = self._normalize_text(episode_title)
            best_match = None
            best_score = 0
            
            for entry in feed.entries:
                entry_title = entry.get("title", "")
                if not entry_title:
                    continue
                    
                normalized_entry = self._normalize_text(entry_title)
                
                # Exact match
                if normalized_entry == target_title:
                    return entry
                
                # Calculate similarity score
                # Check if one contains the other
                if target_title in normalized_entry or normalized_entry in target_title:
                    # Calculate how much of the title matches
                    shorter = min(len(target_title), len(normalized_entry))
                    longer = max(len(target_title), len(normalized_entry))
                    if shorter > 0:
                        score = shorter / longer
                        if score > best_score:
                            best_score = score
                            best_match = entry
                
                # Try word-based matching (at least 3 words in common)
                target_words = set(target_title.split())
                entry_words = set(normalized_entry.split())
                common_words = target_words.intersection(entry_words)
                if len(common_words) >= 3 and len(common_words) / max(len(target_words), 1) > 0.5:
                    score = len(common_words) / max(len(target_words), len(entry_words), 1)
                    if score > best_score:
                        best_score = score
                        best_match = entry
            
            if best_match and best_score > 0.3:  # At least 30% similarity
                return best_match

        # Last resort: try to match by date if available
        # This is a fallback - return None if we can't match
        return None

    def get_episode_audio(self, spotify_url, spotify_info):
        episode_id = None
        if spotify_info:
            episode_id = (
                spotify_info.get("id")
                or spotify_info.get("episode_id")
                or spotify_info.get("episodeId")
            )
            episode_title = spotify_info.get("title")
        else:
            episode_title = None

        if not episode_id:
            match = re.search(r"spotify\.com/episode/([a-zA-Z0-9]+)", spotify_url)
            if match:
                episode_id = match.group(1)

        if not episode_id:
            raise ValueError("Unable to determine Spotify episode ID")

        show_id = self.get_show_id(spotify_url, spotify_info)
        show_name = self._extract_show_name(spotify_info)
        
        # If we don't have show name but have show_id, try to extract from episode page
        if not show_name and show_id:
            try:
                # Try to get show name from episode page
                episode_page = self.session.get(spotify_url, timeout=10)
                if episode_page.status_code == 200:
                    # Look for show name in page
                    show_name_match = re.search(r'"showName":"([^"]+)"', episode_page.text)
                    if show_name_match:
                        show_name = show_name_match.group(1)
            except:
                pass
        
        if not show_id:
            raise ValueError("Unable to determine Spotify show ID for this episode")

        # Try Spotify RSS feed first
        feed = None
        try:
            feed = self._fetch_feed_from_spotify(show_id)
        except requests.HTTPError as http_error:
            # 404 means show not found in spotifeed - fall back to iTunes
            if http_error.response is not None and http_error.response.status_code == 404:
                if not show_name:
                    raise ValueError("Show not found in RSS feed and show name unavailable for iTunes fallback")
                try:
                    feed = self._fetch_feed_from_itunes(show_name)
                except Exception as itunes_error:
                    raise RuntimeError(f"Show not found in Spotify RSS feed (404) and iTunes fallback failed: {str(itunes_error)}")
            else:
                raise
        except (requests.RequestException, RuntimeError) as e:
            # For other errors, try iTunes fallback if we have show name
            error_str = str(e)
            if "404" in error_str or "Not Found" in error_str:
                if not show_name:
                    raise ValueError(f"Show not found in RSS feed ({error_str}) and show name unavailable for iTunes fallback")
                try:
                    feed = self._fetch_feed_from_itunes(show_name)
                except Exception as itunes_error:
                    raise RuntimeError(f"Show not found in Spotify RSS feed and iTunes fallback failed: {str(itunes_error)}")
            else:
                # For non-404 errors, try iTunes as fallback
                if show_name:
                    try:
                        feed = self._fetch_feed_from_itunes(show_name)
                    except Exception:
                        # If iTunes also fails, raise original error
                        raise RuntimeError(f"Failed to fetch RSS feed from Spotify: {error_str}")
                else:
                    raise RuntimeError(f"Failed to fetch RSS feed from Spotify: {error_str}")
        
        if not feed:
            raise RuntimeError("Unable to fetch RSS feed from Spotify or iTunes")

        entry = self._match_episode_entry(feed, episode_id, episode_title)
        if not entry:
            # Last resort: try to use the most recent episode if title is very similar
            if episode_title and feed.entries and "Spotify Episode" not in episode_title:
                target_normalized = self._normalize_text(episode_title)
                best_fallback = None
                best_overlap = 0
                for feed_entry in feed.entries[:20]:  # Check first 20 entries
                    entry_title = self._normalize_text(feed_entry.get("title", ""))
                    if entry_title and target_normalized:
                        # Check if at least 50% of words match
                        target_words = set(target_normalized.split())
                        entry_words = set(entry_title.split())
                        if len(target_words) > 0:
                            overlap = len(target_words.intersection(entry_words)) / len(target_words)
                            if overlap >= 0.5 and overlap > best_overlap:
                                best_overlap = overlap
                                best_fallback = feed_entry
                
                if best_fallback:
                    entry = best_fallback
            
            # If still no match and we have an ID, try matching by checking if the ID appears in any entry's content
            if not entry and episode_id:
                episode_id_lower = episode_id.lower()
                for feed_entry in feed.entries[:50]:  # Check first 50 entries
                    # Check all text fields
                    entry_text = " ".join([
                        str(feed_entry.get("id", "")),
                        str(feed_entry.get("guid", "")),
                        str(feed_entry.get("link", "")),
                        str(feed_entry.get("title", "")),
                        str(feed_entry.get("summary", "")),
                    ]).lower()
                    if episode_id_lower in entry_text:
                        entry = feed_entry
                        break
            
            if not entry:
                raise ValueError(
                    f"Episode not found in the show's RSS feed. "
                    f"Looking for: ID={episode_id}, Title={episode_title}. "
                    f"Feed has {len(feed.entries)} entries."
                )

        # Extract enclosure URL
        enclosure_url = None
        if entry.get("enclosures"):
            enclosure_url = entry.enclosures[0].get("href")
        else:
            for link in entry.get("links", []):
                if link.get("rel") == "enclosure":
                    enclosure_url = link.get("href")
                    break

        if not enclosure_url:
            raise ValueError("RSS entry does not contain an audio enclosure")

        # Determine suggested filename/extension
        filename = entry.get("title") or f"episode_{episode_id}"
        parsed = urlparse(enclosure_url)
        extension = os.path.splitext(parsed.path)[1] if parsed.path else ""
        if not extension:
            extension = ".mp3"

        return {
            "audio_url": enclosure_url,
            "episode_id": episode_id,
            "show_id": show_id,
            "suggested_name": filename,
            "extension": extension,
        }


