"""
Test Rollback Script
"""

import psycopg
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import SUPABASE_DB_URL


def test_rollback():
    """Test the rollback SQL script"""
    conn = None
    try:
        print("\n" + "="*70)
        print("TESTING ROLLBACK: 001_rollback_extension_tables.sql")
        print("="*70 + "\n")
        
        conn = psycopg.connect(SUPABASE_DB_URL)
        cursor = conn.cursor()
        
        # Read and execute rollback file
        migrations_dir = Path(__file__).parent
        rollback_file = migrations_dir / "001_rollback_extension_tables.sql"
        
        with open(rollback_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        cursor.execute(sql_content)
        conn.commit()
        
        print("? Rollback SQL executed successfully!\n")
        return True
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"? Rollback failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        if conn:
            cursor.close()
            conn.close()


def verify_rollback():
    """Verify all tables and columns were removed"""
    conn = None
    try:
        print("="*70)
        print("VERIFICATION: Checking rollback results")
        print("="*70 + "\n")
        
        conn = psycopg.connect(SUPABASE_DB_URL)
        cursor = conn.cursor()
        
        all_removed = True
        
        # Check tables should NOT exist
        print("1. Verifying tables were removed:")
        tables = ['booking_extensions', 'booking_conflicts', 'extension_payments']
        for table in tables:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = %s
                )
            """, (table,))
            exists = cursor.fetchone()[0]
            
            if exists:
                print(f"   ? {table} still exists (FAILED)")
                all_removed = False
            else:
                print(f"   ? {table} removed")
        
        # Check bookings columns should NOT exist
        print("\n2. Verifying bookings columns were removed:")
        columns = ['has_active_extension', 'extension_count', 'is_conflict_affected', 'conflict_id']
        for column in columns:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = 'bookings' AND column_name = %s
                )
            """, (column,))
            exists = cursor.fetchone()[0]
            
            if exists:
                print(f"   ? {column} still exists (FAILED)")
                all_removed = False
            else:
                print(f"   ? {column} removed")
        
        # Check indexes should NOT exist
        print("\n3. Verifying indexes were removed:")
        cursor.execute("""
            SELECT COUNT(*) FROM pg_indexes 
            WHERE indexname LIKE 'idx_booking_extensions%'
               OR indexname LIKE 'idx_booking_conflicts%'
               OR indexname LIKE 'idx_extension_payments%'
        """)
        index_count = cursor.fetchone()[0]
        
        if index_count > 0:
            print(f"   ? {index_count} indexes still exist (FAILED)")
            all_removed = False
        else:
            print(f"   ? All extension indexes removed")
        
        print("\n" + "="*70)
        if all_removed:
            print("? ROLLBACK VERIFICATION COMPLETE - All objects removed!")
        else:
            print("? ROLLBACK VERIFICATION FAILED - Some objects still exist")
        print("="*70 + "\n")
        
        return all_removed
        
    except Exception as e:
        print(f"? Verification failed: {e}")
        return False
        
    finally:
        if conn:
            cursor.close()
            conn.close()


if __name__ == "__main__":
    print("\n" + "="*70)
    print("DATABASE ROLLBACK TEST")
    print("="*70 + "\n")
    
    # Step 1: Test rollback
    if not test_rollback():
        print("\n? Rollback failed. Aborting.")
        sys.exit(1)
    
    # Step 2: Verify rollback
    if not verify_rollback():
        print("\n? Rollback verification failed.")
        sys.exit(1)
    
    print("="*70)
    print("?? ROLLBACK TEST SUCCESSFUL!")
    print("="*70)
    sys.exit(0)
