"""Zenara application factory and shared request configuration."""

import os
import secrets
from pathlib import Path
from datetime import timedelta

from flask import Flask, g, render_template, request, session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate

from .extensions import csrf, db

limiter = Limiter(key_func=get_remote_address)
migrate = Migrate()


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    production = os.environ.get("ZENARA_ENV", "development").lower() == "production"
    secret_key = os.environ.get("ZENARA_SECRET_KEY")
    if production and not secret_key:
        raise RuntimeError("Set ZENARA_SECRET_KEY before running Zenara in production.")
    rate_limit_storage = os.environ.get("ZENARA_RATE_LIMIT_STORAGE_URI", "memory://")
    if production and rate_limit_storage == "memory://":
        raise RuntimeError("Set ZENARA_RATE_LIMIT_STORAGE_URI to a shared store such as Redis in production.")
    app.config.from_mapping(
        SECRET_KEY=secret_key or secrets.token_hex(32),
        SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL", "sqlite:///zenara.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("ZENARA_COOKIE_SECURE", "1" if production else "0").lower() in {"1", "true", "yes"},
        PERMANENT_SESSION_LIFETIME=timedelta(days=7),
        DEBUG=os.environ.get("ZENARA_DEBUG", "0").lower() in {"1", "true", "yes"},
        RATELIMIT_STORAGE_URI=rate_limit_storage,
        RATELIMIT_HEADERS_ENABLED=True,
    )
    if test_config:
        app.config.update(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    migrate.init_app(app, db, compare_type=True, render_as_batch=True)

    from .models import User
    from .auth import auth_bp
    from .calculators import calculators_bp
    from .main import main_bp
    from .productivity import productivity_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(productivity_bp)
    app.register_blueprint(calculators_bp)

    @app.before_request
    def load_signed_in_user():
        user_id = session.get("user_id")
        g.user = db.session.get(User, user_id) if user_id is not None else None
        if user_id is not None and g.user is None:
            session.clear()

    @app.context_processor
    def inject_user():
        return {"current_user": g.get("user")}

    @app.after_request
    def add_security_headers(response):
        # Windows may report .js as text/plain through its MIME registry. With
        # nosniff enabled, browsers then refuse to execute the application scripts.
        if request.endpoint == "static" and request.path.lower().endswith(".js"):
            response.mimetype = "text/javascript"
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; "
            "font-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'",
        )
        return response

    @app.cli.command("import-legacy")
    def import_legacy_command():
        """Import the old shared JSON demo data into a selected user's account."""
        import json

        import click

        from .models import CalendarEvent, Note, Task

        email = click.prompt("Email address of the account to receive the legacy data").strip().lower()
        user = db.session.scalar(db.select(User).filter_by(email=email))
        if user is None:
            raise click.ClickException("No account exists for that email. Create the account first.")

        root = Path(app.root_path).parent
        imported_tasks = imported_notes = 0
        task_file = root / "tasks.json"
        note_file = root / "notes.json"
        existing_data = any(
            db.session.scalar(db.select(db.func.count(model.id)).where(model.user_id == user.id))
            for model in (Task, Note, CalendarEvent)
        )
        if existing_data:
            raise click.ClickException(
                "Import into an account with no tasks, notes, or calendar events to avoid duplicates."
            )
        if task_file.exists():
            with task_file.open(encoding="utf-8") as source:
                old_tasks = json.load(source)
            for old_task in old_tasks:
                title = str(old_task.get("name", "")).strip()[:160]
                if title:
                    db.session.add(Task(user_id=user.id, title=title, completed=bool(old_task.get("complete", False))))
                    imported_tasks += 1
        if note_file.exists():
            with note_file.open(encoding="utf-8") as source:
                old_notes = json.load(source)
            allowed_colors = {"lavender", "mint", "peach", "sky"}
            for old_note in old_notes:
                content = str(old_note.get("text", "")).strip()[:5000]
                if content:
                    color = str(old_note.get("color", "lavender")).lower()
                    db.session.add(
                        Note(
                            user_id=user.id,
                            title="Imported note",
                            content=content,
                            color=color if color in allowed_colors else "lavender",
                        )
                    )
                    imported_notes += 1
        db.session.commit()
        click.echo(f"Imported {imported_tasks} tasks and {imported_notes} notes for {user.email}. Original JSON files were kept.")

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("error.html", code=404, message="That page could not be found."), 404

    @app.errorhandler(500)
    def internal_error(_error):
        db.session.rollback()
        return render_template("error.html", code=500, message="Something went wrong. Please try again."), 500

    return app
