with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

def print_exact(start, end, label):
    print(f"--- {label} (lines {start} to {end}) ---")
    for i in range(start-1, end):
        if lines[i].strip():
            print(f"{i+1}: {repr(lines[i])}")

print_exact(21908, 22070, "Verifications start to render")
print_exact(32580, 32665, "UserMgmt setFilter to applyFilters")
