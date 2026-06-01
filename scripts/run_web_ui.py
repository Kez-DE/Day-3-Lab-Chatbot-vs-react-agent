from __future__ import annotations

import argparse
import errno
import json
import logging
import os
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WEB_ROOT = PROJECT_ROOT / "web"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.agent.agent import ReActAgent
from src.demo_provider import build_demo_agent
from src.telemetry.logger import logger as agent_logger
from src.tools.score_tools import build_score_tool_registry


CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
}


class WebUIHandler(BaseHTTPRequestHandler):
    server_version = "AcademicAgentWebUI/1.0"

    def do_GET(self) -> None:
        if self.path == "/api/health":
            self._send_json({"ok": True})
            return

        path = self.path.split("?", 1)[0]
        if path == "/":
            path = "/index.html"

        target = (WEB_ROOT / unquote(path.lstrip("/"))).resolve()
        if not _is_safe_web_path(target):
            self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)
            return

        if not target.exists() or not target.is_file():
            self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)
            return

        content_type = CONTENT_TYPES.get(target.suffix, "application/octet-stream")
        body = target.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        if self.path != "/api/chat":
            self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)
            return

        try:
            payload = self._read_json()
            message = str(payload.get("message", "")).strip()
            if not message:
                self._send_json(
                    {"error": "Message is required."},
                    status=HTTPStatus.BAD_REQUEST,
                )
                return

            provider = str(payload.get("provider", "demo")).strip().lower()
            model = str(payload.get("model", "")).strip() or None
            max_steps = int(payload.get("max_steps", 5))
            local_model_path = str(
                payload.get("local_model_path", "./models/Phi-3-mini-4k-instruct-q4.gguf")
            )

            agent = _build_agent(provider, model, local_model_path, max_steps)
            answer = agent.run(message)
            self._send_json(
                {
                    "answer": answer,
                    "history": agent.history,
                    "provider": provider,
                    "model": agent.llm.model_name,
                }
            )
        except Exception as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8") or "{}")

    def _send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env")
    args = _parse_args()
    if not args.show_agent_logs:
        _disable_console_logs()

    server = _create_server(args.host, args.port)
    bound_host, bound_port = server.server_address[:2]
    url = f"http://{bound_host}:{bound_port}"
    print(f"Academic Agent Web UI running at {url}")
    if bound_port != args.port:
        print(f"Port {args.port} was busy, so the server used port {bound_port}.")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server.")
    finally:
        server.server_close()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the academic agent web UI.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--show-agent-logs",
        action="store_true",
        help="Print structured agent logs in the server terminal.",
    )
    return parser.parse_args()


def _build_agent(
    provider: str,
    model: str | None,
    local_model_path: str,
    max_steps: int,
) -> ReActAgent:
    if provider == "demo":
        return build_demo_agent(max_steps=max_steps)

    tools = build_score_tool_registry()
    if provider == "openai":
        from src.core.openai_provider import OpenAIProvider

        llm = OpenAIProvider(
            model_name=model or "gpt-4o",
            api_key=os.getenv("OPENAI_API_KEY"),
        )
        return ReActAgent(llm, tools, max_steps=max_steps)

    if provider == "gemini":
        from src.core.gemini_provider import GeminiProvider

        llm = GeminiProvider(
            model_name=model or "gemini-1.5-flash",
            api_key=os.getenv("GEMINI_API_KEY"),
        )
        return ReActAgent(llm, tools, max_steps=max_steps)

    if provider == "local":
        from src.core.local_provider import LocalProvider

        model_path = Path(local_model_path)
        if not model_path.is_absolute():
            model_path = PROJECT_ROOT / model_path
        return ReActAgent(LocalProvider(model_path=str(model_path)), tools, max_steps=max_steps)

    raise ValueError(f"Unsupported provider: {provider}")


def _create_server(host: str, preferred_port: int) -> ThreadingHTTPServer:
    for port in range(preferred_port, preferred_port + 20):
        try:
            return ThreadingHTTPServer((host, port), WebUIHandler)
        except OSError as exc:
            if exc.errno != errno.EADDRINUSE:
                raise
    raise OSError(
        errno.EADDRINUSE,
        f"No free port found from {preferred_port} to {preferred_port + 19}",
    )


def _disable_console_logs() -> None:
    for handler in list(agent_logger.logger.handlers):
        if isinstance(handler, logging.StreamHandler) and not isinstance(
            handler, logging.FileHandler
        ):
            agent_logger.logger.removeHandler(handler)


def _is_safe_web_path(target: Path) -> bool:
    try:
        target.relative_to(WEB_ROOT.resolve())
        return True
    except ValueError:
        return False


if __name__ == "__main__":
    main()
