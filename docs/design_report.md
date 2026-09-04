# Design Report — Tool 9: Dictionary Attack and Known Password Attack

*Group members: ______________  |  Course: CSE406  |  Deadline: Week 11*

*Responsibility split: fill in per-member ownership before submitting
(e.g. Member A — webapp + defense; Member B — attacker tools + report
diagrams).*

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

Both attacks target a small signup/login web application we built
ourselves (`src/app.py`, Flask + SQLite) — per supervisor guidance,
the victim is a basic webapp with real signup/login/database, not an
existing service. The "victim action" is a normal user signing up and
logging in through the browser; the "attacker action" is the two
attacks below, driven by our own HTTP client code (`attacker_dict.py`,
`attacker_spray.py`) — not an existing brute-forcing tool.

**Topology:**

```
        Host-only / internal virtual network (192.168.56.0/24)

  +------------------------+                   +--------------------------+
  |   Attacker VM           |                   |   Victim VM               |
  |   192.168.56.10          |  <-- HTTP:5000 -->|   192.168.56.20            |
  |                           |                   |                            |
  |  attacker_dict.py         |                   |  app.py (Flask)            |
  |  attacker_spray.py        |                   |  db.py + app.db (SQLite)   |
  |  wordlist.txt               |                   |  defense.py (lockout)      |
  |  known_passwords.txt        |                   |  logs/server.log             |
  +------------------------+                   +--------------------------+
                                                          ^
                                                          | HTTP (browser)
                                                    +------------+
                                                    | Legit user  |
                                                    | (victim VM  |
                                                    |  or 3rd host)|
                                                    +------------+
```

*(Replace with your actual VirtualBox host-only subnet/IPs once the
VMs are set up; add a screenshot of `ip addr` from both VMs.)*

## b. Timing diagrams

**Normal (legitimate) signup + login — browser flow:**

```
Browser                                   Server (Flask)
  |  GET /signup                              |
  |------------------------------------------->|
  |                          200 signup form   |
  |<-------------------------------------------|
  |  POST /signup  username=alice&password=... |
  |------------------------------------------->|
  |                302 redirect -> /login       |
  |<-------------------------------------------|
  |  GET /login                                 |
  |------------------------------------------->|
  |                            200 login form   |
  |<-------------------------------------------|
  |  POST /login  username=alice&password=...   |
  |------------------------------------------->|
  |               302 redirect -> /dashboard    |
  |<-------------------------------------------|
  |  GET /dashboard  (Cookie: session=...)       |
  |------------------------------------------->|
  |                        200 "Welcome, alice"  |
  |<-------------------------------------------|
```

**Dictionary attack — repeated exchange, one account:**

```
for each password in wordlist:
    POST /login  username=alice&password=<candidate>
        -> 200 (login page, "invalid username or password")   (repeat, N times)
        ...
    POST /login  username=alice&password=<candidate_k>
        -> 302 Location: /dashboard                            (attack ends: success)
```

**Known-password attack — repeated exchange, many accounts:**

```
for each known_password in {admin123, password123, ...}:
    for each username in {alice, bob, carol, dave, eve, frank}:
        POST /login  username=<username>&password=<known_password>
            -> 200 (failed)  |  302 (success)
```

**With the lockout defense active:**

```
attempt 1..4: POST /login -> 200 "invalid username or password"
attempt 5:    POST /login -> 200 "invalid username or password"   (5th failure -> lockout armed)
attempt 6+:   POST /login -> 429 "account temporarily locked"     (attack blocked for 60s)
```

*(Redraw these as proper sequence diagrams — e.g. with draw.io,
PlantUML, or Mermaid — for the submitted report; the ASCII versions
above are the content to transcribe.)*

## c. Packet / frame / segment details

Transport: standard TCP carrying HTTP/1.1 (Flask's built-in dev
server) — no raw Ethernet/IP crafting is needed for this attack class,
since the exploit is at the application layer. What we designed
ourselves is the **application behavior and payload** the HTTP request
carries and how the server interprets it — not an existing auth
protocol implementation.

**Request (attacker or browser -> server), one per login attempt:**

```
POST /login HTTP/1.1
Host: 192.168.56.20:5000
Content-Type: application/x-www-form-urlencoded
Content-Length: 33

username=alice&password=sunshine
```

**Responses, by outcome:**

| Outcome | Status | Notable headers/body |
|---|---|---|
| Success | `302 FOUND` | `Location: /dashboard`, `Set-Cookie: session=...` |
| Failure | `200 OK` | login page HTML containing "invalid username or password" |
| Locked (defense on) | `429 TOO MANY REQUESTS` | login page HTML containing "account temporarily locked" |

Design notes to include with packet captures:
- Each attempt opens its own TCP connection (the attacker scripts use
  a plain `requests.post()` call per attempt, no session reuse) — a
  full 3-way handshake, HTTP request/response, then FIN/ACK teardown
  per attempt. Capture this in Wireshark and annotate source/
  destination port, sequence numbers, and the HTTP payload of each
  segment (`Follow > HTTP Stream` is the easiest way to show this in
  the report).
- The response to a failed login is intentionally the same generic
  "invalid username or password" whether the username doesn't exist
  or the password is wrong — the app does not leak account existence.
  Constant-shape hashing (`db.py`, `verify_user`) additionally hashes
  against a dummy salt when the username doesn't exist, so a
  nonexistent-user request doesn't return measurably faster than a
  wrong-password request.
- Server-side credential storage: `salt (16 bytes) + SHA-256(salt +
  password)` in undefended mode; `salt + PBKDF2-HMAC-SHA256(password,
  salt, 200000 iterations)` in defended mode. Passwords are sent in
  cleartext form data over plain HTTP in this demo (no TLS) — a
  deliberate simplification consistent with the assignment's other
  plaintext-protocol attacks (e.g. Tool 2's Telnet/HTTP sniffing), and
  worth noting as a limitation vs. a production deployment (which
  would use HTTPS).

## d. Justification

- The victim accounts are deliberately seeded with passwords drawn
  from `wordlist.txt` (alice/bob/carol), so the dictionary attack is
  expected to succeed within the first few dozen attempts — measured
  locally: `alice` cracked in 17/50 attempts (~0.03s, undefended).
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
  network/CPU allows, making a wordlist of any realistic size
  crackable in seconds. This justifies why the lockout + slow-hash
  countermeasure is necessary and measurably effective: in local
  testing, enabling `DEFENSE=1` raised each login attempt's cost from
  roughly 1-2 ms to ~55 ms (PBKDF2, 200,000 iterations) and the
  dictionary attack against `alice` was locked out (`HTTP 429`) after
  6 attempts (~0.27s), fully blocking the crack.

---
*TODO before submission:* replace the ASCII diagrams with drawn
versions, insert VM IP addresses and an `ifconfig`/`ip addr`
screenshot, insert a Wireshark capture screenshot with 2-3 annotated
HTTP request/response pairs (and a "Follow HTTP Stream" view), and a
browser screenshot of a normal signup + login + dashboard flow as the
"victim action" evidence. Numbers above are from local single-host
testing — rerun on your VMs and update.
