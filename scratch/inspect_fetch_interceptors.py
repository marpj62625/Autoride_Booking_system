with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'window.fetch =' in line or 'window.fetch=' in line:
        print(f"\n--- Found window.fetch at line {i+1} ---")
        for j in range(max(0, i-5), min(len(lines), i+35)):
            print(f"{j+1}: {lines[j]}", end='')
