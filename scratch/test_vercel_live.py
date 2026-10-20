import urllib.request
import json
import ssl

ctx = ssl.create_default_context()

urls = [
    'https://autoride-booking-system.vercel.app/api/vehicles',
    'https://autoride-booking-system.vercel.app/admin_app/index.html',
    'https://autoride-booking-system.vercel.app/api/admin/stats?admin_id=1&period=all'
]

for u in urls:
    try:
        req = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'})
        res = urllib.request.urlopen(req, timeout=10, context=ctx)
        print(f"SUCCESS {u}: HTTP {res.getcode()} (length: {len(res.read())})")
    except Exception as e:
        print(f"FAILED {u}: {e}")
