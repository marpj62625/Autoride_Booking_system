# -*- coding: utf-8 -*-
"""
Clean fix: replace the entire buildImgUrl function in all JS files
with a version that uses a properly escaped placeholder.
"""

CLEAN_PLACEHOLDER = (
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

CLEAN_FUNC = (
    "function buildImgUrl(path) {\n"
    "  var _noImg = '" + CLEAN_PLACEHOLDER + "';\n"
    "  if (!path) return _noImg;\n"
    "  if (path.startsWith('http')) return path;\n"
    "  return API_BASE.replace('/api', '') + '/' + path;\n"
    "}"
)

files = [
    'frontend/js/app.js',
    'customer_mobile/www/js/app.js',
    'customer_mobile/android/app/src/main/assets/public/js/app.js',
]

import re

# Match the whole buildImgUrl function regardless of what's in it
func_pattern = re.compile(
    r'function buildImgUrl\(path\)\s*\{[^}]+\}',
    re.DOTALL
)

for path in files:
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        src = f.read()

    new_src, n = func_pattern.subn(CLEAN_FUNC, src, count=1)
    if n == 0:
        print(f'WARNING: buildImgUrl not found in {path}')
    else:
        # Also fix any remaining onerror= placeholders that have the broken SVG
        # Match onerror= with broken data URI and replace with clean one
        broken_onerror = re.compile(
            r"(onerror=[\"']this\.onerror=null;\s*this\.src=\\['\"])data:image/svg\+xml[^\\]*?(\\['\"])",
            re.DOTALL
        )
        def fix_onerror(m):
            return m.group(1) + CLEAN_PLACEHOLDER + m.group(2)
        new_src = broken_onerror.sub(fix_onerror, new_src)

        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_src)
        print(f'{path}: OK')

print('Done.')
