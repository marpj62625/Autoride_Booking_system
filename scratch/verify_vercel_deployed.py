import urllib.request
import time

url_css = "https://autoride-booking-system.vercel.app/admin_app/desktop.css"
url_html = "https://autoride-booking-system.vercel.app/admin_app/index.html"

print("Checking Vercel live deployment...")
for i in range(12):
    try:
        t = int(time.time())
        req_css = urllib.request.Request(f"{url_css}?t={t}", headers={'User-Agent': 'Mozilla/5.0'})
        req_html = urllib.request.Request(f"{url_html}?t={t}", headers={'User-Agent': 'Mozilla/5.0'})
        
        with urllib.request.urlopen(req_css, timeout=10) as r1:
            css_ok = "min-width: 920px" in r1.read().decode('utf-8', errors='ignore')

        with urllib.request.urlopen(req_html, timeout=10) as r2:
            html_ok = "window.showTab = navTo;" in r2.read().decode('utf-8', errors='ignore')

        if css_ok and html_ok:
            print(f"[PASS] Vercel is serving updated desktop.css and index.html on attempt {i+1}!")
            break
        else:
            print(f"[WAIT] Attempt {i+1}: css_ok={css_ok}, html_ok={html_ok}. Waiting...")
    except Exception as e:
        print(f"[ERROR] Attempt {i+1}: {e}")
    time.sleep(5)
else:
    print("[WARN] Timed out waiting for Vercel deployment.")
