from flask import (
    Blueprint, request, flash, redirect, url_for, render_template, session, g
)

from quiz.db import get_db

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("demoteuser", methods=["GET"])
def demoteuser():
    user = request.args.get("user", 0)
    db = get_db()
    status = db.execute(
        "SELECT isadmin FROM users WHERE userid = ?", (user,)
    ).fetchone()
    if status is None:
        flash("Unable to demote user.", "warning")
    elif status["isadmin"] == 0:
        flash("That user is already a standard user.", "warning")
    else:
        db.execute(
            "UPDATE users SET isadmin = 0 WHERE userid = ?", (user,)
        )
        db.commit()
        flash("That admin has been demoted.", "success")
    return redirect(url_for("admin.users", page=request.args.get("page", 0)))


@bp.route("promoteuser", methods=["GET"])
def promoteuser():
    user = request.args.get("user", 0)
    db = get_db()
    status = db.execute(
        "SELECT isadmin FROM users WHERE userid = ?", (user,)
    ).fetchone()
    if status is None:
        flash("Unable to promote user.", "warning")
    elif status["isadmin"] == 1:
        flash("That user is already admin.", "warning")
    else:
        db.execute(
            "UPDATE users SET isadmin = 1 WHERE userid = ?", (user,)
        )
        db.commit()
        flash("Promoted user to admin.", "success")
    return redirect(url_for("admin.users", page=request.args.get("page", 0)))


@bp.route("removeuser", methods=["GET"])
def removeuser():
    user = request.args.get("user", 0)
    if user == 0:
        flash("Unable to remove user.", "warning")
        return redirect(url_for("admin.users", page=request.args.get("page", 0)))
    db = get_db()
    if db.execute(
        "SELECT username FROM users WHERE userid = ?", (user,)
    ).fetchone() is not None:
        db.execute("DELETE FROM users WHERE userid = ?", (user,))
        db.commit()
        db.execute("DELETE FROM game WHERE userid = ?", (user,))
        db.commit()
        flash("User removed.", "success")
        return redirect(url_for("admin.users", page=request.args.get("page", 0)))

    flash("Unable to remove user.", "warning")
    return redirect(url_for("admin.users", page=request.args.get("page", 0)))


@bp.route("users", methods=["GET"])
def users():
    db = get_db()
    advance = True
    try:
        page = int(request.args.get("page", 0))
        assert 0 <= page <= 100000000000000
    except (ValueError, AssertionError):
        page = 0

    start = page * 14
    userssql = db.execute(
        "SELECT userid, username, isadmin FROM users LIMIT 14 OFFSET ?",
        (start,)
    ).fetchall()
    if len(userssql) < 14:
        advance = False
        start = db.execute(
            "SELECT COUNT(*) FROM users"
        ).fetchone()["COUNT(*)"] - 14
        start = max(start, 0)
        userssql = db.execute(
            "SELECT * FROM users LIMIT 14 OFFSET ?",
            (start,)
        ).fetchall()

    users = []
    for u in userssql:
        users.append({"userid": u["userid"], "username": u["username"], "isadmin": u["isadmin"]})

    return render_template("admin/users.html", users=users, start=start, advance=advance)


@bp.route("/removesong", methods=["GET"])
def removesong():
    song = request.args.get("song")
    if song is not None:
        db = get_db()
        if db.execute(
            "SELECT * FROM songs WHERE id = ?", (song,)
        ).fetchone() is not None:
            db.execute("DELETE FROM songs WHERE id = ?", (song,))
            db.commit()
            flash("Song removed.", "success")
            return redirect(url_for("admin.songs", page=request.args.get("page", 0)))

    flash("Unable to remove song.", "warning")
    return redirect(url_for("admin.songs", page=request.args.get("page", 0)))


@bp.route("/songs", methods=("GET", "POST"))
def songs():
    db = get_db()
    if request.method == "POST":
        toadd = []
        idtoindex = {}
        for field in request.form:
            numb = int(field[1:])
            if numb not in idtoindex:
                toadd.append(["", ""])
                idtoindex[numb] = len(toadd) - 1
            if field[0] == "t":
                toadd[idtoindex[numb]][0] = request.form[field].strip()
            else:
                toadd[idtoindex[numb]][1] = request.form[field].strip()

        added = 0
        for song in toadd:
            if song[0] or song[1]:
                if not (song[0] and song[1]):
                    flash(f'Failed to add song "{song[0]}" by "{song[1]}" to the database.', "warning")
                    continue
                db.execute(
                    "INSERT INTO songs (title, artist) VALUES (?, ?)",
                    tuple(song)
                )
                db.commit()
                added += 1

        if added == 0:
            flash("Added 0 songs.", "warning")
        elif added == 1:
            flash("Added 1 song.", "success")
        else:
            flash(f"Added {added} songs.", "success")

    advance = True
    try:
        page = int(request.args.get("page", 0))
        assert 0 <= page <= 100000000000000
    except (ValueError, AssertionError):
        page = 0

    start = page * 14
    songssql = db.execute(
        "SELECT * FROM songs LIMIT 14 OFFSET ?",
        (start,)
    ).fetchall()
    if len(songssql) < 14:
        advance = False
        start = db.execute(
            "SELECT COUNT(*) FROM songs"
        ).fetchone()["COUNT(*)"] - 14
        start = max(start, 0)
        songssql = db.execute(
            "SELECT * FROM songs LIMIT 14 OFFSET ?",
            (start,)
        ).fetchall()

    songs = []
    for s in songssql:
        songs.append({"id": s["id"], "title": s["title"], "artist": s["artist"]})

    return render_template("admin/songs.html", songs=songs, start=start, advance=advance)
