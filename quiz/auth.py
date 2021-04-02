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
    if g.user:
        flash("You are already logged in.", "info")
        return redirect(url_for("index.index"))

    if request.method == "POST":
        username = request.form["username"]
        passwd = request.form["passwd"]
        db = get_db()

        errs = []
        if not valid(username, string.ascii_letters + string.digits + "_<>()/"):
            errs.append("Username is invalid - please use only letters, numbers and underscores")
        elif len(passwd) < 6:
            errs.append("Password must be 6 characters or longer.")

        elif db.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone() is not None:
            errs.append(f"User '{username}' is already registered.")

        if not errs:  # we can now register the user, all data is valid
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(passwd.encode("utf-8"), salt)
            db.execute(
                "INSERT INTO users (username, passwd, isadmin) VALUES (?, ?, ?)",
                (username, hashed, 0)
            )
            db.commit()
            return redirect(url_for("auth.login"))

        for err in errs:  # send errors to the template
            flash(err, "error")

    return render_template("auth/register.html")


@bp.route("/login", methods=("GET", "POST"))
def login():
    if g.user:
        flash("You are already logged in.", "info")
        return redirect(url_for("index.index"))

    if request.method == "POST":
        username = request.form["username"]
        passwd = request.form["passwd"]
        db = get_db()
        err = False
        user = db.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()

        if user is None:
            err = True
        elif not bcrypt.checkpw(passwd.encode("utf8"), user["passwd"]):
            err = True

        if not err:  # user can now be signed in
            token = token_hex()
            session.clear()
            session.permanent = True
            session["sessionid"] = token
            db.execute(
                "DELETE FROM cookies WHERE userid = ?", (user["userid"],)  # delete any previous
            )
            db.execute(
                "INSERT INTO cookies (sessionid, userid, expiration) VALUES (?, ?, ?)",
                (token, user["userid"], round(time.time()) + (30 * 60))  # expires after 1/2 hour
            )
            db.commit()

            flash("Successfully logged in.", "info")
            return redirect(url_for("index.index"))

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
            db.commit()
            g.user = None

        else:
            usr = db.execute(
                "SELECT * FROM users WHERE userid = ?", (cookie["userid"],)
            ).fetchone()
            g.user = {}
            for attr in ("userid", "username", "isadmin"):
                g.user[attr] = usr[attr]

    if g.user is None and request.endpoint in ("passwordreset", "admin", "play"):
        flash("You must be logged in to access this page!", "error")
        return redirect(url_for("auth.login"))  # a valid logged in session is required!

    if request.endpoint == "admin" and not g.user["isadmin"]:
        flash("You must be an admin to access this page!", "error")
        return redirect(url_for("index.index"))


@bp.route('/logout')
def logout():
    db = get_db()
    db.execute(
        "DELETE FROM cookies WHERE sessionid = ?", (session["sessionid"],)
    )
    db.commit()
    session.clear()
    return redirect(url_for("index.index"))
