"""
telemetry/logger.py
Structured JSON logger for ReAct agent traces.
Writes one JSON object per line to logs/agent_trace.jsonl
"""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

_BASE_DIR = Path(__file__).resolve().parents[2]
_LOG_DIR  = _BASE_DIR / "logs"
_LOG_DIR.mkdir(exist_ok=True)
_TRACE_FILE = _LOG_DIR / "agent_trace.jsonl"

# ── stdlib logger for console ─────────────────────────────────────────────────
_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=getattr(logging, _level, logging.INFO),
)
logger = logging.getLogger("agent")


# ── structured trace writer ───────────────────────────────────────────────────

def log_trace(event: str, data: dict) -> None:
    """
    Append a structured trace event to agent_trace.jsonl.

    Args:
        event: e.g. "thought", "action", "observation", "final_answer", "error"
        data:  arbitrary dict payload
    """
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event":     event,
        **data,
    }
    with open(_TRACE_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    # also echo to console at DEBUG level
    logger.debug("[TRACE] %s | %s", event.upper(), json.dumps(data, ensure_ascii=False))


def log_thought(step: int, text: str) -> None:
    log_trace("thought", {"step": step, "text": text})
    logger.info("Thought %d: %s", step, text)


def log_action(step: int, tool: str, inputs: dict) -> None:
    log_trace("action", {"step": step, "tool": tool, "inputs": inputs})
    logger.info("Action  %d: %s(%s)", step, tool, inputs)


def log_observation(step: int, result: dict) -> None:
    log_trace("observation", {"step": step, "result": result})
    logger.info("Obs     %d: %s", step, json.dumps(result, ensure_ascii=False))


def log_final(answer: str) -> None:
    log_trace("final_answer", {"answer": answer})
    logger.info("Final Answer:\n%s", answer)


def log_error(step: int, error: str, context: dict | None = None) -> None:
    log_trace("error", {"step": step, "error": error, "context": context or {}})
    logger.error("Error @ step %d: %s", step, error)
