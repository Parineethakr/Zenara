"""Shared fixtures for the Zenara route tests."""

import pytest

from zenara import create_app
from zenara.extensions import db


@pytest.fixture
def app():
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "pytest-only-secret-key",
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
            "WTF_CSRF_ENABLED": False,
            "RATELIMIT_ENABLED": False,
        }
    )
    with app.app_context():
        db.create_all()

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def register_and_login(client, email, password="a-long-test-password"):
    """Create an account through the public route and sign it in."""
    signup = client.post(
        "/signup",
        data={"name": "Test Student", "email": email, "password": password},
    )
    assert signup.status_code == 302
    return client.post("/login", data={"email": email, "password": password})
