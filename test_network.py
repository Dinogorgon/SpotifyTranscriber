"""Test network interception"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from webdriver_manager.chrome import ChromeDriverManager
import json
import time

episode_id = "5Xb6EpJLvelula9cHaUISg"

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-gpu')

# Enable logging
caps = DesiredCapabilities.CHROME
caps['goog:loggingPrefs'] = {'performance': 'ALL'}

print("Starting Chrome driver...")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options, desired_capabilities=caps)

try:
    url = f"https://open.spotify.com/episode/{episode_id}"
    print(f"Loading {url}")
    driver.get(url)
    
    time.sleep(8)
    
    # Get performance logs (network requests)
    logs = driver.get_log('performance')
    print(f"\nNetwork requests: {len(logs)}")
    
    # Look for API calls that might contain description
    for log in logs:
        message = json.loads(log['message'])
        if message['message']['method'] == 'Network.responseReceived':
            response = message['message']['params']['response']
            url_req = response.get('url', '')
            if 'api.spotify.com' in url_req or 'open.spotify.com' in url_req:
                if 'episode' in url_req.lower() or 'description' in url_req.lower():
                    print(f"\nFound relevant request: {url_req}")
                    
                    # Try to get response body
                    try:
                        request_id = message['message']['params']['requestId']
                        response_body = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': request_id})
                        if response_body and 'body' in response_body:
                            body = response_body['body']
                            if 'description' in body.lower():
                                print(f"Response contains description!")
                                # Try to extract
                                try:
                                    data = json.loads(body)
                                    print(f"Response is JSON, keys: {list(data.keys())[:10]}")
                                except:
                                    print(f"Response preview: {body[:500]}")
                    except Exception as e:
                        pass
finally:
    driver.quit()

