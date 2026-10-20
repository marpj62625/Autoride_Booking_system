import re

with open("admin_app/index.html", "r", encoding="utf-8") as f:
    content = f.read()

# Find dynamic inputs in template strings or innerHTML
dyn_inputs = re.findall(r'<input[^>]*>', content)
print(f"Total HTML inputs in admin_app/index.html: {len(dyn_inputs)}")

# Check any inputs in js strings or functions
js_inputs = re.findall(r'`[^`]*<input[^`]*`', content)
print(f"Template literal chunks with <input: {len(js_inputs)}")

for idx, chunk in enumerate(js_inputs):
    # find all inputs inside chunk
    inps = re.findall(r'<input\s+([^>]+)>', chunk)
    for inp in inps:
        if any(t in inp for t in ['type="hidden"', 'type="checkbox"', 'type="radio"', 'type="file"', 'type="submit"', 'type="button"']):
            continue
        if 'maxlength' not in inp and 'max=' not in inp:
            print(f"Chunk {idx}: {inp[:80]}")
