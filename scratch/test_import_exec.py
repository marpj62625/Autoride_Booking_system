import sys, psycopg
sys.path.insert(0, 'AutorideSystem/backend')
from config import SUPABASE_DB_URL
from psycopg.rows import dict_row
from fleet_import import execute_import_to_database

conn = psycopg.connect(conninfo=SUPABASE_DB_URL)
try:
    with conn.transaction():
        with conn.cursor(row_factory=dict_row) as cur:
            # Test record with new customer name
            sample_records = [
                {
                    'vehicle_id': 14, # Toyota Vios
                    'customer_name': 'Test New Customer QA',
                    'start_date': '2026-10-15',
                    'end_date': '2026-10-16',
                    'total_price': 2000.0,
                    'amount_paid': 2000.0,
                    'user_match_status': 'new_customer'
                }
            ]
            result = execute_import_to_database(
                records_to_import=sample_records,
                auto_create_renters=True,
                cur=cur,
                commit_fn=lambda: None
            )
            print('IMPORT EXECUTE TEST SUCCESSFUL:', result)
        conn.rollback()
        print('Rolled back test successfully.')
finally:
    conn.close()
