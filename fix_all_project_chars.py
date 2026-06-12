
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

SKIP_DIRS = {'node_modules', '.git', '__pycache__', '.gradle', 'build', '.idea', 'venv'}
EXTENSIONS = ('.js', '.html', '.css', '.py')

# Files to skip (test/scratch files that don't affect production)
SKIP_FILES = {
    'scratch/stats4.json',  # UTF-16 file, skip
}

def fix_file(fpath):
    with open(fpath, 'rb') as f:
        raw = f.read()
    
    original = raw

    # Step 1: Fix the garbage 3-byte sequence [C3][82][C2] before ASCII chars (double-encoded Â)
    raw = raw.replace(b'\xc3\x82\xc2', b'')

    # Step 2: Replace 0x97 (Windows-1252 em dash) with ' - '
    raw = raw.replace(b'\x97', b' - ')

    # Step 3: Replace 0x96 (Windows-1252 en dash) with ' - '
    raw = raw.replace(b'\x96', b' - ')

    # Step 4: Replace 0xB7 (middle dot · used as bullet separator) with ' | '
    raw = raw.replace(b'\xb7', b' | ')

    # Step 5: Replace 0xD7 (multiplication sign ×) with 'x'
    raw = raw.replace(b'\xd7', b'x')

    # Step 6: Fix Latin chars in test HTML (Jose Maria etc.) - replace with ASCII
    raw = raw.replace(b'\xe9', b'e')   # é -> e
    raw = raw.replace(b'\xed', b'i')   # í -> i
    raw = raw.replace(b'\xf3', b'o')   # ó -> o
    raw = raw.replace(b'\xfa', b'u')   # ú -> u
    raw = raw.replace(b'\xe1', b'a')   # á -> a

    # Step 7: Remove any remaining lone invalid high bytes
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
                    # Skip bad byte
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
        
        # Verify
        try:
            raw.decode('utf-8')
            return 'FIXED+CLEAN'
        except UnicodeDecodeError as e:
            return f'FIXED but still has issue: {e}'
    else:
        try:
            raw.decode('utf-8')
            return 'ALREADY_CLEAN'
        except:
            return 'UNCHANGED_BUT_DIRTY'

# Files identified with issues
PROBLEM_FILES = [
    'admin_app/index.html',
    'admin_app/test-enhanced-booking-details.html',
    'admin_app/test-render-popup-chart.html',
    'admin_app/test-task-2-3.html',
    'admin_app/test-task-5-expandable-charts.html',
    'admin_app/tests/cancelled-bookings.test.js',
    'admin_app/tests/customer-profile-preview.test.js',
    'admin_app/tests/expandable-charts.test.js',
    'admin_app/verify-task-5-3.html',
    'admin_mobile/android/app/src/main/assets/public/index.html',
    'admin_mobile/www/index.html',
    'customer_mobile/android/app/src/main/assets/public/js/utils.js',
    'customer_mobile/www/js/utils.js',
    'customer_mobile/tests/utils.test.js',
    'frontend/cordova.js',
    'frontend/dashboard.html',
    'frontend/js/app.js',
    'frontend/js/utils.js',
    'frontend/style.css',
]

print('Fixing broken characters in all affected files...\n')
for fpath in PROBLEM_FILES:
    if os.path.exists(fpath):
        result = fix_file(fpath)
        if result != 'ALREADY_CLEAN':
            print(f'{result}: {fpath}')
    else:
        print(f'NOT FOUND: {fpath}')

print('\nDone!')
