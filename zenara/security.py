"""Authentication helpers shared by feature blueprints."""

from functools import wraps

from flask import flash, g, redirect, url_for


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.get("user") is None:
            flash("Please sign in to continue.", "info")
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped_view
