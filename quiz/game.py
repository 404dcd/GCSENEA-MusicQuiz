from flask import (
    Blueprint, render_template, request, g
)

from quiz.db import get_db

bp = Blueprint("game", __name__, url_prefix="/")


def new_song(db, uid, purge_used=False):
    used = db.execute(
        "SELECT used FROM game WHERE userid = ?", (uid,)
    ).fetchone()["used"]

    song = db.execute(
        f"SELECT id FROM songs WHERE id NOT IN ({used}) ORDER BY RANDOM() LIMIT 1"
    ).fetchone()["id"]

    db.execute(
        "UPDATE game SET currsong = ? WHERE userid = ?", (song, uid)
    )
    db.commit()

    if purge_used:
        db.execute(
            "UPDATE game SET used = ? WHERE userid = ?", (str(song), uid)
        )
    else:
        db.execute(
            "UPDATE game SET used = ? WHERE userid = ?", (f"{used},{song}", uid)
        )
    db.commit()
    return song


@bp.route("/play", methods=("GET", "POST"))
def play():
    db = get_db()

    if request.method == "POST":
        new_song(db, g.user["userid"], purge_used=False)

    songid = db.execute(
        "SELECT currsong FROM game WHERE userid = ?", (g.user["userid"],)
    ).fetchone()
    if songid is None:  # Add user to game database on first go
        db.execute(
            "INSERT INTO game (userid, display, currscore, currsong, attempts, used, highscore) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (g.user["userid"], "", 0, 0, 0, "", 0)
        )
        db.commit()
        songid = new_song(db, g.user["userid"], purge_used=True)
    else:
        songid = songid["currsong"]

    song = db.execute(
        "SELECT * FROM songs WHERE id = ?", (songid,)
    ).fetchone()
    words = []
    c = 0
    for w in song["title"].split():
        words.append({"id": c, "letter": w[0]})
    return render_template("game.html", words=words, artist=song["artist"])
