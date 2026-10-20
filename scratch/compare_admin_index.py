with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    text_app = f.read()

with open('admin_mobile/www/index.html', 'r', encoding='utf-8') as f:
    text_mob = f.read()

print("admin_app len:", len(text_app))
print("admin_mobile len:", len(text_mob))

# Check for capacitor or cordova scripts in admin_mobile
for s in ['capacitor.js', 'cordova.js']:
    print(f"in admin_app {s}:", s in text_app)
    print(f"in admin_mobile {s}:", s in text_mob)
