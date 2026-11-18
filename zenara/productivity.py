"""User-scoped task and note management routes."""

from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from .extensions import db
from .models import Note, Task
from .security import login_required

productivity_bp = Blueprint("productivity", __name__)
NOTE_COLORS = {"lavender", "mint", "peach", "sky"}


@productivity_bp.get("/tasks")
@login_required
def tasks():
    items = db.session.scalars(
        db.select(Task)
        .where(Task.user_id == g.user.id)
        .order_by(Task.completed, Task.created_at.desc())
    ).all()
    return render_template("tasks.html", tasks=items)


@productivity_bp.post("/tasks")
@login_required
def add_task():
    title = request.form.get("title", "").strip()
    if not title or len(title) > 160:
        flash("A task needs a title of 1 to 160 characters.", "error")
    else:
        db.session.add(Task(user_id=g.user.id, title=title))
        db.session.commit()
        flash("Task added.", "success")
    return redirect(url_for("productivity.tasks"))


@productivity_bp.post("/tasks/<int:task_id>/toggle")
@login_required
def toggle_task(task_id):
    task = db.session.scalar(
        db.select(Task).where(Task.id == task_id, Task.user_id == g.user.id)
    )
    if task is None:
        abort(404)
    task.completed = not task.completed
    db.session.commit()
    return redirect(url_for("productivity.tasks"))


@productivity_bp.post("/tasks/<int:task_id>/delete")
@login_required
def delete_task(task_id):
    task = db.session.scalar(
        db.select(Task).where(Task.id == task_id, Task.user_id == g.user.id)
    )
    if task is None:
        abort(404)
    db.session.delete(task)
    db.session.commit()
    flash("Task deleted.", "success")
    return redirect(url_for("productivity.tasks"))


@productivity_bp.get("/notes")
@login_required
def notes():
    items = db.session.scalars(
        db.select(Note)
        .where(Note.user_id == g.user.id)
        .order_by(Note.updated_at.desc(), Note.id.desc())
    ).all()
    return render_template("notes.html", notes=items, note_colors=sorted(NOTE_COLORS))


@productivity_bp.post("/notes")
@login_required
def add_note():
    title = request.form.get("title", "").strip() or "Untitled note"
    content = request.form.get("content", "").strip()
    color = request.form.get("color", "lavender")
    if len(title) > 100 or not content or len(content) > 5000:
        flash("Add note text (up to 5,000 characters) and a title under 100 characters.", "error")
    elif color not in NOTE_COLORS:
        flash("Choose one of the available note colors.", "error")
    else:
        db.session.add(
            Note(user_id=g.user.id, title=title, content=content, color=color)
        )
        db.session.commit()
        flash("Note saved.", "success")
    return redirect(url_for("productivity.notes"))


@productivity_bp.post("/notes/<int:note_id>/delete")
@login_required
def delete_note(note_id):
    note = db.session.scalar(
        db.select(Note).where(Note.id == note_id, Note.user_id == g.user.id)
    )
    if note is None:
        abort(404)
    db.session.delete(note)
    db.session.commit()
    flash("Note deleted.", "success")
    return redirect(url_for("productivity.notes"))
