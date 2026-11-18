"""A signed-in user can only read or mutate their own study data."""

from sqlalchemy import select

from tests.conftest import register_and_login
from zenara.extensions import db
from zenara.models import Task


def test_user_cannot_see_or_modify_another_users_tasks(app):
    student_a = app.test_client()
    student_b = app.test_client()
    register_and_login(student_a, "student-a@example.com")
    register_and_login(student_b, "student-b@example.com")

    student_a.post("/tasks", data={"title": "Private task for student A"})
    student_b.post("/tasks", data={"title": "Private task for student B"})

    with app.app_context():
        task_a = db.session.scalar(select(Task).where(Task.title == "Private task for student A"))
        task_b = db.session.scalar(select(Task).where(Task.title == "Private task for student B"))
        task_a_id = task_a.id
        task_b_id = task_b.id

    student_a_tasks = student_a.get("/tasks").get_data(as_text=True)
    student_b_tasks = student_b.get("/tasks").get_data(as_text=True)
    assert "Private task for student A" in student_a_tasks
    assert "Private task for student B" not in student_a_tasks
    assert "Private task for student B" in student_b_tasks
    assert "Private task for student A" not in student_b_tasks

    assert student_a.post(f"/tasks/{task_b_id}/delete").status_code == 404
    assert student_b.post(f"/tasks/{task_a_id}/toggle").status_code == 404

    with app.app_context():
        assert db.session.get(Task, task_a_id) is not None
        assert db.session.get(Task, task_b_id) is not None
