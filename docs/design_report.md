# Design Report — Tool 9: Dictionary Attack and Known Password Attack

*Group members: ______________  |  Course: CSE406  |  Deadline: Week 11*

*Responsibility split: fill in per-member ownership before submitting
(e.g. Member A — victim server + defense; Member B — attacker tools +
report diagrams).*

## a. Definition of the attack + topology diagram

**Dictionary attack**: the attacker targets one specific account and
tries a large ordered list of candidate passwords (a "dictionary" of
common/likely passwords) against it, one at a time, until the server
accepts one or the list is exhausted. The attack works because many
users choose passwords that appear in common wordlists.

**Known password attack (password spraying / credential reuse)**: the
attacker instead starts from a small set of *known* passwords —
defaults, previously breached passwords, or passwords obtained from
another attack (e.g. sniffing) — and tries each one against a **wide
list of accounts**. This exploits password reuse and default
credentials rather than weak individual passwords, and is harder to
detect with a naive per-account lockout because no single account
receives many failed attempts.

Both attacks are implemented as active online attacks against a
custom TCP login service we wrote (`victim_server.py`) — not against
an existing service like SSH/FTP, since the assignment requires our
own protocol implementation.

**Topology:**

```
        Host-only / internal virtual network (192.168.56.0/24)

  +----------------------+                     +----------------------+
  |   Attacker VM        |                     |   Victim VM           |
  |   192.168.56.10       |  <---- TCP:5000 --->|   192.168.56.20        |
  |                        |                     |                        |
  |  attacker_dict.py      |                     |  victim_server.py      |
  |  attacker_spray.py     |                     |  users.json            |
  |  wordlist.txt           |                     |  defense.py (lockout)  |
  |  known_passwords.txt    |                     |  logs/server.log        |
  +----------------------+                     +----------------------+
```

*(Replace with your actual VirtualBox host-only subnet/IPs once the
VMs are set up; add a screenshot of `ip addr` from both VMs.)*

## b. Timing diagrams

**Normal (legitimate) login — single exchange:**

```
Client                          Server
  |  connect                       |
  |-------------------------------->|
  |  USER alice\n                   |
  |-------------------------------->|
  |            331 password required|
  |<--------------------------------|
  |  PASS <correct password>\n      |
  |-------------------------------->|
  |                     230 login ok|
  |<--------------------------------|
  |  close                          |
```

**Dictionary attack — repeated exchange, one account:**

```
for each password in wordlist:
    connect -> USER alice -> 331
    PASS <candidate> -> 530 login failed   (repeat, N times)
    ...
    PASS <candidate_k> -> 230 login ok     (attack ends: success)
```

**Known-password attack — repeated exchange, many accounts:**

```
for each known_password in {admin123, password123, ...}:
    for each username in {alice, bob, carol, dave, eve, frank}:
        connect -> USER <username> -> 331
        PASS <known_password> -> 530 | 230
```

**With the lockout defense active:**

```
attempt 1..4: PASS <candidate> -> 530 login failed
attempt 5:    PASS <candidate> -> 530 login failed   (5th failure -> lockout armed)
attempt 6+:   PASS <candidate> -> 503 account locked (attack blocked for 60s)
```

*(Redraw these as proper sequence diagrams — e.g. with draw.io,
PlantUML, or Mermaid — for the submitted report; the ASCII versions
above are the content to transcribe.)*

## c. Packet / frame / segment details

Transport: standard TCP (SOCK_STREAM) over the virtual network — no
raw Ethernet/IP crafting is needed for this attack class, since the
exploit is at the application layer. What we designed ourselves is the
**application-layer protocol** carried in the TCP payload:

| Direction | Message            | Format                          |
|-----------|---------------------|----------------------------------|
| C -> S    | Username            | `USER <username>\n`             |
| S -> C    | Ack, request password | `331 password required\n`    |
| C -> S    | Password attempt    | `PASS <password>\n`             |
| S -> C    | Success             | `230 login ok\n`                 |
| S -> C    | Failure             | `530 login failed\n`            |
| S -> C    | Locked (defense on) | `503 account locked\n`          |
| S -> C    | Malformed request   | `400 expected USER\|PASS\n`     |

Design notes to include with packet captures:
- One TCP connection = one login attempt (3-way handshake, 2 payload
  round trips, FIN/ACK teardown) — capture this in Wireshark and
  annotate source/destination port, sequence numbers, and the ASCII
  payload of each segment.
- The `USER` response is identical (`331`) whether or not the account
  exists, so the protocol does not leak account existence before the
  password stage — note this as a deliberate design choice.
- Server-side credential storage: `salt (16 bytes) + SHA-256(salt +
  password)` in undefended mode; `salt + PBKDF2-HMAC-SHA256(password,
  salt, 200000 iterations)` in defended mode. Passwords are never
  stored or transmitted in plaintext except as the live attack
  attempt itself (mirroring how a real Telnet/FTP-style plaintext
  login is vulnerable to sniffing, tying back to Tool 2 in this
  course).

## d. Justification

- The victim accounts are deliberately seeded with passwords drawn
  from `wordlist.txt` (alice/bob/carol), so the dictionary attack is
  expected to succeed within the first few dozen attempts — we
  estimate success within *N* attempts out of a *M*-word list (fill
  in actual N from your test run; measured locally: 17/50 attempts).
- `eve` and `frank` share a common default password (`admin123`) that
  also exists in `known_passwords.txt`, so the spray attack is
  expected to compromise both without needing a large wordlist against
  either account individually — validated in local testing (2/6
  accounts compromised in one spray pass).
- `dave` uses a high-entropy password absent from both lists and is
  expected to resist both attacks — this is our negative control,
  demonstrating the attacks fail against passwords that aren't
  guessable from common lists, not just "the tool is broken."
- Without rate limiting, an attacker can attempt logins as fast as the
  network/CPU allows (measured: ~1700 attempts/sec locally against the
  undefended server), making a wordlist of any realistic size
  crackable in seconds. This justifies why the lockout + slow-hash
  countermeasure (Section d of the Final Report) is necessary and
  measurably effective (measured: PBKDF2 raises per-attempt cost from
  ~0.06 ms to ~90 ms, and lockout halts the attack entirely after 5
  failed attempts).

---
*TODO before submission:* replace the ASCII diagrams with drawn
versions, insert VM IP addresses and an `ifconfig`/`ip addr`
screenshot, insert a Wireshark capture screenshot with 2-3 annotated
packets, and fill in the actual measured numbers from your own test
run (some placeholders above are pre-filled from a local test — rerun
on your VMs and update).
