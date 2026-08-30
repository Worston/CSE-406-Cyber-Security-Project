"""Generates and loads the victim server's user credential store.

Each account stores two hashes of the same password: a fast (single
SHA-256) hash used when the server runs undefended, and a slow
(PBKDF2, high iteration count) hash used when --defense is enabled.
This lets the same user store demonstrate both configurations without
regenerating it.
"""
import hashlib
import json
import os
import secrets

USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")
SLOW_HASH_ITERATIONS = 200_000

# Plaintext passwords exist only here, at store-generation time.
SEED_USERS = {
    "alice": "sunshine",
    "bob": "dragon",
    "carol": "letmein",
    "dave": "Xk7$vQ2!mZpL9r",  # strong password: dictionary attack should fail on this one
    "eve": "admin123",         # shared default password: spraying target
    "frank": "admin123",       # shared default password: spraying target
}


def hash_password(password: str, salt: bytes, iterations: int) -> str:
    if iterations <= 1:
        return hashlib.sha256(salt + password.encode()).hexdigest()
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations).hex()


def generate_store(path: str = USERS_FILE) -> None:
    store = {}
    for username, password in SEED_USERS.items():
        salt = secrets.token_bytes(16)
        store[username] = {
            "salt": salt.hex(),
            "fast_hash": hash_password(password, salt, iterations=1),
            "slow_hash": hash_password(password, salt, iterations=SLOW_HASH_ITERATIONS),
        }
    with open(path, "w") as f:
        json.dump(store, f, indent=2)
    print(f"Wrote {len(store)} users to {path}")


def load_store(path: str = USERS_FILE) -> dict:
    with open(path) as f:
        return json.load(f)


def verify_password(store: dict, username: str, password: str, defense: bool) -> bool:
    user = store.get(username)
    iterations = SLOW_HASH_ITERATIONS if defense else 1
    if user is None:
        # Hash against a dummy salt anyway so a nonexistent username doesn't
        # respond measurably faster than a wrong password.
        hash_password(password, bytes(16), iterations)
        return False
    salt = bytes.fromhex(user["salt"])
    expected = user["slow_hash"] if defense else user["fast_hash"]
    return hash_password(password, salt, iterations) == expected


if __name__ == "__main__":
    generate_store()
