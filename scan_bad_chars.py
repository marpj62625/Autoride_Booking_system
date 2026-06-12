import sys
import os

# Force UTF-8 output
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

fpath = 'customer_mobile/www/js/app.js'

with open(fpath, 'rb') as f:
    raw = f.read()

issues = []
i = 0
while i < len(raw):
    b = raw[i]
    if b > 127:
        try:
            if b >= 0xC0 and b < 0xE0 and i+1 < len(raw):
                raw[i:i+2].decode('utf-8')
                i += 2
                continue
            elif b >= 0xE0 and b < 0xF0 and i+2 < len(raw):
                raw[i:i+3].decode('utf-8')
                i += 3
                continue
            elif b >= 0xF0 and i+3 < len(raw):
                raw[i:i+4].decode('utf-8')
                i += 4
                continue
            else:
                ctx_start = max(0, i-80)
                ctx_end = min(len(raw), i+80)
                ctx = raw[ctx_start:ctx_end].decode('utf-8', errors='replace')
                issues.append((i, b, ctx))
        except:
            ctx_start = max(0, i-80)
            ctx_end = min(len(raw), i+80)
            ctx = raw[ctx_start:ctx_end].decode('utf-8', errors='replace')
            issues.append((i, b, ctx))
    i += 1

print(f'Total bad bytes found: {len(issues)}')
for pos, byte_val, ctx in issues[:20]:
    print(f'\nByte 0x{byte_val:02X} at position {pos}:')
    print(f'Context: {ctx}')
