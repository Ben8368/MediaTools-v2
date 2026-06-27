"""Tests for the MediaTools API server."""

from __future__ import annotations

import json
import threading
import time

import pytest

from mediatools.api_server import Task, TaskStore, _draft_to_fetch_options, start_api_server

# ---------------------------------------------------------------------------
# TaskStore tests
# ---------------------------------------------------------------------------

class TestTaskStore:
    def test_add_and_get(self) -> None:
        store = TaskStore()
        task = Task(task_id="t1", title="Test")
        store.add(task)
        assert store.get("t1") is task
        assert task.status == "pending"
        assert task.created_at > 0
        assert task.updated_at >= task.created_at

    def test_update_fields(self) -> None:
        store = TaskStore()
        store.add(Task(task_id="t1"))
        store.update("t1", status="running", progress=0.5, stage="downloading")
        task = store.get("t1")
        assert task is not None
        assert task.status == "running"
        assert task.progress == 0.5
        assert task.stage == "downloading"

    def test_update_unknown_task_noop(self) -> None:
        store = TaskStore()
        store.update("nope", status="running")

    def test_list_all(self) -> None:
        store = TaskStore()
        store.add(Task(task_id="a"))
        store.add(Task(task_id="b"))
        assert len(store.list_all()) == 2

    def test_persists_tasks_to_json(self, tmp_path) -> None:
        storage_path = tmp_path / "tasks.json"
        store = TaskStore(storage_path=storage_path)
        store.add(Task(task_id="persisted", title="Stored", status="completed"))

        reloaded = TaskStore(storage_path=storage_path)
        task = reloaded.get("persisted")
        assert task is not None
        assert task.title == "Stored"
        assert task.status == "completed"

    def test_cancel_marks_task_without_deleting(self) -> None:
        store = TaskStore()
        store.add(Task(task_id="running", status="running", progress=0.5))
        task = store.cancel("running")
        assert task is not None
        assert task.status == "cancelled"
        assert task.cancel_requested is True

    def test_clear_finished_keeps_running_tasks(self) -> None:
        store = TaskStore()
        store.add(Task(task_id="done", status="completed"))
        store.add(Task(task_id="failed", status="failed"))
        store.add(Task(task_id="running", status="running"))
        assert store.clear_finished() == 2
        assert store.get("done") is None
        assert store.get("failed") is None
        assert store.get("running") is not None

    def test_thread_safety(self) -> None:
        store = TaskStore()
        store.add(Task(task_id="shared"))
        errors: list[Exception] = []

        def worker() -> None:
            try:
                for _ in range(50):
                    store.update("shared", progress=0.1)
                    store.get("shared")
                    store.list_all()
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(errors) == 0


# ---------------------------------------------------------------------------
# _draft_to_fetch_options tests
# ---------------------------------------------------------------------------

