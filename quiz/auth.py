import string
import bcrypt

from flask import (
    Blueprint, request, flash, redirect, url_for, render_template
)

from quiz.db import get_db

bp = Blueprint("auth", __name__, url_prefix="/auth")


def valid(checkstr, charset):
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

        if not errs:
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(passwd.encode("utf-8"), salt)
            db.execute(
                "INSERT INTO user (username, passwd, display) VALUES (?, ?, ?)",
                (username, hashed, display)
            )
            db.commit()
            return redirect(url_for("auth.login"))

        for err in errs:
            flash(err, "error")

    return render_template("auth/register.html")
