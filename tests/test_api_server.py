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
        task = Task(task_id="t1", title="Test", status="queued")
        store.add(task)
        assert store.get("t1") is task

    def test_update_fields(self) -> None:
        store = TaskStore()
        store.add(Task(task_id="t1", status="queued"))
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

    def test_thread_safety(self) -> None:
        store = TaskStore()
        store.add(Task(task_id="shared", status="queued"))
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
def api_server():
    server = start_api_server(port=0)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.1)
    yield f"http://127.0.0.1:{port}"
    server.shutdown()
    thread.join(timeout=1)


class TestAPIServerIntegration:
    @pytest.fixture(autouse=True)
    def inject_base_url(self, api_server: str) -> None:
        self.base_url = api_server

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def test_doctor_returns_tools(self) -> None:
        import urllib.request
        resp = urllib.request.urlopen(self._url("/api/doctor"))
        data = json.loads(resp.read())
        assert isinstance(data, list)
        names = [t["name"] for t in data]
        assert "ffmpeg" in names

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

    def test_fetch_list_returns_list(self) -> None:
        import urllib.request
        resp = urllib.request.urlopen(self._url("/api/fetch/tasks"))
        data = json.loads(resp.read())
        assert isinstance(data, list)

    def test_404_for_unknown_route(self) -> None:
        import urllib.error
        import urllib.request
        with pytest.raises(urllib.error.HTTPError) as exc:
            urllib.request.urlopen(self._url("/api/nope"))
        assert exc.value.code == 404
