import urllib.request

try:
    req = urllib.request.Request(
        'https://autoride-booking-system.vercel.app/',
        headers={'User-Agent': 'Mozilla/5.0'}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
    
    print("Vercel index.html length:", len(html))
    print("desktopCameraModal in Vercel index.html:", "desktopCameraModal" in html)
    print("v2026.10.19.9 in Vercel index.html:", "v2026.10.19.9" in html)
    print("v2026.10.19.8 in Vercel index.html:", "v2026.10.19.8" in html)

    req_js = urllib.request.Request(
        'https://autoride-booking-system.vercel.app/js/app.js',
        headers={'User-Agent': 'Mozilla/5.0'}
    )
    with urllib.request.urlopen(req_js, timeout=10) as resp:
        js = resp.read().decode('utf-8', errors='ignore')
    
    print("Vercel app.js length:", len(js))
    print("openDesktopCameraModal in Vercel app.js:", "openDesktopCameraModal" in js)

except Exception as e:
    print("Error checking Vercel:", e)
