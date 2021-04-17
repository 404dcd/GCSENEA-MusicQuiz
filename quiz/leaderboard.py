from flask import (
    Blueprint, render_template, request, g, flash, url_for, redirect
)

from quiz.db import get_db

bp = Blueprint("game", __name__, url_prefix="/")

@bp.route("/leaderboard", methods=("GET"))
def leaderboard():
    return "Leaderboard"