import os

file_path = 'admin_app/index.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Tab switch default date
old_tab_date = """const now = new Date();
                const from = new Date(now.getFullYear(), 0, 1).toISOString().split('T')[0];
                const to = new Date(now.getFullYear(), 11, 31).toISOString().split('T')[0];
                document.getElementById('rptDateFrom').value = from;
                document.getElementById('rptDateTo').value = to;
                Reports.refresh();"""

new_tab_date = """const now = new Date();
                const y = now.getFullYear();
                document.getElementById('rptDateFrom').value = `${y}-01-01`;
                document.getElementById('rptDateTo').value = `${y}-12-31`;
                Reports._filter = 'year';
                Reports.refresh();"""

# 2. Reports object initial _filter
old_filter_def = """_loaded: false,



        _filter: 'month',"""

new_filter_def = """_loaded: false,



        _filter: 'year',"""

# 3. setFilter period calculation
old_set_filter = """const now = new Date();
            let from, to;
            if (period === 'day') {
                from = to = now.toISOString().split('T')[0];
            } else if (period === 'month') {
                from = new Date(now.getFullYear(), now.getMonth(), 1).toISOString().split('T')[0];
                to = new Date(now.getFullYear(), now.getMonth() + 1, 0).toISOString().split('T')[0];
            } else {
                from = new Date(now.getFullYear(), 0, 1).toISOString().split('T')[0];
                to = new Date(now.getFullYear(), 11, 31).toISOString().split('T')[0];
            }"""

new_set_filter = """const now = new Date();
            const y = now.getFullYear();
            const m = String(now.getMonth() + 1).padStart(2, '0');
            const d = String(now.getDate()).padStart(2, '0');
            let from, to;
            if (period === 'day') {
                from = to = `${y}-${m}-${d}`;
            } else if (period === 'month') {
                const lastDay = new Date(y, now.getMonth() + 1, 0).getDate();
                from = `${y}-${m}-01`;
                to = `${y}-${m}-${String(lastDay).padStart(2, '0')}`;
            } else {
                from = `${y}-01-01`;
                to = `${y}-12-31`;
            }"""

# 4 & 5. Chart labels
old_chart_label = "labels: trend.map(t => t.day ? t.day.split('-').slice(1).join('/') : t.label || ''),"
new_chart_label = "labels: trend.map(t => t.label || (t.day ? (t.day.length === 7 ? t.day : t.day.split('-').slice(1).join('/')) : '')),"

# Normalize newlines for matching
normalized_content = content.replace('\r\n', '\n')

print("1. Tab switch match:", old_tab_date in normalized_content)
print("2. Filter def match:", old_filter_def in normalized_content)
print("3. setFilter match:", old_set_filter in normalized_content)
print("4. Chart label count:", normalized_content.count(old_chart_label))

if old_tab_date in normalized_content and old_filter_def in normalized_content and old_set_filter in normalized_content:
    updated = normalized_content.replace(old_tab_date, new_tab_date, 1)
    updated = updated.replace(old_filter_def, new_filter_def, 1)
    updated = updated.replace(old_set_filter, new_set_filter, 1)
    updated = updated.replace(old_chart_label, new_chart_label) # replaces both revenue and bookings chart labels
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(updated)
    print("SUCCESS: admin_app/index.html updated successfully!")
else:
    print("FAIL: One or more targets did not match.")
