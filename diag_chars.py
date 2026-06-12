
# Read raw bytes and find EXACTLY what follows 0xC2 at position 148
fpath = 'customer_mobile/www/js/app.js'

with open(fpath, 'rb') as f:
    raw = f.read()

# Show all occurrences of 0xC2 and what byte follows it
print(f'File size: {len(raw)} bytes')
print()

i = 0
bad_positions = []
while i < len(raw):
    b = raw[i]
    if b == 0xC2:
        next_b = raw[i+1] if i+1 < len(raw) else None
        two_bytes = raw[i:i+2]
        try:
            decoded = two_bytes.decode('utf-8')
            # Valid UTF-8 - skip
            pass
        except:
            ctx = raw[max(0,i-60):i+60]
            ctx_str = ''.join(chr(c) if 32 <= c < 127 else f'[{c:02X}]' for c in ctx)
            bad_positions.append((i, next_b, ctx_str))
    i += 1

print(f'Found {len(bad_positions)} invalid 0xC2 bytes:')
for pos, next_b, ctx in bad_positions:
    print(f'  pos={pos}, next=0x{next_b:02X} ({chr(next_b) if 32<=next_b<127 else "?"})')
    print(f'  Context: {ctx}')
    print()
