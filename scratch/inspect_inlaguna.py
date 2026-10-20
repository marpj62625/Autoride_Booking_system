with open('scratch/car_rental_inlaguna.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

import re
scripts = re.findall(r'<script(?:\s+[^>]*)?>(.*?)</script>', text, re.DOTALL | re.IGNORECASE)
with open('scratch/inlaguna_script.js', 'w', encoding='utf-8') as f:
    f.write('\n// NEXT SCRIPT\n'.join(scripts))

print("Extracted inlaguna scripts to scratch/inlaguna_script.js")
