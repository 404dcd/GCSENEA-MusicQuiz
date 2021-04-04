from flask import (
    Blueprint, render_template, request, g, flash, url_for, redirect
)

from quiz.db import get_db

bp = Blueprint("game", __name__, url_prefix="/")


def new_song(db, uid, purge_used=False):
    used = ""
    if not purge_used:
        used = db.execute(
            "SELECT used FROM game WHERE userid = ?", (uid,)
        ).fetchone()["used"]

    songrecord = db.execute(
        f"SELECT id FROM songs WHERE id NOT IN ({used}) ORDER BY RANDOM() LIMIT 1"
    ).fetchone()
    if songrecord is None:
        return (new_song(db, uid, purge_used=True)[0], True)
    song = songrecord["id"]

    db.execute(
        "UPDATE game SET currsong = ?, attempts = 0 WHERE userid = ?", (song, uid)
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
    return (song, False)


@bp.route("/play", methods=("GET", "POST"))
def play():
    db = get_db()
    uid = g.user["userid"]
    songrecord = db.execute(
        "SELECT currsong FROM game WHERE userid = ?", (uid,)
    ).fetchone()
    songid = 0

    if songrecord is None:  # Add user to game database on first go
        db.execute(
            "INSERT INTO game (userid, display, currscore, currsong, attempts, used, highscore) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (uid, "", 0, 0, 0, "", 0)
        )
        db.commit()
        songid = new_song(db, uid, purge_used=True)[0]

    else:
        songid = songrecord["currsong"]
        song = db.execute(
            "SELECT title FROM songs WHERE id = ?", (songid,)
        ).fetchone()

        if request.method == "POST":
            words = song["title"].split()
            count = 0
            for wid, word in request.form.items():
                correct = words[int(wid[1:])][1:]
                if word.lower().strip() == correct:
                    count += 1

            attempts = db.execute(
                "SELECT attempts FROM game WHERE userid = ?", (uid,)
            ).fetchone()["attempts"]
            if count == len(request.form):  # if song was correct
                pts = 1
                if attempts == 0:
                    pts = 3
                db.execute(
                    "UPDATE game SET currscore = currscore + ? WHERE userid = ?", (pts, uid)
                )
                db.commit()
                songid, ranout = new_song(db, uid)

                if ranout:
                    flash("You just correctly guessed all songs in the database!")
                    return redirect(url_for("index.index"))
                else:
                    flash("Good job, that's correct.")

            elif attempts == 0:  # have another go
                db.execute(
                    "UPDATE game SET attempts = attempts + 1 WHERE userid = ?", (uid,)
                )
                db.commit()
                flash(f"You entered {count} of {len(request.form)} correctly. Have another go.")

            else:  # game over
                flash(f"The correct title was '{song['title']}'")
                score = db.execute(
                    "SELECT currscore, highscore FROM game WHERE userid = ?", (uid,)
                ).fetchone()
                msg = f"You got {score['currscore']}"

                if score["currscore"] > score["highscore"]:
                    flash(msg + " - your new personal best!")
                    db.execute(
                        "UPDATE game SET highscore = currscore WHERE userid = ?", (uid,)
                    )
                    db.commit()
                else:
                    flash(msg + ".")

                db.execute(
                    "UPDATE game SET currscore = 0 WHERE userid = ?", (uid,)
                )
                db.commit()
                songid = new_song(db, uid, purge_used=True)[0]
                return redirect(url_for("index.index"))

    song = db.execute(
        "SELECT * FROM songs WHERE id = ?", (songid,)
    ).fetchone()
    return render_template("game.html", words=song["title"].split(), artist=song["artist"])
