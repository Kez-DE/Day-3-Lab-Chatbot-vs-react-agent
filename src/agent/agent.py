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
- Validate a student before evaluating that student.
- Use the dataset as one lab semester; do not invent status or semester fields.
- Average score means arithmetic average on the 10-point scale.
- If a tool returns not found or an error, explain that instead of inventing data.
"""

    def run(self, user_input: str) -> str:
        logger.log_event("AGENT_START", {"input": user_input, "model": self.llm.model_name})

        prompt = user_input
        last_observation = ""
        self.history = []

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
