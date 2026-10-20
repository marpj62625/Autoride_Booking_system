import sys

sys.stdout.reconfigure(encoding='utf-8')

# 1. Update backend/app.py
with open('backend/app.py', 'r', encoding='utf-8') as f:
    backend_content = f.read()

old_cors = '''CORS(app, resources={r"/*": {

    "origins": "*",

    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],

    "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"]

}})'''

new_cors = '''CORS(app, resources={r"/*": {
    "origins": "*",
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    "allow_headers": ["Content-Type", "Authorization", "X-Requested-With", "X-Admin-Id", "x-admin-id", "X-User-Id", "x-user-id", "Accept", "Origin"]
}})

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, X-Admin-Id, x-admin-id, X-User-Id, x-user-id, Accept, Origin'
    return response'''

assert old_cors in backend_content, "Error: old_cors not found in backend/app.py!"
backend_content = backend_content.replace(old_cors, new_cors, 1)

with open('backend/app.py', 'w', encoding='utf-8') as f:
    f.write(backend_content)
print("Updated backend/app.py CORS headers successfully.")

# 2. Update admin_app/index.html and admin_mobile/www/index.html
with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    admin_content = f.read()

old_api_base = '''    // API URL: auto-detect - works on Vercel (web) and Android APK (Capacitor)
    const API_BASE = (function() {
        // Always use production URL on native Capacitor APK (window.Capacitor.isNative is true on real device)
        if (window.Capacitor && window.Capacitor.isNative) {
            return 'https://autoride-booking-system.vercel.app';
        }
        // Capacitor serves from capacitor:// protocol on some versions
        if (window.location.protocol === 'capacitor:') {
            return 'https://autoride-booking-system.vercel.app';
        }
        // Capacitor on Android serves from localhost - force production
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            // Check if running as installed APK (not local web dev server)
            if (window.Capacitor) {
                return 'https://autoride-booking-system.vercel.app';
            }
            return 'http://localhost:5000';
        }
        // Web: Vercel or HTTPS - use origin
        if (window.location.hostname.includes('vercel.app') || window.location.protocol === 'https:') {
            return window.location.origin;
        }
        // Fallback
        return 'https://autoride-booking-system.vercel.app';
    })();

    const API_URL = API_BASE + '/api';'''

new_api_base = '''    // API URL: auto-detect - works on Vercel (web) and Android APK (Capacitor)
    const API_BASE = (function() {
        // 1. Mobile devices / Android APK / Capacitor
        const isMobileOrCap = (typeof window.Capacitor !== 'undefined' && window.Capacitor) ||
                              window.location.protocol === 'capacitor:' ||
                              window.location.protocol === 'file:' ||
                              /android|iphone|ipad|ipod/i.test(navigator.userAgent || '');
        if (isMobileOrCap) {
            return 'https://autoride-booking-system.vercel.app';
        }

        // 2. Local PC development (only if explicitly running on port 5000)
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            if (window.location.port === '5000') {
                return 'http://localhost:5000';
            }
            return 'https://autoride-booking-system.vercel.app';
        }

        // 3. Web: Vercel or HTTPS
        if (window.location.hostname.includes('vercel.app') || window.location.protocol === 'https:') {
            return window.location.origin;
        }

        // 4. Default Fallback
        return 'https://autoride-booking-system.vercel.app';
    })();

    const API_URL = API_BASE + '/api';
    window.API_BASE = API_BASE;
    window.API_URL = API_URL;'''

assert old_api_base in admin_content, "Error: old_api_base not found in admin_app/index.html!"
admin_content = admin_content.replace(old_api_base, new_api_base, 1)

with open('admin_app/index.html', 'w', encoding='utf-8') as f:
    f.write(admin_content)
print("Updated admin_app/index.html successfully.")

with open('admin_mobile/www/index.html', 'w', encoding='utf-8') as f:
    f.write(admin_content)
print("Updated admin_mobile/www/index.html successfully.")

# 3. Update admin_mobile/capacitor.config.json
new_cap_config = '''{
  "appId": "com.autoride.admin",
  "appName": "Autoride Admin",
  "webDir": "www",
  "server": {
    "cleartext": true,
    "androidScheme": "https",
    "iosScheme": "https",
    "allowNavigation": [
      "autoride-booking-system.vercel.app",
      "https://autoride-booking-system.vercel.app",
      "fydfsgjrlowrrtlmefwq.supabase.co",
      "https://fydfsgjrlowrrtlmefwq.supabase.co",
      "*.googleapis.com",
      "*.google.com"
    ]
  },
  "plugins": {
    "PushNotifications": {
      "presentationOptions": [
        "badge",
        "sound",
        "alert"
      ]
    }
  }
}
'''
with open('admin_mobile/capacitor.config.json', 'w', encoding='utf-8') as f:
    f.write(new_cap_config)
print("Updated admin_mobile/capacitor.config.json successfully.")
