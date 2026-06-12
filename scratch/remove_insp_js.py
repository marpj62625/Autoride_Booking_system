with open('admin_mobile/www/index.html', 'rb') as f:
    content = f.read().decode('cp1252')

# Remove the "Attach Inspection Events" JS block
block = (
    '\r\n            // Attach Inspection Events\r\n'
    '            const btnAdd = document.getElementById(\'mBtnAddInsp\');\r\n'
    '            const form = document.getElementById(\'mInspForm\');\r\n'
    '            const btnCancel = document.getElementById(\'mBtnCancelInsp\');\r\n'
    '            const btnSave = document.getElementById(\'mBtnSaveInsp\');\r\n'
    '\r\n'
    '            btnAdd.onclick = () => { form.style.display = \'block\'; btnAdd.style.display = \'none\'; };\r\n'
    '            btnCancel.onclick = () => { form.style.display = \'none\'; btnAdd.style.display = \'block\'; };\r\n'
    '            btnSave.onclick = () => this.saveInspection(id);\r\n'
    '\r\n'
    '            this.fetchInspections(id);\r\n'
)

if block in content:
    content = content.replace(block, '\r\n')
    print('Step 1 done - Attach Inspection Events block removed')
else:
    print('Block not found exactly, trying line-by-line...')
    # Find the start
    idx = content.find('// Attach Inspection Events')
    if idx >= 0:
        end_idx = content.find('this.fetchInspections(id);', idx)
        if end_idx >= 0:
            end_idx = content.find('\r\n', end_idx) + 2  # include the newline
            content = content[:idx-12] + content[end_idx:]  # -12 for the leading \r\n            
            print('Step 1 done (fallback) - block removed')
        else:
            print('  Could not find fetchInspections after comment')
    else:
        print('  Could not find comment')

# Remove the two mInspForm/mBtnAddInsp references in saveInspection
old2 = (
    '                    document.getElementById(\'mInspForm\').style.display = \'none\';\r\n'
    '                    document.getElementById(\'mBtnAddInsp\').style.display = \'block\';\r\n'
)
if old2 in content:
    content = content.replace(old2, '')
    print('Step 2 done - mInspForm/mBtnAddInsp in saveInspection removed')
else:
    print('Step 2: pattern not found')

with open('admin_mobile/www/index.html', 'wb') as f:
    f.write(content.encode('cp1252'))
print('Saved')
