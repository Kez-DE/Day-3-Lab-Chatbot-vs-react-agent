from src.tools.score_tools import (
    calculate_average_score,
    categorize_academic_performance,
    get_student_marks,
    list_courses,
    validate_student,
)


def test_validate_student_requires_id_name_and_id_card():
    result = validate_student(30, "Royce Lowe", "822067")

    assert result["found"] is True
    assert result["student"]["id"] == 30
    assert result["student"]["name"] == "Royce Lowe"
    assert result["student"]["id_card"] == "822067"


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


def test_calculate_average_score_for_royce_lowe():
    result = calculate_average_score("822067")

    assert result["average_score"] == 8.39
    assert result["passed_all_courses"] is True
    assert result["failed_courses"] == []


def test_categorize_academic_performance_good_case():
    result = categorize_academic_performance("822067")

    assert result["category"] == "Giỏi"
    assert result["base_category"] == "Giỏi"
    assert result["average_score"] == 8.39
    assert result["passed_all_courses"] is True


def test_categorize_academic_performance_fair_case():
    result = categorize_academic_performance("107226")

    assert result["category"] == "Khá"
    assert result["average_score"] == 6.96
    assert result["passed_all_courses"] is True


def test_failed_course_caps_category_below_fair():
    # Axl Waters has average 6.31 but DSA = 3.16, so final category must not be Khá or above.
    result = categorize_academic_performance("876012")

    assert result["base_category"] == "Trung bình"
    assert result["category"] == "Trung bình"
    assert result["passed_all_courses"] is False
    assert result["failed_courses"] == [
        {"course": "Data Structures and Algorithms", "score": 3.16}
    ]


def test_unknown_student_returns_not_found():
    result = validate_student("UNKNOWN-ID", "Unknown Student", "999999")

    assert result["found"] is False
    assert "999999" in result["message"]


def test_list_courses_matches_dataset_columns():
    assert list_courses() == [
        "Computer Science",
        "Microeconomics",
        "Data Structures and Algorithms",
        "Calculus",
        "Linear Algebra",
    ]