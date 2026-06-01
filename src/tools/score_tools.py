from __future__ import annotations

import csv
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable

DATA_PATH = Path(__file__).resolve().parents[2] / "Data" / "database.csv"

COURSE_COLUMNS = [
    "Computer Science",
    "Microeconomics",
    "Data Structures and Algorithms",
    "Calculus",
    "Linear Algebra",
]

PASS_THRESHOLD = 4.0

GRADE_POLICY = [
    (9.0, "Xuất sắc"),
    (8.0, "Giỏi"),
    (6.5, "Khá"),
    (5.0, "Trung bình"),
    (0.0, "Yếu"),
]


def _parse_score(value: str) -> float:
    return float(value.strip().replace(",", "."))


@lru_cache(maxsize=1)
def _load_rows() -> tuple[dict[str, Any], ...]:
    rows: list[dict[str, Any]] = []
    with DATA_PATH.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file, delimiter=";")
        for raw in reader:
            row: dict[str, Any] = {
                "ID": int(raw["ID"]),
                "Name": raw["Name"].strip(),
                "ID_Card": raw["ID_Card"].strip(),
            }
            for course in COURSE_COLUMNS:
                row[course] = _parse_score(raw[course])
            rows.append(row)
    return tuple(rows)


def _student_payload(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["ID"],
        "name": row["Name"],
        "id_card": row["ID_Card"],
    }


def _find_student(identifier: str | int) -> dict[str, Any] | None:
    query = str(identifier).strip().lower()
    for row in _load_rows():
        if (
            str(row["ID"]).lower() == query
            or row["ID_Card"].lower() == query
            or row["Name"].lower() == query
        ):
            return dict(row)
    return None


def list_courses() -> list[str]:
    """Return all course names available in the score dataset."""
    return COURSE_COLUMNS.copy()


def validate_student(student_id: str | int, name: str, id_card: str | int) -> dict[str, Any]:
    """Validate a student by requiring internal ID, exact full name, and ID card."""
    expected = {
        "student_id": str(student_id).strip(),
        "name": str(name).strip(),
        "id_card": str(id_card).strip(),
    }
    row = _find_student(expected["id_card"])
    if row is None:
        return {
            "found": False,
            "message": f"No student found for ID card: {expected['id_card']}",
            "expected": expected,
        }

    mismatches: dict[str, dict[str, Any]] = {}
    if str(row["ID"]) != expected["student_id"]:
        mismatches["student_id"] = {"expected": expected["student_id"], "actual": row["ID"]}
    if row["Name"].strip().lower() != expected["name"].lower():
        mismatches["name"] = {"expected": expected["name"], "actual": row["Name"]}
    if row["ID_Card"] != expected["id_card"]:
        mismatches["id_card"] = {"expected": expected["id_card"], "actual": row["ID_Card"]}

    if mismatches:
        return {
            "found": False,
            "message": "Student identity validation failed because one or more fields do not match the dataset.",
            "expected": expected,
            "mismatches": mismatches,
        }

    return {
        "found": True,
        "student": _student_payload(row),
        "status": "Found in current dataset",
    }


def get_student_marks(identifier: str | int) -> dict[str, Any]:
    """Return all course marks for one student."""
    row = _find_student(identifier)
    if row is None:
        return {
            "found": False,
            "message": f"No student found for identifier: {identifier}",
        }
    return {
        "found": True,
        "student": _student_payload(row),
        "marks": {course: row[course] for course in COURSE_COLUMNS},
    }


def calculate_average_score(identifier: str | int) -> dict[str, Any]:
    """Calculate the arithmetic average on the 10-point scale for one student."""
    marks_result = get_student_marks(identifier)
    if not marks_result["found"]:
        return marks_result

    marks = marks_result["marks"]
    failed_courses = [
        {"course": course, "score": score}
        for course, score in marks.items()
        if score < PASS_THRESHOLD
    ]
    average_score = round(sum(marks.values()) / len(marks), 2)
    return {
        "found": True,
        "student": marks_result["student"],
        "average_score": average_score,
        "course_count": len(marks),
        "failed_courses": failed_courses,
        "passed_all_courses": not failed_courses,
    }


def grade_policy_lookup() -> dict[str, Any]:
    """Return the academic classification policy used by the lab."""
    return {
        "scale": "10-point scale",
        "pass_threshold": PASS_THRESHOLD,
        "categories": [
            {"name": "Xuất sắc", "rule": "average_score >= 9.0"},
            {"name": "Giỏi", "rule": "8.0 <= average_score < 9.0"},
            {"name": "Khá", "rule": "6.5 <= average_score < 8.0"},
            {"name": "Trung bình", "rule": "5.0 <= average_score < 6.5"},
            {"name": "Yếu", "rule": "average_score < 5.0"},
        ],
        "eligibility_note": "A student must pass every course to be categorized as Khá or above.",
    }


