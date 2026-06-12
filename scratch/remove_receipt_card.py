with open('admin_mobile/www/index.html', 'rb') as f:
    content = f.read().decode('cp1252')

# ?? 1. Remove the entire paymentProofHtml block (declaration + try/catch) ??
# Find start: "            // Fetch payment proof images for this booking"
# Find end:   the closing "}" of the catch block, then the blank line after
block_start = '            // Fetch payment proof images for this booking\r\n            let paymentProofHtml = \'\';\r\n'
block_end   = '            }\r\n\r\n            const paymentBg'

idx1 = content.find(block_start)
idx2 = content.find(block_end, idx1)

if idx1 < 0 or idx2 < 0:
    print('Block markers not found', idx1, idx2)
    # try LF
    block_start2 = '            // Fetch payment proof images for this booking\n            let paymentProofHtml = \'\';\n'
    idx1 = content.find(block_start2)
    print('LF idx1:', idx1)
else:
    # Remove from start of block up to (but not including) "            const paymentBg"
    content = content[:idx1] + content[idx2 + len('            }\r\n\r\n'):]
    print('Step 1 done - block removed')

# ?? 2. Remove ${paymentProofHtml} line from the template ??
for variant in [
    '                        ${paymentProofHtml}\r\n',
    '                        ${paymentProofHtml}\n',
]:
    if variant in content:
        content = content.replace(variant, '')
        print('Step 2 done - template usage removed')
        break
else:
    print('Step 2: template usage not found')
    idx = content.find('paymentProofHtml')
    print('Remaining occurrences at:', idx)

with open('admin_mobile/www/index.html', 'wb') as f:
    f.write(content.encode('cp1252'))
print('Saved')
