import sys

path = r'c:\Users\patri\OneDrive\Desktop\AutorideSystem2side\AutorideSystem\frontend\vehicles.html'

with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Duplication starts at line 30 (index 29)
# We want to remove from index 29 (line 30) up to the second occurrence of similar tags or just a fixed count.
# Better: detect the second index of '<!DOCTYPE html>' or similar and remove between them.

# Actually, the audit showed duplication from line 27 to somewhere around 130.
# I'll just remove lines 30 to 57 precisely as identified in the view_file.

# Index 29 is line 30.
# Index 56 is line 57.
# We remove lines 30 through 57 (inclusive).
new_lines = lines[:29] + lines[57:]

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Duplicates removed from vehicles.html")