class TestDraftToOptions:
    def test_basic_draft(self) -> None:
        draft = {
            "urls": "https://example.com/video",
            "output_dir": "downloads",
            "subtitles_only": False,
            "subtitle_mode": "both",
            "sub_langs": "original",
            "convert_subs": "srt",
            "preset": "mp4",
            "name_template": "{title}.{ext}",
            "max_concurrent": 1,
        }
        options = _draft_to_fetch_options(draft)
        assert len(options) == 1
        assert options[0].url == "https://example.com/video"
        assert options[0].write_subtitles is True
        assert options[0].write_auto_subtitles is True

    def test_multiline_urls(self) -> None:
        draft = {"urls": "https://a.example/1\nhttps://b.example/2", "output_dir": "out"}
        options = _draft_to_fetch_options(draft)
        assert len(options) == 2
        assert options[0].url == "https://a.example/1"
        assert options[1].url == "https://b.example/2"

    def test_empty_urls_raises(self) -> None:
        draft = {"urls": "   \n  ", "output_dir": "out"}
        with pytest.raises(ValueError, match="至少需要输入一个 URL"):
            _draft_to_fetch_options(draft)

    def test_subtitles_only_clears_preset(self) -> None:
        draft = {
            "urls": "https://example.com/video",
            "output_dir": "out",
            "subtitles_only": True,
            "preset": "mp4",
        }
        options = _draft_to_fetch_options(draft)
        assert options[0].subtitles_only is True
        assert options[0].preset is None

    def test_codec_target_clears_default_mp4_preset(self) -> None:
        draft = {
            "urls": "https://example.com/video",
            "output_dir": "out",
            "preset": "mp4",
            "audio_codec": "aac",
        }
        options = _draft_to_fetch_options(draft)
        assert options[0].audio_codec == "aac"
        assert options[0].preset is None

    def test_null_codec_fields_stay_none(self) -> None:
        draft = {
            "urls": "https://example.com/video",
            "output_dir": "out",
            "video_codec": None,
            "audio_codec": None,
            "video_bitrate": None,
            "audio_bitrate": None,
        }
        options = _draft_to_fetch_options(draft)
        assert options[0].video_codec is None
        assert options[0].audio_codec is None
        assert options[0].video_bitrate is None
        assert options[0].audio_bitrate is None

    def test_subtitle_mode_manual(self) -> None:
        draft = {"urls": "https://example.com/video", "output_dir": "out", "subtitle_mode": "manual"}  # noqa: E501
        options = _draft_to_fetch_options(draft)
        assert options[0].write_subtitles is True
        assert options[0].write_auto_subtitles is False

    def test_subtitle_mode_auto(self) -> None:
        draft = {"urls": "https://example.com/video", "output_dir": "out", "subtitle_mode": "auto"}
        options = _draft_to_fetch_options(draft)
        assert options[0].write_subtitles is False
        assert options[0].write_auto_subtitles is True

    def test_subtitle_mode_none(self) -> None:
        draft = {"urls": "https://example.com/video", "output_dir": "out", "subtitle_mode": "none"}
        options = _draft_to_fetch_options(draft)
        assert options[0].write_subtitles is False
        assert options[0].write_auto_subtitles is False

    def test_urls_as_string_array(self) -> None:
        """Frontend sends urls as string[], not newline-separated string."""
        draft = {
            "urls": ["https://a.example/1", "https://b.example/2"],
            "output_dir": "out",
        }
        options = _draft_to_fetch_options(draft)
        assert len(options) == 2
        assert options[0].url == "https://a.example/1"
        assert options[1].url == "https://b.example/2"

    def test_legacy_write_subs_fields(self) -> None:
        """Frontend may send write_subs/write_auto_subs instead of subtitle_mode."""
        draft = {
            "urls": "https://example.com/video",
            "output_dir": "out",
            "write_subs": True,
            "write_auto_subs": False,
        }
        options = _draft_to_fetch_options(draft)
        assert options[0].write_subtitles is True
        assert options[0].write_auto_subtitles is False

    def test_legacy_write_auto_subs_only(self) -> None:
        draft = {
            "urls": "https://example.com/video",
            "output_dir": "out",
            "write_subs": False,
            "write_auto_subs": True,
        }
        options = _draft_to_fetch_options(draft)
        assert options[0].write_subtitles is False
        assert options[0].write_auto_subtitles is True


# ---------------------------------------------------------------------------
# HTTP endpoint integration tests
# ---------------------------------------------------------------------------

@pytest.fixture(scope="class")
def api_server(tmp_path_factory: pytest.TempPathFactory):
    storage_path = tmp_path_factory.mktemp("api-server") / "tasks.json"
    server = start_api_server(host="127.0.0.1", port=0, storage_path=storage_path)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.1)
    yield f"http://127.0.0.1:{port}", server
    server.shutdown()
    thread.join(timeout=1)


