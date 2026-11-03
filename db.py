"""
Database Connector Module for MCA Classroom Notes Portal.
=========================================================
Supports cloud Neon PostgreSQL (with SSL) as primary database,
with seamless fallback to local SQLite.
"""

import os
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
from config import DATABASE_URL, DEFAULT_DEMO_USER

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQLITE_PATH = os.path.join(BASE_DIR, "notes_portal.db")


class UniversalRow(dict):
    """Row wrapper that supports both dict key access and tuple/index access."""
    def __getitem__(self, item):
        if isinstance(item, int):
            return list(self.values())[item]
        return super().__getitem__(item)

    def __iter__(self):
        return iter(self.values())


class UniversalCursor:
    """Wraps cursor to provide consistent dict/index row access and parameter translation."""
    def __init__(self, cursor, is_postgres=False):
        self.cursor = cursor
        self.is_postgres = is_postgres

    def _translate_query(self, query):
        if self.is_postgres:
            # Convert SQLite-style '?' placeholders to PostgreSQL '%s'
            return query.replace("?", "%s")
        return query

    def execute(self, query, params=None):
        translated = self._translate_query(query)
        if params is None:
            return self.cursor.execute(translated)
        return self.cursor.execute(translated, tuple(params))

    def fetchone(self):
        row = self.cursor.fetchone()
        if row is None:
            return None
        if self.is_postgres:
            return UniversalRow(row)
        return row

    def fetchall(self):
        rows = self.cursor.fetchall()
        if not rows:
            return []
        if self.is_postgres:
            return [UniversalRow(r) for r in rows]
        return rows

    @property
    def lastrowid(self):
        if hasattr(self.cursor, "lastrowid"):
            return self.cursor.lastrowid
        return None

    def close(self):
        self.cursor.close()


class UniversalConnection:
    """Wraps database connection across PostgreSQL and SQLite."""
    def __init__(self, conn, is_postgres=False):
        self.conn = conn
        self.is_postgres = is_postgres

    def cursor(self):
        if self.is_postgres:
            raw_cur = self.conn.cursor(cursor_factory=RealDictCursor)
        else:
            raw_cur = self.conn.cursor()
        return UniversalCursor(raw_cur, is_postgres=self.is_postgres)

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()


def get_db():
    """
    Returns an active database connection.
    Prioritizes Neon PostgreSQL; falls back to local SQLite if offline.
    """
    if DATABASE_URL:
        try:
            pg_conn = psycopg2.connect(DATABASE_URL)
            pg_conn.autocommit = True
            return UniversalConnection(pg_conn, is_postgres=True)
        except Exception as e:
            print(f"[Warning] Failed to connect to Neon PostgreSQL: {e}. Falling back to SQLite.")

    # Fallback to SQLite
    sqlite_conn = sqlite3.connect(SQLITE_PATH, check_same_thread=False)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_conn.execute("PRAGMA foreign_keys = ON")
    return UniversalConnection(sqlite_conn, is_postgres=False)


def get_db_status():
    """Returns database type and connection health."""
    if DATABASE_URL:
        try:
            conn = psycopg2.connect(DATABASE_URL)
            conn.close()
            return {"type": "Neon PostgreSQL (Cloud)", "status": "Connected (Online)", "is_neon": True}
        except Exception as e:
            return {"type": "SQLite (Local Fallback)", "status": f"Fallback Mode ({e})", "is_neon": False}
    return {"type": "SQLite (Local)", "status": "Active (Local)", "is_neon": False}


def init_db():
    """Initializes tables on the active database."""
    conn = get_db()
    cursor = conn.cursor()

    if conn.is_postgres:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                subject VARCHAR(150) NOT NULL,
                semester VARCHAR(50) DEFAULT 'Sem 1',
                note_type VARCHAR(50) DEFAULT 'Notes',
                description TEXT NOT NULL,
                original_filename VARCHAR(255) NOT NULL,
                stored_filename VARCHAR(255) NOT NULL,
                file_size BIGINT NOT NULL,
                uploader_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                download_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
    else:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                subject TEXT NOT NULL,
                semester TEXT DEFAULT 'Sem 1',
                note_type TEXT DEFAULT 'Notes',
                description TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                stored_filename TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                uploader_id INTEGER NOT NULL,
                download_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (uploader_id) REFERENCES users (id) ON DELETE CASCADE
            );
        """)

    # Ensure demo user payal is present
    cursor.execute("SELECT id FROM users WHERE username = ?", (DEFAULT_DEMO_USER["username"],))
    row = cursor.fetchone()
    if not row:
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (DEFAULT_DEMO_USER["username"], DEFAULT_DEMO_USER["email"], DEFAULT_DEMO_USER["password_hash"])
        )
    else:
        cursor.execute(
            "UPDATE users SET password_hash = ? WHERE username = ?",
            (DEFAULT_DEMO_USER["password_hash"], DEFAULT_DEMO_USER["username"])
        )

    conn.commit()
    conn.close()
