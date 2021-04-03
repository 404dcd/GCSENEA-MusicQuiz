from flask import (
    Blueprint, render_template, request, g
)

from quiz.db import get_db

bp = Blueprint("game", __name__, url_prefix="/")


def new_song(db, uid):
    used = map(int, db.execute(
        "SELECT used FROM songs WHERE userid = ?", (uid,)
    ).fetchone().split(" "))

    song = db.execute(
        f"SELECT id FROM songs WHERE id NOT IN ({', '.join(used)}) ORDER BY RANDOM() LIMIT 1"
    ).fetchone()

    db.execute(
        "UPDATE game SET currsong = ? WHERE userid = ?", (song, uid)
    )
    db.commit()


@bp.route("/play", methods=("GET", "POST"))
def index():
    db = get_db()

    if request.method == "POST":
        # User is submitting an answer here
        pass

    if db.execute(
        "SELECT * FROM game WHERE userid = ?", (g.user["userid"],)
    ).fetchone() is None:  # Add user to game database on first go
        db.execute(
            "INSERT INTO game (userid, display, currscore, currsong, attempts, used, highscore) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (g.user["userid"], "", 0, 0, 0, "", 0)
        )
        db.commit()
        new_song(db, g.user["userid"])

    return render_template("game.html")
