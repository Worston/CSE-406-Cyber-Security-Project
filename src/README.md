# Dictionary Attack + Known Password Attack — Webapp Version

Per supervisor guidance: a basic signup/login webapp (Flask + SQLite)
is the victim application. "Victim action" = signing up and logging
in normally. "Attacker action" = the two attacks below. Defense
(lockout + slow password hashing) is implemented as a core part of
the project, not just the bonus.

Password hashing itself is hand-written in `db.py` (salted SHA-256 in
vulnerable mode, salted PBKDF2-HMAC-SHA256 in defended mode) — Flask
is used only as the web/HTTP framework, not as an attack tool. The
attacker scripts are our own code driving plain HTTP requests, not an
existing brute-forcer.

## One-time setup

From the project root:
```
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
```

## Demo 1 — vulnerable (baseline)

```
cd src
rm -f app.db
../.venv/bin/python seed.py                 # creates demo accounts, fast hash, no lockout
../.venv/bin/python app.py                   # starts server on 0.0.0.0:5000
```

In a browser: open `http://<victim-ip>:5000/signup`, create a new
account, then log in with it — this is the "victim" normal-use
screenshot for the report.

From the attacker machine/terminal:
```
python attacker_dict.py --url http://<victim-ip>:5000 --user alice --wordlist wordlist.txt
python attacker_spray.py --url http://<victim-ip>:5000 --userlist targets.txt --passwords known_passwords.txt
```

Expected: `alice` cracked within ~20 attempts; `eve` and `frank`
compromised by the shared default password `admin123`; `dave` (strong
password) resists both.

## Demo 2 — defended

```
cd src
rm -f app.db
../.venv/bin/python seed.py --defense
DEFENSE=1 ../.venv/bin/python app.py
```

Re-run the exact same attacker commands. Expected: each login attempt
takes noticeably longer (PBKDF2, ~200k iterations), and the account
locks (`HTTP 429`) after 5 failed attempts within 30s, for 60s —
blocking the dictionary attack outright. Compare `logs/server.log`
and the attacker logs between the two runs for the report's
before/after evidence.

## Seeded accounts (`seed.py`)

| user  | password       | role                                            |
|-------|----------------|--------------------------------------------------|
| alice | sunshine       | dictionary-attack target                          |
| bob   | dragon         | dictionary-attack target                          |
| carol | letmein        | dictionary-attack target                          |
| dave  | Xk7$vQ2!mZpL9r | negative control — should resist both attacks     |
| eve   | admin123       | known-password / spray target (shared default)    |
| frank | admin123       | known-password / spray target (shared default)    |

## Response signals the attacker tools rely on

- `HTTP 302` (redirect to `/dashboard`) → login succeeded
- `HTTP 429` → account locked (defense mode only)
- `HTTP 200` → login failed

## Two-VM setup

Copy the whole project (or at least `src/` and `requirements.txt`) to
both VMs and create a **fresh venv on each** — don't copy `.venv/`
itself across machines, since its activation scripts have absolute
paths baked in and it may not match the VM's Python build:

```
python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt
```

Victim VM runs `app.py` bound to `0.0.0.0`; attacker VM runs the two
attacker scripts pointed at the victim's IP over `http://`. Capture a
browser screenshot of a normal signup/login on the victim VM, and a
Wireshark trace of the HTTP POST traffic for the design report's
packet-detail section.
