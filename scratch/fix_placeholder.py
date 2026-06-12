# -*- coding: utf-8 -*-
"""Replace all via.placeholder.com URLs with a self-hosted SVG data URI."""
import re

# Inline SVG: grey rectangle with car emoji + "No Image" text
# No external request, works offline and on Vercel
PLACEHOLDER = (
    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' "
    "width='400' height='200'%3E"
    "%3Crect width='400' height='200' fill='%23f3f4f6'/%3E"
    "%3Ctext x='200' y='90' font-family='Arial' font-size='36' "
    "text-anchor='middle' fill='%23d1d5db'%3E%F0%9F%9A%97%3C/text%3E"
    "%3Ctext x='200' y='130' font-family='Arial' font-size='13' "
    "text-anchor='middle' fill='%239ca3af'%3ENo Image%3C/text%3E"
    "%3C/svg%3E"
)

files = [
    'frontend/js/app.js',
    'customer_mobile/www/js/app.js',
    'customer_mobile/android/app/src/main/assets/public/js/app.js',
]

pattern = re.compile(r'https://via\.placeholder\.com/[0-9x]+\?text=[A-Za-z+%]+')

for path in files:
    with open(path, 'r', encoding='latin-1') as f:
        src = f.read()
    orig_count = len(pattern.findall(src))
    new_src = pattern.sub(PLACEHOLDER, src)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_src)
    print(f'{path}: replaced {orig_count} placeholder URL(s)')

print('Done.')
