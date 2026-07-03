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
                score INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
            """
        )

        # Databases created before the `score` column existed need it added
        # explicitly, since CREATE TABLE IF NOT EXISTS above is a no-op for them.
        existing_columns = {row["name"] for row in conn.execute("PRAGMA table_info(users)")}
        if "score" not in existing_columns:
            conn.execute("ALTER TABLE users ADD COLUMN score INTEGER NOT NULL DEFAULT 0")


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


def adjust_score(user_id, delta):
    """Apply `delta` (positive or negative) to the given user's score and
    return their new total. Used both for the checkmate bonus and the
    deviation penalty.

    The score is clamped to a minimum of 0 in the same statement (via
    MAX), so a string of penalties can never push a player negative.
    """
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET score = MAX(0, score + ?) WHERE id = ?",
            (delta, user_id),
        )
    return find_user_by_id(user_id)["score"]


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
