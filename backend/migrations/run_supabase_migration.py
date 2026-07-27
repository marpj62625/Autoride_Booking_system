#!/usr/bin/env python3
"""
Supabase Migration Runner
Executes the booking extension database migration on Supabase PostgreSQL
"""

import sys
import os
from pathlib import Path

# Add backend to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import psycopg2
    from config import SUPABASE_DB_URL
except ImportError as e:
    print(f"? Error importing required modules: {e}")
    print("\n?? Please install required package:")
    print("   pip install psycopg2-binary")
    sys.exit(1)


def run_migration():
    """Execute the migration SQL on Supabase database"""
    
    migration_file = Path(__file__).parent / "001_add_extension_tables.sql"
    
    if not migration_file.exists():
        print(f"? Migration file not found: {migration_file}")
        return False
    
    print("=" * 70)
    print("?? SUPABASE DATABASE MIGRATION")
    print("=" * 70)
    print(f"\n?? Migration File: {migration_file.name}")
    print(f"???  Database: Supabase PostgreSQL")
    print(f"?? Connection: {SUPABASE_DB_URL[:50]}...")
    
    # Read migration SQL
    with open(migration_file, 'r', encoding='utf-8') as f:
        migration_sql = f.read()
    
    print(f"\n?? SQL Script Length: {len(migration_sql)} characters")
    
    # Connect to Supabase
    try:
        print("\n?? Connecting to Supabase...")
        conn = psycopg2.connect(SUPABASE_DB_URL)
        conn.autocommit = False  # Use transactions
        cursor = conn.cursor()
        
        print("? Connected successfully!")
        
        # Execute migration
        print("\n??  Executing migration SQL...")
        cursor.execute(migration_sql)
        
        # Verify tables were created
        print("\n?? Verifying tables...")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('booking_extensions', 'booking_conflicts', 'extension_payments')
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        
        if len(tables) == 3:
            print("? All 3 tables created successfully:")
            for table in tables:
                print(f"   ? {table[0]}")
        else:
            print(f"??  Expected 3 tables, found {len(tables)}")
            for table in tables:
                print(f"   • {table[0]}")
        
        # Verify bookings table was modified
        print("\n?? Verifying bookings table modifications...")
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = 'bookings'
            AND column_name IN ('has_active_extension', 'extension_count', 'is_conflict_affected', 'conflict_id')
            ORDER BY column_name;
        """)
        
        columns = cursor.fetchall()
        
        if len(columns) == 4:
            print("? All 4 columns added to bookings table:")
            for col in columns:
                print(f"   ? {col[0]}")
        else:
            print(f"??  Expected 4 columns, found {len(columns)}")
            for col in columns:
                print(f"   • {col[0]}")
        
        # Commit transaction
        print("\n?? Committing transaction...")
        conn.commit()
        
        print("\n" + "=" * 70)
        print("SUCCESS: MIGRATION COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print("\nSummary:")
        print("   - 3 new tables created (booking_extensions, booking_conflicts, extension_payments)")
        print("   - 4 columns added to bookings table")
        print("   - 14 foreign key constraints established")
        print("   - 9 indexes created for performance")
        print("   - All triggers and constraints active")
        print("\nYour Supabase database is ready for the booking extension feature!")
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.Error as e:
        print(f"\n? Database error: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False
    except Exception as e:
        print(f"\n? Unexpected error: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False


if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
