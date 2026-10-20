with open("backend/app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

def print_around(line_no, n=15):
    print(f"\n--- Around Line {line_no} ---")
    start = max(0, line_no - n - 1)
    end = min(len(lines), line_no + n)
    for i in range(start, end):
        print(f"{i+1}: {lines[i]}", end="")

print_around(2639)
print_around(4815)
print_around(5931)
print_around(17234)
