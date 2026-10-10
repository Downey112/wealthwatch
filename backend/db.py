"""Database access for WealthWatch.

Uses Azure SQL / SQL Server (via pymssql) when DB_SERVER is set, and a local
SQLite file otherwise so the API runs on a laptop with no cloud resources.
"""
import logging
import os
import sqlite3
from decimal import Decimal

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

    @property
    def limit_clause(self):
        """Row-limit clause to append after ORDER BY; takes one parameter."""
        if self.engine == "mssql":
            return "OFFSET 0 ROWS FETCH NEXT %s ROWS ONLY"
        return "LIMIT %s"

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
        if self.engine == "mssql":
            cursor = self.execute(
                f"INSERT INTO {table} ({columns}) OUTPUT INSERTED.{id_column} "
                f"VALUES ({placeholders})",
                values.values(),
            )
            return int(cursor.fetchone()[0])
        cursor = self.execute(
            f"INSERT INTO {table} ({columns}) VALUES ({placeholders})", values.values()
        )
        return int(cursor.lastrowid)

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


def connect():
    server = os.environ.get("DB_SERVER")
    if server:
        import pymssql  # imported lazily so local SQLite runs do not need it

        logging.info("Connecting to SQL Server %s", server)
        conn = pymssql.connect(
            server=server,
            database=os.environ.get("DB_NAME"),
            user=os.environ.get("DB_USER"),
            password=os.environ.get("DB_PASSWORD"),
            autocommit=False,
        )
        return Database(conn, "mssql")

    path = os.environ.get("SQLITE_PATH") or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "wealthwatch.db"
    )
    conn = sqlite3.connect(path)
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
