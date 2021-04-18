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


def final_score(db, uid):
    score = db.execute(
        "SELECT currscore, highscore FROM game WHERE userid = ?", (uid,)
    ).fetchone()
    msg = f"You got {score['currscore']}"

    if score["currscore"] > score["highscore"]:
        flash(msg + " - your new personal best!", "primary")
        db.execute(
            "UPDATE game SET highscore = currscore WHERE userid = ?", (uid,)
        )
        db.commit()
    else:
        flash(msg + ".", "primary")

    db.execute(
        "UPDATE game SET currscore = 0 WHERE userid = ?", (uid,)
    )
    db.commit()


def titleToArray(title):
    ws = []
    for w in title.split():
        if w[0] == "(":
            ws.append("(")
            w = w[1:]
        if w[-1] == ")":
            ws.append(w[:-1])
            ws.append(")")
        else:
            ws.append(w)
    return ws


ALPHABET = "abcdefghijklmnopqrstuvwxyz0123456789"


def filterChars(string):
    ret = ""
    for c in string.lower().strip():
        if c in ALPHABET:
            ret += c
    return ret

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
            "INSERT INTO game (userid, currscore, currsong, attempts, used, highscore) VALUES (?, ?, ?, ?, ?, ?)",
            (uid, 0, 0, 0, "", 0)
        )
        db.commit()
        songid = new_song(db, uid, purge_used=True)[0]

    else:
        songid = songrecord["currsong"]
        song = db.execute(
            "SELECT title FROM songs WHERE id = ?", (songid,)
        ).fetchone()

        if song is None:  # song database was changed between requests, probably safe to start over
            songid = new_song(db, uid, purge_used=True)[0]
            song = db.execute(
                "SELECT title FROM songs WHERE id = ?", (songid,)
            ).fetchone()

        if request.method == "POST":
            words = titleToArray(song["title"])
            count = 0
            for wid, word in request.form.items():
                correct = words[int(wid[1:])][1:]
                if filterChars(word) == filterChars(correct):
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
                    flash("You just correctly guessed all songs in the database!", "primary")
                    final_score(db, uid)
                    return redirect(url_for("leaderboard.leaderboard"))
                else:
                    flash("Good job, that's correct.", "primary")

            elif attempts == 0:  # have another go
                db.execute(
                    "UPDATE game SET attempts = attempts + 1 WHERE userid = ?", (uid,)
                )
                db.commit()
                flash(f"You entered {count} of {len(request.form)} correctly. Have another go.", "primary")

            else:  # game over
                flash(f"The correct title was '{song['title']}'", "primary")
                final_score(db, uid)
                new_song(db, uid, purge_used=True)
                return redirect(url_for("leaderboard.leaderboard"))

    song = db.execute(
        "SELECT * FROM songs WHERE id = ?", (songid,)
    ).fetchone()
    return render_template("game.html", words=titleToArray(song["title"]), artist=song["artist"])
