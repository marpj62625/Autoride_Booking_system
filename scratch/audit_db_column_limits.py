import re

with open('database/autoride.sql', 'r', encoding='utf-8', errors='ignore') as f:
    sql = f.read()

# Find CREATE TABLE statements and columns
tables = re.findall(r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:`|")?([a-zA-Z0-9_]+)(?:`|")?\s*\((.*?)\)\s*ENGINE', sql, re.DOTALL | re.IGNORECASE)

print(f"Total tables in SQL schema: {len(tables)}")
varchar_cols = []

for table_name, body in tables:
    for line in body.split('\n'):
        line = line.strip().rstrip(',')
        m = re.search(r'(?:`|")?([a-zA-Z0-9_]+)(?:`|")?\s+(VARCHAR|CHAR)\((\d+)\)', line, re.I)
        if m:
            col_name = m.group(1)
            col_type = m.group(2).upper()
            max_len = int(m.group(3))
            varchar_cols.append({
                'table': table_name,
                'column': col_name,
                'type': f"{col_type}({max_len})",
                'max_len': max_len
            })


varchar_cols.sort(key=lambda x: (x['table'], x['column']))
print(f"Total limited VARCHAR/CHAR columns: {len(varchar_cols)}")

with open('scratch/db_varchar_limits.txt', 'w', encoding='utf-8') as out:
    for c in varchar_cols:
        out.write(f"{c['table']:<25} {c['column']:<25} {c['type']:<15}\n")

print("Dumped to scratch/db_varchar_limits.txt")
