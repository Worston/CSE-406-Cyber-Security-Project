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
attacks below. No existing brute-forcing tool (Hydra, Medusa, etc.) is
used — the webapp, its password hashing, the lockout defense, and both
attacker tools are implemented in this repo from scratch, as required
by the assignment brief (`CSE406ProjectJan2026.pdf`). Flask/SQLite are
used only as the web/database *framework*, the same way the brief
allows standard libraries as "environment" — the attack and defense
logic itself is hand-written.

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
| [`src/wordlist.txt`](src/wordlist.txt) | Dictionary attack candidate passwords |
| [`src/known_passwords.txt`](src/known_passwords.txt) | Spray attack's known/default passwords |
| [`src/targets.txt`](src/targets.txt) | Spray attack's target account list |
| [`docs/design_report.md`](docs/design_report.md) | Attack definitions, topology, timing & packet diagrams |
| [`CSE406ProjectJan2026.pdf`](CSE406ProjectJan2026.pdf) | Original assignment brief |

See [`src/README.md`](src/README.md) for setup and run instructions
(single-host and two-VM), and [`docs/design_report.md`](docs/design_report.md)
for the write-up required by the assignment.

## Quick start

```bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt

cd src
../.venv/bin/python seed.py                                  # create demo accounts
../.venv/bin/python app.py &                                  # undefended target on :5000

../.venv/bin/python attacker_dict.py --url http://127.0.0.1:5000 \
    --user alice --wordlist wordlist.txt                      # dictionary attack

../.venv/bin/python attacker_spray.py --url http://127.0.0.1:5000 \
    --userlist targets.txt --passwords known_passwords.txt     # spray attack
```

Re-run with `DEFENSE=1` (and `seed.py --defense` against a fresh
`app.db`) to see the lockout + slow-hash countermeasure block both
attacks; details in [`src/README.md`](src/README.md).

## Requirements

Python 3.8+, plus Flask and requests (`requirements.txt`) — install
into a virtualenv, not system-wide.

## Scope & disclaimer

This project targets **only the webapp implemented in this repo**,
run locally or on a private/host-only virtual network created for the
assignment. It is coursework for CSE406 (BUET) and is not intended to
be run against any system you do not own or have explicit permission
to test.

## License

MIT — see [LICENSE](LICENSE).
