
import psycopg2
from config import DB_CONFIG

def check():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("SELECT * FROM admins LIMIT 1")
    colnames = [desc[0] for desc in cur.description]
    print(f"ADMIN COLUMNS: {colnames}")
    cur.close()
    conn.close()

if __name__ == "__main__":
    check()
