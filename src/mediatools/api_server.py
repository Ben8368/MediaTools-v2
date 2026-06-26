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
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from socketserver import ThreadingMixIn
from typing import Any
from urllib.parse import urlparse

from mediatools.api_tasks import Task, TaskStore
from mediatools.commands.doctor import build_doctor_report
from mediatools.core.config import get_data_dir, get_max_concurrent_downloads
from mediatools.core.fetch import FetchOptions, fetch_many, make_fetch_options
from mediatools.core.fetch_types import validate_url

DEFAULT_MAX_CONCURRENT = 8


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


def _optional_string(value: object) -> str | None:
    """Return a stripped string while preserving JSON null / missing values."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _draft_to_fetch_options(draft: dict[str, object]) -> list[FetchOptions]:
    urls = _normalize_urls(draft.get("urls", ""))
    if not urls:
        raise ValueError("至少需要输入一个 URL")

    output_dir = Path(str(draft.get("output_dir", "downloads")))
    subtitles_only = bool(draft.get("subtitles_only"))
    sub_langs = str(draft.get("sub_langs", "original"))
    convert_subs = _optional_string(draft.get("convert_subs", "srt"))
    name_template = _optional_string(draft.get("name_template"))

    write_subs, write_auto_subs = _resolve_subtitle_flags(draft)

    video_codec = _optional_string(draft.get("video_codec"))
    audio_codec = _optional_string(draft.get("audio_codec"))
    video_bitrate = _optional_string(draft.get("video_bitrate"))
    audio_bitrate = _optional_string(draft.get("audio_bitrate"))
    preset = _optional_string(draft.get("preset")) or "mp4"
    if (video_codec or audio_codec) and preset == "mp4":
        preset = None

    template = FetchOptions(
        url="",
        output_dir=output_dir,
        write_subtitles=write_subs,
        write_auto_subtitles=write_auto_subs,
        subtitles_only=subtitles_only,
        subtitle_languages=sub_langs,
        convert_subs=convert_subs,
        preset=preset if not subtitles_only else None,
        filename_template=name_template,
        video_codec=video_codec,
        audio_codec=audio_codec,
        video_bitrate=video_bitrate,
        audio_bitrate=audio_bitrate,
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

        if store.is_cancel_requested(task_id):
            return
        store.update(
            task_id,
            status="running",
            stage="connecting",
            started_at=time.time(),
            progress=0.05,
        )
        result = fetch_many(options, dry_run=False, max_workers=workers, timeout=3600.0)
        if store.is_cancel_requested(task_id):
            return

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

        store.update(
            task_id,
            status=status,
            stage=stage,
            progress=1.0,
            output_files=output_files,
            completed_at=time.time(),
            result=payload,
        )
    except Exception as exc:
        store.update(
            task_id,
            status="failed",
            stage="failed",
            progress=0.0,
            error=str(exc),
            completed_at=time.time(),
        )


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
        parts = [part for part in path.split("/") if part]

        if path == "/api/doctor" and self.command == "GET":
            self._handle_doctor()
        elif path == "/api/fetch/plan" and self.command == "POST":
            self._handle_fetch_plan()
        elif path == "/api/fetch/tasks" and self.command == "POST":
            self._handle_fetch_submit()
        elif path == "/api/fetch/tasks" and self.command == "GET":
            self._handle_fetch_list()
        elif path == "/api/fetch/tasks" and self.command == "DELETE":
            self._handle_fetch_clear()
        elif (
            len(parts) == 4
            and parts[:3] == ["api", "fetch", "tasks"]
            and self.command == "DELETE"
        ):
            self._handle_fetch_delete(parts[3])
        elif (
            len(parts) == 5
            and parts[:3] == ["api", "fetch", "tasks"]
            and parts[4] == "cancel"
            and self.command == "POST"
        ):
            self._handle_fetch_cancel(parts[3])
        else:
            _json_response(self, {"error": "Not Found"}, status=404)

    def do_GET(self) -> None:
        self._route()

    def do_POST(self) -> None:
        self._route()

    def do_DELETE(self) -> None:
        self._route()

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
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
                status="pending",
                stage="queued",
                params={**draft, "urls": [opt.url for opt in options], "url": first_url},
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
                {"task_id": task_id, "status": "pending", "url_count": len(options)},
                status=201,
            )
        except ValueError as exc:
            _json_response(self, {"error": str(exc)}, status=400)
        except Exception as exc:
            _json_response(self, {"error": str(exc)}, status=500)

    # ---- Fetch list ----

    def _handle_fetch_list(self) -> None:
        tasks = self.server.server_store.list_all()
        sorted_tasks = sorted(tasks, key=lambda task: task.created_at, reverse=True)
        _json_response(self, [t.to_dict() for t in sorted_tasks])

    def _handle_fetch_cancel(self, task_id: str) -> None:
        task = self.server.server_store.cancel(task_id)
        if task is None:
            _json_response(self, {"error": "Task not found"}, status=404)
            return
        _json_response(self, {"ok": True, "task": task.to_dict()})

    def _handle_fetch_delete(self, task_id: str) -> None:
        deleted = self.server.server_store.delete(task_id)
        if not deleted:
            _json_response(self, {"error": "Task not found"}, status=404)
            return
        _json_response(self, {"ok": True, "deleted": 1})

    def _handle_fetch_clear(self) -> None:
        try:
            draft = _read_json_body(self)
        except ValueError:
            draft = {}
        raw_ids = draft.get("task_ids")
        task_ids = [str(v) for v in raw_ids] if isinstance(raw_ids, list) else None
        deleted = self.server.server_store.clear_finished(task_ids)
        _json_response(self, {"ok": True, "deleted": deleted})


# ---------------------------------------------------------------------------
# Server runner
# ---------------------------------------------------------------------------

class ThreadedAPIServer(ThreadingMixIn, HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


def start_api_server(
    host: str = "127.0.0.1",
    port: int = 7860,
    storage_path: Path | None = None,
) -> ThreadedAPIServer:
    if storage_path is None:
        storage_path = get_data_dir() / "api-tasks.json"
    store = TaskStore(storage_path=storage_path)
    server = ThreadedAPIServer((host, port), APIRequestHandler)
    server.server_store = store
    print(f"[api] MediaTools API server listening on http://{host}:{port}", file=sys.stderr)
    return server


if __name__ == "__main__":
    srv = start_api_server()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n[api] Shutting down.", file=sys.stderr)
        srv.shutdown()
