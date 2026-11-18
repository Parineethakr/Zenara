"""Dashboard, calendar, profile, and focus-timer pages."""

import calendar as month_calendar
from datetime import date

from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from .extensions import db
from .models import CalendarEvent, Note, Task
from .security import login_required

main_bp = Blueprint("main", __name__)


@main_bp.get("/")
def index():
    if g.get("user") is not None:
        return redirect(url_for("main.dashboard"))
    return render_template("index.html")


@main_bp.get("/dashboard")
@login_required
def dashboard():
    user = g.user
    task_count = db.session.scalar(
        db.select(db.func.count(Task.id)).where(Task.user_id == user.id, Task.completed.is_(False))
    ) or 0
    note_count = db.session.scalar(
        db.select(db.func.count(Note.id)).where(Note.user_id == user.id)
    ) or 0
    upcoming_count = db.session.scalar(
        db.select(db.func.count(CalendarEvent.id)).where(
            CalendarEvent.user_id == user.id,
            CalendarEvent.starts_on >= date.today(),
        )
    ) or 0
    return render_template(
        "dashboard.html",
        open_tasks=task_count,
        note_count=note_count,
        upcoming_count=upcoming_count,
    )


@main_bp.get("/profile")
@login_required
def profile():
    return render_template("profile.html")


@main_bp.route("/calendar", methods=["GET", "POST"])
@login_required
def calendar():
    view = request.args.get("view", "month")
    if view not in {"month", "list"}:
        view = "month"
    sort_order = request.args.get("sort", "asc")
    if sort_order not in {"asc", "desc"}:
        sort_order = "asc"
    today = date.today()
    try:
        month_value = request.args.get("month", today.strftime("%Y-%m"))
        selected_month = date.fromisoformat(f"{month_value}-01" if len(month_value) == 7 else month_value).replace(day=1)
    except ValueError:
        selected_month = today.replace(day=1)

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        start_value = request.form.get("starts_on", "")
        end_value = request.form.get("ends_on", "")
        try:
            starts_on = date.fromisoformat(start_value)
            ends_on = date.fromisoformat(end_value) if end_value else None
        except ValueError:
            flash("Choose a valid event date.", "error")
            return redirect(url_for("main.calendar", view=request.form.get("view", "month"), month=request.form.get("month", today.strftime("%Y-%m")), sort=request.form.get("sort", "asc")))

        if not title or len(title) > 160 or len(description) > 500:
            flash("Enter a title (up to 160 characters) and description (up to 500).", "error")
        elif ends_on and ends_on < starts_on:
            flash("The end date must be the same as or after the start date.", "error")
        else:
            db.session.add(
                CalendarEvent(
                    user_id=g.user.id,
                    title=title,
                    description=description,
                    starts_on=starts_on,
                    ends_on=ends_on,
                )
            )
            db.session.commit()
            flash("Event added to your calendar.", "success")
        return redirect(url_for("main.calendar", view=request.form.get("view", "month"), month=request.form.get("month", today.strftime("%Y-%m")), sort=request.form.get("sort", "asc")))

    ordering = (CalendarEvent.starts_on.desc(), CalendarEvent.id.desc()) if sort_order == "desc" else (CalendarEvent.starts_on, CalendarEvent.id)
    events = db.session.scalars(
        db.select(CalendarEvent)
        .where(CalendarEvent.user_id == g.user.id)
        .order_by(*ordering)
    ).all()
    month_weeks = []
    for week in month_calendar.Calendar(firstweekday=6).monthdatescalendar(selected_month.year, selected_month.month):
        month_weeks.append([
            {"day": day, "events": [event for event in events if event.starts_on == day]}
            for day in week
        ])
    previous_month = date(selected_month.year - (selected_month.month == 1), (selected_month.month - 2) % 12 + 1, 1)
    next_month = date(selected_month.year + (selected_month.month == 12), selected_month.month % 12 + 1, 1)
    return render_template(
        "calendar.html", events=events, view=view, sort_order=sort_order, today=today,
        selected_month=selected_month, month_weeks=month_weeks,
        previous_month=previous_month, next_month=next_month,
    )


@main_bp.post("/calendar/<int:event_id>/delete")
@login_required
def delete_event(event_id):
    event = db.session.scalar(
        db.select(CalendarEvent).where(
            CalendarEvent.id == event_id,
            CalendarEvent.user_id == g.user.id,
        )
    )
    if event is None:
        abort(404)
    db.session.delete(event)
    db.session.commit()
    flash("Event deleted.", "success")
    return redirect(url_for(
        "main.calendar",
        view=request.form.get("view", "month"), month=request.form.get("month", date.today().strftime("%Y-%m")),
        sort=request.form.get("sort", "asc"),
    ))


@main_bp.get("/pomodoro")
@login_required
def pomodoro():
    return render_template("pomodoro.html")
