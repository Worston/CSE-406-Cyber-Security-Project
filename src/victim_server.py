"""Custom TCP login server used as the attack target.

Wire protocol, one login attempt per TCP connection (own protocol, not
an existing service like FTP/SSH/Telnet):

    C -> S: USER <username>\\n
    S -> C: 331 password required\\n
    C -> S: PASS <password>\\n
    S -> C: 230 login ok\\n | 530 login failed\\n | 503 account locked\\n

The USER step never reveals whether the account exists, only whether a
password is required next, so the attacker learns nothing until PASS.
"""
import argparse
import logging
import os
import socketserver
import threading

from defense import LockoutTracker
from users import load_store, verify_password

lock = threading.Lock()
tracker = LockoutTracker()


class LoginHandler(socketserver.StreamRequestHandler):
    def handle(self):
        store = self.server.user_store
        defense = self.server.defense_enabled
        addr = self.client_address[0]

        line = self.rfile.readline().decode(errors="replace").strip()
        if not line.startswith("USER "):
            self.wfile.write(b"400 expected USER\n")
            return
        username = line[5:]
        self.wfile.write(b"331 password required\n")

        line = self.rfile.readline().decode(errors="replace").strip()
        if not line.startswith("PASS "):
            self.wfile.write(b"400 expected PASS\n")
            return
        password = line[5:]

        with lock:
            if defense and tracker.is_locked(username):
                self.wfile.write(b"503 account locked\n")
                logging.info("LOCKED  user=%s from=%s", username, addr)
                return

            ok = verify_password(store, username, password, defense)
            if ok:
                tracker.record_success(username)
            elif defense:
                tracker.record_failure(username)

        if ok:
            self.wfile.write(b"230 login ok\n")
            logging.info("SUCCESS user=%s from=%s", username, addr)
        else:
            self.wfile.write(b"530 login failed\n")
            logging.info("FAIL    user=%s from=%s", username, addr)


class LoginServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--defense", action="store_true",
                         help="enable lockout + slow (PBKDF2) password hashing")
    parser.add_argument("--log", default=os.path.join(os.path.dirname(__file__), "logs", "server.log"))
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.log), exist_ok=True)
    logging.basicConfig(filename=args.log, level=logging.INFO, format="%(asctime)s %(message)s")
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
    logging.getLogger().addHandler(console)

    server = LoginServer((args.host, args.port), LoginHandler)
    server.user_store = load_store()
    server.defense_enabled = args.defense
    print(f"victim_server listening on {args.host}:{args.port} (defense={'ON' if args.defense else 'OFF'})")
    server.serve_forever()


if __name__ == "__main__":
    main()
