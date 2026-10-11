"""Database access for WealthWatch.

Uses Postgres (via psycopg) when DATABASE_URL or POSTGRES_URL is set, and a local SQLite file
otherwise so the API runs on a laptop with no cloud resources.
"""
import os
import sqlite3
from decimal import Decimal
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

NON_LIBPQ_OPTIONS = ("supa", "pgbouncer")

SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    display_name TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    amount DECIMAL(10,2) NOT NULL CHECK (amount > 0),
    type TEXT NOT NULL CHECK (type IN ('income', 'expense')),
    category TEXT NOT NULL,
    description TEXT,
    transaction_date DATE NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_user_date ON transactions(user_id, transaction_date);
"""

sqlite3.register_adapter(Decimal, float)


class Database:
    """Thin wrapper that hides the differences between the two engines."""

    def __init__(self, conn, engine):
        self.conn = conn
        self.engine = engine

    def execute(self, sql, params=()):
        if self.engine == "sqlite":
            sql = sql.replace("%s", "?")
        cursor = self.conn.cursor()
        cursor.execute(sql, tuple(params))
        return cursor

    def insert(self, table, id_column, values):
        """Insert one row and return its generated id.

        Table and column names come from code, never from the request.
        """
        columns = ", ".join(values)
        placeholders = ", ".join(["%s"] * len(values))
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        if self.engine == "postgres":
            cursor = self.execute(f"{sql} RETURNING {id_column}", values.values())
            return int(cursor.fetchone()[0])
        return int(self.execute(sql, values.values()).lastrowid)

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is not None:
            self.rollback()
        self.close()
        return False


def postgres_url():
    """DATABASE_URL, or the POSTGRES_URL that Vercel's Supabase integration sets."""
    url = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL")
    if not url:
        return None
    # The integration appends routing hints that libpq rejects as unknown options.
    parts = urlsplit(url)
    query = [(k, v) for k, v in parse_qsl(parts.query) if k not in NON_LIBPQ_OPTIONS]
    return urlunsplit(parts._replace(query=urlencode(query)))


def connect():
    url = postgres_url()
    if url:
        import psycopg  # imported lazily so local SQLite runs do not need it

        # prepare_threshold=None: Supabase's transaction pooler hands each
        # transaction to a different server connection, which breaks
        # server-side prepared statements.
        conn = psycopg.connect(url, prepare_threshold=None, connect_timeout=10)
        return Database(conn, "postgres")

    path = os.environ.get("SQLITE_PATH") or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "wealthwatch.db"
    )
    # FastAPI runs the request's dependencies and handler on different
    # threads; the connection is still only used by one request at a time.
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SQLITE_SCHEMA)
    return Database(conn, "sqlite")


def get_or_create_user(db, email):
    row = db.execute("SELECT user_id FROM users WHERE email = %s", (email,)).fetchone()
    if row:
        return row[0]
    try:
        user_id = db.insert(
            "users", "user_id", {"email": email, "display_name": email.split("@")[0]}
        )
        db.commit()
        return user_id
    except Exception:
        # Another request created the same user first; read that row instead.
        db.rollback()
        row = db.execute("SELECT user_id FROM users WHERE email = %s", (email,)).fetchone()
        if not row:
            raise
        return row[0]
