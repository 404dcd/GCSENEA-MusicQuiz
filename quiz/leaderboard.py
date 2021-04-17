from flask import (
    Blueprint, render_template, request, g, flash, url_for, redirect
)

from quiz.db import get_db

bp = Blueprint("leaderboard", __name__, url_prefix="/")


@bp.route("/leaderboard", methods=["GET"])
def leaderboard():
    db = get_db()
    advance = True
    try:
        page = int(request.args.get("page", 0))
        assert 0 <= page <= 1000000000000000
    except (ValueError, AssertionError):
        page = 0

    start = page * 10
    userssql = db.execute(
        "SELECT userid, highscore FROM game ORDER BY highscore DESC LIMIT 10 OFFSET ?",
        (start,)
    ).fetchall()
    if len(userssql) < 10:
        advance = False
        userssql = db.execute(
            "SELECT userid, highscore FROM game ORDER BY highscore LIMIT 10"
        ).fetchall()[::-1]
        start = db.execute(
            "SELECT COUNT(*) FROM game"
        ).fetchone()["COUNT(*)"] - len(userssql)

    users = []
    for u in userssql:
        name = db.execute(
            "SELECT username FROM users WHERE userid = ?",
            (u["userid"],)
        ).fetchone()
        users.append({"userid": u["userid"], "name": name["username"], "highscore": u["highscore"]})

    return render_template("leaderboard.html", users=users, start=start, advance=advance)
