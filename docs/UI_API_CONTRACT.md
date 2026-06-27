# Light Frontend API Contract

This document defines the first v2 frontend boundary for the Legacy-style download workbench.

## Scope

- The frontend owns forms, task display, status rendering, and result navigation.
- Python owns media operations, URL validation, filesystem safety, subprocess execution, and summary generation.
- The local API adapter is now the frontend boundary: preview plans are dry-run style contract checks, while submitted tasks are persisted in the local task registry.

## Endpoints

### `GET /api/doctor`

Returns tool availability for the right status panel.

```json
[
  { "name": "ffmpeg", "available": true, "path": "C:/ffmpeg/bin/ffmpeg.exe" },
  { "name": "ffprobe", "available": true, "path": "C:/ffmpeg/bin/ffprobe.exe" },
  { "name": "yt-dlp", "available": true, "path": "C:/Windows/System32/yt-dlp.exe" }
]
```

### `GET /api/system/metrics`

Returns a best-effort runtime snapshot for the right status panel. CPU, memory,
network speed, uptime, and platform-specific GPU data should degrade quietly when
the current host cannot provide a metric.

```json
{
  "runtime": { "uptime_seconds": 91 },
  "system": {
    "cpu_percent": 12.5,
    "memory_percent": 68.1,
    "gpu_percent": 45.0,
    "gpu_available": true,
    "gpu_detail": "macOS IOAccelerator"
  },
  "network": {
    "upload": { "text": "12 KB/s" },
    "download": { "text": "1.2 MB/s" },
    "upload_bytes_per_sec": 12288,
    "download_bytes_per_sec": 1258291
  }
}
```

### `GET /api/workspace`

Returns the current project workspace used as the default starting point for
path pickers.

```json
{
  "workspace": { "project_root": "/Users/ben/Project/Code/MediaTools-v2" },
  "project_root": "/Users/ben/Project/Code/MediaTools-v2"
}
```

### `GET /api/filebrowser/disks`

Returns local filesystem roots for the directory picker.

```json
{
  "ok": true,
  "disks": [
    { "name": "根目录 /", "path": "/", "total": 994662584320, "used": 120000000000, "free": 874662584320 }
  ]
}
```

### `POST /api/filebrowser/list`

Lists folders and files under a directory for the path picker.

```json
{ "directory": "/Users/ben/Downloads" }
```

```json
{
  "ok": true,
  "path": "/Users/ben/Downloads",
  "directories": [],
  "files": []
}
```

### `POST /api/filebrowser/directories`

Creates a directory selected from the path picker.

```json
{ "path": "/Users/ben/Downloads/MediaTools" }
```

```json
{ "ok": true, "path": "/Users/ben/Downloads/MediaTools" }
```

### `POST /api/fetch/plan`

Returns the validated CLI-equivalent plan without network access.

```json
{
  "urls": ["https://example.com/video"],
  "output_dir": "downloads",
  "subtitles_only": false,
  "write_subs": true,
  "write_auto_subs": true,
  "sub_langs": "original",
  "convert_subs": "srt",
  "preset": "mp4",
  "cookies_from_browser": "chrome",
  "name_template": "{lang}-{author}-{title}-{platform}.{ext}",
  "max_concurrent": 1,
  "dry_run": true,
  "video_codec": "h264",
  "audio_codec": "aac",
  "video_bitrate": null,
  "audio_bitrate": null
}
```

### `POST /api/fetch/tasks`

Submits a validated download task and returns a task record.

When `video_codec` or `audio_codec` is provided, the downloader fetches the
highest quality format first, then auto-transcodes with ffmpeg if the codec
doesn't match. Accepted codec names: `h264`, `h265`/`hevc`, `av1`, `aac`,
`opus`, `mp3`, or any ffmpeg encoder name (e.g. `libx264`).

```json
{
  "task_id": "fetch-20260625-001",
  "status": "pending",
  "url_count": 1
}
```

### `GET /api/fetch/tasks`

Returns active and recent task rows for the workbench list.

```json
[
  {
    "id": "fetch-20260625-001",
    "title": "Example Video",
    "source_url": "https://example.com/video",
    "status": "running",
    "progress": 0.42,
    "stage": "downloading",
    "created_at": 1782390000.0,
    "updated_at": 1782390002.0,
    "started_at": 1782390001.0,
    "completed_at": null,
    "params": {
      "urls": ["https://example.com/video"],
      "url": "https://example.com/video"
    },
    "result": {},
    "output_files": []
  }
]
```

### `POST /api/fetch/tasks/{task_id}/cancel`

Marks a pending or running task as cancelled in the local task registry.
The current subprocess-backed downloader may still finish its underlying `yt-dlp`
process; a future process-runner change is required for hard cancellation.

```json
{
  "ok": true,
  "task": {
    "id": "fetch-20260625-001",
    "status": "cancelled",
    "stage": "cancel_requested"
  }
}
```

### `DELETE /api/fetch/tasks/{task_id}`

Deletes one task record from the local task registry.

```json
{ "ok": true, "deleted": 1 }
```

### `DELETE /api/fetch/tasks`

Deletes completed, failed, cancelled, paused, or partial task records. When
`task_ids` is provided, only matching finished records are removed.

```json
{ "task_ids": ["fetch-20260625-001"] }
```

```json
{ "ok": true, "deleted": 1 }
```

## Migration Rule

Legacy UI source may provide layout, density, component structure, visual rhythm, and copy. Legacy API calls, AI analysis hooks, file manager coupling, and platform-specific automation remain out of the first v2 frontend.
