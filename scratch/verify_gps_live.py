import urllib.request
import json
import ssl

ctx = ssl.create_default_context()
req = urllib.request.Request('https://autoride-booking-system.vercel.app/api/admin/gps-locations', headers={'User-Agent': 'Mozilla/5.0'})
res = urllib.request.urlopen(req, timeout=10, context=ctx)
data = json.loads(res.read().decode('utf-8'))

print(f"Total fleet vehicles returned: {len(data)}")
for v in data:
    plate = v.get('plate_number')
    if plate in ['DBJ 9483', 'DUY 6527', 'DAT 1396']:
        print(f"Vehicle #{v.get('id')} ({v.get('name')}, {plate}):")
        print(f"  Tracker: {v.get('gps_device_name')}")
        print(f"  Token: {v.get('gps_device_token')}")
        print(f"  Coords: Lat {v.get('latitude')}, Lng {v.get('longitude')}")
        print(f"  Status: {v.get('gps_status')}")
        print(f"  Last Update: {v.get('last_gps_update')}")