def _base_category(average_score: float) -> str:
    for minimum_score, category in GRADE_POLICY:
        if average_score >= minimum_score:
            return category
    return "Yếu"


def categorize_academic_performance(identifier: str | int) -> dict[str, Any]:
    """Categorize a student's academic performance using marks and policy."""
    average_result = calculate_average_score(identifier)
    if not average_result["found"]:
        return average_result

    average_score = average_result["average_score"]
    base_category = _base_category(average_score)
    failed_courses = average_result["failed_courses"]
    final_category = base_category
    eligibility_note = "Eligible for the average-based category."

    if failed_courses and base_category in {"Xuất sắc", "Giỏi", "Khá"}:
        final_category = "Trung bình"
        eligibility_note = "Category capped below Khá because at least one course is below 4.0."

    return {
        **average_result,
        "base_category": base_category,
        "category": final_category,
        "policy": grade_policy_lookup(),
        "eligibility_note": eligibility_note,
    }


def get_course_summary(course_name: str) -> dict[str, Any]:
    """Summarize one course across the full class."""
    course = _normalize_course(course_name)
    if course is None:
        return {
            "found": False,
            "message": f"Unknown course: {course_name}",
            "available_courses": list_courses(),
        }

    scores = [row[course] for row in _load_rows()]
    fail_count = sum(1 for score in scores if score < PASS_THRESHOLD)
    return {
        "found": True,
        "course": course,
        "student_count": len(scores),
        "average": round(sum(scores) / len(scores), 2),
        "min": min(scores),
        "max": max(scores),
        "fail_count": fail_count,
        "pass_rate": round(((len(scores) - fail_count) / len(scores)) * 100, 2),
    }


def get_low_score_students(course_name: str, threshold: float = 5.0) -> dict[str, Any]:
    """Return students below a threshold for one course."""
    course = _normalize_course(course_name)
    if course is None:
        return {
            "found": False,
            "message": f"Unknown course: {course_name}",
            "available_courses": list_courses(),
        }

    students = [
        {
            "id": row["ID"],
            "name": row["Name"],
            "id_card": row["ID_Card"],
            "score": row[course],
        }
        for row in _load_rows()
        if row[course] < threshold
    ]
    students.sort(key=lambda item: item["score"])
    return {
        "found": True,
        "course": course,
        "threshold": threshold,
        "count": len(students),
        "students": students,
    }


def compare_courses() -> dict[str, Any]:
    """Compare all courses using average score and pass rate."""
    summaries = [get_course_summary(course) for course in COURSE_COLUMNS]
    summaries.sort(key=lambda item: item["average"])
    return {
        "courses": summaries,
        "lowest_average_course": summaries[0]["course"],
        "highest_average_course": summaries[-1]["course"],
    }


def _normalize_course(course_name: str) -> str | None:
    query = course_name.strip().lower()
    for course in COURSE_COLUMNS:
        if course.lower() == query:
            return course
    return None


def build_score_tool_registry() -> list[dict[str, Any]]:
    """Build tool metadata for ReActAgent."""
    return [
        _tool("validate_student", "Validate a student using all three required fields: internal student_id, exact full name, and ID card. Arguments: student_id, name, id_card.", validate_student),
        _tool("get_student_marks", "Return all course marks for one student by ID, ID card, or name.", get_student_marks),
        _tool("calculate_average_score", "Calculate a student's average score and failed courses.", calculate_average_score),
        _tool("grade_policy_lookup", "Return the pass threshold and academic classification policy.", grade_policy_lookup),
        _tool("categorize_academic_performance", "Return average score, failed courses, and final academic category for one student.", categorize_academic_performance),
        _tool("list_courses", "List all courses in the dataset.", list_courses),
        _tool("get_course_summary", "Return average, min, max, fail count, and pass rate for one course.", get_course_summary),
        _tool("get_low_score_students", "Return students below a score threshold for one course. Arguments: course_name, optional threshold.", get_low_score_students),
        _tool("compare_courses", "Compare all courses by average score and pass rate.", compare_courses),
    ]


def _tool(name: str, description: str, function: Callable[..., Any]) -> dict[str, Any]:
    return {"name": name, "description": description, "function": function}
