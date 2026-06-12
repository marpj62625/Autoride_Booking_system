import os
for path in ['customer_mobile/android/app/src/main/res/values/strings.xml', 'admin_mobile/android/app/src/main/res/values/strings.xml']:
    if os.path.exists(path):
        with open(path, 'r') as f:
            content = f.read()
        
        # Add color element if not present
        if 'name="colorPrimary"' not in content:
            new_color = '\n    <color name="colorPrimary">#00B14F</color>\n</resources>'
            content = content.replace('</resources>', new_color)
            with open(path, 'w') as f:
                f.write(content)
            print(f'Updated {path}')
