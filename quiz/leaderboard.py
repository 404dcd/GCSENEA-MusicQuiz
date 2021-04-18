from flask import (
    Blueprint, render_template, request, g
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
        start = db.execute(
            "SELECT COUNT(*) FROM game"
        ).fetchone()["COUNT(*)"] - 10
        start = max(start, 0)
        userssql = db.execute(
            "SELECT userid, highscore FROM game ORDER BY highscore DESC LIMIT 10 OFFSET ?",
            (start,)
        ).fetchall()

    users = []
    gotuser = False
    douser = True
    if g.user is None:
        douser = False
    for u in userssql:
        name = db.execute(
            "SELECT username FROM users WHERE userid = ?",
            (u["userid"],)
        ).fetchone()
        if douser:
            if u["userid"] == g.user["userid"]:
                gotuser = True
        users.append({"userid": u["userid"], "name": name["username"], "highscore": u["highscore"]})

    insert = None
    if douser and not gotuser:
        al = db.execute(
            "SELECT userid, highscore FROM game ORDER BY highscore DESC"
        ).fetchall()
        c = 0
        found = False
        hs = 0
        for uid in al:
            c += 1
            if uid["userid"] == g.user["userid"]:
                hs = uid["highscore"]
                found = True
                break
        if found:
            insert = (c, hs)

    return render_template("leaderboard.html", users=users, start=start, advance=advance, insert=insert)
