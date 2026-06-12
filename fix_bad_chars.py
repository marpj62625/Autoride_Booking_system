
# Fix the single bad byte 0x97 (Windows-1252 em dash) in app.js
# Replace it with proper UTF-8 em dash (—) or a simple hyphen (-)

for fpath in ['customer_mobile/www/js/app.js', 'customer_mobile/android/app/src/main/assets/public/js/app.js']:
    with open(fpath, 'rb') as f:
        raw = f.read()

    # Replace 0x97 (Windows-1252 em dash) with UTF-8 hyphen-minus (-)
    fixed = raw.replace(b'\x97', b'-')

    if fixed != raw:
        with open(fpath, 'wb') as f:
            f.write(fixed)
        count = raw.count(b'\x97')
        print(f'Fixed {count} bad byte(s) in {fpath}')
    else:
        print(f'No bad bytes found in {fpath}')
