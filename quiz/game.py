from flask import (
    Blueprint, render_template, request, g
)

from quiz.db import get_db

bp = Blueprint("game", __name__, url_prefix="/")


@bp.route("/play", methods=("GET", "POST"))
def index():
    db = get_db()

    if request.method == "POST":
        pass

    if db.execute(
            "SELECT * FROM game WHERE userid = ?", (g.user["userid"],)
    ).fetchone() is None:  # Add user to game database on first go
        db.execute(
            "INSERT INTO game (userid, display, currscore, currsong, highscore) VALUES (?, ?, ?, ?, ?)",
            (g.user["userid"], "", 0, 0, 0)
        )
        db.commit()

    if db.execute(
        "SELECT * FROM game WHERE userid = ? AND currsong = 0", (g.user["userid"],)
    ).fetchone() is not None:  # If they have finished the game, load a new song
        db.execute(
            "UPDATE INTO game (userid, display, currscore, currsong, highscore) VALUES (?, ?, ?, ?, ?)",
            (g.user["userid"], "", 0, 0, 0)
        )
        db.commit()

    return render_template("game.html")
