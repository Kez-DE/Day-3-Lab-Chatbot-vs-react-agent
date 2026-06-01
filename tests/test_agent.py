from src.agent.agent import ReActAgent
from src.core.llm_provider import LLMProvider
from src.demo_provider import build_demo_agent
from src.tools.score_tools import build_score_tool_registry


class ScriptedProvider(LLMProvider):
    def __init__(self, responses):
        super().__init__(model_name="scripted-test-model")
        self.responses = list(responses)
        self.calls = []

    def generate(self, prompt, system_prompt=None):
        self.calls.append({"prompt": prompt, "system_prompt": system_prompt})
        content = self.responses.pop(0)
        return {
            "content": content,
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            "latency_ms": 1,
            "provider": "scripted",
        }

    def stream(self, prompt, system_prompt=None):
        yield self.generate(prompt, system_prompt)["content"]


def test_react_agent_executes_tool_and_returns_final_answer():
    provider = ScriptedProvider(
        [
            "Thought: I need to validate the student.\nAction: validate_student(30, \"Royce Lowe\", \"822067\")",
            "Thought: I have the student.\nAction: categorize_academic_performance(822067)",
            "Final Answer: Royce Lowe is categorized as Giỏi with average score 8.39.",
        ]
    )
    agent = ReActAgent(provider, build_score_tool_registry(), max_steps=5)

    answer = agent.run("Evaluate student_id 30 name Royce Lowe id_card 822067")

    assert "Giỏi" in answer
    assert "Observation:" in provider.calls[1]["prompt"]
    assert "Royce Lowe" in provider.calls[1]["prompt"]


def test_react_agent_handles_unknown_tool_without_crashing():
    provider = ScriptedProvider(
        [
            "Thought: I will call a missing tool.\nAction: missing_tool(822067)",
            "Final Answer: I could not use that tool, so I should ask for a valid action.",
        ]
    )
    agent = ReActAgent(provider, build_score_tool_registry(), max_steps=3)

    answer = agent.run("Evaluate student_id 30 name Royce Lowe id_card 822067")

    assert "valid action" in answer
    assert "Tool missing_tool not found" in provider.calls[1]["prompt"]


def test_react_agent_timeout_returns_last_observation():
    provider = ScriptedProvider(
        [
            "Thought: validate.\nAction: validate_student(30, \"Royce Lowe\", \"822067\")",
            "Thought: validate again.\nAction: validate_student(30, \"Royce Lowe\", \"822067\")",
        ]
    )
    agent = ReActAgent(provider, build_score_tool_registry(), max_steps=2)

    answer = agent.run("Evaluate student_id 30 name Royce Lowe id_card 822067")

    assert "max steps" in answer.lower()
    assert "Royce Lowe" in answer


def test_react_agent_returns_natural_clarification_without_retry_loop():
    provider = ScriptedProvider(
        [
            "Please provide a student ID card, internal ID, or exact full name so I can look up marks."
        ]
    )
    agent = ReActAgent(provider, build_score_tool_registry(), max_steps=5)

    answer = agent.run("s")

    assert "student ID" in answer
    assert len(provider.calls) == 1


def test_system_prompt_guides_single_identifier_mark_lookup():
    provider = ScriptedProvider(["Final Answer: done"])
    agent = ReActAgent(provider, build_score_tool_registry())

    prompt = agent.get_system_prompt()

    assert "the user must provide all three fields" in prompt
    assert "điểm của 822067" in prompt
    assert "Never call validate_student with None" in prompt


def test_react_agent_requires_full_identity_before_student_info():
    provider = ScriptedProvider(["Final Answer: should not be called"])
    agent = ReActAgent(provider, build_score_tool_registry(), max_steps=5)

    answer = agent.run("điểm của 822067")

    assert "student_id, name và id_card" in answer
    assert provider.calls == []


def test_demo_agent_returns_marks_after_full_identity_for_mark_request():
    agent = build_demo_agent()

    answer = agent.run("điểm của student_id 30 name Royce Lowe id_card 822067")

    assert "Computer Science" in answer
    assert "Linear Algebra" in answer
    assert "Academic category" not in answer


def test_agent_accepts_natural_identity_order_for_student_info():
    agent = build_demo_agent()

    answer = agent.run("đưa ra điểm của sinh viên 1 Kiara Perkins 620602")

    assert "Kiara Perkins" in answer
    assert "Computer Science" in answer
    assert "Linear Algebra" in answer


def test_agent_accepts_semicolon_identity_order_for_student_info():
    agent = build_demo_agent()

    answer = agent.run("điểm của 38;Jair Ball;505496")

    assert "Jair Ball" in answer
    assert "Computer Science: 9.73" in answer


def test_agent_accepts_vietnamese_labeled_identity_in_any_order():
    agent = build_demo_agent()

    answer = agent.run(
        "Cho tôi điểm của sinh viên Royce Lowe, mã sinh viên 30, số CCCD 822067"
    )

    assert "Royce Lowe" in answer
    assert "Computer Science: 9.30" in answer
    assert "Linear Algebra: 9.85" in answer


def test_agent_accepts_vietnamese_labeled_identity_reordered():
    agent = build_demo_agent()

    answer = agent.run("Cho tôi điểm số CCCD 822067, mã sinh viên 30, sinh viên Royce Lowe")

    assert "Royce Lowe" in answer
    assert "Computer Science: 9.30" in answer


def test_demo_agent_explains_identity_mismatches():
    agent = build_demo_agent()

    answer = agent.run("đưa ra điểm của 31 Abby Pruitt 432848")

    assert "mismatch" in answer.lower()
    assert "student_id" in answer
    assert "dataset has 35" in answer
