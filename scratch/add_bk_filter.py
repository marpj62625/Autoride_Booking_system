with open('admin_mobile/www/index.html', 'rb') as f:
    content = f.read().decode('cp1252')

# 1. Add _filter property to Bookings object
old_data = '    const Bookings = {\r\n        data: [],'
new_data = '    const Bookings = {\r\n        data: [],\r\n        _filter: \'all\','
content = content.replace(old_data, new_data, 1)
print('Step 1: _filter property added')

# 2. Replace render() to apply filtering + add setFilter method
old_render = (
    '        render() {\r\n'
    '            const list = document.getElementById(\'bookingsList\');\r\n'
    '            if (this.data.length === 0) {'
)

new_render = (
    '        setFilter(filter, btn) {\r\n'
    '            this._filter = filter;\r\n'
    '            document.querySelectorAll(\'.bk-chip\').forEach(b => {\r\n'
    '                const active = b.dataset.filter === filter;\r\n'
    '                b.style.background  = active ? \'var(--primary)\' : \'var(--surface-container)\';\r\n'
    '                b.style.borderColor = active ? \'var(--primary)\' : \'var(--border)\';\r\n'
    '                b.style.color       = active ? \'white\' : \'var(--text-main)\';\r\n'
    '                b.classList.toggle(\'bk-chip-active\', active);\r\n'
    '            });\r\n'
    '            this.render();\r\n'
    '        },\r\n'
    '        render() {\r\n'
    '            const list = document.getElementById(\'bookingsList\');\r\n'
    '            // Apply status filter\r\n'
    '            const statusMap = { pending: \'Pending\', confirmed: \'Confirmed\', approved: \'Approved\', picked_up: \'Picked Up\', completed: \'Completed\', cancelled: \'Cancelled\' };\r\n'
    '            const filtered = this._filter === \'all\' ? this.data : this.data.filter(b => { const s = (b.status||\'\').toLowerCase().replace(\' \', \'_\'); return s === this._filter || (b.status||\'\') === statusMap[this._filter]; });\r\n'
    '            if (filtered.length === 0) {'
)

if old_render in content:
    content = content.replace(old_render, new_render, 1)
    print('Step 2: render() updated with filter + setFilter added')
else:
    print('ERROR: render pattern not found')

# 3. Replace the this.data.map( with filtered.map( in render
old_map = '            list.innerHTML = this.data.map(b => `'
new_map = '            list.innerHTML = filtered.map(b => `'
if old_map in content:
    content = content.replace(old_map, new_map, 1)
    print('Step 3: this.data.map -> filtered.map')
else:
    print('ERROR: map pattern not found')

with open('admin_mobile/www/index.html', 'wb') as f:
    f.write(content.encode('cp1252'))
print('Saved')