class TestAPIServerIntegration:
    @pytest.fixture(autouse=True)
    def inject_base_url(self, api_server) -> None:
        self.base_url, self.server = api_server

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def test_doctor_returns_tools(self) -> None:
        import urllib.request
        resp = urllib.request.urlopen(self._url("/api/doctor"))
        data = json.loads(resp.read())
        assert isinstance(data, list)
        names = [t["name"] for t in data]
        assert "ffmpeg" in names

    def test_system_metrics_returns_runtime_snapshot(self) -> None:
        import urllib.request
        resp = urllib.request.urlopen(self._url("/api/system/metrics"))
        data = json.loads(resp.read())
        assert "runtime" in data
        assert "system" in data
        assert "network" in data
        assert isinstance(data["runtime"]["uptime_seconds"], int)
        assert isinstance(data["system"]["cpu_percent"], (int, float))
        assert isinstance(data["system"]["memory_percent"], (int, float))
        assert isinstance(data["system"]["gpu_percent"], (int, float))
        assert isinstance(data["system"]["gpu_available"], bool)
        assert isinstance(data["network"]["upload_bytes_per_sec"], int)
        assert isinstance(data["network"]["download_bytes_per_sec"], int)

    def test_workspace_returns_project_root(self) -> None:
        import urllib.request
        resp = urllib.request.urlopen(self._url("/api/workspace"))
        data = json.loads(resp.read())
        assert data["workspace"]["project_root"]
        assert data["project_root"] == data["workspace"]["project_root"]

    def test_filebrowser_disks_returns_roots(self) -> None:
        import urllib.request
        resp = urllib.request.urlopen(self._url("/api/filebrowser/disks"))
        data = json.loads(resp.read())
        assert data["ok"] is True
        assert data["disks"]
        assert {"name", "path", "total", "used", "free"} <= set(data["disks"][0])

    def test_filebrowser_lists_directory(self, tmp_path) -> None:
        import urllib.request
        (tmp_path / "folder").mkdir()
        (tmp_path / "clip.mp4").write_text("video", encoding="utf-8")
        draft = {"directory": str(tmp_path)}
        req = urllib.request.Request(
            self._url("/api/filebrowser/list"),
            data=json.dumps(draft).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read())
        assert data["ok"] is True
        assert data["path"] == str(tmp_path.resolve())
        assert data["directories"][0]["name"] == "folder"
        assert data["files"][0]["name"] == "clip.mp4"

    def test_filebrowser_creates_directory(self, tmp_path) -> None:
        import urllib.request
        target = tmp_path / "downloads"
        draft = {"path": str(target)}
        req = urllib.request.Request(
            self._url("/api/filebrowser/directories"),
            data=json.dumps(draft).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read())
        assert resp.status == 201
        assert data["ok"] is True
        assert target.is_dir()

    def test_fetch_plan_returns_command(self) -> None:
        import urllib.request
        draft = {"urls": "https://example.com/video", "output_dir": "out"}
        req = urllib.request.Request(
            self._url("/api/fetch/plan"),
            data=json.dumps(draft).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read())
        assert "items" in data
        assert len(data["items"]) == 1

    def test_fetch_plan_empty_urls_400(self) -> None:
        import urllib.error
        import urllib.request
        draft = {"urls": "", "output_dir": "out"}
        req = urllib.request.Request(
            self._url("/api/fetch/plan"),
            data=json.dumps(draft).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with pytest.raises(urllib.error.HTTPError) as exc:
            urllib.request.urlopen(req)
        assert exc.value.code == 400

    def test_fetch_submit_returns_201(self) -> None:
        import urllib.request
        draft = {"urls": "https://example.com/video", "output_dir": "out"}
        req = urllib.request.Request(
            self._url("/api/fetch/tasks"),
            data=json.dumps(draft).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        resp = urllib.request.urlopen(req)
        assert resp.status == 201
        data = json.loads(resp.read())
        assert "task_id" in data
        assert data["status"] == "pending"

    def test_start_api_server_respects_host(self, tmp_path) -> None:
        server = start_api_server(
            host="127.0.0.1",
            port=0,
            storage_path=tmp_path / "tasks.json",
        )
        try:
            assert server.server_address[0] == "127.0.0.1"
        finally:
            server.server_close()

    def test_fetch_list_returns_list(self) -> None:
        import urllib.request
        resp = urllib.request.urlopen(self._url("/api/fetch/tasks"))
        data = json.loads(resp.read())
        assert isinstance(data, list)
        if data:
            assert "created_at" in data[0]

    def test_fetch_cancel_endpoint_marks_task_cancelled(self) -> None:
        import urllib.request
        self.server.server_store.add(Task(task_id="cancel-me", status="running"))

        cancel_req = urllib.request.Request(
            self._url("/api/fetch/tasks/cancel-me/cancel"),
            data=json.dumps({}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        cancel_resp = urllib.request.urlopen(cancel_req)
        data = json.loads(cancel_resp.read())
        assert data["task"]["status"] == "cancelled"

    def test_fetch_clear_endpoint_removes_finished_tasks(self) -> None:
        import urllib.request
        self.server.server_store.add(Task(task_id="clear-me", status="completed"))
        draft = {"task_ids": ["clear-me"]}
        req = urllib.request.Request(
            self._url("/api/fetch/tasks"),
            data=json.dumps(draft).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="DELETE",
        )
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read())
        assert data["ok"] is True
        assert data["deleted"] == 1

    def test_404_for_unknown_route(self) -> None:
        import urllib.error
        import urllib.request
        with pytest.raises(urllib.error.HTTPError) as exc:
            urllib.request.urlopen(self._url("/api/nope"))
        assert exc.value.code == 404
