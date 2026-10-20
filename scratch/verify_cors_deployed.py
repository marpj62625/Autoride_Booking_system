import urllib.request, time

for attempt in range(10):
    time.sleep(4)
    req = urllib.request.Request('https://autoride-booking-system.vercel.app/api/vehicles', method='OPTIONS')
    req.add_header('Origin', 'https://localhost')
    req.add_header('Access-Control-Request-Method', 'GET')
    req.add_header('Access-Control-Request-Headers', 'x-admin-id, content-type')

    try:
        res = urllib.request.urlopen(req, timeout=10)
        allow_headers = res.headers.get('Access-Control-Allow-Headers', '')
        allows = 'x-admin-id' in allow_headers.lower()
        print(f"Attempt {attempt+1}: Status {res.getcode()}, Allows x-admin-id? {allows}")
        if allows:
            print("VERIFIED! Vercel deployed new CORS headers successfully!")
            break
    except Exception as e:
        print(f"Attempt {attempt+1}: Error {e}")
