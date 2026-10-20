with open('backend/app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

keywords = ['Maintenance', 'Repair', 'Sold', 'Service', 'Unavailable']
for i, line in enumerate(lines):
    if any(k in line for k in keywords) and ('status' in line.lower() or 'veh' in line.lower()):
        print(f"{i+1}: {line.strip()[:110]}")
