
# Fix all bad/broken characters in the JS files
# The issue is Windows-1252 special characters mixed in a UTF-8 file
# C2 + 80-9F range = Windows-1252 "smart" characters that render as garbage

# Windows-1252 to proper UTF-8 replacements
REPLACEMENTS = {
    b'\xc2\x96': b'-',        # en dash -> hyphen
    b'\xc2\x97': b'-',        # em dash -> hyphen
    b'\xc2\x91': b"'",        # left smart quote -> apostrophe
    b'\xc2\x92': b"'",        # right smart quote -> apostrophe
    b'\xc2\x93': b'"',        # left double quote -> quote
    b'\xc2\x94': b'"',        # right double quote -> quote
    b'\xc2\x80': b'',         # euro sign (remove if looks broken)
    b'\xc2\xa0': b' ',        # non-breaking space -> regular space
    b'\xc2\x85': b'...',      # ellipsis -> dots
    b'\x97':     b'-',        # raw 0x97 em dash -> hyphen
    b'\x96':     b'-',        # raw 0x96 en dash -> hyphen
    b'\x91':     b"'",
    b'\x92':     b"'",
    b'\x93':     b'"',
    b'\x94':     b'"',
}

files = [
    'customer_mobile/www/js/app.js',
    'customer_mobile/android/app/src/main/assets/public/js/app.js',
]

for fpath in files:
    with open(fpath, 'rb') as f:
        content = f.read()
    
    original = content
    total_fixes = 0
    
    for bad, good in REPLACEMENTS.items():
        count = content.count(bad)
        if count:
            content = content.replace(bad, good)
            total_fixes += count
            print(f'  Replaced {count}x {bad.hex()} in {fpath}')
    
    if content != original:
        with open(fpath, 'wb') as f:
            f.write(content)
        print(f'FIXED {total_fixes} bad chars in {fpath}')
    else:
        print(f'No changes needed in {fpath}')
    
    # Final verify
    try:
        content.decode('utf-8')
        print(f'  VERIFIED: File is clean UTF-8!')
    except UnicodeDecodeError as e:
        print(f'  WARNING: Still has encoding issue: {e}')
