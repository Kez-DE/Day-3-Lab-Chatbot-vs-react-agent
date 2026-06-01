from __future__ import annotations

from typing import Any

from src.agent.agent import ReActAgent
from src.core.llm_provider import LLMProvider
from src.tools.score_tools import build_score_tool_registry


class DemoAcademicProvider(LLMProvider):
    """
    Deterministic provider for offline demos and tests.

    It follows the same Thought/Action/Observation contract expected from a real LLM,
    but avoids requiring an API key during lab verification.
    """

    def __init__(self):
        super().__init__(model_name="demo-academic-provider")

    def generate(self, prompt: str, system_prompt: str | None = None) -> dict[str, Any]:
        identifier = _extract_identifier_from_prompt(prompt)
        validation_args = _validation_args_from_prompt(prompt) or _validation_args_for_identifier(
            identifier
        )
        if "Observation:" not in prompt:
            content = (
                "Thought: I need to validate the student using all required identity fields.\n"
                f"Action: validate_student({validation_args})"
            )
        elif '"found": false' in prompt:
            content = _final_answer_from_observation(prompt)
        elif _is_marks_request(prompt) and "get_student_marks" not in prompt:
            content = (
                "Thought: The student exists, so I need the course marks.\n"
                f"Action: get_student_marks({identifier})"
            )
        elif _is_marks_request(prompt):
            content = _final_answer_from_observation(prompt)
        elif "categorize_academic_performance" not in prompt:
            content = (
                "Thought: The student exists, so I need marks, average score, failed courses, "
                "and final category.\n"
                f"Action: categorize_academic_performance({identifier})"
            )
        else:
            content = _final_answer_from_observation(prompt)

        return {
            "content": content,
            "usage": {
                "prompt_tokens": max(1, len(prompt.split())),
                "completion_tokens": max(1, len(content.split())),
                "total_tokens": max(1, len(prompt.split()) + len(content.split())),
            },
            "latency_ms": 0,
            "provider": "demo",
        }

    def stream(self, prompt: str, system_prompt: str | None = None):
        yield self.generate(prompt, system_prompt)["content"]


def build_demo_agent(max_steps: int = 5) -> ReActAgent:
    return ReActAgent(DemoAcademicProvider(), build_score_tool_registry(), max_steps=max_steps)


def _extract_identifier_from_prompt(prompt: str) -> str:
    import re

    id_card_match = re.search(
        r"\b(?:id[_\s-]*card|id\s+card|cccd|cmnd)\s*[:=]?\s*(\d{1,6})\b",
        prompt,
        flags=re.IGNORECASE,
    )
    if id_card_match:
        return id_card_match.group(1)

    matches = re.findall(r"\b\d{1,6}\b", prompt)
    return matches[0] if matches else "UNKNOWN"


def _validation_args_for_identifier(identifier: str) -> str:
    # The demo provider uses the ID card from the query to prepare a full validation
    # call. In a real UI, these three values would come from form fields.
    known_students = {
        "822067": (30, "Royce Lowe", "822067"),
        "107226": (4, "Emmanuel Myers", "107226"),
        "876012": (10, "Axl Waters", "876012"),
    }
    student_id, name, id_card = known_students.get(identifier, ("UNKNOWN", "UNKNOWN", identifier))
    return f'{student_id!r}, {name!r}, {id_card!r}'


def _validation_args_from_prompt(prompt: str) -> str | None:
    import re

    student_id_match = re.search(r"\bstudent_id:\s*(\d{1,6})\b", prompt)
    name_match = re.search(r"\bname:\s*(.+)", prompt)
    id_card_match = re.search(r"\bid_card:\s*(\d{1,6})\b", prompt)
    if not (student_id_match and name_match and id_card_match):
        return None

    return (
        f"{student_id_match.group(1)!r}, "
        f"{name_match.group(1).strip()!r}, "
        f"{id_card_match.group(1)!r}"
    )


def _is_marks_request(prompt: str) -> bool:
    lowered = prompt.lower()
    asks_for_marks = any(term in lowered for term in ["điểm", "diem", "mark", "score"])
    asks_for_performance = any(
        term in lowered
        for term in [
            "academic performance",
            "học lực",
            "hoc luc",
            "average",
            "trung bình",
            "trung binh",
            "category",
            "failed",
        ]
    )
    return asks_for_marks and not asks_for_performance


def _final_answer_from_observation(prompt: str) -> str:
    # Keep final synthesis deterministic for offline evaluation. The real provider
    # path still uses OpenAI/Gemini/local models through LLMProvider.
    import json
    import re

    observations = re.findall(r"Observation:\s*(\{.*?\})(?=\n\nThought:|\Z)", prompt, flags=re.DOTALL)
    if not observations:
        return "Final Answer: I could not find a valid observation to summarize."

    try:
        data = json.loads(observations[-1])
    except json.JSONDecodeError:
        return f"Final Answer: {observations[-1].strip()}"

    if not data.get("found", True):
        return f"Final Answer: {_not_found_message(data)}"

    student = data["student"]
    if "marks" in data:
        marks_text = ", ".join(
            f"{course}: {score:.2f}" for course, score in data["marks"].items()
        )
        return (
            "Final Answer: "
            f"{student['name']} (ID Card: {student['id_card']}) has these marks: "
            f"{marks_text}."
        )

    failed_courses = data.get("failed_courses", [])
    failed_text = "none" if not failed_courses else ", ".join(
        f"{item['course']} ({item['score']:.2f})" for item in failed_courses
    )
    return (
        "Final Answer: "
        f"{student['name']} (ID Card: {student['id_card']}) has an average score of "
        f"{data['average_score']:.2f} on the 10-point scale. "
        f"Failed courses: {failed_text}. "
        f"Passed all courses: {data['passed_all_courses']}. "
        f"Academic category: {data['category']}."
    )


def _not_found_message(data: dict[str, Any]) -> str:
    message = data.get("message", "Student was not found.")
    mismatches = data.get("mismatches")
    if not mismatches:
        return message

    details = []
    for field, values in mismatches.items():
        details.append(
            f"{field}: provided {values.get('expected')}, dataset has {values.get('actual')}"
        )
    return f"{message} Mismatches: {', '.join(details)}."
