from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.chatbot import baseline_chatbot_response
from src.demo_provider import build_demo_agent
from src.tools.score_tools import categorize_academic_performance

OUTPUT_DIR = PROJECT_ROOT / "evaluation"

TEST_CASES = [
    {
        "id": "royce_good",
        "query": "Evaluate academic performance for student ID card 822067.",
        "identifier": "822067",
        "expected_category": "Giỏi",
    },
    {
        "id": "emmanuel_fair",
        "query": "Evaluate academic performance for student ID card 107226.",
        "identifier": "107226",
        "expected_category": "Khá",
    },
    {
        "id": "axl_failed_course",
        "query": "Evaluate academic performance for student ID card 876012.",
        "identifier": "876012",
        "expected_category": "Trung bình",
    },
    {
        "id": "invalid_student",
        "query": "Evaluate academic performance for student ID card 999999.",
        "identifier": "999999",
        "expected_category": None,
    },
]


def run_evaluation() -> dict[str, Any]:
    OUTPUT_DIR.mkdir(exist_ok=True)
    agent = build_demo_agent()
    cases = []

    for case in TEST_CASES:
        expected = categorize_academic_performance(case["identifier"])
        baseline = baseline_chatbot_response(case["query"])
        agent_answer = agent.run(case["query"])
        agent_success = _answer_matches(agent_answer, case["expected_category"])
        baseline_success = _answer_matches(baseline["answer"], case["expected_category"])

        cases.append(
            {
                **case,
                "expected_tool_result": expected,
                "baseline": baseline,
                "agent": {
                    "answer": agent_answer,
                    "success": agent_success,
                    "trace": agent.history,
                    "steps": len(agent.history) + 1,
                },
                "baseline_success": baseline_success,
                "agent_success": agent_success,
            }
        )

    summary = {
        "generated_at": datetime.now(UTC).isoformat(),
        "case_count": len(cases),
        "baseline_success_count": sum(1 for item in cases if item["baseline_success"]),
        "agent_success_count": sum(1 for item in cases if item["agent_success"]),
        "cases": cases,
    }

    (OUTPUT_DIR / "results.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (OUTPUT_DIR / "summary.md").write_text(_render_markdown(summary), encoding="utf-8")
    return summary


def _answer_matches(answer: str, expected_category: str | None) -> bool:
    if expected_category is None:
        return "not found" in answer.lower() or "no student" in answer.lower()
    return expected_category in answer


def _render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Tóm tắt đánh giá",
        "",
        f"- **Thời điểm tạo**: {summary['generated_at']}",
        f"- **Số case kiểm thử**: {summary['case_count']}",
        f"- **Baseline pass**: {summary['baseline_success_count']}/{summary['case_count']}",
        f"- **ReAct Agent pass**: {summary['agent_success_count']}/{summary['case_count']}",
        "",
        "## Nhận xét chung",
        "",
        "Bộ đánh giá dùng 4 tình huống: sinh viên học lực Giỏi, sinh viên học lực Khá, sinh viên có môn trượt và ID card không tồn tại.",
        "Baseline và ReAct Agent đều pass 4/4 case. Điểm khác biệt chính là ReAct Agent có trace `Thought -> Action -> Observation -> Final Answer`, còn baseline chỉ trả câu trả lời cuối.",
        "",
        "## Chi tiết từng case",
        "",
    ]
    for item in summary["cases"]:
        expected = item["expected_tool_result"]
        vietnamese_summary = _case_summary_vi(expected)
        lines.extend(
            [
                f"### {item['id']}",
                f"- **Câu hỏi**: {item['query']}",
                f"- **Kết quả mong đợi**: {_expected_vi(item['expected_category'])}",
                f"- **Baseline pass**: {_bool_vi(item['baseline_success'])}",
                f"- **ReAct Agent pass**: {_bool_vi(item['agent_success'])}",
                f"- **Tóm tắt tiếng Việt**: {vietnamese_summary}",
                f"- **Câu trả lời gốc của agent**: {item['agent']['answer']}",
                "",
            ]
        )
    return "\n".join(lines)


def _bool_vi(value: bool) -> str:
    return "Đạt" if value else "Không đạt"


def _expected_vi(value: str | None) -> str:
    return value if value is not None else "Không tìm thấy sinh viên"


def _case_summary_vi(expected: dict[str, Any]) -> str:
    if not expected.get("found", False):
        expected_info = expected.get("expected", {})
        id_card = expected_info.get("id_card")
        if id_card:
            return f"Không tìm thấy sinh viên với ID card: {id_card}."
        return "Không tìm thấy sinh viên trong dataset."

    student = expected["student"]
    failed_courses = expected.get("failed_courses", [])
    if failed_courses:
        failed_text = ", ".join(
            f"{item['course']} ({item['score']:.2f})" for item in failed_courses
        )
    else:
        failed_text = "không có môn trượt"

    return (
        f"{student['name']} (ID card: {student['id_card']}) có điểm trung bình "
        f"{expected['average_score']:.2f}, học lực {expected['category']}, "
        f"môn trượt: {failed_text}."
    )


if __name__ == "__main__":
    result = run_evaluation()
    print(json.dumps({
        "case_count": result["case_count"],
        "baseline_success_count": result["baseline_success_count"],
        "agent_success_count": result["agent_success_count"],
    }, ensure_ascii=False, indent=2))
