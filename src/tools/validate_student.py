"""
tools/validate_student.py
Tool 1 — Validate student identity.

Accepts student_id (row ID), student_name, or id_card.
Returns student status or a structured error.
"""

import re
from src.core.database import find_by_id, find_by_name, find_by_id_card

# ── injection guard ───────────────────────────────────────────────────────────
_INJECTION_RE = re.compile(
    r"(ignore\s+.*instructions|drop\s+table|<script|or\s+1=1|--|';)",
    re.IGNORECASE,
)


def _sanitize(value: str) -> str:
    if _INJECTION_RE.search(value):
        raise ValueError(f"Potentially malicious input detected: {value!r}")
    return value.strip()


# ── main tool ─────────────────────────────────────────────────────────────────

def validate_student(
    student_id: str = "",
    student_name: str = "",
    id_card: str = "",
) -> dict:
    """
    Validate a student by any one identifier.

    Priority: student_id > id_card > student_name

    Returns:
        {
            "valid": bool,
            "student": { id, name, id_card } | None,
            "status": "Đang học" | "Thôi học" | "Không tìm thấy" | "Lỗi đầu vào",
            "error": str | None,
        }
    """
    # ── sanitize inputs ───────────────────────────────────────────────────────
    try:
        student_id   = _sanitize(str(student_id))
        student_name = _sanitize(str(student_name))
        id_card      = _sanitize(str(id_card))
    except ValueError as exc:
        return {
            "valid": False,
            "student": None,
            "status": "Lỗi đầu vào",
            "error": str(exc),
        }

    if not any([student_id, student_name, id_card]):
        return {
            "valid": False,
            "student": None,
            "status": "Lỗi đầu vào",
            "error": "Phải cung cấp ít nhất một trong: student_id, student_name, id_card.",
        }

    # ── lookup ────────────────────────────────────────────────────────────────
    record = None
    if student_id:
        record = find_by_id(student_id)
    if record is None and id_card:
        record = find_by_id_card(id_card)
    if record is None and student_name:
        record = find_by_name(student_name)

    if record is None:
        return {
            "valid": False,
            "student": None,
            "status": "Không tìm thấy",
            "error": f"Không tìm thấy sinh viên với thông tin đã cung cấp.",
        }

    # ── all students in DB are active (status field not in CSV) ──────────────
    student_info = {
        "id":      record["id"],
        "name":    record["name"],
        "id_card": record["id_card"],
    }

    return {
        "valid": True,
        "student": student_info,
        "status": "Đang học",
        "error": None,
    }
