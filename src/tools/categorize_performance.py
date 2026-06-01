"""
tools/categorize_performance.py
Tool 4 — Grade policy lookup + academic performance categorization.
"""


# ── policy definition ─────────────────────────────────────────────────────────

GRADE_POLICY = {
    "passing_score":   4.0,
    "semester":        "Spring 2026",
    "rankings": [
        {"label": "Xuất sắc", "min_gpa": 9.0,  "max_gpa": 10.0, "no_fail_required": True},
        {"label": "Giỏi",     "min_gpa": 8.0,  "max_gpa": 9.0,  "no_fail_required": True},
        {"label": "Khá",      "min_gpa": 6.5,  "max_gpa": 8.0,  "no_fail_required": True},
        {"label": "Trung bình","min_gpa": 5.0, "max_gpa": 6.5,  "no_fail_required": False},
        {"label": "Yếu",      "min_gpa": 0.0,  "max_gpa": 5.0,  "no_fail_required": False},
    ],
    "note": (
        "Để đạt loại Khá trở lên, sinh viên không được trượt bất kỳ môn nào "
        "(không có môn nào < 4.0)."
    ),
}


def grade_policy_lookup() -> dict:
    """Return the full grade policy for Spring 2026."""
    return GRADE_POLICY


# ── categorization logic ──────────────────────────────────────────────────────

def categorize_academic_performance(
    gpa: float,
    failed_subjects: list[str],
) -> dict:
    """
    Determine academic ranking given a GPA and failed subject list.

    Business rule: if the nominal rank requires no_fail_required=True
    but the student has failed subjects, demote to 'Trung bình'.

    Args:
        gpa:             Calculated semester GPA.
        failed_subjects: List of subject names with score < 4.0.

    Returns:
        {
            "gpa": float,
            "ranking": str,
            "has_failed_subjects": bool,
            "failed_subjects": [str],
            "note": str,
        }
    """
    has_failed = len(failed_subjects) > 0

    nominal_rank = "Yếu"
    for tier in GRADE_POLICY["rankings"]:
        if tier["min_gpa"] <= gpa < tier["max_gpa"] or (
            tier["max_gpa"] == 10.0 and gpa == 10.0
        ):
            nominal_rank = tier["label"]
            no_fail_required = tier["no_fail_required"]
            break
    else:
        no_fail_required = False

    # Demotion rule
    if no_fail_required and has_failed:
        final_rank = "Trung bình"
        note = (
            f"GPA {gpa:.2f} đủ điều kiện '{nominal_rank}' nhưng bị hạ xuống "
            f"'Trung bình' do trượt môn: {', '.join(failed_subjects)}."
        )
    else:
        final_rank = nominal_rank
        if has_failed:
            note = (
                f"Xếp loại '{final_rank}'. "
                f"Môn trượt: {', '.join(failed_subjects)}."
            )
        else:
            note = f"Xếp loại '{final_rank}'. Không có môn nào dưới 4.0."

    return {
        "gpa": gpa,
        "ranking": final_rank,
        "has_failed_subjects": has_failed,
        "failed_subjects": failed_subjects,
        "note": note,
    }
