import shutil

with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

dup_str = """            const statusMap = { pending: 'Pending', confirmed: 'Confirmed', approved: 'Approved', picked_up: 'Picked Up', completed: 'Completed', cancelled: 'Cancelled' };



            // Apply status filter
            const statusMap = { pending: 'Pending', confirmed: 'Confirmed', approved: 'Approved', picked_up: 'Picked Up', completed: 'Completed', cancelled: 'Cancelled' };"""

clean_str = """            // Apply status filter
            const statusMap = { pending: 'Pending', confirmed: 'Confirmed', approved: 'Approved', picked_up: 'Picked Up', completed: 'Completed', cancelled: 'Cancelled' };"""

if dup_str in text:
    text = text.replace(dup_str, clean_str)
    print("[OK] Removed duplicate statusMap declaration.")
else:
    # try with standard single newlines or regex
    import re
    text = re.sub(
        r"const statusMap = \{[^;]+\};\s*// Apply status filter\s*const statusMap = \{[^;]+\};",
        clean_str,
        text
    )
    print("[OK] Replaced via regex.")

with open('admin_app/index.html', 'w', encoding='utf-8') as f:
    f.write(text)

shutil.copyfile('admin_app/index.html', 'admin_mobile/www/index.html')
print("[OK] Synchronized to admin_mobile/www/index.html.")
