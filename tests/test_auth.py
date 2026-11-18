"""Signup, login, and protected-page behavior."""

from tests.conftest import register_and_login


def test_user_can_sign_up_and_log_in(client):
    response = register_and_login(client, "student@example.com")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")
    with client.session_transaction() as session:
        assert session.get("user_id") is not None
        assert session.get("_permanent") is True


def test_wrong_password_does_not_authenticate(client):
    signup = client.post(
        "/signup",
        data={
            "name": "Test Student",
            "email": "student@example.com",
            "password": "a-long-test-password",
        },
    )
    assert signup.status_code == 302

    response = client.post(
        "/login",
        data={"email": "student@example.com", "password": "incorrect-password"},
    )

    assert response.status_code == 401
    with client.session_transaction() as session:
        assert "user_id" not in session


def test_protected_page_redirects_signed_out_user(client):
    response = client.get("/dashboard")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]
