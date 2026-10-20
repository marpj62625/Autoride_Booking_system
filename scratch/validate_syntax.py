import py_compile
import subprocess
import sys
import re

print("Validating syntax across updated files...")

# 1. Check Python syntax
try:
    py_compile.compile('backend/app.py', doraise=True)
    print("[PASS] backend/app.py compiled successfully with no syntax errors.")
except Exception as e:
    print(f"[FAIL] backend/app.py syntax error: {e}")
    sys.exit(1)

# 2. Extract script tags and test with Node.js
def test_html_scripts(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()

    # Find script tags without src
    script_pattern = re.compile(r'<script\b[^>]*>(.*?)</script>', re.DOTALL | re.IGNORECASE)
    scripts = script_pattern.findall(html)
    print(f"Testing {len(scripts)} script blocks in {filepath}...")

    # Write each script block to a temporary file and run node --check
    for idx, s in enumerate(scripts):
        if not s.strip():
            continue
        test_file = f'scratch/test_script_{idx}.js'
        with open(test_file, 'w', encoding='utf-8') as sf:
            sf.write(s)
        res = subprocess.run(['node', '--check', test_file], capture_output=True, text=True)
        if res.returncode != 0:
            print(f"[FAIL] Syntax error in script block {idx} of {filepath}:")
            print(res.stderr)
            sys.exit(1)
        else:
            print(f"  [PASS] Script block {idx} valid.")

test_html_scripts('admin_app/index.html')
test_html_scripts('admin_mobile/www/index.html')
print("[ALL SYNTAX TESTS PASSED!]")
