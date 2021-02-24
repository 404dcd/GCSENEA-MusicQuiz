import sqlite3

import click
import secrets
import bcrypt
from flask import current_app, g
from flask.cli import with_appcontext


SEC_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config["DATABASE"],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e=None):
    db = g.pop("db", None)

    if db is not None:
        db.close()


def init_db():
    db = get_db()

    with current_app.open_resource("schema.sql") as fh:
        db.executescript(fh.read().decode("utf8"))
    adminpass = ""
    for i in range(20):
        adminpass += secrets.choice(SEC_ALPHABET)
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(adminpass.encode("utf-8"), salt)
    db.execute(
        "INSERT INTO users (username, passwd, isadmin) VALUES (?, ?, ?)",
        ("admin", hashed, 1)
    )
    db.commit()
    return adminpass


@click.command("init-db")
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    adminpass = init_db()
    click.echo("Initialized database. Admin user was generated with the following credentials:\n")
    click.echo("Username: admin")
    click.echo(f"Password: {adminpass}\n")
    click.echo("Please consider changing this password by going to the change password page.")


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
