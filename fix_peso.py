
import os
import sys
sys.stdout.reconfigure(encoding='utf-8')

# The real broken peso signs are literal '?' used as ₱ in these files
# We need to be CAREFUL - only replace '?' when it's used as currency symbol
# Pattern: ?${  or  ?0.00  or  ?{  before a number/variable

import re

fixes = {
    'frontend/dashboard.html': [
        # line 415: Base ?${...} + Extras ?${...}
        (b'Base ?${', b'Base \xe2\x82\xb1${'),
        (b'Extras ?${', b'Extras \xe2\x82\xb1${'),
        # line 419: <span class="price">?${
        (b'class="price">?${', b'class="price">\xe2\x82\xb1${'),
        # Any remaining ?$ patterns for currency
        (b'<span>\u0026#8369;', b'<span>\xe2\x82\xb1'),
        # Refund Pending line with peso
        (b'?${parseFloat(b.refund_amount', b'\xe2\x82\xb1${parseFloat(b.refund_amount'),
        (b'?${parseFloat(b.total_price', b'\xe2\x82\xb1${parseFloat(b.total_price'),
        (b'?${parseFloat(b.base_price', b'\xe2\x82\xb1${parseFloat(b.base_price'),
        (b'?${parseFloat(b.addon_price', b'\xe2\x82\xb1${parseFloat(b.addon_price'),
        (b'?${parseFloat(b.balance_amount', b'\xe2\x82\xb1${parseFloat(b.balance_amount'),
        (b'?${parseFloat(b.downpayment', b'\xe2\x82\xb1${parseFloat(b.downpayment'),
        (b'<span class="price">?', b'<span class="price">\xe2\x82\xb1'),
    ],
    'frontend/payment.html': [
        (b'>?0.00<', b'>\xe2\x82\xb10.00<'),
        (b'"amountDisplay">?', b'"amountDisplay">\xe2\x82\xb1'),
    ],
    'frontend/vehicles.html': [
        (b'`?${e.target.value}`', b'`\xe2\x82\xb1${e.target.value}`'),
        (b"'?${e.target.value}'", b"'\xe2\x82\xb1${e.target.value}'"),
        (b"textContent = `?${", b"textContent = `\xe2\x82\xb1${"),
        (b'priceLabel\').textContent = `?', b"priceLabel').textContent = `\xe2\x82\xb1"),
    ],
}

for fpath, replacements in fixes.items():
    if not os.path.exists(fpath):
        print(f'NOT FOUND: {fpath}')
        continue
    
    with open(fpath, 'rb') as f:
        content = f.read()
    
    original = content
    total = 0
    for old, new in replacements:
        count = content.count(old)
        if count:
            content = content.replace(old, new)
            total += count
            print(f'  Replaced {count}x: {old.decode("utf-8", errors="replace")} -> {new.decode("utf-8", errors="replace")}')
    
    if content != original:
        with open(fpath, 'wb') as f:
            f.write(content)
        print(f'FIXED {total} instances in {fpath}\n')
    else:
        print(f'No changes in {fpath}\n')
