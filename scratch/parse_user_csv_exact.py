import csv, datetime

with open('scratch/oct_dec_calendar.csv', 'r', encoding='utf-8') as f:
    rows = list(csv.reader(f))

for i, row in enumerate(rows):
    if any('2026-10' in c for c in row):
        print(f"Row {i} (Header):", row[:10])
        print(f"Row {i+1} (DOW):", rows[i+1][:20])
        print(f"Row {i+2} (Days):", [(idx, val) for idx, val in enumerate(rows[i+2]) if val])
        for r_j in range(i+3, i+12):
            if r_j < len(rows):
                v_name = rows[r_j][0]
                cells = [(idx, val) for idx, val in enumerate(rows[r_j]) if val and idx > 0]
                print(f"  {v_name}: {cells}")
        break
