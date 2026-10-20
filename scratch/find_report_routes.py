with open("backend/app.py", "r", encoding="utf-8") as f:
    backend_code = f.read()

import re
matches = re.finditer(r"@app\.route\(['\"]([^'\"]*reports[^'\"]*)['\"]", backend_code)
for m in matches:
    lno = backend_code[:m.start()].count('\n') + 1
    print(f"Line {lno}: {m.group(1)}")
