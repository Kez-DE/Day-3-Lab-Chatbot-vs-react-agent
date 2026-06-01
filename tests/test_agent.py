from src.agent.agent import ReActAgent
from src.core.llm_provider import LLMProvider
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

    answer = agent.run("Evaluate student 822067")

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

    answer = agent.run("Evaluate student 822067")

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

    answer = agent.run("Evaluate student 822067")

    assert "max steps" in answer.lower()
    assert "Royce Lowe" in answer
