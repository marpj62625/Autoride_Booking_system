import logging
import time
from contextlib import contextmanager
import psycopg
from config import SUPABASE_DB_URL
from flask import g
from psycopg.rows import dict_row

logger = logging.getLogger(__name__)

def get_connection():
    """Direct connection for serverless with autocommit and transient pooler retry."""
    last_err = None
    for attempt in range(3):
        try:
            return psycopg.connect(
                conninfo=SUPABASE_DB_URL,
                autocommit=True,
                prepare_threshold=None,
                connect_timeout=10,
            )
        except Exception as e:
            last_err = e
            msg = str(e).lower()
            is_transient = any(k in msg for k in ('echeckouttimeout', 'timeout', 'ssl connection', 'connection refused', 'temporarily unavailable'))
            if not is_transient or attempt == 2:
                raise
            time.sleep(0.3 * (attempt + 1))
    raise last_err

def release_connection(conn):
    if conn:
        try:
            if not conn.closed:
                conn.close()
        except Exception as e:
            logger.warning("Error releasing database connection: %s", e)

def get_db():
    if 'db_conn' not in g or getattr(g, 'db_conn', None) is None or g.db_conn.closed:
        g.db_conn = get_connection()
    return g.db_conn

def get_cursor():
    conn = get_db()
    try:
        if hasattr(conn, 'info') and hasattr(conn.info, 'transaction_status'):
            if conn.info.transaction_status == 3:  # TransactionStatus.INERROR
                logger.warning("Connection was in INERROR transaction state; executing rollback.")
                conn.rollback()
    except Exception as e:
        logger.warning("Error checking transaction status: %s", e)
    return conn.cursor(row_factory=dict_row)

def commit_db():
    conn = get_db()
    if not conn.autocommit:
        conn.commit()

@contextmanager
def transaction_scope():
    """Context manager for multi-statement atomic transactions in psycopg 3."""
    conn = get_db()
    with conn.transaction():
        yield conn

def init_db_helpers(app):
    @app.teardown_appcontext
    def close_db(e=None):
        db_conn = g.pop('db_conn', None)
        if db_conn is not None:
            release_connection(db_conn)

def init_pool():
    # Placeholder to avoid import errors in other files
    pass
