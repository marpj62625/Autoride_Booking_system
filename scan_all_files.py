
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Scan ALL source files across the entire project
EXTENSIONS = ('.js', '.html', '.css', '.py', '.json')
SKIP_DIRS = {'node_modules', '.git', '__pycache__', '.gradle', 'build', '.idea', 'venv'}

results = {}

for root, dirs, files in os.walk('.'):
    # Skip heavy/irrelevant directories
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
    
    for fname in files:
        if not fname.endswith(EXTENSIONS):
            continue
        fpath = os.path.join(root, fname)
        
        try:
            with open(fpath, 'rb') as f:
                raw = f.read()
        except Exception:
            continue
        
        bad_bytes = []
        i = 0
        while i < len(raw):
            b = raw[i]
            if b > 127:
                try:
                    if 0xC0 <= b < 0xE0 and i+1 < len(raw):
                        seq = raw[i:i+2]
                        seq.decode('utf-8')
                        i += 2
                        continue
                    elif 0xE0 <= b < 0xF0 and i+2 < len(raw):
                        seq = raw[i:i+3]
                        seq.decode('utf-8')
                        i += 3
                        continue
                    elif 0xF0 <= b and i+3 < len(raw):
                        seq = raw[i:i+4]
                        seq.decode('utf-8')
                        i += 4
                        continue
                    else:
                        ctx = raw[max(0,i-50):i+50].decode('utf-8', errors='replace')
                        bad_bytes.append((i, b, ctx))
                except UnicodeDecodeError:
                    ctx = raw[max(0,i-50):i+50].decode('utf-8', errors='replace')
                    bad_bytes.append((i, b, ctx))
            i += 1
        
        if bad_bytes:
            results[fpath] = bad_bytes

print(f'Found broken characters in {len(results)} files:\n')
for fpath, issues in sorted(results.items()):
    print(f'FILE: {fpath}  ({len(issues)} bad bytes)')
    for pos, byte_val, ctx in issues[:3]:
        clean_ctx = ctx.replace('\r','').replace('\n',' ')
        print(f'  pos={pos} byte=0x{byte_val:02X}  ...{clean_ctx}...')
    if len(issues) > 3:
        print(f'  ... and {len(issues)-3} more')
    print()
