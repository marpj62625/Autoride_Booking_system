import psycopg
from config import SUPABASE_DB_URL
from flask import g
from psycopg.rows import dict_row

def get_connection():
    """Direct connection for serverless (debugging pool issues)"""
    return psycopg.connect(conninfo=SUPABASE_DB_URL, prepare_threshold=None)

def release_connection(conn):
    if conn:
        conn.close()

def get_db():
    if 'db_conn' not in g:
        g.db_conn = get_connection()
    return g.db_conn

def get_cursor():
    conn = get_db()
    return conn.cursor(row_factory=dict_row)

def commit_db():
    conn = get_db()
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
