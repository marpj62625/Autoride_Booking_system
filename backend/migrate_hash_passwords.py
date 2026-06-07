# -*- coding: utf-8 -*-
"""
One-time migration: hash all plain-text passwords in the users table.

Identifies unhashed passwords (ones that don't start with the bcrypt prefix '$2b$')
and replaces them with bcrypt hashes.

Run once:
    python backend/migrate_hash_passwords.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import psycopg
import bcrypt
from config import SUPABASE_DB_URL


def migrate():
    conn = psycopg.connect(SUPABASE_DB_URL)
    try:
        cur = conn.cursor()

        # Fetch all users with a password that is NOT already a bcrypt hash
        # bcrypt hashes always start with '$2b$' (or '$2a$' older format)
        cur.execute("""
            SELECT id, email, password
            FROM users
            WHERE password IS NOT NULL
              AND password != ''
              AND password NOT LIKE '$2%'
        """)
        rows = cur.fetchall()

        print(f"Found {len(rows)} user(s) with unhashed passwords.")

        if not rows:
            print("Nothing to migrate.")
            return

        updated = 0
        for row in rows:
            user_id, email, plain_pw = row[0], row[1], row[2]
            try:
                hashed = bcrypt.hashpw(plain_pw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                cur.execute(
                    "UPDATE users SET password = %s WHERE id = %s",
                    (hashed, user_id)
                )
                updated += 1
                print(f"  Hashed password for user id={user_id} ({email})")
            except Exception as e:
                print(f"  ERROR for user id={user_id} ({email}): {e}")

        conn.commit()
        print(f"\nMigration complete: {updated}/{len(rows)} passwords hashed.")

    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    print("=" * 60)
    print("PASSWORD HASHING MIGRATION")
    print("=" * 60)
    migrate()
    print("=" * 60)
