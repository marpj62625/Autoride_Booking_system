import re

with open('C:/Users/patri/OneDrive/Desktop/AutorideSystem2sides/AutorideSystem/backend/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_query = "            SELECT TO_CHAR(b.start_date, 'YYYY-MM-DD') as day, SUM(b.total_price) as amount"
new_query = "            SELECT TO_CHAR(b.start_date, 'YYYY-MM-DD') as day, SUM(b.total_price) as amount, COUNT(b.id) as booking_count"

content = content.replace(old_query, new_query)

with open('C:/Users/patri/OneDrive/Desktop/AutorideSystem2sides/AutorideSystem/backend/app.py', 'w', encoding='utf-8') as f:
    f.write(content)
