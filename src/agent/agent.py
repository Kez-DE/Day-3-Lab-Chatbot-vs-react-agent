"""
src/agent/agent.py
ReAct Agent — Thought / Action / Observation loop với Gemini LLM.
Hỗ trợ 2 chế độ:
  - chat mode: nhận câu hỏi tự nhiên, LLM tự quyết định gọi tool nào
  - direct mode: gọi thẳng run_agent() với student_id/name/id_card
"""

import os
import re
import json
from dotenv import load_dotenv

from src.tools.validate_student       import validate_student
from src.tools.get_student_marks      import get_student_marks
from src.tools.calculate_gpa          import calculate_gpa
from src.tools.categorize_performance import (
    grade_policy_lookup,
    categorize_academic_performance,
)
from src.telemetry.logger import (
    log_thought, log_action, log_observation,
    log_final, log_error,
)

load_dotenv()

# ── Tool registry ─────────────────────────────────────────────────────────────
TOOLS = {
    "validate_student":               validate_student,
    "get_student_marks":              get_student_marks,
    "calculate_gpa":                  calculate_gpa,
    "grade_policy_lookup":            grade_policy_lookup,
    "categorize_academic_performance": categorize_academic_performance,
}

TOOL_DESCRIPTIONS = """
Các tool có sẵn:

1. validate_student(student_id, student_name, id_card)
   → Xác thực sinh viên. Trả về thông tin cơ bản và trạng thái.

2. get_student_marks(student_id, semester)
   → Lấy điểm tất cả môn học của sinh viên.

3. grade_policy_lookup()
   → Lấy chính sách qua môn và bảng xếp loại học lực.

4. calculate_gpa(student_id)
   → Tính GPA và kiểm tra môn trượt.

5. categorize_academic_performance(gpa, failed_subjects)
   → Xếp loại học lực dựa trên GPA và môn trượt.
"""

SYSTEM_PROMPT = f"""Bạn là AI agent tra cứu điểm sinh viên. Bạn hoạt động theo vòng lặp ReAct:
Thought → Action → Observation → ... → Final Answer.

{TOOL_DESCRIPTIONS}

Quy tắc:
- Luôn bắt đầu bằng validate_student trước khi làm bất cứ điều gì.
- Nếu validate thất bại → dừng ngay, trả Final Answer thông báo lỗi.
- Không bao giờ tự suy đoán điểm số — phải gọi tool để lấy dữ liệu thật.
- Mỗi bước viết rõ Thought, sau đó Action theo đúng format JSON.

Format bắt buộc cho mỗi bước:
Thought: <suy nghĩ của bạn>
Action: {{"tool": "<tên tool>", "args": {{<tham số>}}}}

Khi đã có đủ thông tin:
Final Answer: <kết quả đầy đủ>
"""


# ── LLM setup ─────────────────────────────────────────────────────────────────
def _get_llm():
    provider = os.getenv("DEFAULT_PROVIDER", "google").lower()
    if provider == "google":
        from src.core.gemini_provider import GeminiProvider
        model = os.getenv("DEFAULT_MODEL", "gemini-2.0-flash")
        return GeminiProvider(model_name=model)
    elif provider == "openai":
        from src.core.openai_provider import OpenAIProvider
        model = os.getenv("DEFAULT_MODEL", "gpt-4o")
        return OpenAIProvider(model_name=model)
    else:
        return None


