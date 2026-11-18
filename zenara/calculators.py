"""Validated attendance and credit-weighted GPA calculations."""

from flask import Blueprint, jsonify, render_template, request

from .security import login_required

calculators_bp = Blueprint("calculators", __name__)
SUBJECT_COUNT = 5
GRADE_POINTS = {"A": 4.0, "B": 3.0, "C": 2.0, "D": 1.0, "F": 0.0}


@calculators_bp.get("/attendance")
@login_required
def attendance_page():
    return render_template("calculator.html", kind="attendance")


@calculators_bp.post("/calculate_attendance")
@login_required
def calculate_attendance():
    results = []
    for index in range(1, SUBJECT_COUNT + 1):
        try:
            total = int(request.form.get(f"total_classes_{index}", ""))
            attended = int(request.form.get(f"classes_attended_{index}", ""))
        except (TypeError, ValueError):
            return jsonify({"error": "Enter whole numbers for all five subjects."}), 400
        if total < 1 or attended < 0 or attended > total:
            return jsonify({"error": "For each subject, attended classes must be between 0 and total classes."}), 400
        percentage = attended / total * 100
        results.append(
            {
                "subject": f"Subject {index}",
                "attendance_percentage": round(percentage, 2),
                "status": "Good" if percentage >= 75 else "Below 75% — seek permission to write exams",
            }
        )
    return jsonify({"results": results})


@calculators_bp.get("/cgpa")
@login_required
def cgpa_page():
    return render_template("calculator.html", kind="cgpa")


@calculators_bp.post("/calculate_cgpa")
@login_required
def calculate_cgpa():
    weighted_points = 0.0
    total_credits = 0
    for index in range(1, SUBJECT_COUNT + 1):
        try:
            credits = int(request.form.get(f"credits_{index}", ""))
            grade = request.form.get(f"grade_{index}", "").upper()
        except (TypeError, ValueError):
            return jsonify({"error": "Enter whole-number credits and a valid grade for all five subjects."}), 400
        if not 1 <= credits <= 60:
            return jsonify({"error": "Each subject must have between 1 and 60 credits."}), 400
        if grade not in GRADE_POINTS:
            return jsonify({"error": "Choose a valid grade for each subject."}), 400
        weighted_points += credits * GRADE_POINTS[grade]
        total_credits += credits

    return jsonify({"cgpa": round(weighted_points / total_credits, 2), "scale": 4.0})
