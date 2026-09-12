import psycopg
from config import SUPABASE_DB_URL
from flask import g
from psycopg.rows import dict_row

def get_connection():
    """Direct connection for serverless with autocommit to prevent connection pool exhaustion in pgBouncer transaction mode"""
    return psycopg.connect(conninfo=SUPABASE_DB_URL, autocommit=True, prepare_threshold=None)

def release_connection(conn):
    if conn:
        try:
            if not conn.closed:
                conn.close()
        except Exception:
            pass

def get_db():
    if 'db_conn' not in g or getattr(g, 'db_conn', None) is None or g.db_conn.closed:
        g.db_conn = get_connection()
    return g.db_conn

def get_cursor():
    conn = get_db()
    try:
        if hasattr(conn, 'info') and hasattr(conn.info, 'transaction_status'):
            if conn.info.transaction_status == 3:  # TransactionStatus.INERROR
                conn.rollback()
    except Exception:
        pass
    return conn.cursor(row_factory=dict_row)

def commit_db():
    conn = get_db()
    if not conn.autocommit:
        conn.commit()

def init_db_helpers(app):
    @app.teardown_appcontext
    def close_db(e=None):
        db_conn = g.pop('db_conn', None)
        if db_conn is not None:
            release_connection(db_conn)

def init_pool():
    # Placeholder to avoid import errors in other files
    pass
