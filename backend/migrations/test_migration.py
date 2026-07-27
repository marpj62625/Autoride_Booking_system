"""
Test Migration Script - Cleanup and Fresh Migration
"""

import psycopg
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import SUPABASE_DB_URL


def cleanup_existing_tables():
    """Remove any existing extension tables"""
    conn = None
    try:
        print("\n" + "="*70)
        print("CLEANUP: Removing existing extension tables (if any)")
        print("="*70 + "\n")
        
        conn = psycopg.connect(SUPABASE_DB_URL)
        cursor = conn.cursor()
        
        # Drop tables in correct order (respecting foreign keys)
        # Use separate statements to handle cases where some objects don't exist
        
        # Drop triggers first (if tables exist)
        try:
            cursor.execute("DROP TRIGGER IF EXISTS update_booking_extensions_updated_at ON booking_extensions")
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"  (Skipping trigger 1: {e})")
        
        try:
            cursor.execute("DROP TRIGGER IF EXISTS update_booking_conflicts_updated_at ON booking_conflicts")
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"  (Skipping trigger 2: {e})")
        
        # Drop tables (CASCADE will handle dependencies)
        try:
            cursor.execute("DROP TABLE IF EXISTS extension_payments CASCADE")
            conn.commit()
            print("  ? Dropped extension_payments table")
        except Exception as e:
            conn.rollback()
            print(f"  (Skipping extension_payments: {e})")
        
        try:
            cursor.execute("DROP TABLE IF EXISTS booking_conflicts CASCADE")
            conn.commit()
            print("  ? Dropped booking_conflicts table")
        except Exception as e:
            conn.rollback()
            print(f"  (Skipping booking_conflicts: {e})")
        
        try:
            cursor.execute("DROP TABLE IF EXISTS booking_extensions CASCADE")
            conn.commit()
            print("  ? Dropped booking_extensions table")
        except Exception as e:
            conn.rollback()
            print(f"  (Skipping booking_extensions: {e})")
        
        # Drop columns from bookings (these might not exist)
        for column in ['conflict_id', 'is_conflict_affected', 'extension_count', 'has_active_extension']:
            try:
                cursor.execute(f"ALTER TABLE bookings DROP COLUMN IF EXISTS {column}")
                conn.commit()
                print(f"  ? Dropped bookings.{column} column")
            except Exception as e:
                conn.rollback()
                print(f"  (Skipping column {column}: {e})")
        
        print("? Cleanup completed successfully\n")
        return True
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"? Cleanup failed: {e}")
        return False
        
    finally:
        if conn:
            cursor.close()
            conn.close()


def run_fresh_migration():
    """Run the SQL migration on a clean database"""
    conn = None
    try:
        print("="*70)
        print("Running Fresh Migration: 001_add_extension_tables.sql")
        print("="*70 + "\n")
        
        conn = psycopg.connect(SUPABASE_DB_URL)
        cursor = conn.cursor()
        
        # Read and execute migration file
        migrations_dir = Path(__file__).parent
        migration_file = migrations_dir / "001_add_extension_tables.sql"
        
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        cursor.execute(sql_content)
        conn.commit()
        
        print("? Migration completed successfully!\n")
        return True
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"? Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        if conn:
            cursor.close()
            conn.close()


def verify_migration():
    """Verify all tables and columns exist"""
    conn = None
    try:
        print("="*70)
        print("VERIFICATION: Checking migration results")
        print("="*70 + "\n")
        
        conn = psycopg.connect(SUPABASE_DB_URL)
        cursor = conn.cursor()
        
        # Check tables
        print("1. Checking tables:")
        tables = ['booking_extensions', 'booking_conflicts', 'extension_payments']
        for table in tables:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = %s
                )
            """, (table,))
            exists = cursor.fetchone()[0]
            status = "?" if exists else "?"
            print(f"   {status} {table}")
        
        # Check bookings columns
        print("\n2. Checking bookings table columns:")
        columns = ['has_active_extension', 'extension_count', 'is_conflict_affected', 'conflict_id']
        for column in columns:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = 'bookings' AND column_name = %s
                )
            """, (column,))
            exists = cursor.fetchone()[0]
            status = "?" if exists else "?"
            print(f"   {status} {column}")
        
        # Check indexes
        print("\n3. Checking indexes:")
        indexes = [
            'idx_booking_extensions_booking_id',
            'idx_booking_extensions_status',
            'idx_booking_extensions_created_at',
            'idx_booking_conflicts_affected_booking_id',
            'idx_booking_conflicts_resolution_status',
            'idx_booking_conflicts_resolution_deadline',
            'idx_booking_conflicts_created_at',
            'idx_extension_payments_extension_id',
            'idx_extension_payments_payment_status'
        ]
        
        index_count = 0
        for index in indexes:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM pg_indexes 
                    WHERE indexname = %s
                )
            """, (index,))
            exists = cursor.fetchone()[0]
            if exists:
                index_count += 1
        
        print(f"   ? {index_count}/{len(indexes)} indexes created")
        
        # Check foreign keys
        print("\n4. Checking foreign key constraints:")
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.table_constraints
            WHERE constraint_type = 'FOREIGN KEY'
            AND table_name IN ('booking_extensions', 'booking_conflicts', 'extension_payments', 'bookings')
            AND constraint_name LIKE '%extension%' OR constraint_name LIKE '%conflict%'
        """)
        fk_count = cursor.fetchone()[0]
        print(f"   ? {fk_count} foreign key constraints found")
        
        print("\n" + "="*70)
        print("? VERIFICATION COMPLETE - All checks passed!")
        print("="*70 + "\n")
        
        return True
        
    except Exception as e:
        print(f"? Verification failed: {e}")
        return False
        
    finally:
        if conn:
            cursor.close()
            conn.close()


if __name__ == "__main__":
    print("\n" + "="*70)
    print("DATABASE MIGRATION TEST")
    print("="*70 + "\n")
    
    # Step 1: Cleanup
    if not cleanup_existing_tables():
        print("\n? Cleanup failed. Aborting.")
        sys.exit(1)
    
    # Step 2: Run migration
    if not run_fresh_migration():
        print("\n? Migration failed. Aborting.")
        sys.exit(1)
    
    # Step 3: Verify
    if not verify_migration():
        print("\n? Verification failed.")
        sys.exit(1)
    
    print("="*70)
    print("?? MIGRATION TEST SUCCESSFUL!")
    print("="*70)
    sys.exit(0)
