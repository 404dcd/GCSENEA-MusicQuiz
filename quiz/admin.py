from flask import (
    Blueprint, request, flash, redirect, url_for, render_template, session, g
)

from quiz.db import get_db

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/songs", methods=["GET"])
def songs():
    db = get_db()
    advance = True
    try:
        page = int(request.args.get("page", 0))
        assert 0 <= page <= 100000000000000
    except (ValueError, AssertionError):
        page = 0

    start = page * 50
    songssql = db.execute(
        "SELECT * FROM songs LIMIT 50 OFFSET ?",
        (start,)
    ).fetchall()
    if len(songssql) < 50:
        advance = False
        start = db.execute(
            "SELECT COUNT(*) FROM songs"
        ).fetchone()["COUNT(*)"] - 50
        start = max(start, 0)
        songssql = db.execute(
            "SELECT * FROM songs LIMIT 50 OFFSET ?",
            (start,)
        ).fetchall()

    songs = []
    for s in songssql:
        songs.append({"id": s["id"], "title": s["title"], "artist": s["artist"]})

    return render_template("admin/songs.html", songs=songs, start=start, advance=advance)
