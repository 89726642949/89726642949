import os
import sqlite3
from typing import Any, Dict, Iterable, Optional

from .utils import data_dir, ensure_dirs, now_str


DB_FILENAME = "app.db"


def db_path() -> str:
    return os.path.join(data_dir(), DB_FILENAME)


class Database:
    def __init__(self):
        ensure_dirs()
        self._conn = sqlite3.connect(db_path())
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")

    @property
    def conn(self) -> sqlite3.Connection:
        return self._conn

    def close(self):
        self._conn.close()

    def execute(self, sql: str, params: Iterable[Any] = ()):
        cur = self._conn.execute(sql, params)
        self._conn.commit()
        return cur

    def executemany(self, sql: str, params_seq: Iterable[Iterable[Any]]):
        cur = self._conn.executemany(sql, params_seq)
        self._conn.commit()
        return cur

    def fetchall(self, sql: str, params: Iterable[Any] = ()):
        cur = self._conn.execute(sql, params)
        return cur.fetchall()

    def fetchone(self, sql: str, params: Iterable[Any] = ()):
        cur = self._conn.execute(sql, params)
        return cur.fetchone()


def init_db(db: Database) -> None:
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            doc_number TEXT,
            record_date TEXT,
            interested TEXT,
            origin TEXT,
            subject TEXT,
            status TEXT,
            tags TEXT,
            notes TEXT,
            attachment_path TEXT,
            attachment_mode TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            process_number TEXT,
            court TEXT,
            deadline_date TEXT,
            deadline_status TEXT,
            convocation_date TEXT,
            convocation_location TEXT,
            convoked_person TEXT,
            attended INTEGER,
            justification TEXT,
            schedule_datetime TEXT,
            schedule_type TEXT,
            schedule_location TEXT,
            schedule_confirmed INTEGER,
            recipient TEXT,
            send_method TEXT,
            send_date TEXT,
            project_stage TEXT,
            project_responsible TEXT,
            project_due_date TEXT,
            project_status TEXT
        )
        """
    )
    db.execute("CREATE INDEX IF NOT EXISTS idx_records_date ON records (record_date)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_records_category ON records (category)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_records_status ON records (status)")

    ensure_default_settings(db)


def ensure_default_settings(db: Database) -> None:
    defaults: Dict[str, str] = {
        "autolock_minutes": "10",
        "custom_outros_name": "Outros",
    }
    for key, value in defaults.items():
        if not db.fetchone("SELECT key FROM settings WHERE key = ?", (key,)):
            db.execute(
                "INSERT INTO settings (key, value) VALUES (?, ?)",
                (key, value),
            )


def get_setting(db: Database, key: str, default: Optional[str] = None) -> str:
    row = db.fetchone("SELECT value FROM settings WHERE key = ?", (key,))
    if row:
        return row["value"]
    return default or ""


def set_setting(db: Database, key: str, value: str) -> None:
    if db.fetchone("SELECT key FROM settings WHERE key = ?", (key,)):
        db.execute("UPDATE settings SET value = ? WHERE key = ?", (value, key))
    else:
        db.execute("INSERT INTO settings (key, value) VALUES (?, ?)", (key, value))


def update_timestamps(values: Dict[str, Any], is_new: bool) -> Dict[str, Any]:
    now = now_str()
    if is_new:
        values["created_at"] = now
    values["updated_at"] = now
    return values
