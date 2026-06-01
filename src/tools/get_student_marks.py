"""
tools/get_student_marks.py
Tool 2 — Retrieve all subject marks for a validated student.
"""

from src.core.database import find_by_id

SEMESTER = "Spring 2026"


def get_student_marks(student_id: str, semester: str = SEMESTER) -> dict:
    """
    Return all subject scores for a student.

    Args:
        student_id: The row ID of the student (from validate_student result).
        semester:   Label only — all data maps to Spring 2026.

    Returns:
        {
            "found": bool,
            "student_id": str,
            "semester": str,
            "scores": { subject: float, ... } | None,
            "error": str | None,
        }
    """
    record = find_by_id(str(student_id))

    if record is None:
        return {
            "found": False,
            "student_id": student_id,
            "semester": semester,
            "scores": None,
            "error": f"Không tìm thấy sinh viên ID={student_id}.",
        }

    return {
        "found": True,
        "student_id": str(record["id"]),
        "semester": semester,
        "scores": record["scores"],   # { subject: float }
        "error": None,
    }
