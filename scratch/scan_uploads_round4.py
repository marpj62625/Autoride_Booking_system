import re

with open("backend/app.py", "r", encoding="utf-8") as f:
    backend_content = f.read()

# Check all file uploads
file_uploads = re.findall(r"request\.files\['([^']+)'\]", backend_content)
print(f"Total request.files access points: {set(file_uploads)}")

# Check each file upload site
for fu in set(file_uploads):
    matches = [m.start() for m in re.finditer(rf"request\.files\['{fu}'\]", backend_content)]
    print(f"\nUpload field '{fu}' ({len(matches)} occurrences):")
    for pos in matches:
        line_no = backend_content[:pos].count('\n') + 1
        fn_match = re.search(r"def\s+([a-zA-Z0-9_]+)", backend_content[max(0, pos-2000):pos])
        fn_name = fn_match.group(1) if fn_match else "unknown"
        snippet = backend_content[pos:min(len(backend_content), pos+500)]
        has_ext_check = any(k in snippet for k in ['ALLOWED_EXTENSIONS', 'endswith', 'splitext', 'allowed_file'])
        has_size_check = any(k in snippet for k in ['MAX_CONTENT_LENGTH', 'content_length', 'seek', 'read', 'len('])
        print(f"  Line {line_no} in {fn_name}: ext_check={has_ext_check}, size_check={has_size_check}")
