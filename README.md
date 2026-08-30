# Dictionary Attack & Known-Password (Spray) Attack — CSE406 Tool 9

A from-scratch demonstration of two classic online password-guessing
attacks — a **dictionary attack** (many passwords against one account)
and a **known-password / spray attack** (a few known passwords against
many accounts) — against a custom TCP login service, plus a working
countermeasure (account lockout + slow password hashing).

No existing brute-forcing tool (Hydra, Medusa, etc.) or existing login
protocol (SSH/FTP/Telnet) is used: the victim server, wire protocol,
and both attacker tools are implemented in this repo from scratch, as
required by the assignment brief (`CSE406ProjectJan2026.pdf`).

## Contents

| Path | Purpose |
|------|---------|
| [`src/victim_server.py`](src/victim_server.py) | Custom TCP login server (the attack target) |
| [`src/attacker_dict.py`](src/attacker_dict.py) | Dictionary attack: one account, many passwords |
| [`src/attacker_spray.py`](src/attacker_spray.py) | Known-password attack: many accounts, few passwords |
| [`src/defense.py`](src/defense.py) | Lockout tracker (countermeasure) |
| [`src/users.py`](src/users.py) | Seeds and loads the hashed credential store |
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
cd src
python3 users.py                                            # generate users.json
python3 victim_server.py --host 0.0.0.0 --port 5000 &        # undefended target

python3 attacker_dict.py --host 127.0.0.1 --port 5000 \
    --user alice --wordlist wordlist.txt                     # dictionary attack

python3 attacker_spray.py --host 127.0.0.1 --port 5000 \
    --userlist targets.txt --passwords known_passwords.txt   # spray attack
```

Re-run the victim server with `--defense` to see the lockout +
slow-hash countermeasure block both attacks; details in
[`src/README.md`](src/README.md).

## Requirements

Python 3.8+, standard library only — no third-party packages.

## Scope & disclaimer

This project targets **only the custom server implemented in this
repo**, running on a private/host-only virtual network created for the
assignment. It is coursework for CSE406 (BUET) and is not intended to
be run against any system you do not own or have explicit permission
to test.

## License

MIT — see [LICENSE](LICENSE).
