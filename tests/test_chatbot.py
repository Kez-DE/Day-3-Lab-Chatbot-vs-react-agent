from src.chatbot import baseline_chatbot_response


def test_baseline_chatbot_evaluates_known_student():
    result = baseline_chatbot_response("Evaluate academic performance for student ID card 822067.")

    assert result["success"] is True
    assert "Royce Lowe" in result["answer"]
    assert "Giỏi" in result["answer"]


def test_baseline_chatbot_handles_missing_identifier():
    result = baseline_chatbot_response("Evaluate this student please")

    assert result["success"] is False
    assert "student ID" in result["answer"]
