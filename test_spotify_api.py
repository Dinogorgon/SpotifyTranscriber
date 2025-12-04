"""Try Spotify API endpoints"""
import requests
import json

episode_id = "5Xb6EpJLvelula9cHaUISg"

# Try various Spotify endpoints
endpoints = [
    f"https://api.spotify.com/v1/episodes/{episode_id}",
    f"https://open.spotify.com/oembed?url=https://open.spotify.com/episode/{episode_id}",
    f"https://embed.spotify.com/oembed/?url=https://open.spotify.com/episode/{episode_id}",
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
}

for endpoint in endpoints:
    print(f"\n=== Trying {endpoint} ===")
    try:
        r = requests.get(endpoint, headers=headers, timeout=10)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            try:
                data = r.json()
                print(f"Response keys: {list(data.keys())[:10]}")
                if 'description' in data:
                    print(f"Description found: {data['description'][:200]}")
                if 'html' in data:
                    print(f"HTML length: {len(data['html'])}")
            except:
                print(f"Response: {r.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")

