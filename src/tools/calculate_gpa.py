"""
tools/calculate_gpa.py
Tool 3 — Calculate semester GPA from subject scores.

Handles the decimal-parsing edge case (European comma separator)
that caused the v1 agent bug documented in the debugging case study.
"""

from src.core.database import find_by_id


def _safe_float(value) -> float:
    """
    Robustly convert a score value to float.
    Handles: float, int, '8,5' (comma), '8.5' (dot).
    Raises ValueError with a clear message on failure.
    """
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.strip().replace(",", ".")
        try:
            return float(cleaned)
        except ValueError:
            raise ValueError(
                f"Cannot parse score value: {value!r}. "
                "Expected a number like '8.5' or '8,5'."
            )
    raise TypeError(f"Unexpected score type: {type(value).__name__}")


def calculate_gpa(student_id: str) -> dict:
    """
    Calculate the average GPA across all subjects.

    Returns:
        {
            "student_id": str,
            "gpa": float (rounded to 2 dp) | None,
            "scores": { subject: float } | None,
            "failed_subjects": [str],   # subjects with score < 4.0
            "error": str | None,
        }
    """
    record = find_by_id(str(student_id))

    if record is None:
        return {
            "student_id": student_id,
            "gpa": None,
            "scores": None,
            "failed_subjects": [],
            "error": f"Không tìm thấy sinh viên ID={student_id}.",
        }

    try:
        scores = {subj: _safe_float(val) for subj, val in record["scores"].items()}
    except (ValueError, TypeError) as exc:
        return {
            "student_id": student_id,
            "gpa": None,
            "scores": None,
            "failed_subjects": [],
            "error": f"Lỗi parse điểm: {exc}",
        }

    gpa = round(sum(scores.values()) / len(scores), 2)
    failed = [subj for subj, sc in scores.items() if sc < 4.0]

    return {
        "student_id": str(record["id"]),
        "gpa": gpa,
        "scores": scores,
        "failed_subjects": failed,
        "error": None,
    }
