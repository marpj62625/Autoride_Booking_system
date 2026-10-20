import os

target = "Could not load vehicles"
for root, dirs, files in os.walk('.'):
    if '.git' in root or 'node_modules' in root or '.gradle' in root:
        continue
    for f in files:
        if f.endswith(('.html', '.js', '.py')):
            fpath = os.path.join(root, f)
            try:
                with open(fpath, 'r', encoding='utf-8', errors='ignore') as fp:
                    content = fp.read()
                    if target.lower() in content.lower():
                        print(f"Found in {fpath}")
                        for i, line in enumerate(content.splitlines()):
                            if target.lower() in line.lower():
                                print(f"  Line {i+1}: {line.strip()}")
            except Exception as e:
                pass
