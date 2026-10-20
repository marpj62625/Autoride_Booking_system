with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

def print_exact(start, end, label):
    print(f"--- {label} (lines {start} to {end}) ---")
    for i in range(start-1, end):
        print(f"{i+1}: {repr(lines[i])}")

print_exact(6329, 6355, "tabNew Header")
print_exact(6491, 6515, "tabAll Header")
print_exact(10048, 10065, "umSearch Header")
print_exact(18458, 18465, "Bookings decl")
print_exact(18685, 18712, "renderNew filter")
print_exact(18968, 18980, "render filter")
