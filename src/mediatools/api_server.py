"""HTTP API adapter layer for the MediaTools download workbench.

Implements a minimal JSON API server using only stdlib.
Routes match the light-frontend contract in ``docs/UI_API_CONTRACT.md``.
"""

from __future__ import annotations

import json
import sys
import threading
import time
import uuid
from collections.abc import Sequence
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from socketserver import ThreadingMixIn
from typing import Any
from urllib.parse import urlparse

from mediatools.commands.doctor import build_doctor_report
from mediatools.core.config import get_max_concurrent_downloads
from mediatools.core.fetch import FetchOptions, fetch_many, make_fetch_options
from mediatools.core.fetch_types import validate_url

DEFAULT_MAX_CONCURRENT = 8


# ---------------------------------------------------------------------------
# In-memory task store
# ---------------------------------------------------------------------------

class Task:
    """Lightweight task record tracked in memory."""

    __slots__ = (
        "id", "title", "source_url", "status", "progress",
        "stage", "output_files", "error",
    )

    def __init__(
        self,
        task_id: str,
        title: str = "",
        source_url: str = "",
        status: str = "queued",
        progress: float = 0.0,
        stage: str = "queued",
        output_files: Sequence[str] | None = None,
        error: str | None = None,
    ) -> None:
        self.id = task_id
        self.title = title
        self.source_url = source_url
        self.status = status
        self.progress = progress
        self.stage = stage
        self.output_files = list(output_files) if output_files else []
        self.error = error

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "title": self.title,
            "source_url": self.source_url,
            "status": self.status,
            "progress": self.progress,
            "stage": self.stage,
            "output_files": list(self.output_files),
            "error": self.error,
        }