# ── Parse Action từ LLM output ────────────────────────────────────────────────
def _parse_action(text: str):
    """Trích xuất JSON action từ output của LLM."""
    match = re.search(r'Action:\s*(\{.*?\})', text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        return None


def _parse_final(text: str):
    """Trích xuất Final Answer từ output của LLM."""
    match = re.search(r'Final Answer:\s*(.*)', text, re.DOTALL)
    return match.group(1).strip() if match else None


def _parse_thought(text: str):
    match = re.search(r'Thought:\s*(.*?)(?=Action:|Final Answer:|$)', text, re.DOTALL)
    return match.group(1).strip() if match else text.strip()


# ── Execute tool call ─────────────────────────────────────────────────────────
def _call_tool(tool_name: str, args: dict):
    if tool_name not in TOOLS:
        return {"error": f"Tool '{tool_name}' không tồn tại."}
    try:
        return TOOLS[tool_name](**args)
    except Exception as e:
        return {"error": str(e)}


# ── Chat Agent (LLM mode) ─────────────────────────────────────────────────────
def chat_agent(user_message: str, max_steps: int = 8) -> str:
    """
    Nhận câu hỏi tự nhiên, LLM tự quyết định gọi tool nào.
    Trả về Final Answer dạng text.
    """
    llm = _get_llm()
    if llm is None:
        return "❌ Không tìm thấy LLM provider. Kiểm tra DEFAULT_PROVIDER trong .env"

    conversation = f"User: {user_message}\n\n"
    step = 0

    while step < max_steps:
        step += 1

        # Gọi LLM
        try:
            response = llm.generate(
                prompt=conversation + "Assistant:",
                system_prompt=SYSTEM_PROMPT,
            )
            llm_output = response["content"]
        except Exception as e:
            log_error(step, str(e))
            return f"❌ Lỗi LLM: {e}"

        # Parse thought
        thought = _parse_thought(llm_output)
        log_thought(step, thought)

        # Check Final Answer
        final = _parse_final(llm_output)
        if final:
            log_final(final)
            return final

        # Parse Action
        action = _parse_action(llm_output)
        if not action:
            # LLM không trả về action đúng format — coi như final
            log_final(llm_output)
            return llm_output

        tool_name = action.get("tool", "")
        tool_args = action.get("args", {})

        log_action(step, tool_name, tool_args)

        # Gọi tool thật
        observation = _call_tool(tool_name, tool_args)
        log_observation(step, observation)

        # Thêm vào conversation history
        conversation += (
            f"Thought: {thought}\n"
            f"Action: {json.dumps(action, ensure_ascii=False)}\n"
            f"Observation: {json.dumps(observation, ensure_ascii=False)}\n\n"
        )

    return "❌ Agent vượt quá số bước tối đa mà không có Final Answer."


# ── Direct Agent (rule-based, không cần LLM) ─────────────────────────────────
def run_agent(
    student_id:   str = "",
    student_name: str = "",
    id_card:      str = "",
    semester:     str = "Spring 2026",
) -> str:
    """
    Chạy ReAct loop cố định 4 bước — không cần LLM, dùng cho API trực tiếp.
    """
    # Step 1
    log_thought(1, "Xác thực thông tin sinh viên.")
    log_action(1, "validate_student", {"student_id": student_id, "student_name": student_name, "id_card": id_card})
    val = validate_student(student_id=student_id, student_name=student_name, id_card=id_card)
    log_observation(1, val)

    if not val["valid"]:
        msg = f"❌ Không thể tra cứu: {val['error']}\nTrạng thái: {val['status']}"
        log_error(1, val["error"])
        log_final(msg)
        return msg

    student     = val["student"]
    resolved_id = str(student["id"])

    # Step 2
    log_thought(2, f"Sinh viên hợp lệ: {student['name']}. Tra cứu điểm.")
    log_action(2, "get_student_marks", {"student_id": resolved_id, "semester": semester})
    marks = get_student_marks(resolved_id, semester)
    log_observation(2, marks)

    if not marks["found"]:
        msg = f"❌ Lỗi lấy điểm: {marks['error']}"
        log_error(2, marks["error"])
        log_final(msg)
        return msg

    # Step 3
    log_thought(3, "Lấy chính sách qua môn.")
    log_action(3, "grade_policy_lookup", {})
    policy = grade_policy_lookup()
    log_observation(3, policy)

    # Step 4
    log_thought(4, "Tính GPA và xếp loại.")
    log_action(4, "calculate_gpa", {"student_id": resolved_id})
    gpa_result = calculate_gpa(resolved_id)
    log_observation(4, gpa_result)

    if gpa_result["error"]:
        msg = f"❌ Lỗi tính GPA: {gpa_result['error']}"
        log_error(4, gpa_result["error"])
        log_final(msg)
        return msg

    perf = categorize_academic_performance(
        gpa=gpa_result["gpa"],
        failed_subjects=gpa_result["failed_subjects"],
    )

    scores      = gpa_result["scores"]
    score_lines = "\n".join(
        f"  • {subj:<40} {score:.2f}" + ("  ❌ Trượt" if score < 4.0 else "")
        for subj, score in scores.items()
    )

    answer = (
        f"{'='*60}\n"
        f"KẾT QUẢ HỌC TẬP — {semester}\n"
        f"{'='*60}\n"
        f"Sinh viên : {student['name']}\n"
        f"MSSV      : {student['id']}\n"
        f"CCCD      : {student['id_card']}\n"
        f"{'─'*60}\n"
        f"Điểm các môn:\n{score_lines}\n"
        f"{'─'*60}\n"
        f"GPA học kỳ      : {gpa_result['gpa']:.2f}\n"
        f"Xếp loại học lực: {perf['ranking']}\n"
        f"{'─'*60}\n"
        f"Ghi chú: {perf['note']}\n"
        f"{'='*60}"
    )

    log_final(answer)
    return answer