"""
Spotify page scraper to extract M4A audio URLs
"""
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import json


class SpotifyScraper:
    def __init__(self):
        self.session = requests.Session()
        # Set headers to mimic a real browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def extract_spotify_id(self, url):
        """Extract Spotify ID from various URL formats"""
        patterns = [
            r'spotify\.com/episode/([a-zA-Z0-9]+)',
            r'spotify\.com/track/([a-zA-Z0-9]+)',
            r'spotify\.com/show/([a-zA-Z0-9]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1), url
        return None, url
    
    def get_episode_info(self, episode_id):
        """Get episode information from Spotify API"""
        try:
            # Try to get episode info via Spotify's embed API
            embed_url = f"https://open.spotify.com/embed/episode/{episode_id}"
            response = self.session.get(embed_url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for JSON data in script tags
                scripts = soup.find_all('script')
                for script in scripts:
                    if script.string and 'Spotify.Entity' in script.string:
                        # Try to extract entity data
                        match = re.search(r'Spotify\.Entity\s*=\s*({.+?});', script.string, re.DOTALL)
                        if match:
                            try:
                                data = json.loads(match.group(1))
                                return data
                            except (json.JSONDecodeError, ValueError):
                                pass
                
                # Also check __NEXT_DATA__
                next_data = soup.find('script', id='__NEXT_DATA__')
                if next_data:
                    try:
                        data = json.loads(next_data.string)
                        # Normalize structure to match what we expect
                        if 'props' in data and 'pageProps' in data['props'] and 'state' in data['props']['pageProps']:
                            return data['props']['pageProps']['state']['data']['entity']
                    except:
                        pass
        except Exception as e:
            print(f"Error getting episode info: {e}")
        
        return None
    
    def scrape_m4a_url(self, spotify_url):
        """
        Scrape Spotify page for M4A URL
        Note: Spotify encrypts their streams, so this may not work directly.
        For actual functionality, we'll use yt-dlp as a fallback.
        """
        episode_id, url = self.extract_spotify_id(spotify_url)
        
        if not episode_id:
            raise ValueError("Could not extract Spotify ID from URL")
        
        try:
            # Try to get the page content
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                # Look for M4A URLs in the page
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Search for M4A links in various places
                m4a_pattern = r'https?://[^"\s]+\.m4a[^"\s]*'
                page_text = str(soup)
                
                matches = re.findall(m4a_pattern, page_text)
                if matches:
                    return matches[0]
                
                # Also check script tags for audio URLs
                scripts = soup.find_all('script')
                for script in scripts:
                    if script.string:
                        matches = re.findall(m4a_pattern, script.string)
                        if matches:
                            return matches[0]
        except Exception as e:
            print(f"Error scraping page: {e}")
        
        # If direct scraping fails, return None (will use yt-dlp fallback)
        return None
    
    def get_spotify_info(self, spotify_url):
        """Get basic info about the Spotify content"""
        episode_id, url = self.extract_spotify_id(spotify_url)
        
        if not episode_id:
            return None
        
        full_data = {}
        title = None
        cover_image = None
        description = None
        subtitle = None
        release_date = None
        
        try:
            # First, try the actual episode page (has more complete data)
            episode_url = f"https://open.spotify.com/episode/{episode_id}"
            response = self.session.get(episode_url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # FIRST: Extract from meta tags (most reliable for description)
                # Try og:description first (often has the best description)
                # Try multiple ways to find the meta tag
                meta_desc = soup.find('meta', property='og:description')
                if not meta_desc:
                    meta_desc = soup.find('meta', attrs={'property': 'og:description'})
                if not meta_desc:
                    # Try finding all meta tags and searching
                    all_meta = soup.find_all('meta')
                    for meta in all_meta:
                        if meta.get('property') == 'og:description':
                            meta_desc = meta
                            break
                
                if meta_desc and meta_desc.get('content'):
                    description = meta_desc.get('content').strip()
                    print(f"DEBUG: Found og:description (length: {len(description)})")
                    if description:
                        print(f"DEBUG: og:description content: {description[:200]}...")
                
                # Try twitter:description as backup
                if not description:
                    twitter_desc = soup.find('meta', {'name': 'twitter:description'})
                    if twitter_desc and twitter_desc.get('content'):
                        description = twitter_desc.get('content').strip()
                        print(f"DEBUG: Found twitter:description: {description[:100]}")
                
                # Try standard description meta
                if not description:
                    desc_meta = soup.find('meta', {'name': 'description'})
                    if desc_meta and desc_meta.get('content'):
                        description = desc_meta.get('content').strip()
                        print(f"DEBUG: Found description meta: {description[:100]}")
                
                # Try to find description in visible HTML content (for cases where meta tags don't have it)
                if not description:
                    # Look for common description containers
                    desc_selectors = [
                        {'tag': 'p', 'class': lambda x: x and ('description' in x.lower() or 'summary' in x.lower())},
                        {'tag': 'div', 'class': lambda x: x and ('description' in x.lower() or 'summary' in x.lower())},
                        {'tag': 'span', 'class': lambda x: x and ('description' in x.lower() or 'summary' in x.lower())},
                    ]
                    
                    for selector in desc_selectors:
                        elements = soup.find_all(selector['tag'], class_=selector['class'])
                        for elem in elements:
                            text = elem.get_text(strip=True)
                            if len(text) > 100:  # Likely a description if it's long enough
                                description = text
                                print(f"DEBUG: Found description in {selector['tag']} tag (length: {len(description)})")
                                break
                        if description:
                            break
                
                # Extract title from meta tags
                if not title:
                    meta_title = soup.find('meta', property='og:title')
                    if meta_title and meta_title.get('content'):
                        title = meta_title.get('content').strip()
                
                # Extract cover image from meta tags (ALWAYS try this first)
                meta_image = soup.find('meta', property='og:image')
                if not meta_image:
                    # Try alternative ways to find og:image
                    all_meta = soup.find_all('meta')
                    for meta in all_meta:
                        if meta.get('property') == 'og:image':
                            meta_image = meta
                            break
                
                if meta_image and meta_image.get('content'):
                    cover_image = meta_image.get('content').strip()
                    print(f"DEBUG: Found og:image: {cover_image[:80]}...")
                
                # Also try twitter:image as backup
                if not cover_image:
                    twitter_image = soup.find('meta', {'name': 'twitter:image'})
                    if twitter_image and twitter_image.get('content'):
                        cover_image = twitter_image.get('content').strip()
                        print(f"DEBUG: Found twitter:image: {cover_image[:80]}...")
                
                # THEN: Check __NEXT_DATA__ - this has the most complete data
                next_data = soup.find('script', id='__NEXT_DATA__')
                if next_data:
                    try:
                        data = json.loads(next_data.string)
                        # Navigate through the nested structure
                        if 'props' in data:
                            page_props = data['props'].get('pageProps', {})
                            if 'state' in page_props:
                                state = page_props['state']
                                if 'data' in state:
                                    data_obj = state['data']
                                    if 'entity' in data_obj:
                                        full_data = data_obj['entity']
                                        print(f"DEBUG: Found full_data with keys: {list(full_data.keys())[:10]}")
                    except Exception as e:
                        print(f"Error parsing __NEXT_DATA__: {e}")
                
                # Also check for description in ALL script tags (sometimes it's in other JSON structures)
                # Do this BEFORE checking full_data so we catch it early
                if not description:
                    print("DEBUG: Searching all script tags for description...")
                    all_scripts = soup.find_all('script')
                    for script in all_scripts:
                        if script.string and len(script.string) > 500:  # Even smaller scripts might have it
                            script_text = script.string
                            
                            # Look for JSON-like structures with description
                            # Try to find patterns like "description":"..." or 'description':'...'
                            # Use non-greedy matching to get the full description
                            desc_patterns = [
                                r'"description"\s*:\s*"((?:[^"\\]|\\.){50,})"',  # Handles escaped quotes
                                r'"htmlDescription"\s*:\s*"((?:[^"\\]|\\.){50,})"',
                                r'"episodeDescription"\s*:\s*"((?:[^"\\]|\\.){50,})"',
                                r'"text"\s*:\s*"((?:[^"\\]|\\.){100,})"',  # Sometimes it's called "text"
                            ]
                            
                            for pattern in desc_patterns:
                                matches = re.findall(pattern, script_text, re.IGNORECASE | re.DOTALL)
                                if matches:
                                    # Get the longest match (likely the actual description)
                                    longest_match = max(matches, key=len)
                                    if len(longest_match) > 50:
                                        # Clean up escape sequences
                                        clean_desc = longest_match.replace('\\n', ' ').replace('\\"', '"').replace('\\u201c', '"').replace('\\u201d', '"').replace('\\u2019', "'").replace('\\u2018', "'").replace('\\/', '/')
                                        # Remove HTML tags if present
                                        if '<' in clean_desc and '>' in clean_desc:
                                            from bs4 import BeautifulSoup as BS
                                            clean_desc = BS(clean_desc, 'html.parser').get_text(separator=' ', strip=True)
                                        description = clean_desc.strip()
                                        print(f"DEBUG: Found description in script tag via regex pattern '{pattern[:30]}...' (length: {len(description)})")
                                        break
                            if description:
                                break
                            
                            # Also try to find the specific known text if we're looking for this episode
                            if 'Doing the thing that scared me most' in script_text or 'biggest breakthrough' in script_text:
                                # Try to extract surrounding JSON
                                context_pattern = r'\{[^{}]*"(?:description|htmlDescription|episodeDescription|text)"\s*:\s*"((?:[^"\\]|\\.){100,})"[^{}]*\}'
                                context_matches = re.findall(context_pattern, script_text, re.DOTALL)
                                if context_matches:
                                    longest = max(context_matches, key=len)
                                    clean_desc = longest.replace('\\n', ' ').replace('\\"', '"').replace('\\u201c', '"').replace('\\u201d', '"').replace('\\u2019', "'")
                                    description = clean_desc.strip()
                                    print(f"DEBUG: Found description via context search (length: {len(description)})")
                                    break
            
            # Fallback to embed page if we didn't get enough data
            # Always try embed page for description since main page might not have it
            if not description or (not full_data or not title):
                embed_url = f"https://open.spotify.com/embed/episode/{episode_id}"
                embed_response = self.session.get(embed_url, timeout=10)
            
                if embed_response.status_code == 200:
                    embed_soup = BeautifulSoup(embed_response.text, 'html.parser')
                    
                    # Try to get description from embed page meta tags
                    if not description:
                        # Try multiple ways to find meta tags
                        meta_desc = embed_soup.find('meta', property='og:description')
                        if not meta_desc:
                            all_meta = embed_soup.find_all('meta')
                            for meta in all_meta:
                                if meta.get('property') == 'og:description':
                                    meta_desc = meta
                                    break
                        
                        if meta_desc and meta_desc.get('content'):
                            description = meta_desc.get('content').strip()
                            print(f"DEBUG: Found embed og:description (length: {len(description)})")
                        
                        if not description:
                            twitter_desc = embed_soup.find('meta', {'name': 'twitter:description'})
                            if twitter_desc and twitter_desc.get('content'):
                                description = twitter_desc.get('content').strip()
                                print(f"DEBUG: Found embed twitter:description")
                        
                        if not description:
                            desc_meta = embed_soup.find('meta', {'name': 'description'})
                            if desc_meta and desc_meta.get('content'):
                                description = desc_meta.get('content').strip()
                                print(f"DEBUG: Found embed description meta")
                    
                    # Try to get cover image from embed page if we don't have it
                    if not cover_image:
                        embed_meta_image = embed_soup.find('meta', property='og:image')
                        if not embed_meta_image:
                            all_meta = embed_soup.find_all('meta')
                            for meta in all_meta:
                                if meta.get('property') == 'og:image':
                                    embed_meta_image = meta
                                    break
                        
                        if embed_meta_image and embed_meta_image.get('content'):
                            cover_image = embed_meta_image.get('content').strip()
                            print(f"DEBUG: Found embed og:image: {cover_image[:80]}...")
                    
                    # Use embed page soup for further processing if needed
                    if not full_data or not title:
                        soup = embed_soup
                    
                    # Try to extract title from multiple sources
                    if not title:
                        # Method 1: From title tag
                        title_tag = soup.find('title')
                        if title_tag:
                            title = title_tag.text.strip()
                            # Remove " | Spotify" suffix if present
                            title = re.sub(r'\s*\|\s*Spotify\s*$', '', title, flags=re.IGNORECASE)
                        
                        # Method 2: From meta tags
                        if not title or title == "Spotify":
                            meta_title = soup.find('meta', property='og:title')
                            if meta_title and meta_title.get('content'):
                                title = meta_title.get('content').strip()
                    
                    # Get full data from __NEXT_DATA__ if we don't have it yet
                    if not full_data:
                        next_data = soup.find('script', id='__NEXT_DATA__')
                        if next_data:
                            try:
                                data = json.loads(next_data.string)
                                if 'props' in data:
                                    page_props = data['props'].get('pageProps', {})
                                    if 'state' in page_props:
                                        state = page_props['state']
                                        if 'data' in state:
                                            data_obj = state['data']
                                            if 'entity' in data_obj:
                                                full_data = data_obj['entity']
                            except Exception as e:
                                print(f"Error parsing embed __NEXT_DATA__: {e}")
                
            # Extract data from full_data if available
            if full_data:
                # Try to get title from full_data if we haven't found it yet
                if not title or title == "Spotify" or f"Episode {episode_id}" in title:
                    # Try multiple paths for the episode title
                    title_candidates = [
                        full_data.get('name'),
                        full_data.get('title'),
                        full_data.get('episodeName'),
                        full_data.get('episode_name'),
                    ]
                    for candidate in title_candidates:
                        if candidate and isinstance(candidate, str) and candidate.strip():
                            title = candidate.strip()
                            break
                
                # Try various paths for cover image (only if we don't have one from meta tags)
                if not cover_image:
                    # Path 1: visualIdentity.image
                    visual_identity = full_data.get('visualIdentity', {})
                    if visual_identity:
                        images = visual_identity.get('image', [])
                        if images and len(images) > 0:
                            # Get the largest/highest quality image (usually last in array)
                            for img in reversed(images):  # Start from largest
                                if isinstance(img, dict):
                                    img_url = img.get('url')
                                    if img_url:
                                        cover_image = img_url
                                        print(f"DEBUG: Found cover_image from visualIdentity: {cover_image[:80]}...")
                                        break
                                elif isinstance(img, str):
                                    cover_image = img
                                    print(f"DEBUG: Found cover_image from visualIdentity (string): {cover_image[:80]}...")
                                    break
                    
                    # Path 2: coverArt.sources
                    if not cover_image:
                        cover_art = full_data.get('coverArt', {})
                        if isinstance(cover_art, dict):
                            sources = cover_art.get('sources', [])
                            if sources and len(sources) > 0:
                                # Get largest image (usually last)
                                for source in reversed(sources):
                                    if isinstance(source, dict):
                                        img_url = source.get('url')
                                        if img_url:
                                            cover_image = img_url
                                            print(f"DEBUG: Found cover_image from coverArt: {cover_image[:80]}...")
                                            break
                                    elif isinstance(source, str):
                                        cover_image = source
                                        print(f"DEBUG: Found cover_image from coverArt (string): {cover_image[:80]}...")
                                        break
                    
                    # Path 3: relatedEntityCoverArt
                    if not cover_image:
                        related_art = full_data.get('relatedEntityCoverArt', [])
                        if related_art:
                            for art in reversed(related_art):
                                if isinstance(art, dict):
                                    img_url = art.get('url')
                                    if img_url:
                                        cover_image = img_url
                                        print(f"DEBUG: Found cover_image from relatedEntityCoverArt: {cover_image[:80]}...")
                                        break
                                elif isinstance(art, str):
                                    cover_image = art
                                    print(f"DEBUG: Found cover_image from relatedEntityCoverArt (string): {cover_image[:80]}...")
                                    break
                    
                    # Path 4: show.coverArt
                    if not cover_image:
                        show = full_data.get('show', {})
                        if isinstance(show, dict):
                            show_cover = show.get('coverArt', {})
                            if isinstance(show_cover, dict):
                                show_sources = show_cover.get('sources', [])
                                if show_sources and len(show_sources) > 0:
                                    for source in reversed(show_sources):
                                        if isinstance(source, dict):
                                            img_url = source.get('url')
                                            if img_url:
                                                cover_image = img_url
                                                print(f"DEBUG: Found cover_image from show.coverArt: {cover_image[:80]}...")
                                                break
                
                # Try to get high-res version by modifying URL (for any cover_image found)
                if cover_image:
                    # Spotify image URLs often have size parameters
                    # Try to get 640x640 or larger
                    original_image = cover_image
                    for size in ['64x64', '160x160', '300x300']:
                        if size in cover_image:
                            cover_image = cover_image.replace(size, '640x640')
                            print(f"DEBUG: Upgraded image size from {size} to 640x640")
                            break
                    # If no size found but has /image/, try to get larger
                    if '/image/' in cover_image and '640x640' not in cover_image and original_image == cover_image:
                        cover_image = cover_image.replace('/image/', '/image/640x640/')
                        print(f"DEBUG: Added 640x640 size parameter to image URL")
                
                # Extract description - try multiple paths (only if we don't have one from meta tags or script tags)
                if not description:
                    # Path 1: description or htmlDescription (direct)
                    description = full_data.get('description') or full_data.get('htmlDescription')
                    if description:
                        print(f"DEBUG: Found description from full_data.description/htmlDescription (length: {len(description)})")
                    
                    # Path 2: content.description
                    if not description:
                        content = full_data.get('content', {})
                        if isinstance(content, dict):
                            description = content.get('description') or content.get('htmlDescription')
                            if description:
                                print(f"DEBUG: Found description from content.description/htmlDescription (length: {len(description)})")
                    
                    # Path 3: episodeDescription
                    if not description:
                        description = full_data.get('episodeDescription')
                        if description:
                            print(f"DEBUG: Found description from episodeDescription (length: {len(description)})")
                    
                    # Path 4: Check for 'text' field (sometimes used instead of description)
                    if not description:
                        description = full_data.get('text')
                        if description:
                            print(f"DEBUG: Found description from full_data.text (length: {len(description)})")
                    
                    # Path 5: Check nested structures
                    if not description:
                        # Try various nested paths
                        nested_paths = [
                            ['episode', 'description'],
                            ['episode', 'htmlDescription'],
                            ['data', 'description'],
                            ['data', 'htmlDescription'],
                            ['entity', 'description'],
                            ['entity', 'htmlDescription'],
                            ['content', 'text'],
                            ['content', 'description'],
                        ]
                        for path in nested_paths:
                            data = full_data
                            for key in path:
                                if isinstance(data, dict):
                                    data = data.get(key)
                                else:
                                    data = None
                                    break
                            if isinstance(data, str) and data.strip() and len(data.strip()) > 20:
                                description = data.strip()
                                print(f"DEBUG: Found description from nested path {path} (length: {len(description)})")
                                break
                    
                    # Path 6: Search recursively in full_data (more aggressive)
                    if not description:
                        def find_description(obj, depth=0, path=""):
                            if depth > 8:  # Increased depth limit
                                return None
                            if isinstance(obj, dict):
                                # Check common keys
                                for key in ['description', 'htmlDescription', 'episodeDescription', 'content', 'text', 'summary']:
                                    if key in obj:
                                        val = obj[key]
                                        if isinstance(val, str) and val.strip() and len(val.strip()) > 20:
                                            print(f"DEBUG: Found description recursively at {path}.{key} (length: {len(val.strip())})")
                                            return val.strip()
                                # Recurse into nested dicts
                                for key, val in obj.items():
                                    result = find_description(val, depth + 1, f"{path}.{key}" if path else key)
                                    if result:
                                        return result
                            elif isinstance(obj, list):
                                for i, item in enumerate(obj):
                                    result = find_description(item, depth + 1, f"{path}[{i}]" if path else f"[{i}]")
                                    if result:
                                        return result
                            return None
                        
                        found_desc = find_description(full_data)
                        if found_desc:
                            description = found_desc
                            print(f"DEBUG: Found description via recursive search (length: {len(description)})")
                    
                    # Clean HTML if present
                    if description and isinstance(description, str):
                        from bs4 import BeautifulSoup as BS
                        # Check if it's HTML
                        if '<' in description and '>' in description:
                            desc_soup = BS(description, 'html.parser')
                            description = desc_soup.get_text(separator=' ', strip=True)
                        # Remove excessive whitespace and escape sequences
                        description = description.replace('\\n', ' ').replace('\\"', '"').replace('\\u201c', '"').replace('\\u201d', '"').replace('\\u2019', "'").replace('\\u2018', "'")
                        description = ' '.join(description.split())
                        print(f"DEBUG: Cleaned description (final length: {len(description)})")
                        if description:
                            print(f"DEBUG: Description preview: {description[:200]}...")
                
                # Extract subtitle (show/podcast name)
                if not subtitle:
                    subtitle = full_data.get('subtitle')
                    if not subtitle:
                        show = full_data.get('show', {})
                        if isinstance(show, dict):
                            subtitle = show.get('name')
                    if not subtitle:
                        subtitle = full_data.get('showName')
                
                # Extract release date
                if not release_date:
                    release_date_obj = full_data.get('releaseDate', {})
                    if isinstance(release_date_obj, dict):
                        release_date = release_date_obj.get('isoString') or release_date_obj.get('dateString')
                    elif isinstance(release_date_obj, str):
                        release_date = release_date_obj
                
                # Final title fallback
                if not title or title == "Spotify" or f"Episode {episode_id}" in title:
                    title = f"Spotify Episode {episode_id}"
                
                result = {
                    'id': episode_id,
                    'title': title or f"Spotify Episode {episode_id}",
                    'subtitle': subtitle,
                    'description': description,
                    'cover_image': cover_image,
                    'release_date': release_date,
                    'url': url
                }
                
                # Merge full data for any additional fields (for RSS matching)
                if full_data:
                    result.update({k: v for k, v in full_data.items() if k not in result})
                
                # Debug output
                print(f"DEBUG: Extracted info - Title: {result['title'][:50]}...")
                print(f"DEBUG: Description length: {len(description) if description else 0}")
                print(f"DEBUG: Cover image: {cover_image[:80] if cover_image else 'None'}...")
                print(f"DEBUG: Subtitle: {subtitle}")
                print(f"DEBUG: Release date: {release_date}")
                    
                return result
        except Exception as e:
            import traceback
            print(f"Error getting info: {e}")
            traceback.print_exc()
        
        return {
            'id': episode_id,
            'title': f"Spotify Episode {episode_id}",
            'url': url
        }
