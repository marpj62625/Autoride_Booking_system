#!/usr/bin/env python3
"""
Apply Extension Tables Migration to Supabase Database
This script executes the migration directly on Supabase PostgreSQL
"""

import psycopg2
import sys
import os

# Add backend to path to import config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import SUPABASE_DB_URL

def apply_migration_to_supabase():
    """Apply the extension tables migration to Supabase database"""
    
    print("=" * 70)
    print("APPLYING MIGRATION TO SUPABASE DATABASE")
    print("=" * 70)
    
    # Read migration SQL file
    migration_file = os.path.join(os.path.dirname(__file__), '001_add_extension_tables.sql')
    
    if not os.path.exists(migration_file):
        print(f"? ERROR: Migration file not found: {migration_file}")
        return False
    
    print(f"\n?? Reading migration file: {migration_file}")
    with open(migration_file, 'r', encoding='utf-8') as f:
        migration_sql = f.read()
    
    print(f"? Migration SQL loaded ({len(migration_sql)} characters)")
    
    # Connect to Supabase
    print(f"\n?? Connecting to Supabase database...")
    print(f"   URL: {SUPABASE_DB_URL.split('@')[1] if '@' in SUPABASE_DB_URL else 'configured'}")
    
    try:
        conn = psycopg2.connect(SUPABASE_DB_URL)
        cursor = conn.cursor()
        print("? Connected to Supabase successfully!")
        
        # Check if tables already exist
        print("\n?? Checking if migration already applied...")
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('booking_extensions', 'booking_conflicts', 'extension_payments')
        """)
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        if len(existing_tables) == 3:
            print(f"??  WARNING: All extension tables already exist in Supabase:")
            for table in existing_tables:
                print(f"   - {table}")
            
            response = input("\n? Do you want to re-run the migration? (yes/no): ").lower()
            if response != 'yes':
                print("? Migration cancelled by user.")
                cursor.close()
                conn.close()
                return False
        elif len(existing_tables) > 0:
            print(f"??  WARNING: Some extension tables exist:")
            for table in existing_tables:
                print(f"   - {table}")
        else:
            print("? No existing extension tables found. Ready to migrate.")
        
        # Execute migration
        print("\n?? Executing migration on Supabase...")
        cursor.execute(migration_sql)
        conn.commit()
        print("? Migration executed successfully!")
        
        # Verify tables were created
        print("\n? Verifying migration...")
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('booking_extensions', 'booking_conflicts', 'extension_payments')
        """)
        created_tables = [row[0] for row in cursor.fetchall()]
        
        print(f"\n?? Tables in Supabase:")
        for table in created_tables:
            cursor.execute(f"""
                SELECT COUNT(*) FROM information_schema.columns 
                WHERE table_name = '{table}' AND table_schema = 'public'
            """)
            column_count = cursor.fetchone()[0]
            print(f"   ? {table} ({column_count} columns)")
        
        # Check bookings table columns
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'bookings' AND table_schema = 'public'
            AND column_name IN ('has_active_extension', 'extension_count', 'is_conflict_affected', 'conflict_id')
        """)
        booking_columns = [row[0] for row in cursor.fetchall()]
        
        print(f"\n?? New columns in 'bookings' table:")
        for col in booking_columns:
            print(f"   ? {col}")
        
        # Check indexes
        cursor.execute("""
            SELECT indexname FROM pg_indexes 
            WHERE schemaname = 'public' 
            AND indexname LIKE '%extension%' OR indexname LIKE '%conflict%'
        """)
        indexes = [row[0] for row in cursor.fetchall()]
        
        print(f"\n?? Indexes created: {len(indexes)}")
        for idx in indexes:
            print(f"   ? {idx}")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 70)
        print("? MIGRATION APPLIED TO SUPABASE SUCCESSFULLY!")
        print("=" * 70)
        print("\n?? Your Supabase database now supports booking extensions with conflict resolution!")
        print("?? Next step: Run Wave 2 tasks to implement backend APIs")
        
        return True
        
    except psycopg2.Error as e:
        print(f"\n? DATABASE ERROR: {e}")
        print("\n?? Common issues:")
        print("   - Check if Supabase connection URL is correct in config.py")
        print("   - Verify that 'bookings', 'users', 'vehicles', 'admins' tables exist")
        print("   - Check if you have proper permissions on Supabase")
        return False
        
    except Exception as e:
        print(f"\n? UNEXPECTED ERROR: {e}")
        return False

if __name__ == '__main__':
    print("\n?? Starting Supabase Migration Application...")
    success = apply_migration_to_supabase()
    sys.exit(0 if success else 1)
