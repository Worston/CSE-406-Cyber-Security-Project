# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

CSE406 (BUET) coursework: a from-scratch demonstration of two online
password-guessing attacks — a **dictionary attack** (many passwords
against one account) and a **known-password / spray attack** (a few
known passwords against many accounts) — against a small Flask +
SQLite signup/login webapp, plus a working countermeasure (account
lockout + slow password hashing).

Per the assignment brief (`CSE406ProjectJan2026.pdf`), no existing
brute-forcing tool (Hydra, Medusa, etc.) may be used: the webapp, its
password hashing, the lockout defense, and both attacker tools must
all be hand-written. Flask/SQLite are used only as the web/DB
*framework* (the assignment's allowed "environment"); the attack and
defense logic itself lives in this repo. Keep this constraint in mind
when modifying `db.py`/`defense.py` — don't replace the hand-rolled
hashing or lockout logic with a library call.

**Scope**: targets only the webapp in this repo, run locally or on a
private/host-only VM network for the assignment. Not for use against
systems the user doesn't own or have permission to test.

## Commands

Setup (from project root):
```bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt   # flask, requests
```

Run the vulnerable (baseline) target:
```bash
cd src
rm -f app.db
../.venv/bin/python seed.py          # creates demo accounts, fast hash, no lockout
../.venv/bin/python app.py           # serves on 0.0.0.0:5000
```

Run the defended target (lockout + slow PBKDF2 hashing):
```bash
cd src
rm -f app.db
../.venv/bin/python seed.py --defense
DEFENSE=1 ../.venv/bin/python app.py
```

Run the attacks (from `src/`, against either target):
```bash
../.venv/bin/python attacker_dict.py --url http://127.0.0.1:5000 --user alice --wordlist wordlist.txt
../.venv/bin/python attacker_spray.py --url http://127.0.0.1:5000 --userlist targets.txt --passwords known_passwords.txt
```

There is no test suite, linter, or build step in this repo — it's a
small demo app driven manually per the above.

## Architecture

- **`app.py`** — Flask webapp under attack. Routes: `/signup`,
  `/login`, `/dashboard`, `/logout`. A single `DEFENSE_MODE` flag (env
  var `DEFENSE=1`) toggles the countermeasure at runtime; both modes
  share the same routes/templates so the same attacker scripts work
  against either. Login responses are the attack-visible signal:
  `302` = success, `429` = locked out (defense mode only), `200` =
  failed. Logs every signup/login outcome to `src/logs/server.log`.
- **`db.py`** — SQLite user store (`src/app.db`) with hand-written
  password hashing: `defense=False` → single fast salted SHA-256;
  `defense=True` → salted PBKDF2-HMAC-SHA256 at `SLOW_HASH_ITERATIONS`
  (200k). `verify_user` hashes against a dummy salt even when the
  username doesn't exist, to avoid a timing side-channel that leaks
  username validity.
- **`defense.py`** — `LockoutTracker`: in-memory per-username failed-attempt
  window (`MAX_ATTEMPTS`/`WINDOW_SECONDS`) and lockout duration
  (`LOCKOUT_SECONDS`). Guarded by a `threading.Lock` in `app.py` around
  the check-then-record sequence in `/login`.
- **`seed.py`** — inserts a fixed set of demo accounts directly via
  `db.create_user`, bypassing the signup form. Must be re-run against
  a fresh `app.db` whenever the hashing mode changes (hash format must
  match the server's current `--defense`/`DEFENSE` setting or logins
  will fail). Seeded accounts and their intended role:
  - `alice`/`bob`/`carol` — weak passwords, dictionary-attack targets
  - `dave` — strong password, negative control (should resist both attacks)
  - `eve`/`frank` — shared weak default password, spray-attack targets
- **`attacker_dict.py`** — dictionary attack: iterates a wordlist
  against one `--user`, stops on first `302` (cracked) or `429`
  (locked out). Exposes `try_login()`, imported by `attacker_spray.py`.
- **`attacker_spray.py`** — spray attack: iterates passwords in the
  *outer* loop and usernames in the *inner* loop (one known password
  against every account before moving to the next password) so that a
  per-account failed-attempt threshold is less likely to trip than a
  per-account sweep would.
- **`templates/`** — signup/login/dashboard Jinja templates; take a
  `defense` flag to adjust copy shown to the user.
- **Word/target lists** — `wordlist.txt` (dictionary candidates),
  `known_passwords.txt` and `targets.txt` (spray attack passwords and
  target accounts).
- **`docs/design_report.tex`** — the assignment write-up (attack
  definitions, network topology, timing/packet diagrams); generally
  not something Claude needs to touch unless asked to update the report.

## Two-VM setup note

For the assignment's victim/attacker VM topology, copy `src/` and
`requirements.txt` to both VMs and create a **fresh venv on each** —
don't copy `.venv/` across machines (its activation scripts have
absolute paths and may not match the other VM's Python build).
