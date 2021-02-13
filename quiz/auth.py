import string
import bcrypt
from secrets import token_hex
import time

from flask import (
    Blueprint, request, flash, redirect, url_for, render_template, session, g
)

from quiz.db import get_db

bp = Blueprint("auth", __name__, url_prefix="/auth")


def valid(checkstr, charset):  # returns True if a non-empty checkstr contains only charset
    for char in checkstr:
        if char not in charset:
            return False
    return bool(checkstr)


@bp.route("/register", methods=("GET", "POST"))
def register():
    if request.method == "POST":
        username = request.form["username"]
        passwd = request.form["passwd"]
        display = request.form["display"]
        db = get_db()

        errs = []
        if not valid(username, string.ascii_letters + string.digits + "_"):
            errs.append("Username is invalid - please use only letters, numbers and underscores")
        elif len(passwd) < 6:
            errs.append("Password must be 6 characters or longer.")
        elif not valid(display, string.ascii_letters + string.digits + string.punctuation + " "):
            errs.append("Display name is invalid - please use only letters, digits and punctuation")

        elif db.execute(
            "SELECT id FROM user WHERE username = ?", (username,)
        ).fetchone() is not None:
            errs.append(f"User {username} is already registered.")

        if not errs:  # we can now register the user, all data is valid
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(passwd.encode("utf-8"), salt)
            db.execute(
                "INSERT INTO user (username, passwd, display, isadmin) VALUES (?, ?, ?, ?)",
                (username, hashed, display, 0)
            )
            db.commit()
            return redirect(url_for("auth.login"))

        for err in errs:  # send errors to the template
            flash(err, "error")

    return render_template("auth/register.html")


@bp.route("/login", methods=("GET", "POST"))
def login():
    if request.method == "POST":
        username = request.form["username"]
        passwd = request.form["passwd"]
        db = get_db()
        err = False
        user = db.execute(
            "SELECT * FROM user WHERE username = ?", (username,)
        ).fetchone()

        if user is None:
            err = True
        elif not bcrypt.checkpw(passwd, user["passwd"]):
            err = True

        if not err:  # user can now be signed in
            token = token_hex()
            session.clear()
            session.permanent = True
            session["sessionid"] = token
            db.execute(
                "INSERT INTO cookies (sessionid, userid, expiration) VALUES (?, ?, ?)",
                (token, user["userid"], round(time.time()) + (30 * 60))  # expires after 1/2 hour
            )

            return redirect(url_for("index"))

        flash("Invalid username or password.", "error")

    return render_template("auth/login.html")


@bp.before_app_request
def load_logged_in_user():
    sessionid = session.get("sessionid")

    if sessionid is None:
        g.user = None

    else:
        db = get_db()
        cookie = db.execute(
            "SELECT * FROM cookies WHERE sessionid = ?", (sessionid,)
        ).fetchone()

        if cookie is None or cookie["expiration"] < time.time():  # expired or not found
            session.clear()  # clear the bad cookie
            db.execute(
                "DELETE FROM cookies WHERE sessionid = ?", (sessionid,)
            )
            g.user = None

        else:
            g.user = db.execute(
                "SELECT * FROM users WHERE userid = ", (cookie["userid"],)
            ).fetchone()

    if g.user is None and request.endpoint in ("admin", "play", "passwordreset"):
        return redirect(url_for("auth.login"))  # a valid logged in session is required!
