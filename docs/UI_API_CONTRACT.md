# Light Frontend API Contract

This document defines the first v2 frontend boundary for the Legacy-style download workbench.

## Scope

- The frontend owns forms, task display, status rendering, and result navigation.
- Python owns media operations, URL validation, filesystem safety, subprocess execution, and summary generation.
- The first frontend version may preview CLI-equivalent plans before a local API adapter exists.

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
  "name_template": "{lang}-{author}-{title}-{platform}.{ext}",
  "max_concurrent": 1,
  "dry_run": true
}
```

### `POST /api/fetch/tasks`

Submits a validated download task and returns a task record.

```json
{
  "task_id": "fetch-20260625-001",
  "status": "queued",
  "summary_json": "downloads/summary.json"
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
    "output_files": []
  }
]
```

## Migration Rule

Legacy UI source may provide layout, density, component structure, visual rhythm, and copy. Legacy API calls, AI analysis hooks, file manager coupling, and platform-specific automation remain out of the first v2 frontend.
