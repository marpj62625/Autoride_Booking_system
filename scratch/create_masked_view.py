import sys
sys.path.insert(0, 'backend')
from app import app, get_cursor, commit_db

with app.app_context():
    cur = get_cursor()

    # Create or replace masked_users view in public schema
    view_sql = """
    CREATE OR REPLACE VIEW masked_users AS
    SELECT 
        id,
        full_name,
        CASE 
            WHEN email IS NULL OR email = '' THEN email
            WHEN LENGTH(SPLIT_PART(email, '@', 1)) <= 3 THEN CONCAT(LEFT(SPLIT_PART(email, '@', 1), 1), '***@', SPLIT_PART(email, '@', 2))
            ELSE CONCAT(LEFT(SPLIT_PART(email, '@', 1), 2), '*********', RIGHT(SPLIT_PART(email, '@', 1), 2), '@', SPLIT_PART(email, '@', 2))
        END AS email,
        phone,
        role,
        is_verified,
        is_email_verified,
        is_frozen,
        is_regular_customer,
        loyalty_points,
        created_at
    FROM users;
    """

    cur.execute(view_sql)
    commit_db()
    print("[SUCCESS] View 'masked_users' created or replaced successfully!")

    # Test reading from the view
    cur.execute("SELECT id, full_name, email, phone, role FROM masked_users ORDER BY id ASC LIMIT 10")
    rows = cur.fetchall()
    print("\n--- Sample data from 'masked_users' view: ---")
    for r in rows:
        print(f"ID: {r['id']:3d} | {r['full_name'][:25]:25s} | Email: {r['email']}")
