from __future__ import annotations

import re
from typing import Any

from src.tools.score_tools import categorize_academic_performance


def baseline_chatbot_response(query: str) -> dict[str, Any]:
    """
    Minimal non-agent baseline.

    The baseline intentionally does not run a ReAct loop. It only extracts a likely
    student identifier and calls one deterministic summary function. This provides a
    simple comparison point for the ReAct agent in the lab report.
    """
    identifier = _extract_identifier(query)
    if identifier is None:
        return {
            "answer": "I need a student ID card, internal ID, or exact full name to evaluate performance.",
            "used_tools": [],
            "success": False,
        }

    result = categorize_academic_performance(identifier)
    if not result["found"]:
        return {
            "answer": result["message"],
            "used_tools": ["categorize_academic_performance"],
            "success": False,
        }

    answer = (
        f"{result['student']['name']} has an average score of "
        f"{result['average_score']:.2f} and is categorized as {result['category']}."
    )
    return {
        "answer": answer,
        "used_tools": ["categorize_academic_performance"],
        "success": True,
    }


def _extract_identifier(query: str) -> str | None:
    digit_match = re.search(r"\b\d{1,6}\b", query)
    if digit_match:
        return digit_match.group(0)

    name_match = re.search(r"student\s+([A-Z][A-Za-z]+\s+[A-Z][A-Za-z]+)", query)
    if name_match:
        return name_match.group(1)
    return None
