import sys, psycopg, re
sys.path.insert(0, 'AutorideSystem/backend')
from config import SUPABASE_DB_URL
from psycopg.rows import dict_row

conn = psycopg.connect(conninfo=SUPABASE_DB_URL)
cur = conn.cursor(row_factory=dict_row)

cur.execute("SELECT id, full_name, email, phone FROM users")
all_users = cur.fetchall()
conn.close()

csv_names = [
    'JOEM MARK REYES BULOTANO', 'CHRISTOPHER CATAPANG', 'JAY KARL GONZALES',
    'SUNLINE ELECTRONICS', 'MERRY JOY TORRES', 'MARJHERIE CATAPANG-BERENA',
    'JOSH YOUAYN MALLARI', 'JAYMIE CACHERO', 'SHARMAINE BERNABE RUTAQUIO',
    'HUBBERT SANCHEZ', 'CHERRYLYN GARDIOLA', 'MICHAELLA ANGELA TABLASON',
    'JAY-AR CABILES'
]

print(f"Checking {len(csv_names)} CSV names against all {len(all_users)} registered users in DB:\n")
for cn in csv_names:
    cn_clean = re.sub(r'[^a-zA-Z0-9]', '', cn.lower())
    matches = []
    for u in all_users:
        u_clean = re.sub(r'[^a-zA-Z0-9]', '', (u['full_name'] or '').lower())
        if cn_clean in u_clean or u_clean in cn_clean:
            matches.append(u)
        else:
            w1 = set(cn.lower().split())
            w2 = set((u['full_name'] or '').lower().split())
            overlap = w1.intersection(w2) - {'de', 'delos', 'reyes', 'san', 'angela'}
            if len(overlap) >= 2:
                matches.append(u)
    if matches:
        for m in matches:
            print(f"[MATCH!] CSV '{cn}' -> User #{m['id']}: '{m['full_name']}' ({m['email']})")
    else:
        print(f"[NEW GUEST] '{cn}' -> Walang registered account sa system.")
