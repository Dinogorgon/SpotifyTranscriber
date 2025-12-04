"""Test Selenium extraction"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import json
import time

episode_id = "5Xb6EpJLvelula9cHaUISg"

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

print("Starting Chrome driver...")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

try:
    url = f"https://open.spotify.com/episode/{episode_id}"
    print(f"Loading {url}")
    driver.get(url)
    
    time.sleep(10)  # Wait longer
    
    # Check page source
    page_source = driver.page_source
    print(f"Page source length: {len(page_source)}")
    print(f"Contains __NEXT_DATA__: {'__NEXT_DATA__' in page_source}")
    print(f"Contains description: {'description' in page_source.lower()}")
    
    # Check for __NEXT_DATA__
    next_data = driver.execute_script("return document.getElementById('__NEXT_DATA__')?.textContent")
    print(f"__NEXT_DATA__ found via JS: {next_data is not None}")
    
    # Try to find it in page source
    if '__NEXT_DATA__' in page_source:
        import re
        match = re.search(r'<script[^>]*id=["\']__NEXT_DATA__["\'][^>]*>(.+?)</script>', page_source, re.DOTALL)
        if match:
            print("Found __NEXT_DATA__ in page source!")
            next_data = match.group(1)
    
    if next_data:
        data = json.loads(next_data)
        print(f"Data keys: {list(data.keys())}")
        
        # Navigate to entity
        entity = None
        if 'props' in data:
            page_props = data['props'].get('pageProps', {})
            if 'state' in page_props:
                state = page_props['state']
                if 'data' in state:
                    data_obj = state['data']
                    if 'entity' in data_obj:
                        entity = data_obj['entity']
        
        if entity:
            print(f"Entity keys: {list(entity.keys())[:20]}")
            
            # Check for description
            desc = entity.get('description') or entity.get('htmlDescription') or entity.get('episodeDescription')
            print(f"Description found: {desc is not None}")
            if desc:
                print(f"Description length: {len(desc)}")
                print(f"Description preview: {desc[:200]}")
            
            # Check for image
            visual = entity.get('visualIdentity', {})
            if visual:
                images = visual.get('image', [])
                print(f"Images found: {len(images)}")
                if images:
                    print(f"First image: {images[0] if isinstance(images[0], str) else images[0].get('url', 'N/A')}")
finally:
    driver.quit()

