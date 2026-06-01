import ast
import json
import re
from typing import Any, Dict, List

from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger
from src.telemetry.metrics import tracker


class ReActAgent:
    """
    ReAct-style agent that follows a Thought -> Action -> Observation loop.

    Tools are dictionaries with:
    - name: public tool name used by the LLM
    - description: short usage contract
    - function: Python callable
    """

    ACTION_PATTERN = re.compile(r"Action\s*:\s*([a-zA-Z_][\w]*)\s*\((.*?)\)", re.DOTALL)
    FINAL_PATTERN = re.compile(r"Final(?:\s+Answer)?\s*:\s*(.*)", re.DOTALL | re.IGNORECASE)
    STUDENT_INFO_PATTERN = re.compile(
        r"\b(student|sinh\s*viên|diem|điểm|marks?|scores?|hoc\s*luc|học\s*lực|"
        r"academic|performance|average|trung\s*bình|failed|trượt)\b",
        re.IGNORECASE,
    )
    STUDENT_ID_PATTERN = re.compile(
        r"\b(?:student[_\s-]*id|internal[_\s-]*id|id\s+sinh\s*viên|"
        r"mã\s*(?:số\s*)?sinh\s*viên|ma\s*(?:so\s*)?sinh\s*vien)\s*"
        r"[:=]?\s*(\d{1,6})\b",
        re.IGNORECASE,
    )
    ID_CARD_PATTERN = re.compile(
        r"\b(?:id[_\s-]*card|id\s+card|(?:số|so)\s*cccd|(?:số|so)\s*cmnd|"
        r"cccd|cmnd|card|mã\s*thẻ|ma\s*the)\s*"
        r"[:=]?\s*(\d{1,6})\b",
        re.IGNORECASE,
    )
    NAME_PATTERN = re.compile(
        r"\b(?:name|tên|ten)\s*[:=]?\s*(.+?)(?=\s+\b(?:student[_\s-]*id|"
        r"internal[_\s-]*id|id\s+sinh\s*viên|mã\s+sinh\s*viên|ma\s+sinh\s*vien|"
        r"id[_\s-]*card|id\s+card|cccd|cmnd|card|mã\s*thẻ|ma\s*the)\b|[,;]|\Z)",
        re.IGNORECASE | re.DOTALL,
    )
    STUDENT_NAME_PATTERN = re.compile(
        r"\b(?:sinh\s*viên|student)\s+([^\d,;]+?)(?=\s*,|\s*;|\s+\b(?:"
        r"student[_\s-]*id|internal[_\s-]*id|id\s+sinh\s*viên|"
        r"mã\s*(?:số\s*)?sinh\s*viên|ma\s*(?:so\s*)?sinh\s*vien|"
        r"id[_\s-]*card|id\s+card|(?:số|so)\s*cccd|(?:số|so)\s*cmnd|"
        r"cccd|cmnd|card|mã\s*thẻ|ma\s*the)\b|\Z)",
        re.IGNORECASE | re.DOTALL,
    )
    NATURAL_IDENTITY_PATTERN = re.compile(
        r"(?:\b(?:sinh\s*viên|student)\b\s*)?(\d{1,6})\s+([^\d,;]+?)\s+(\d{1,6})\b",
        re.IGNORECASE | re.DOTALL,
    )
    DELIMITED_IDENTITY_PATTERN = re.compile(
        r"(\d{1,6})\s*[;,]\s*([^;,0-9]+?)\s*[;,]\s*(\d{1,6})\b",
        re.IGNORECASE | re.DOTALL,
    )

    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 5):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.history: list[dict[str, Any]] = []

    def get_system_prompt(self) -> str:
        tool_descriptions = "\n".join(
            [f"- {tool['name']}: {tool['description']}" for tool in self.tools]
        )
        return f"""You are a careful academic advising ReAct agent.
You must answer using only information returned by tools.

Available tools:
{tool_descriptions}

Use this format exactly:
Thought: explain the next required step briefly.
Action: tool_name(argument1, argument2)

After you receive an Observation, continue if another tool is needed.
When enough evidence exists, answer with:
Final Answer: concise answer with marks, average score, pass/fail status, and academic category when relevant.

Rules:
- Answer in the same language as the user when possible.
- For any student-specific information, the user must provide all three fields: student_id, name, and id_card.
- If any identity field is missing, ask for the missing fields and do not call tools.
- Always call validate_student(student_id, name, id_card) before returning marks, scores, average score, failed courses, or academic category.
- After validate_student returns found=true, call get_student_marks(validated_id_card) for marks/scores/điểm requests.
- After validate_student returns found=true, call categorize_academic_performance(validated_id_card) for academic performance, học lực, average score, failed courses, or category requests.
- Never call validate_student with None, UNKNOWN, or missing identity values.
- Use the dataset as one lab semester; do not invent status or semester fields.
- Average score means arithmetic average on the 10-point scale.
- If a tool returns not found or an error, explain that instead of inventing data.
- trả lời bằng tiếng việt khi user hỏi về điểm, học lực, điểm trung bình, môn trượt, xếp loại học lực.
Examples:
User: điểm của 822067
Final Answer: Vui lòng cung cấp đủ student_id, name và id_card trước khi xem thông tin sinh viên.

User: student_id 30 name Royce Lowe id_card 822067 điểm
Thought: I must validate the full student identity before returning marks.
Action: validate_student(30, "Royce Lowe", "822067")

User: student_id 30 name Royce Lowe id_card 822067 học lực
Thought: I must validate the full student identity before returning academic performance.
Action: validate_student(30, "Royce Lowe", "822067")
"""

    def run(self, user_input: str) -> str:
        logger.log_event("AGENT_START", {"input": user_input, "model": self.llm.model_name})

        prompt = user_input
        last_observation = ""
        self.history = []
        identity_fields = self._extract_identity_fields(user_input)
        identity_check = self._identity_requirement_message(user_input, identity_fields)
        if identity_check is not None:
            logger.log_event(
                "IDENTITY_REQUIRED",
                {"input": user_input, "message": identity_check},
            )
            logger.log_event("AGENT_END", {"steps": 0, "status": "identity_required"})
            return identity_check
        if self.STUDENT_INFO_PATTERN.search(user_input) and all(identity_fields.values()):
            prompt = (
                f"{user_input}\n\n"
                "Parsed identity fields to use exactly:\n"
                f"student_id: {identity_fields['student_id']}\n"
                f"name: {identity_fields['name']}\n"
                f"id_card: {identity_fields['id_card']}"
            )

        for step in range(1, self.max_steps + 1):
            result = self.llm.generate(prompt, system_prompt=self.get_system_prompt())
            tracker.track_request(
                provider=result.get("provider", "unknown"),
                model=self.llm.model_name,
                usage=result.get("usage", {}),
                latency_ms=result.get("latency_ms", 0),
            )

            content = result.get("content", "").strip()
            logger.log_event("LLM_RESPONSE", {"step": step, "content": content})

            final_answer = self._parse_final_answer(content)
            if final_answer is not None:
                logger.log_event("FINAL_ANSWER", {"step": step, "answer": final_answer})
                logger.log_event("AGENT_END", {"steps": step, "status": "completed"})
                return final_answer

            action = self._parse_action(content)
            if action is None:
                observation = "Parser error: no valid Action or Final Answer found."
                logger.log_event("PARSER_ERROR", {"step": step, "content": content})
                if content:
                    self.history.append(
                        {"step": step, "llm_response": content, "observation": observation}
                    )
                    logger.log_event(
                        "AGENT_END", {"steps": step, "status": "direct_response"}
                    )
                    return content
            else:
                tool_name, args = action
                observation = self._execute_tool(tool_name, args)
                logger.log_event(
                    "TOOL_CALL",
                    {"step": step, "tool": tool_name, "args": args, "observation": observation},
                )

            self.history.append(
                {"step": step, "llm_response": content, "observation": observation}
            )
            last_observation = observation
            prompt = f"{prompt}\n\n{content}\nObservation: {observation}"

        logger.log_event("AGENT_END", {"steps": self.max_steps, "status": "max_steps"})
        return (
            "Reached max steps before a final answer. Last observation: "
            f"{last_observation}"
        )

    def _parse_final_answer(self, text: str) -> str | None:
        match = self.FINAL_PATTERN.search(text)
        if not match:
            return None
        answer = match.group(1).strip()
        return answer or None

    def _parse_action(self, text: str) -> tuple[str, str] | None:
        match = self.ACTION_PATTERN.search(text)
        if not match:
            return None
        return match.group(1).strip(), match.group(2).strip()

    def _execute_tool(self, tool_name: str, args: str) -> str:
        for tool in self.tools:
            if tool["name"] == tool_name:
                function = tool.get("function")
                if function is None:
                    return f"Tool {tool_name} has no function attached."
                try:
                    parsed_args = self._parse_args(args)
                    result = function(*parsed_args)
                    return json.dumps(result, ensure_ascii=False, indent=2)
                except Exception as exc:  # defensive boundary between LLM output and Python tools
                    return f"Tool {tool_name} error: {exc}"
        return f"Tool {tool_name} not found."

    def _parse_args(self, args: str) -> list[Any]:
        if not args:
            return []

        # Support simple ReAct calls such as
        # validate_student(30, "Royce Lowe", "822067"),
        # get_low_score_students("Calculus", 5.0), and keyword-looking calls
        # by falling back to literal values.
        wrapped = f"f({args})"
        expression = ast.parse(wrapped, mode="eval")
        call = expression.body
        if not isinstance(call, ast.Call):
            return [args]

        parsed: list[Any] = []
        for arg in call.args:
            parsed.append(ast.literal_eval(arg))
        for keyword in call.keywords:
            parsed.append(ast.literal_eval(keyword.value))
        return parsed

    def _identity_requirement_message(
        self, user_input: str, provided: dict[str, str | None] | None = None
    ) -> str | None:
        if not self.STUDENT_INFO_PATTERN.search(user_input):
            return None

        provided = provided or self._extract_identity_fields(user_input)
        missing = [
            field
            for field in ("student_id", "name", "id_card")
            if not provided.get(field)
        ]
        if not missing:
            return None

        return (
            "Vui lòng cung cấp đủ student_id, name và id_card trước khi xem "
            "thông tin sinh viên. Ví dụ: student_id 30 name Royce Lowe "
            "id_card 822067 điểm."
        )

    def _extract_identity_fields(self, user_input: str) -> dict[str, str | None]:
        student_id_match = self.STUDENT_ID_PATTERN.search(user_input)
        id_card_match = self.ID_CARD_PATTERN.search(user_input)
        name_match = self.NAME_PATTERN.search(user_input)
        student_name_match = self.STUDENT_NAME_PATTERN.search(user_input)

        name = None
        if name_match:
            name = name_match.group(1).strip()
        elif student_name_match:
            name = student_name_match.group(1).strip()
        if name:
            name = re.sub(r"\s+", " ", name)

        fields = {
            "student_id": student_id_match.group(1) if student_id_match else None,
            "name": name,
            "id_card": id_card_match.group(1) if id_card_match else None,
        }
        if all(fields.values()):
            return fields

        unlabelled_match = self.DELIMITED_IDENTITY_PATTERN.search(user_input)
        if not unlabelled_match:
            unlabelled_match = self.NATURAL_IDENTITY_PATTERN.search(user_input)

        if unlabelled_match:
            natural_name = re.sub(r"\s+", " ", unlabelled_match.group(2).strip())
            return {
                "student_id": unlabelled_match.group(1),
                "name": natural_name,
                "id_card": unlabelled_match.group(3),
            }

        return fields
