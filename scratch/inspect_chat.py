with open('AutorideSystem/backend/app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if '/chat' in l or 'def chat' in l or ('messages' in l and 'route' in l):
        print(f"Line {i+1}: {l.strip()}")
        for j in range(i, min(len(lines), i+15)):
            print(f"  {j+1}: {lines[j].strip()}")
        print('-'*30)
