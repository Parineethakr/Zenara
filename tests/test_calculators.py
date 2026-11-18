"""Calculator validation and result behavior."""

import pytest

from tests.conftest import register_and_login


@pytest.fixture
def signed_in_client(client):
    register_and_login(client, "calculator@example.com")
    return client


def test_attendance_marks_under_75_percent_for_attention(signed_in_client):
    response = signed_in_client.post(
        "/calculate_attendance",
        data={
            "total_classes_1": "4", "classes_attended_1": "3",  # exactly 75%
            "total_classes_2": "3", "classes_attended_2": "2",  # below 75%
            "total_classes_3": "1", "classes_attended_3": "0",
            "total_classes_4": "5", "classes_attended_4": "5",
            "total_classes_5": "2", "classes_attended_5": "2",
        },
    )

    assert response.status_code == 200
    results = response.get_json()["results"]
    assert results[0]["attendance_percentage"] == 75.0
    assert results[0]["status"] == "Good"
    assert results[1]["attendance_percentage"] == pytest.approx(66.67)
    assert "seek permission" in results[1]["status"]


@pytest.mark.parametrize(
    "total,attended",
    [("0", "0"), ("4", "5"), ("not-a-number", "2")],
)
def test_attendance_rejects_invalid_class_counts(signed_in_client, total, attended):
    data = {}
    for index in range(1, 6):
        data[f"total_classes_{index}"] = "4"
        data[f"classes_attended_{index}"] = "2"
    data["total_classes_1"] = total
    data["classes_attended_1"] = attended

    response = signed_in_client.post("/calculate_attendance", data=data)

    assert response.status_code == 400
    assert "error" in response.get_json()


def test_cgpa_is_weighted_by_credits(signed_in_client):
    response = signed_in_client.post(
        "/calculate_cgpa",
        data={
            "credits_1": "3", "grade_1": "A",
            "credits_2": "1", "grade_2": "B",
            "credits_3": "2", "grade_3": "C",
            "credits_4": "2", "grade_4": "D",
            "credits_5": "2", "grade_5": "F",
        },
    )

    assert response.status_code == 200
    assert response.get_json() == {"cgpa": 2.1, "scale": 4.0}


def test_cgpa_rejects_invalid_grade(signed_in_client):
    data = {f"credits_{index}": "3" for index in range(1, 6)}
    data.update({f"grade_{index}": "A" for index in range(1, 6)})
    data["grade_3"] = "X"

    response = signed_in_client.post("/calculate_cgpa", data=data)

    assert response.status_code == 400
    assert "error" in response.get_json()
