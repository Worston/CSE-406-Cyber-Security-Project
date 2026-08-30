# Dictionary Attack + Known Password Attack — Tool 9

Custom TCP login server ("victim") and two attacker tools, built from
scratch (no existing brute-forcing/cracking tool used). See the wire
protocol documented at the top of `victim_server.py`.

## Setup

```
cd src
python3 users.py          # generates users.json (seeded accounts)
```

Seeded accounts (`users.py` for the plaintext — used only to build the
report/demo, real passwords are never sent anywhere except the attack
itself):

| user  | role in the demo                                   |
|-------|------------------------------------------------------|
| alice | dictionary-attack target (weak password)              |
| bob   | dictionary-attack target (weak password)              |
| carol | dictionary-attack target (weak password)              |
| dave  | negative control — strong password, should NOT crack  |
| eve   | known-password / spray target (shared default pw)     |
| frank | known-password / spray target (same shared default)   |

## Run — undefended (baseline)

Terminal 1 (victim):
```
python3 victim_server.py --host 0.0.0.0 --port 5000
```

Terminal 2 (attacker) — dictionary attack on one account:
```
python3 attacker_dict.py --host <victim_ip> --port 5000 --user alice --wordlist wordlist.txt
```

Terminal 2 (attacker) — known-password attack across accounts:
```
python3 attacker_spray.py --host <victim_ip> --port 5000 --userlist targets.txt --passwords known_passwords.txt
```

## Run — defended (bonus countermeasure: lockout + slow hash)

```
python3 victim_server.py --host 0.0.0.0 --port 5000 --defense
```

Re-run the same attacker commands against this server and compare
`logs/attacker_dict.log` / `logs/attacker_spray.log` and
`logs/server.log` against the undefended run.

## Two-VM setup

1. Create two VMs (attacker, victim) on a VirtualBox/VMware host-only
   or internal network.
2. Run `victim_server.py` on the victim VM, bound to `0.0.0.0`.
3. Run the attacker scripts from the attacker VM pointed at the
   victim's IP.
4. Capture a Wireshark trace on either VM for the packet-detail
   section of the design report (Wireshark is used only to observe
   traffic, not as part of the attack tool itself).
