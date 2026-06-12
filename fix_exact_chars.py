
# The pattern is [C3][82][C2]- which are 3 garbage bytes before a hyphen
# C3 82 = Â in UTF-8, then C2 alone (invalid) before -
# These should just be ' -' (space-hyphen)
# The sequence bytes are: 0xC3 0x82 0xC2 0x2D -> should be ' -'

files = [
    'customer_mobile/www/js/app.js',
    'customer_mobile/android/app/src/main/assets/public/js/app.js',
]

for fpath in files:
    with open(fpath, 'rb') as f:
        raw = f.read()
    
    original = raw
    
    # Replace the garbage sequence [C3][82][C2][2D] with just ' -'
    raw = raw.replace(b'\xc3\x82\xc2\x2d', b' -')
    
    # Also catch any remaining lone 0xC2 before regular ASCII
    import re
    # Replace 0xC2 followed by any non-continuation byte (not 0x80-0xBF)
    result = bytearray()
    i = 0
    while i < len(raw):
        b = raw[i]
        if b == 0xC2 and i+1 < len(raw):
            next_b = raw[i+1]
            if not (0x80 <= next_b <= 0xBF):
                # Invalid sequence - skip the 0xC2
                i += 1
                continue
        result.append(b)
        i += 1
    raw = bytes(result)
    
    if raw != original:
        with open(fpath, 'wb') as f:
            f.write(raw)
        print(f'Fixed {fpath}')
    
    # Verify
    try:
        raw.decode('utf-8')
        print(f'  VERIFIED CLEAN: {fpath}')
    except UnicodeDecodeError as e:
        print(f'  Still has issue: {e}')
