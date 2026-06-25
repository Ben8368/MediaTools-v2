"""Task records and persistence for the local API adapter."""

from __future__ import annotations

import json
import threading
import time
from collections.abc import Sequence
from pathlib import Path

from mediatools.core.config import ensure_dir


class Task:
    """Lightweight task record tracked by the local API adapter."""

    __slots__ = (
        "id", "title", "source_url", "status", "progress",
        "stage", "output_files", "error", "created_at", "updated_at",
        "started_at", "completed_at", "params", "result", "cancel_requested",
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
        created_at: float | None = None,
        updated_at: float | None = None,
        started_at: float | None = None,
        completed_at: float | None = None,
        params: dict[str, object] | None = None,
        result: dict[str, object] | None = None,
        cancel_requested: bool = False,
    ) -> None:
        now = time.time()
        self.id = task_id
        self.title = title
        self.source_url = source_url
        self.status = status
        self.progress = progress
        self.stage = stage
        self.output_files = list(output_files) if output_files else []
        self.error = error
        self.created_at = created_at if created_at is not None else now
        self.updated_at = updated_at if updated_at is not None else self.created_at
        self.started_at = started_at
        self.completed_at = completed_at
        self.params = dict(params) if params else {}
        self.result = dict(result) if result else {}
        self.cancel_requested = cancel_requested

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
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "params": dict(self.params),
            "result": dict(self.result),
            "cancel_requested": self.cancel_requested,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Task:
        output_files = data.get("output_files", [])
        if not isinstance(output_files, list):
            output_files = []
        return cls(
            task_id=str(data.get("id", "")),
            title=str(data.get("title", "")),
            source_url=str(data.get("source_url", "")),
            status=str(data.get("status", "queued")),
            progress=float(data.get("progress", 0.0)),
            stage=str(data.get("stage", "queued")),
            output_files=[str(p) for p in output_files if p],
            error=str(data["error"]) if data.get("error") is not None else None,
            created_at=float(data.get("created_at", time.time())),
            updated_at=float(data.get("updated_at", time.time())),
            started_at=float(data["started_at"]) if data.get("started_at") is not None else None,
            completed_at=(
                float(data["completed_at"])
                if data.get("completed_at") is not None
                else None
            ),
            params=data.get("params") if isinstance(data.get("params"), dict) else None,
            result=data.get("result") if isinstance(data.get("result"), dict) else None,
            cancel_requested=bool(data.get("cancel_requested", False)),
        )


class TaskStore:
    """Thread-safe task registry with optional JSON persistence."""

    def __init__(self, storage_path: Path | None = None) -> None:
        self._lock = threading.Lock()
        self._tasks: dict[str, Task] = {}
        self._storage_path = storage_path
        self._load()

    def add(self, task: Task) -> None:
        with self._lock:
            self._tasks[task.id] = task
            self._persist_locked()

    def update(self, task_id: str, **fields: object) -> None:
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return
            for key, value in fields.items():
                if hasattr(task, key):
                    setattr(task, key, value)
            task.updated_at = time.time()
            self._persist_locked()

    def cancel(self, task_id: str) -> Task | None:
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return None
            if task.status in {"completed", "failed", "cancelled"}:
                return task
            now = time.time()
            task.cancel_requested = True
            task.status = "cancelled"
            task.stage = "cancel_requested"
            task.progress = min(task.progress, 0.99)
            task.completed_at = now
            task.updated_at = now
            self._persist_locked()
            return task

    def is_cancel_requested(self, task_id: str) -> bool:
        with self._lock:
            task = self._tasks.get(task_id)
            return bool(task and task.cancel_requested)

    def delete(self, task_id: str) -> bool:
        with self._lock:
            if task_id not in self._tasks:
                return False
            del self._tasks[task_id]
            self._persist_locked()
            return True

    def clear_finished(self, task_ids: Sequence[str] | None = None) -> int:
        finished = {"completed", "failed", "cancelled", "paused", "partial"}
        selected = set(task_ids or [])
        with self._lock:
            ids = [
                task_id
                for task_id, task in self._tasks.items()
                if task.status in finished and (not selected or task_id in selected)
            ]
            for task_id in ids:
                del self._tasks[task_id]
            if ids:
                self._persist_locked()
            return len(ids)

    def get(self, task_id: str) -> Task | None:
        with self._lock:
            return self._tasks.get(task_id)

    def list_all(self) -> list[Task]:
        with self._lock:
            return list(self._tasks.values())

    def _load(self) -> None:
        if self._storage_path is None or not self._storage_path.exists():
            return
        try:
            data = json.loads(self._storage_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        if not isinstance(data, list):
            return
        for item in data:
            if isinstance(item, dict):
                task = Task.from_dict(item)
                if task.id:
                    self._tasks[task.id] = task

    def _persist_locked(self) -> None:
        if self._storage_path is None:
            return
        ensure_dir(self._storage_path.parent)
        payload = [task.to_dict() for task in self._tasks.values()]
        self._storage_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
