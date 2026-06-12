# -*- coding: utf-8 -*-
"""
Fix the broken SVG data URI placeholder in JS files.
The previous version had unescaped single quotes that broke JS string literals.
Replace with a clean version using %27 for single quotes and no quotes in SVG attrs.
"""
import re

# Clean SVG - use double-quoted attributes, all special chars URL-encoded
# Single quotes encoded as %27 so they don't break JS string literals
PLACEHOLDER = (
    "data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22"
    "%20width%3D%22400%22%20height%3D%22200%22%3E"
    "%3Crect%20width%3D%22400%22%20height%3D%22200%22%20fill%3D%22%23f3f4f6%22%2F%3E"
    "%3Ctext%20x%3D%22200%22%20y%3D%2285%22%20font-family%3D%22Arial%22"
    "%20font-size%3D%2240%22%20text-anchor%3D%22middle%22"
    "%20fill%3D%22%23d1d5db%22%3E%F0%9F%9A%97%3C%2Ftext%3E"
    "%3Ctext%20x%3D%22200%22%20y%3D%22130%22%20font-family%3D%22Arial%22"
    "%20font-size%3D%2214%22%20text-anchor%3D%22middle%22"
    "%20fill%3D%22%239ca3af%22%3ENo%20Image%3C%2Ftext%3E"
    "%3C%2Fsvg%3E"
)

files = [
    'frontend/js/app.js',
    'customer_mobile/www/js/app.js',
    'customer_mobile/android/app/src/main/assets/public/js/app.js',
]

# Pattern matches the broken placeholder (starts with data:image/svg+xml,)
# It may span to different ending points due to the broken string - match the whole mess
broken_pattern = re.compile(
    r"data:image/svg\+xml,%3Csvg xmlns='http://www\.w3\.org/2000/svg'[^']*'",
    re.DOTALL
)

for path in files:
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        src = f.read()

    # Count occurrences of the broken placeholder
    broken_count = len(broken_pattern.findall(src))

    # Also simple replace for the known exact string
    # Use a direct string replace approach - find 'data:image/svg+xml,...' blocks
    # Strategy: replace everything from data:image/svg+xml to the next unescaped '
    # that ends the JS string

    # Simple approach: replace the known bad prefix
    bad_prefix = "data:image/svg+xml,%3Csvg xmlns="
    # Find all occurrences and replace up to the closing quote
    result = []
    i = 0
    replacements = 0
    while i < len(src):
        idx = src.find(bad_prefix, i)
        if idx == -1:
            result.append(src[i:])
            break
        result.append(src[i:idx])
        # Find the end of this JS string (the closing single quote after the SVG)
        # The string started with ' before data:, so find the next unescaped '
        # after the SVG content ends with %3E
        end_marker = src.find("'", idx + len(bad_prefix))
        if end_marker == -1:
            result.append(src[idx:])
            i = len(src)
        else:
            result.append(PLACEHOLDER)
            i = end_marker + 1  # skip the closing quote - we DON'T consume it
            # Actually the closing quote is needed, step back
            i = end_marker  # leave the closing quote in place
            replacements += 1
        # Safety break
        if replacements > 20:
            break

    src = ''.join(result)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(src)
    print(f'{path}: {replacements} replacement(s)')

print('Done.')