class TaskStore:
    """Thread-safe in-memory task registry."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._tasks: dict[str, Task] = {}

    def add(self, task: Task) -> None:
        with self._lock:
            self._tasks[task.id] = task

    def update(self, task_id: str, **fields: object) -> None:
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return
            for key, value in fields.items():
                if hasattr(task, key):
                    setattr(task, key, value)

    def get(self, task_id: str) -> Task | None:
        with self._lock:
            return self._tasks.get(task_id)

    def list_all(self) -> list[Task]:
        with self._lock:
            return list(self._tasks.values())


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _json_response(handler: BaseHTTPRequestHandler, data: object, status: int = 200) -> None:
    body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _read_json_body(handler: BaseHTTPRequestHandler) -> dict[str, object]:
    length_header = handler.headers.get("Content-Length")
    if not length_header:
        raise ValueError("Missing Content-Length")
    raw = handler.rfile.read(int(length_header))
    result = json.loads(raw)
    if not isinstance(result, dict):
        raise ValueError("Request body must be a JSON object")
    return result


def _normalize_urls(raw: object) -> list[str]:
    """Accept both string[] and newline-separated string for URLs."""
    if isinstance(raw, list):
        return [str(u).strip() for u in raw if str(u).strip()]
    if isinstance(raw, str):
        return [line.strip() for line in raw.splitlines() if line.strip()]
    raise ValueError("urls must be a string or array of strings")


def _resolve_subtitle_flags(draft: dict[str, object]) -> tuple[bool, bool]:
    """Resolve subtitle flags from either new or legacy field names.

    Supports:
    - subtitle_mode: "manual" | "auto" | "both" | "none" (new)
    - write_subs / write_auto_subs: bool (legacy, from frontend)
    """
    # New-style field takes precedence
    subtitle_mode = str(draft.get("subtitle_mode", ""))
    if subtitle_mode:
        if subtitle_mode == "manual":
            return True, False
        if subtitle_mode == "auto":
            return False, True
        if subtitle_mode == "both":
            return True, True
        # "none" or unrecognized
        return False, False

    # Legacy-style fields from frontend
    write_subs = bool(draft.get("write_subs", False))
    write_auto_subs = bool(draft.get("write_auto_subs", False))
    return write_subs, write_auto_subs


def _draft_to_fetch_options(draft: dict[str, object]) -> list[FetchOptions]:
    urls = _normalize_urls(draft.get("urls", ""))
    if not urls:
        raise ValueError("至少需要输入一个 URL")

    output_dir = Path(str(draft.get("output_dir", "downloads")))
    subtitles_only = bool(draft.get("subtitles_only"))
    sub_langs = str(draft.get("sub_langs", "original"))
    convert_subs = str(draft.get("convert_subs", "srt"))
    preset = str(draft.get("preset", "mp4"))
    name_template = str(draft.get("name_template", ""))

    write_subs, write_auto_subs = _resolve_subtitle_flags(draft)

    template = FetchOptions(
        url="",
        output_dir=output_dir,
        write_subtitles=write_subs,
        write_auto_subtitles=write_auto_subs,
        subtitles_only=subtitles_only,
        subtitle_languages=sub_langs,
        convert_subs=convert_subs if convert_subs else None,
        preset=preset if not subtitles_only else None,
        filename_template=name_template if name_template else None,
    )
    return make_fetch_options(urls, template)


def _run_download_task(
    store: TaskStore,
    task_id: str,
    options: list[FetchOptions],
    max_workers: int = 1,
) -> None:
    try:
        max_concurrent = get_max_concurrent_downloads(DEFAULT_MAX_CONCURRENT)
        workers = min(max_workers, max_concurrent)

        store.update(task_id, status="running", stage="connecting")
        result = fetch_many(options, dry_run=False, max_workers=workers, timeout=3600.0)

        payload = result.to_dict()
        items = payload.get("items", [])
        output_files: list[str] = []
        for item in items:
            if isinstance(item, dict) and item.get("status") == "succeeded":
                od = item.get("output_dir", "")
                output_files.append(str(od))

        if result.failed > 0 and result.succeeded > 0:
            status = "partial"
            stage = "completed"
        elif result.failed > 0:
            status = "failed"
            stage = "failed"
            errors = [
                str(it.get("error", ""))
                for it in items
                if isinstance(it, dict) and it.get("status") == "failed"
            ]
            store.update(task_id, error="; ".join(errors))
        else:
            status = "completed"
            stage = "completed"

        store.update(task_id, status=status, stage=stage, progress=1.0, output_files=output_files)
    except Exception as exc:
        store.update(task_id, status="failed", stage="failed", progress=0.0, error=str(exc))


# ---------------------------------------------------------------------------
# Request handler
# ---------------------------------------------------------------------------

class APIRequestHandler(BaseHTTPRequestHandler):

    server_store: TaskStore

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        print(f"[api] {format % args}", file=sys.stderr)

    def _route(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        if path == "/api/doctor" and self.command == "GET":
            self._handle_doctor()
        elif path == "/api/fetch/plan" and self.command == "POST":
            self._handle_fetch_plan()
        elif path == "/api/fetch/tasks" and self.command == "POST":
            self._handle_fetch_submit()
        elif path == "/api/fetch/tasks" and self.command == "GET":
            self._handle_fetch_list()
        else:
            _json_response(self, {"error": "Not Found"}, status=404)

    def do_GET(self) -> None:
        self._route()

    def do_POST(self) -> None:
        self._route()

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    # ---- Doctor ----

    def _handle_doctor(self) -> None:
        report = build_doctor_report()
        tools_data: list[dict[str, object]] = []
        for name in ("ffmpeg", "ffprobe", "yt-dlp"):
            info = report[name]
            assert isinstance(info, dict)
            tools_data.append({
                    "name": name,
                    "available": bool(info["available"]),
                    "path": info["path"],
                })
        _json_response(self, tools_data)

    # ---- Fetch plan ----

    def _handle_fetch_plan(self) -> None:
        try:
            draft = _read_json_body(self)
            options = _draft_to_fetch_options(draft)

            from mediatools.core.fetch import build_fetch_args

            items: list[dict[str, object]] = []
            urls: list[str] = []
            commands: list[str] = []
            warnings: list[str] = []

            for opt in options:
                urls.append(opt.url)
                try:
                    validate_url(opt.url)
                except Exception:
                    warnings.append(f"无效 URL: {opt.url}")

            for opt in options:
                try:
                    cmd_args = build_fetch_args(opt)
                    cmd_str = " ".join(cmd_args)
                    commands.append(cmd_str)
                    items.append({
                        "url": opt.url,
                        "command": cmd_str,
                        "status": "planned",
                    })
                except Exception as exc:
                    items.append({
                        "url": opt.url,
                        "command": "",
                        "status": "error",
                        "error": str(exc),
                    })

            safe_draft: dict[str, object] = {k: v for k, v in draft.items() if k != "urls"}
            safe_draft["urls_parsed"] = urls

            _json_response(self, {
                "draft": safe_draft,
                "items": items,
                "command": commands[0] if commands else "",
                "warnings": warnings,
            })
        except ValueError as exc:
            _json_response(self, {"error": str(exc)}, status=400)
        except Exception as exc:
            _json_response(self, {"error": str(exc)}, status=500)

    # ---- Fetch submit ----

    def _handle_fetch_submit(self) -> None:
        try:
            draft = _read_json_body(self)
            options = _draft_to_fetch_options(draft)
            if not options:
                raise ValueError("没有有效的 URL")

            task_id = f"fetch-{int(time.time())}-{uuid.uuid4().hex[:6]}"
            first_url = options[0].url
            title = first_url.rsplit("/", 1)[-1][:60] or first_url[:60]
            max_workers = int(draft.get("max_concurrent", 1))

            task = Task(
                task_id=task_id,
                title=title,
                source_url=first_url if len(options) == 1 else f"{len(options)} URLs",
                status="queued",
                stage="queued",
            )
            store = self.server.server_store
            store.add(task)

            thread = threading.Thread(
                target=_run_download_task,
                args=(store, task_id, list(options)),
                kwargs={"max_workers": max_workers},
                daemon=True,
            )
            thread.start()

            _json_response(
                self,
                {"task_id": task_id, "status": "queued", "url_count": len(options)},
                status=201,
            )
        except ValueError as exc:
            _json_response(self, {"error": str(exc)}, status=400)
        except Exception as exc:
            _json_response(self, {"error": str(exc)}, status=500)

    # ---- Fetch list ----

    def _handle_fetch_list(self) -> None:
        tasks = self.server.server_store.list_all()
        _json_response(self, [t.to_dict() for t in tasks])


# ---------------------------------------------------------------------------
# Server runner
# ---------------------------------------------------------------------------

class ThreadedAPIServer(ThreadingMixIn, HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


def start_api_server(port: int = 7860) -> ThreadedAPIServer:
    store = TaskStore()
    server = ThreadedAPIServer(("127.0.0.1", port), APIRequestHandler)
    server.server_store = store
    print(f"[api] MediaTools API server listening on http://127.0.0.1:{port}", file=sys.stderr)
    return server


if __name__ == "__main__":
    srv = start_api_server()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n[api] Shutting down.", file=sys.stderr)
        srv.shutdown()
