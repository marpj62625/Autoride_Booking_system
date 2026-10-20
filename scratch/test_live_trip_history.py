import urllib.request
import json
import ssl
import time

ctx = ssl.create_default_context()

print('Checking live sync-all...')
try:
    req = urllib.request.Request('https://autoride-booking-system.vercel.app/api/admin/gps/sync-all', headers={'User-Agent': 'Mozilla/5.0'})
    res = urllib.request.urlopen(req, timeout=12, context=ctx)
    print('Sync-all live response:', res.read().decode('utf-8'))
except Exception as e:
    print('Sync-all error:', e)

print('\nChecking history for vehicles 12, 18, 35...')
for vid in [12, 18, 35]:
    try:
        req = urllib.request.Request(f'https://autoride-booking-system.vercel.app/api/vehicles/{vid}/gps-history', headers={'User-Agent': 'Mozilla/5.0'})
        res = urllib.request.urlopen(req, timeout=12, context=ctx)
        data = json.loads(res.read().decode('utf-8'))
        total = data.get('total_points')
        logs = data.get('logs', [])
        print(f"Vehicle #{vid}: total_points = {total}, logs returned = {len(logs)}")
        if logs:
            first = logs[0]
            print(f"  Latest log -> Lat: {first.get('latitude')}, Lng: {first.get('longitude')}, Time: {first.get('created_at_str')}")
    except Exception as e:
        print(f"Vehicle #{vid} history error: {e}")
