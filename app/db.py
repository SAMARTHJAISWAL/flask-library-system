import os
import sqlite3

from flask import current_app

SCHEMA = """
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    isbn TEXT UNIQUE NOT NULL,
    quantity INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_books_title ON books (title);
CREATE INDEX IF NOT EXISTS idx_books_author ON books (author);
CREATE TABLE IF NOT EXISTS members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);
"""


def get_connection() -> sqlite3.Connection:
    """Open a connection to the database configured on the current app."""
    return sqlite3.connect(current_app.config["DATABASE_PATH"])


def init_db(database_path: str) -> None:
    directory = os.path.dirname(database_path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    conn = sqlite3.connect(database_path)
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()
