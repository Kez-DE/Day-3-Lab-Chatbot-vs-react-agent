from __future__ import annotations

import argparse
import logging
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.agent.agent import ReActAgent
from src.demo_provider import build_demo_agent
from src.telemetry.logger import logger as agent_logger
from src.tools.score_tools import build_score_tool_registry


EXIT_COMMANDS = {"exit", "quit", "q", ":q"}
IDENTITY_REQUIRED_PREFIX = "Vui lòng cung cấp đủ student_id, name và id_card"
IDENTITY_ONLY_PATTERN = re.compile(r"^\s*\d{1,6}\s+[^\d,;]+?\s+\d{1,6}\s*$")


def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env")
    args = _parse_args()
    if not args.show_logs:
        _disable_console_logs()
    agent = _build_agent(args)

    print("Academic ReAct Agent terminal chat")
    print("Type your question, or type 'exit' to quit.")
    print(
        "Example: Evaluate academic performance for student_id 30 "
        "name Royce Lowe id_card 822067."
    )
    print()

    pending_student_query: str | None = None
    while True:
        try:
            user_input = input("You> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            return

        if not user_input:
            continue
        if user_input.lower() in EXIT_COMMANDS:
            print("Bye.")
            return

        if pending_student_query and _looks_like_identity_only(user_input):
            user_input = f"{pending_student_query} {user_input}"
            pending_student_query = None

        try:
            answer = agent.run(user_input)
        except Exception as exc:
            print(f"Agent error: {exc}")
            continue

        if answer.startswith(IDENTITY_REQUIRED_PREFIX):
            pending_student_query = user_input
        else:
            pending_student_query = None

        print(f"Agent> {answer}\n")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Chat directly with the academic ReAct agent from the terminal."
    )
    parser.add_argument(
        "--provider",
        choices=["demo", "openai", "gemini", "local"],
        default="demo",
        help="LLM provider to use. Defaults to demo for offline terminal chat.",
    )
    parser.add_argument(
        "--model",
        default=os.getenv("DEFAULT_MODEL"),
        help="Model name for OpenAI or Gemini providers.",
    )
    parser.add_argument(
        "--local-model-path",
        default=os.getenv("LOCAL_MODEL_PATH", "./models/Phi-3-mini-4k-instruct-q4.gguf"),
        help="Path to a GGUF model when using --provider local.",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=5,
        help="Maximum ReAct steps per user question.",
    )
    parser.add_argument(
        "--show-logs",
        action="store_true",
        help="Print structured agent logs in the terminal while chatting.",
    )
    return parser.parse_args()


def _build_agent(args: argparse.Namespace) -> ReActAgent:
    provider = args.provider.lower()
    if provider == "demo":
        return build_demo_agent(max_steps=args.max_steps)

    tools = build_score_tool_registry()
    if provider == "openai":
        from src.core.openai_provider import OpenAIProvider

        model_name = args.model or "gpt-4o"
        llm = OpenAIProvider(
            model_name=model_name,
            api_key=os.getenv("OPENAI_API_KEY"),
        )
        return ReActAgent(llm, tools, max_steps=args.max_steps)

    if provider == "gemini":
        from src.core.gemini_provider import GeminiProvider

        model_name = args.model or "gemini-1.5-flash"
        llm = GeminiProvider(
            model_name=model_name,
            api_key=os.getenv("GEMINI_API_KEY"),
        )
        return ReActAgent(llm, tools, max_steps=args.max_steps)

    if provider == "local":
        from src.core.local_provider import LocalProvider

        model_path = Path(args.local_model_path)
        if not model_path.is_absolute():
            model_path = PROJECT_ROOT / model_path
        llm = LocalProvider(model_path=str(model_path))
        return ReActAgent(llm, tools, max_steps=args.max_steps)

    raise ValueError(f"Unsupported provider: {args.provider}")


def _disable_console_logs() -> None:
    for handler in list(agent_logger.logger.handlers):
        if isinstance(handler, logging.StreamHandler) and not isinstance(
            handler, logging.FileHandler
        ):
            agent_logger.logger.removeHandler(handler)


def _looks_like_identity_only(user_input: str) -> bool:
    return bool(IDENTITY_ONLY_PATTERN.match(user_input))


if __name__ == "__main__":
    main()
