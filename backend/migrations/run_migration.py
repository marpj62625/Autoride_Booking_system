"""
Migration Runner Script
Executes SQL migration files on the database
"""

import psycopg
import sys
import os
from pathlib import Path

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import SUPABASE_DB_URL


def run_sql_file(cursor, filepath, migration_name):
    """Execute SQL from a file"""
    print(f"\n{'='*70}")
    print(f"Running {migration_name}")
    print(f"File: {filepath}")
    print(f"{'='*70}\n")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    try:
        cursor.execute(sql_content)
        print(f"\n? {migration_name} completed successfully!")
        return True
    except Exception as e:
        print(f"\n? {migration_name} failed!")
        print(f"Error: {e}")
        raise


def verify_tables_created(cursor):
    """Verify that all tables were created successfully"""
    print("\n" + "="*70)
    print("Verifying Migration Results")
    print("="*70 + "\n")
    
    tables_to_check = [
        'booking_extensions',
        'booking_conflicts',
        'extension_payments'
    ]
    
    for table in tables_to_check:
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = %s
            )
        """, (table,))
        exists = cursor.fetchone()[0]
        
        if exists:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"? Table '{table}' exists (rows: {count})")
        else:
            print(f"? Table '{table}' NOT FOUND")
            return False
    
    # Verify bookings table columns
    print("\nVerifying bookings table columns:")
    columns_to_check = [
        'has_active_extension',
        'extension_count',
        'is_conflict_affected',
        'conflict_id'
    ]
    
    for column in columns_to_check:
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'bookings' AND column_name = %s
            )
        """, (column,))
        exists = cursor.fetchone()[0]
        
        if exists:
            print(f"? Column 'bookings.{column}' exists")
        else:
            print(f"? Column 'bookings.{column}' NOT FOUND")
            return False
    
    # Verify indexes
    print("\nVerifying indexes:")
    indexes_to_check = [
        'idx_booking_extensions_booking_id',
        'idx_booking_extensions_status',
        'idx_booking_conflicts_affected_booking_id',
        'idx_booking_conflicts_resolution_status',
        'idx_extension_payments_extension_id'
    ]
    
    for index in indexes_to_check:
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM pg_indexes 
                WHERE indexname = %s
            )
        """, (index,))
        exists = cursor.fetchone()[0]
        
        if exists:
            print(f"? Index '{index}' exists")
        else:
            print(f"? Index '{index}' NOT FOUND")
    
    print("\n" + "="*70)
    print("? All verification checks passed!")
    print("="*70 + "\n")
    return True


def run_migration():
    """Run the migration script"""
    conn = None
    try:
        print("\nConnecting to database...")
        conn = psycopg.connect(SUPABASE_DB_URL)
        cursor = conn.cursor()
        print("? Connected successfully\n")
        
        # Get migration file path
        migrations_dir = Path(__file__).parent
        migration_file = migrations_dir / "001_add_extension_tables.sql"
        
        if not migration_file.exists():
            raise FileNotFoundError(f"Migration file not found: {migration_file}")
        
        # Run migration
        run_sql_file(cursor, migration_file, "Migration 001: Add Extension Tables")
        
        # Commit changes
        conn.commit()
        print("\n? Transaction committed successfully")
        
        # Verify results
        verify_tables_created(cursor)
        
        return True
        
    except Exception as e:
        if conn:
            conn.rollback()
            print("\n??  Transaction rolled back due to error")
        print(f"\n? Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        if conn:
            cursor.close()
            conn.close()
            print("\nDatabase connection closed.")


def run_rollback():
    """Run the rollback script"""
    conn = None
    try:
        print("\n" + "!"*70)
        print("WARNING: This will delete all extension-related data!")
        print("!"*70)
        
        response = input("\nAre you sure you want to rollback? (type 'yes' to confirm): ")
        if response.lower() != 'yes':
            print("Rollback cancelled.")
            return False
        
        print("\nConnecting to database...")
        conn = psycopg.connect(SUPABASE_DB_URL)
        cursor = conn.cursor()
        print("? Connected successfully\n")
        
        # Get rollback file path
        migrations_dir = Path(__file__).parent
        rollback_file = migrations_dir / "001_rollback_extension_tables.sql"
        
        if not rollback_file.exists():
            raise FileNotFoundError(f"Rollback file not found: {rollback_file}")
        
        # Run rollback
        run_sql_file(cursor, rollback_file, "Rollback 001: Remove Extension Tables")
        
        # Commit changes
        conn.commit()
        print("\n? Rollback completed successfully")
        
        return True
        
    except Exception as e:
        if conn:
            conn.rollback()
            print("\n??  Transaction rolled back due to error")
        print(f"\n? Rollback failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        if conn:
            cursor.close()
            conn.close()
            print("\nDatabase connection closed.")


if __name__ == "__main__":
    print("="*70)
    print("Database Migration Runner")
    print("="*70)
    
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        success = run_rollback()
    else:
        success = run_migration()
    
    sys.exit(0 if success else 1)
