from src.tools.score_tools import (
    calculate_average_score,
    categorize_academic_performance,
    get_student_marks,
    list_courses,
    validate_student,
)

def test_validate_student_rejects_mismatched_identity_fields():
    result = validate_student(30, "Wrong Name", "822067")

    assert result["found"] is False
    assert "validation failed" in result["message"]
    assert "name" in result["mismatches"]


def test_get_student_marks_converts_decimal_comma_scores():
    result = get_student_marks("822067")

    assert result["found"] is True
    assert result["marks"]["Computer Science"] == 9.30
    assert result["marks"]["Linear Algebra"] == 9.85