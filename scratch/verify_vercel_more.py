import urllib.request
import time
import re

url = "https://autoride-booking-system.vercel.app/?t="
for i in range(15):
    try:
        t = int(time.time())
        req = urllib.request.Request(url + str(t), headers={'User-Agent': 'Mozilla/5.0', 'Cache-Control': 'no-cache, no-store, must-revalidate'})
        with urllib.request.urlopen(req, timeout=10) as r:
            html = r.read().decode('utf-8', errors='ignore')
            m = re.search(r'name=["\']build-version["\']\s+content=["\']([^"\']+)["\']', html)
            ver = m.group(1) if m else 'unknown'
            print(f"Attempt {i+1}: ver={ver}")
            if ver == '2026.10.19.3':
                print("SUCCESS: v2026.10.19.3 is LIVE!")
                break
    except Exception as e:
        print(f"Attempt {i+1} err: {e}")
    time.sleep(6)
