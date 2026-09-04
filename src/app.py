"""Demo signup/login webapp — the attack target.

Run with DEFENSE=1 to enable the lockout + slow-hash countermeasure,
DEFENSE unset/0 for the deliberately vulnerable baseline. Both modes
share the same routes; only the hashing cost and lockout enforcement
differ, so the same attacker tools can be pointed at either.
"""
import logging
import os
import threading

from flask import Flask, redirect, render_template, request, session, url_for

import db
from defense import LockoutTracker

BASE_DIR = os.path.dirname(__file__)
os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)

DEFENSE_MODE = os.environ.get("DEFENSE", "0") == "1"

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-not-for-production")

lock = threading.Lock()
tracker = LockoutTracker()

logging.basicConfig(
    filename=os.path.join(BASE_DIR, "logs", "server.log"),
    level=logging.INFO,
    format="%(asctime)s %(message)s",
)
console = logging.StreamHandler()
console.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
logging.getLogger().addHandler(console)

db.init_db()


@app.route("/")
def index():
    return redirect(url_for("dashboard" if "username" in session else "login"))


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html", defense=DEFENSE_MODE, error=None)

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    if not username or not password:
        return render_template("signup.html", defense=DEFENSE_MODE, error="username and password required"), 400

    if not db.create_user(username, password, DEFENSE_MODE):
        return render_template("signup.html", defense=DEFENSE_MODE, error="username already taken"), 400

    logging.info("SIGNUP  user=%s from=%s", username, request.remote_addr)
    return redirect(url_for("login", signed_up="1"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template(
            "login.html", defense=DEFENSE_MODE, error=None, signed_up=request.args.get("signed_up")
        )

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    with lock:
        if DEFENSE_MODE and tracker.is_locked(username):
            logging.info("LOCKED  user=%s from=%s", username, request.remote_addr)
            return render_template(
                "login.html", defense=DEFENSE_MODE, error="account temporarily locked, try again later", signed_up=None
            ), 429

        ok = db.verify_user(username, password, DEFENSE_MODE)
        if ok:
            tracker.record_success(username)
        elif DEFENSE_MODE:
            tracker.record_failure(username)

    if ok:
        session["username"] = username
        logging.info("SUCCESS user=%s from=%s", username, request.remote_addr)
        return redirect(url_for("dashboard"))

    logging.info("FAIL    user=%s from=%s", username, request.remote_addr)
    return render_template("login.html", defense=DEFENSE_MODE, error="invalid username or password", signed_up=None), 200


@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html", username=session["username"])


@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))


if __name__ == "__main__":
    print(f"webapp starting on 0.0.0.0:5000 (defense={'ON' if DEFENSE_MODE else 'OFF'})")
    app.run(host="0.0.0.0", port=5000, debug=False)
