from flask import (
    Blueprint, render_template, request, g, flash, url_for, redirect
)

from quiz.db import get_db

bp = Blueprint("leaderboard", __name__, url_prefix="/")


@bp.route("/leaderboard", methods=["GET"])
def leaderboard():
    db = get_db()
    try:
        page = int(request.args.get("page", 0))
        assert 0 <= page <= 1000000000000000
    except (ValueError, AssertionError):
        page = 0

    userssql = db.execute(
        "SELECT userid, highscore FROM game ORDER BY highscore DESC LIMIT 10 OFFSET ?",
        (page * 10,)
    ).fetchall()
    if len(userssql) < 10:
        userssql = db.execute(
            "SELECT userid, highscore FROM game ORDER BY highscore LIMIT 10"
        ).fetchall()[::-1]

    users = []
    for u in userssql:
        name = db.execute(
            "SELECT username FROM users WHERE userid = ?",
            (u["userid"],)
        ).fetchone()
        users.append((u["userid"], name["username"], u["highscore"]))

    print(users)
    return "hi"
