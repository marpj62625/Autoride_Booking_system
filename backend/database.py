import psycopg
from psycopg_pool import ConnectionPool
from config import SUPABASE_DB_URL

db_pool = None

def init_pool():
    global db_pool
    if db_pool is None:
        try:
            db_pool = ConnectionPool(conninfo=SUPABASE_DB_URL, min_size=1, max_size=10)
        except Exception as e:
            print(f"Error creating connection pool: {e}")
            raise e

from flask import g
from psycopg.rows import dict_row

def get_connection():
    init_pool()
    return db_pool.getconn()

def release_connection(conn):
    if db_pool and conn:
        db_pool.putconn(conn)

def get_db():
    """Helper to get a database connection for the current request context"""
    if 'db_conn' not in g:
        g.db_conn = get_connection()
    return g.db_conn

def get_cursor():
    """Helper function to safely get a database cursor"""
    conn = get_db()
    # dict_row makes fetchone and fetchall return generic dictionaries
    return conn.cursor(row_factory=dict_row)

def commit_db():
    """Helper function to safely commit database changes"""
    conn = get_db()
    conn.commit()

def init_db_helpers(app):
    @app.teardown_appcontext
    def close_db(e=None):
        """Release the database connection back to the pool at the end of the request"""
        db_conn = g.pop('db_conn', None)
        if db_conn is not None:
            release_connection(db_conn)
