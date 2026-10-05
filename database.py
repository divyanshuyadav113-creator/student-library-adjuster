"""
database.py
Handles the SQLite connection and schema creation for the Library
Management System. Plain sqlite3 is used (no ORM) to keep the project
dependency-light and easy for anyone reading the code on GitHub.
"""

import sqlite3
from contextlib import contextmanager

DB_PATH = "library.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_cursor(commit=False):
    """Context manager that yields a cursor and closes the connection
    for you. Pass commit=True for INSERT/UPDATE/DELETE statements."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        yield cur
        if commit:
            conn.commit()
    finally:
        conn.close()


def init_db():
    """Creates all tables if they do not already exist."""
    with get_cursor(commit=True) as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                isbn TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                category TEXT DEFAULT 'General',
                total_copies INTEGER NOT NULL DEFAULT 1,
                available_copies INTEGER NOT NULL DEFAULT 1,
                qr_path TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT,
                joined_on TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id INTEGER NOT NULL,
                member_id INTEGER NOT NULL,
                issue_date TEXT NOT NULL,
                due_date TEXT NOT NULL,
                return_date TEXT,
                fine_amount REAL DEFAULT 0,
                fine_paid INTEGER DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'ISSUED',
                FOREIGN KEY (book_id) REFERENCES books (id),
                FOREIGN KEY (member_id) REFERENCES members (id)
            )
        """)
    print("Database initialized ->", DB_PATH)


if __name__ == "__main__":
    init_db()
