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


def checkep(ep):
    if ep:
        if "." in ep and ep.split(".")[0] == "admin":
            return True
    return False


@bp.route("/register", methods=("GET", "POST"))
def register():
    if g.user:
        flash("You are already logged in.", "info")
        return redirect(url_for("index.index"))

    if request.method == "POST":
        username = request.form["username"]
        passwd1 = request.form["passwd1"]
        passwd2 = request.form["passwd2"]
        db = get_db()

        errs = []
        if not valid(username, string.ascii_letters + string.digits + "_"):
            errs.append("Username is invalid - please use only letters, numbers and underscores")
        if len(passwd1) < 6 or len(passwd2) < 6:
            errs.append("Password must be 6 characters or longer.")
        if passwd1 != passwd2:
            errs.append("Passwords do not match.")

        if db.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone() is not None:
            errs.append("That user is already registered.")

        if not errs:  # we can now register the user, all data is valid
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(passwd1.encode("utf-8"), salt)
            db.execute(
                "INSERT INTO users (username, passwd, isadmin) VALUES (?, ?, ?)",
                (username, hashed, 0)
            )
            db.commit()
            return redirect(url_for("auth.login"))

        for err in errs:  # send errors to the template
            flash(err, "danger")

    return render_template("auth/register.html")


@bp.route("/changepw", methods=("GET", "POST"))
def changepw():
    if request.method == "POST":
        passwd1 = request.form["passwd1"]
        passwd2 = request.form["passwd2"]
        db = get_db()

        errs = []
        if len(passwd1) < 6 or len(passwd2) < 6:
            errs.append("Password must be 6 characters or longer.")
        if passwd1 != passwd2:
            errs.append("Passwords do not match.")

        if not errs:  # we can now change passwd
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(passwd1.encode("utf-8"), salt)
            db.execute(
                "UPDATE users SET passwd = ? WHERE userid = ?",
                (hashed, g.user["userid"])
            )
            db.commit()
            return redirect(url_for("auth.logout"))

        for err in errs:  # send errors to the template
            flash(err, "danger")

    return render_template("auth/changepw.html")



@bp.route("/login", methods=("GET", "POST"))
def login():
    if g.user:
        flash("You are already logged in.", "info")
        return redirect(url_for("index.index"))

    if request.method == "POST":
        username = request.form["username"]
        passwd = request.form["passwd"]
        remember = "remember-me" in request.form
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
            expire = 60 * 10
            if remember:
                expire = 60 * 60 * 24 * 7
            db.execute(
                "INSERT INTO cookies (sessionid, userid, expiration) VALUES (?, ?, ?)",
                (token, user["userid"], round(time.time()) + expire)
            )
            db.commit()

            flash("Successfully logged in.", "success")
            return redirect(url_for("index.index"))

        flash("Invalid username or password.", "danger")

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

    if g.user is None:
        if request.endpoint in ("auth.changepw", "game.play") or checkep(request.endpoint):
            flash("You must be logged in to access this page!", "danger")
            return redirect(url_for("auth.login"))  # a valid logged in session is required!

    elif checkep(request.endpoint) and not g.user["isadmin"]:
        flash("You must be an admin to access this page!", "danger")
        return redirect(url_for("index.index"))


@bp.route('/logout')
def logout():
    if "sessionid" not in session:
        return redirect(url_for("index.index"))
    db = get_db()
    db.execute(
        "DELETE FROM cookies WHERE sessionid = ?", (session["sessionid"],)
    )
    db.commit()
    session.clear()
    return redirect(url_for("index.index"))
