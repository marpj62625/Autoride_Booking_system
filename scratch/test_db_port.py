import psycopg
import sys

URL_5432 = 'postgresql://postgres.fydfsgjrlowrrtlmefwq:Autoride777%25*@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres'
URL_6543 = 'postgresql://postgres.fydfsgjrlowrrtlmefwq:Autoride777%25*@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres'

print("Testing port 5432...")
try:
    conn = psycopg.connect(conninfo=URL_5432)
    cur = conn.cursor()
    cur.execute("SELECT 1")
    print("Port 5432 connection successful!", cur.fetchone())
    conn.close()
except Exception as e:
    print("Port 5432 connection failed:", e)

print("Testing port 6543...")
try:
    conn = psycopg.connect(conninfo=URL_6543)
    cur = conn.cursor()
    cur.execute("SELECT 1")
    print("Port 6543 connection successful!", cur.fetchone())
    conn.close()
except Exception as e:
    print("Port 6543 connection failed:", e)
