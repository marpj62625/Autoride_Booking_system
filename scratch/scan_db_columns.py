import re

with open('AutorideSystem/backend/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find all CREATE TABLE or ADD COLUMN statements
create_tables = re.findall(r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([a-zA-Z_0-9]+)\s*\((.*?)\);', content, re.DOTALL | re.IGNORECASE)

print(f"Total CREATE TABLE statements found: {len(create_tables)}")
for table_name, body in create_tables:
    cols = re.findall(r'([a-zA-Z_0-9]+)\s+(VARCHAR\(\d+\)|TEXT|NUMERIC\([^\)]+\)|INTEGER|BOOLEAN|DATE|TIMESTAMP[^\,\n]*)', body, re.IGNORECASE)
    print(f"\nTable: {table_name}")
    for col, col_type in cols:
        print(f"  {col}: {col_type}")

# Also check ALTER TABLE ADD COLUMN
add_cols = re.findall(r'ALTER\s+TABLE\s+([a-zA-Z_0-9]+)\s+ADD\s+COLUMN\s+(?:IF\s+NOT\s+EXISTS\s+)?([a-zA-Z_0-9]+)\s+([a-zA-Z0-9_\(\)]+)', content, re.IGNORECASE)
print(f"\nTotal ADD COLUMN statements found: {len(add_cols)}")
for tbl, col, ctype in add_cols:
    print(f"  {tbl}.{col}: {ctype}")
