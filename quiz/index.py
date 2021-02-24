from flask import (
    Blueprint
)

bp = Blueprint("index", __name__, url_prefix="/")


@bp.route("/", methods=("GET", "POST"))
def index():
    return "You've reached the index page."
