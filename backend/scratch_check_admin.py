import psycopg
from psycopg.rows import dict_row

conn_str = "postgresql://postgres.fydfsgjrlowrrtlmefwq:Autoride777%25*@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres"

def check_admin():
    try:
        with psycopg.connect(conn_str, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, email, password, role, is_verified FROM users WHERE email = 'superadmin@autoride.com'")
                user = cur.fetchone()
                if user:
                    print(f"FOUND ADMIN: {user}")
                else:
                    print("ADMIN NOT FOUND")
                    # List all admins
                    cur.execute("SELECT email, role, is_verified FROM users WHERE role IN ('admin', 'super_admin')")
                    admins = cur.fetchall()
                    print(f"EXISTING ADMINS: {admins}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    check_admin()
