"""Creates the demo accounts directly in the database (bypassing the
signup form, purely for convenience when resetting between demo runs).

Run once per fresh app.db, matching --defense to whatever mode the
server is currently running in (hashing must match).
"""
import argparse

import db

# Plaintext passwords exist only here, at seed time.
SEED_USERS = {
    "alice": "sunshine",          # dictionary-attack target
    "bob": "dragon",              # dictionary-attack target
    "carol": "letmein",           # dictionary-attack target
    "dave": "Xk7$vQ2!mZpL9r",     # negative control: strong password, should not crack
    "eve": "admin123",            # known-password / spray target (shared default)
    "frank": "admin123",          # known-password / spray target (shared default)
}


def seed(defense: bool) -> None:
    db.init_db()
    created = 0
    for username, password in SEED_USERS.items():
        if db.create_user(username, password, defense):
            created += 1
    print(f"Seeded {created} new user(s) (defense={'ON' if defense else 'OFF'})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--defense", action="store_true", help="hash seeded passwords in defended mode")
    args = parser.parse_args()
    seed(args.defense)
