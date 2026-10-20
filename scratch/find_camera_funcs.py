with open('frontend/js/app.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'Camera.getPhoto' in l or 'pickProfilePicture' in l or 'captureLicenseWithCamera' in l or 'addInspectionPhoto' in l:
        print(f'Line {i+1}: {l.strip()}')
        for j in range(max(0, i-5), min(len(lines), i+30)):
            if lines[j].strip().startswith('function ') or 'Camera' in lines[j]:
                print(f'   {j+1}: {lines[j].strip()}')
