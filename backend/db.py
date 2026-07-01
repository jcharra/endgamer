"""SQLite persistence for user accounts.

Keeps the account store dead simple: a single `users` table, plain sqlite3
(no ORM), with one connection opened per call. The app is small enough that
this is not a bottleneck, and it avoids adding a dependency for a single
table.
"""

import os
import sqlite3
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "app.db")


def get_connection():
    """Open a fresh connection to the accounts database, with rows returned
    as dict-like `sqlite3.Row` objects so callers can use column names.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create the `users` table if it does not exist yet. Safe to call on
    every app startup.

    `password_hash` and `google_sub` are both nullable because an account
    may be created through only one of the two auth methods (e.g. a
    Google-only sign-in never sets a password).
    """
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT,
                name TEXT,
                google_sub TEXT UNIQUE,
                created_at TEXT NOT NULL
            )
            """
        )


def create_user(email, password_hash, name):
    """Insert a new email/password account and return the created row."""
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO users (email, password_hash, name, created_at) VALUES (?, ?, ?, ?)",
            (email, password_hash, name, now),
        )
        user_id = cursor.lastrowid
    return find_user_by_id(user_id)


def find_user_by_email(email):
    """Return the user row for the given email, or None if no such account exists."""
    with get_connection() as conn:
        return conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()


def find_user_by_id(user_id):
    """Return the user row for the given id, or None if no such account exists."""
    with get_connection() as conn:
        return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def find_or_create_google_user(sub, email, name):
    """Resolve a Google sign-in to a local user account.

    Looks up the account by Google's stable subject id first. If none is
    found but an account with the same email already exists (e.g. it was
    originally created via email/password), the two are linked by writing
    the Google id onto that existing row. Otherwise a brand new
    Google-only account is created.
    """
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE google_sub = ?", (sub,)).fetchone()
        if row is not None:
            return row

        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if row is not None:
            conn.execute("UPDATE users SET google_sub = ? WHERE id = ?", (sub, row["id"]))
            user_id = row["id"]
        else:
            now = datetime.now(timezone.utc).isoformat()
            cursor = conn.execute(
                "INSERT INTO users (email, name, google_sub, created_at) VALUES (?, ?, ?, ?)",
                (email, name, sub, now),
            )
            user_id = cursor.lastrowid

    return find_user_by_id(user_id)
