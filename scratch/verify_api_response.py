import sys
sys.path.append('backend')
import psycopg
from config import SUPABASE_DB_URL
from psycopg.rows import dict_row

conn = psycopg.connect(conninfo=SUPABASE_DB_URL)
cur = conn.cursor(row_factory=dict_row)

for aid in [20, 24]:
    cur.execute("""
        SELECT id, title, message, type, is_read, created_at 
        FROM notifications 
        WHERE user_id = %s AND type LIKE 'admin_%%' 
        ORDER BY created_at DESC 
        LIMIT 5
    """, (aid,))
    rows = cur.fetchall()
    print(f"\n=== ADMIN {aid} NOTIFICATIONS (TOP 5) ===")
    for r in rows:
        print(f"[{r['id']}] {'[UNREAD]' if not r['is_read'] else '[READ]'} {r['created_at'].isoformat()} | {r['type']}")
        print(f"     Title: {r['title']}")
        print(f"     Message: {r['message']}")

cur.close()
conn.close()
