
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

def fix_file(fpath):
    with open(fpath, 'rb') as f:
        raw = f.read()
    
    original = raw

    # Common Windows-1252 bad bytes -> ASCII replacements
    raw = raw.replace(b'\xc3\x82\xc2', b'')   # garbage triple sequence
    raw = raw.replace(b'\x97', b' - ')          # em dash
    raw = raw.replace(b'\x96', b' - ')          # en dash
    raw = raw.replace(b'\xb7', b' | ')          # middle dot
    raw = raw.replace(b'\xd7', b'x')            # multiplication sign

    # Remove any remaining lone invalid high bytes
    result = bytearray()
    i = 0
    while i < len(raw):
        b = raw[i]
        if b > 127:
            try:
                if 0xC0 <= b < 0xE0 and i+1 < len(raw):
                    seq = raw[i:i+2]
                    seq.decode('utf-8')
                    result.extend(seq)
                    i += 2
                    continue
                elif 0xE0 <= b < 0xF0 and i+2 < len(raw):
                    seq = raw[i:i+3]
                    seq.decode('utf-8')
                    result.extend(seq)
                    i += 3
                    continue
                elif 0xF0 <= b and i+3 < len(raw):
                    seq = raw[i:i+4]
                    seq.decode('utf-8')
                    result.extend(seq)
                    i += 4
                    continue
                else:
                    i += 1
                    continue
            except UnicodeDecodeError:
                i += 1
                continue
        result.append(b)
        i += 1

    raw = bytes(result)

    if raw != original:
        with open(fpath, 'wb') as f:
            f.write(raw)
        try:
            raw.decode('utf-8')
            return 'FIXED+CLEAN'
        except UnicodeDecodeError as e:
            return f'FIXED but issue remains: {e}'
    return 'ALREADY_CLEAN'

# Remaining files with issues (skip scratch/ and iOS as they don't affect production)
REMAINING = [
    'admin_app/booking-management.css',
    'admin_app/shared-enhancements.css',
    'admin_app/shared-utils.js',
    'admin_mobile/ios/App/App/public/index.html',
]

print('Fixing remaining files...\n')
for fpath in REMAINING:
    if os.path.exists(fpath):
        result = fix_file(fpath)
        print(f'{result}: {fpath}')
    else:
        print(f'NOT FOUND: {fpath}')

print('\nDone!')
