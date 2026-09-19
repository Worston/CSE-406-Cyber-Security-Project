# Dictionary Attack & Known-Password (Spray) Attack — CSE406 Tool 9

A from-scratch demonstration of two classic online password-guessing
attacks — a **dictionary attack** (many passwords against one account)
and a **known-password / spray attack** (a few known passwords against
many accounts) — against a small Flask + SQLite signup/login webapp,
plus a working countermeasure (account lockout + slow password
hashing).

Per supervisor guidance, the victim is a basic web application with
its own signup/login/database: "victim action" is signing up and
logging in normally through the browser; "attacker action" is the two
attacks below. Defense (lockout + slow password hashing) is a core
part of the project, not just the bonus. No existing brute-forcing
tool (Hydra, Medusa, etc.) is used — the webapp, its password hashing,
the lockout defense, and both attacker tools are implemented in this
repo from scratch, as required by the assignment brief
(`CSE406ProjectJan2026.pdf`). Flask/SQLite are used only as the
web/database *framework*, the same way the brief allows standard
libraries as "environment" — the attack and defense logic itself is
hand-written.

Password hashing itself is hand-written in `src/db.py` (salted
SHA-256 in vulnerable mode, salted PBKDF2-HMAC-SHA256 in defended
mode). The attacker scripts are our own code driving plain HTTP
requests, not an existing brute-forcer.

## Contents

| Path | Purpose |
|------|---------|
| [`src/app.py`](src/app.py) | Flask webapp: signup, login, dashboard (the attack target) |
| [`src/db.py`](src/db.py) | SQLite user store + hand-written password hashing (fast/slow modes) |
| [`src/defense.py`](src/defense.py) | Lockout tracker (countermeasure) |
| [`src/seed.py`](src/seed.py) | Creates the demo accounts |
| [`src/attacker_dict.py`](src/attacker_dict.py) | Dictionary attack: one account, many passwords |
| [`src/attacker_spray.py`](src/attacker_spray.py) | Known-password attack: many accounts, few passwords |
| [`src/templates/`](src/templates) | Signup / login / dashboard pages |
| [`src/wordlist.txt`](src/wordlist.txt) | Dictionary attack candidate passwords (top 1000 real-world leaked passwords, from [SecLists](https://github.com/danielmiessler/SecLists)) |
| [`src/known_passwords.txt`](src/known_passwords.txt) | Spray attack's known/default passwords (from SecLists' Default-Credentials and corporate seasonal-spray corpora) |
| [`src/targets.txt`](src/targets.txt) | Spray attack's target account list |
| [`docs/design_report.tex`](docs/design_report.tex) | Design report: attack definitions, topology, timing & packet diagrams |
| [`docs/final_report.tex`](docs/final_report.tex) | Final report: steps, observations, and defense assessment |
| [`CSE406ProjectJan2026.pdf`](CSE406ProjectJan2026.pdf) | Original assignment brief |

## One-time setup

From the project root:

```bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
```

## Demo 1 — vulnerable (baseline)

```bash
cd src
rm -f app.db
../.venv/bin/python seed.py                 # creates demo accounts, fast hash, no lockout
../.venv/bin/python app.py                   # starts server on 0.0.0.0:5000
```

In a browser: open `http://<victim-ip>:5000/signup`, create a new
account, then log in with it — this is the "victim" normal-use
screenshot for the report.

From the attacker machine/terminal:

```bash
python attacker_dict.py --url http://<victim-ip>:5000 --user alice --wordlist wordlist.txt
python attacker_spray.py --url http://<victim-ip>:5000 --userlist targets.txt --passwords known_passwords.txt
```

Expected: `alice` cracked within ~50 attempts; `eve` and `frank`
compromised by the shared default password `admin123`; `dave` (strong
password) resists both.

## Demo 2 — defended

```bash
cd src
rm -f app.db
../.venv/bin/python seed.py --defense
DEFENSE=1 ../.venv/bin/python app.py
```

Re-run the exact same attacker commands. Expected: each login attempt
that actually checks a password takes noticeably longer (PBKDF2,
~200k iterations), and the account locks (`HTTP 429`) after 5 failed
attempts within 30s, for 60s — blocking the dictionary attack
outright. A locked-out attempt skips hashing entirely and comes back
fast, since the lockout check happens before the password is ever
checked. Compare `src/logs/server.log` and the attacker logs between
the two runs for the report's before/after evidence.

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

## Two-VM / two-device setup

Copy the whole project (or at least `src/` and `requirements.txt`) to
both machines and create a **fresh venv on each** — don't copy
`.venv/` itself across machines, since its activation scripts have
absolute paths baked in and it may not match the other machine's
Python build:

```bash
python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt
```

Victim machine runs `app.py` bound to `0.0.0.0`; attacker machine runs
the two attacker scripts pointed at the victim's IP over `http://`.
Capture a browser screenshot of a normal signup/login on the victim
machine, and terminal screenshots of an attack run for the final
report's evidence.

## Requirements

Python 3.8+, plus Flask and requests (`requirements.txt`) — install
into a virtualenv, not system-wide.

## Scope & disclaimer

This project targets **only the webapp implemented in this repo**,
run locally or on a private/host-only network created for the
assignment. It is coursework for CSE406 (BUET) and is not intended to
be run against any system you do not own or have explicit permission
to test.

## License

MIT — see [LICENSE](LICENSE).
