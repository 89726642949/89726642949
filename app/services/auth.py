import bcrypt
from typing import Optional

from .db import Database
from .utils import now_str


def has_user(db: Database) -> bool:
    row = db.fetchone("SELECT id FROM users LIMIT 1")
    return bool(row)


def create_user(db: Database, username: str, password: str) -> None:
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    db.execute(
        "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
        (username, hashed.decode("utf-8"), now_str()),
    )


def verify_user(db: Database, username: str, password: str) -> bool:
    row = db.fetchone(
        "SELECT password_hash FROM users WHERE username = ?",
        (username,),
    )
    if not row:
        return False
    hashed = row["password_hash"].encode("utf-8")
    return bcrypt.checkpw(password.encode("utf-8"), hashed)


def update_password(db: Database, username: str, new_password: str) -> None:
    hashed = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt())
    db.execute(
        "UPDATE users SET password_hash = ? WHERE username = ?",
        (hashed.decode("utf-8"), username),
    )
