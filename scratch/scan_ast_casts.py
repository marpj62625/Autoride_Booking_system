import ast
import re

with open("backend/app.py", "r", encoding="utf-8") as f:
    code = f.read()

tree = ast.parse(code)

findings = []

for node in ast.walk(tree):
    # Check for calls like int(...), float(...) where argument is not surrounded by try/except
    # or inside function without try/except
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ('int', 'float'):
        # Check if argument is a Call to .get()
        if node.args and isinstance(node.args[0], ast.Call) and isinstance(node.args[0].func, ast.Attribute) and node.args[0].func.attr == 'get':
            findings.append((node.lineno, node.func.id, ast.unparse(node.args[0])))

print(f"Total direct int()/float() on .get(): {len(findings)}")
for lineno, fn, arg in findings:
    # check if this line is in a try block
    print(f"Line {lineno}: {fn}({arg})")
