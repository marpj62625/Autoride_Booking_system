with open('frontend/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Let's inspect line 1430 to 1585
print("Lines 1430 to 1585:")
for i in range(1428, 1585):
    print(f"{i+1}: {lines[i]}", end='')
