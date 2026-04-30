#!/usr/bin/env python3
import psycopg
from config import SUPABASE_DB_URL
from psycopg.rows import dict_row
import sys

# Ensure UTF-8 output if possible, but fall back to ASCII friendly marks
def get_mark(success):
    if success:
        return "[OK]"
    return "[ERROR]"

conn = None
try:
    print(f"Connecting to Supabase PostgreSQL...")
    conn = psycopg.connect(SUPABASE_DB_URL)
    
    # Use dict_row for PostgreSQL to get results as dictionaries
    cursor = conn.cursor(row_factory=dict_row)
    
    print(f"{get_mark(True)} Database connection successful!")
    
    # In PostgreSQL, we query information_schema for tables
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)
    tables = cursor.fetchall()
    
    print(f"\n{get_mark(True)} Found {len(tables)} tables in 'public' schema:")
    for table in tables:
        print(f"  - {table['table_name']}")
    
    # Check row counts
    print(f"\n{get_mark(True)} Table statistics:")
    for table in tables:
        table_name = table['table_name']
        cursor.execute(f'SELECT COUNT(*) as cnt FROM {table_name}')
        result = cursor.fetchone()
        count = result['cnt'] if result else 0
        print(f"  - {table_name}: {count} rows")
    
    print(f"\n{get_mark(True)} Supabase connection test passed!")
    
except Exception as e:
    print(f"\n{get_mark(False)} Error: {str(e)}")
    sys.exit(1)
    
finally:
    if conn:
        conn.close()
