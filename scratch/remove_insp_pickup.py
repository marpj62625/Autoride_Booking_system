with open('admin_mobile/www/index.html', 'rb') as f:
    content = f.read().decode('cp1252')

# ?? 1. Remove Vehicle Inspections section + mInspForm ??
# From the blank line before <div style="margin-top: 10px;"> (Vehicle Inspections)
# to the end of mInspForm </div>, then blank line
block1_start = '\r\n                    <div style="margin-top: 10px;">\r\n                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">\r\n                            <h3 style="font-size: 1.1rem; color: #0f172a; font-weight: 800;">Vehicle Inspections</h3>'

# Find where this block ends (after mInspForm closing div + blank line)
# mInspForm ends at </div> then blank line then <div style="display: flex; flex-direction: column;
block1_end = '\r\n\r\n                    <div style="display: flex; flex-direction: column; gap: 12px; margin-top: 5px;">'

idx1 = content.find(block1_start)
idx2 = content.find(block1_end, idx1)

if idx1 >= 0 and idx2 >= 0:
    content = content[:idx1] + '\r\n' + content[idx2:]
    print('Step 1 done - Vehicle Inspections + mInspForm removed')
else:
    print('ERROR step 1:', idx1, idx2)
    # Try to find pieces
    idx_a = content.find('Vehicle Inspections</h3>')
    idx_b = content.find('mInspForm')
    print('  Vehicle Inspections at:', idx_a)
    print('  mInspForm at:', idx_b)

# ?? 2. Remove "Mark as Picked Up" button block ??
pickup_block = '                        ${b.status === \'Confirmed\' || b.status === \'Approved\' ? `\r\n                            <button onclick="Bookings.pickup(${b.id})" style="width: 100%; background: #00B14F; color: white; bord'

# Find the full conditional block
idx3 = content.find("${b.status === 'Confirmed' || b.status === 'Approved' ? `")
if idx3 >= 0:
    # Find the end of this conditional: ` : ''}`  followed by newline
    end_pat = "` : ''}\r\n\r\n                        ${b.status === 'Picked Up'"
    idx4 = content.find(end_pat, idx3)
    if idx4 >= 0:
        # Remove from start of this block to end of ` : ''}`
        end_of_block = idx4 + len("` : ''}")
        content = content[:idx3] + content[end_of_block:]
        print('Step 2 done - Mark as Picked Up removed')
    else:
        # Try simpler find
        end_pat2 = "` : ''}\r\n"
        idx4 = content.find(end_pat2, idx3)
        print('  alt end at:', idx4)
        print(repr(content[idx3:idx3+200]))
else:
    print('ERROR step 2: pickup conditional not found')

with open('admin_mobile/www/index.html', 'wb') as f:
    f.write(content.encode('cp1252'))
print('Saved')
