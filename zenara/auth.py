"""Signup, login, and logout routes."""

import re

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from sqlalchemy.exc import IntegrityError

from .extensions import db
from .models import User
from . import limiter

auth_bp = Blueprint("auth", __name__)
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


@auth_bp.route("/signup", methods=["GET", "POST"])
@limiter.limit("5 per hour", methods=["POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        errors = []

        if not name or len(name) > 80:
            errors.append("Enter a name of 1 to 80 characters.")
        if len(email) > 254 or not EMAIL_PATTERN.fullmatch(email):
            errors.append("Enter a valid email address.")
        if len(password) < 10 or len(password.encode("utf-8")) > 72:
            errors.append("Use a password of at least 10 characters and at most 72 bytes.")
        if not errors and db.session.scalar(db.select(User).filter_by(email=email)):
            errors.append("An account with that email already exists.")

        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("auth/signup.html", name=name, email=email), 400

        user = User(name=name, email=email)
        user.set_password(password)
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("An account with that email already exists.", "error")
            return render_template("auth/signup.html", name=name, email=email), 400

        flash("Your account is ready. Sign in to get started.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/signup.html")


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute", methods=["POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = db.session.scalar(db.select(User).filter_by(email=email))

        if user is not None and user.check_password(password):
            session.clear()
            session["user_id"] = user.id
            session.permanent = True
            flash(f"Welcome back, {user.name}.", "success")
            return redirect(url_for("main.dashboard"))

        flash("Email or password was not recognized.", "error")
        return render_template("auth/login.html", email=email), 401

    return render_template("auth/login.html")


@auth_bp.post("/logout")
def logout():
    session.clear()
    flash("You have signed out.", "info")
    return redirect(url_for("main.index"))
