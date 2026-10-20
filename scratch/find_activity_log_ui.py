with open('admin_app/index.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer(r'ActivityLog|filterActivity|loadActivityLogs|tab-activity', text)]
print(f"Total occurrences: {len(matches)}")
for idx in matches[:10]:
    start = max(0, idx - 80)
    end = min(len(text), idx + 200)
    print(text[start:end])
    print("="*40)
