import hashlib
import os
import secrets
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "app.db")
SLOW_HASH_ITERATIONS = 200_000


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            salt TEXT NOT NULL,
            password_hash TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def _hash(password: str, salt: bytes, defense: bool) -> str:
    if defense:
        return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, SLOW_HASH_ITERATIONS).hex()
    return hashlib.sha256(salt + password.encode()).hexdigest()


def create_user(username: str, password: str, defense: bool) -> bool:
    salt = secrets.token_bytes(16)
    password_hash = _hash(password, salt, defense)
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO users (username, salt, password_hash) VALUES (?, ?, ?)",
            (username, salt.hex(), password_hash),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def verify_user(username: str, password: str, defense: bool) -> bool:
    conn = get_connection()
    row = conn.execute(
        "SELECT salt, password_hash FROM users WHERE username = ?", (username,)
    ).fetchone()
    conn.close()
    if row is None:
        # Hash against a dummy salt anyway so a nonexistent username doesn't
        # respond measurably faster than a wrong password would.
        _hash(password, bytes(16), defense)
        return False
    salt = bytes.fromhex(row["salt"])
    return _hash(password, salt, defense) == row["password_hash"]
