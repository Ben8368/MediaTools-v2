# 2026-06-27 YouTube 原语言字幕正则匹配修复

## 背景

用户在轻前端添加 YouTube 下载任务：

- URL：`https://youtu.be/-28MFc9TMw0?si=kPw_JjDvpygGV-Q_`
- 输出目录：项目内 `downloads`
- 参数记录：`write_subs=true`、`write_auto_subs=true`、`sub_langs=original`、`convert_subs=srt`、`cookies_from_browser=chrome`

任务最终失败，但 `downloads` 下留下 74 个 `.vtt` 文件，文件名形如：

```text
UN-Mediastorm影视飓风-“超微距”下的瑞士长什么样？-Youtube.kk-zh-CN.vtt
UN-Mediastorm影视飓风-“超微距”下的瑞士长什么样？-Youtube.en-zh-CN.vtt
UN-Mediastorm影视飓风-“超微距”下的瑞士长什么样？-Youtube.zh-CN.vtt
```

任务记录中的错误为：

```text
ERROR: Unable to download video subtitles for 'ky-zh-CN': HTTP Error 429: Too Many Requests
```

## 根因

`yt-dlp --sub-langs` 接收的是正则表达式列表，而不是严格语言码列表。

旧逻辑在 `--sub-langs original` 探测到 `zh-CN` 时展开为：

```text
zh-CN-orig,zh-CN,zh-orig,zh
```

这些裸字符串会作为正则片段匹配字幕标签，因此 `zh-CN` 不只匹配原始 `zh-CN`，还会匹配 `kk-zh-CN`、`en-zh-CN`、`ky-zh-CN` 等“翻译成中文”的字幕标签，导致 yt-dlp 连续请求大量机器翻译字幕，最终被 YouTube 限流。

第二轮真实反馈继续暴露一个更严重的策略问题：当 `yt-dlp --print language` 探测失败时，旧逻辑会把 `original` 降级为 `all`。这等于在“只要原语言”的用户意图下下载所有字幕。与此同时，单次 yt-dlp 命令中字幕处理可能先于视频下载执行，字幕 429 会让整个任务失败，导致最关键的视频文件也没有产出。

## 修复

- `src/mediatools/core/fetch_resolution.py`：`original` 展开出的语言标签改为锚定正则，例如 `^zh\-CN\-orig$,^zh\-CN$,^zh\-orig$,^zh$`。
- `src/mediatools/core/fetch_resolution.py`：探测失败时不再降级为 `all`；普通视频任务会禁用字幕并继续下载视频。
- `src/mediatools/core/fetch.py`：失败摘要改为记录已解析后的命令，避免日志继续显示未解析的 `original`。
- `src/mediatools/core/fetch.py`：普通“视频 + 字幕”任务拆成两步，先下载视频，再以 best-effort 方式下载字幕；字幕下载失败后保留视频任务成功和视频产物登记。
- `src/mediatools/core/fetch.py`：字幕-only + `original` 且探测失败时明确失败，拒绝下载全部字幕。
- `tests/test_fetch_resolution.py`：新增 `zh-CN` 回归测试，确保不会再保留裸 `zh-CN` 片段；更新探测失败行为为禁用字幕。
- `tests/test_fetch.py`：新增视频优先、字幕 429 不阻塞视频、探测失败只下载视频、字幕-only 探测失败明确失败的回归测试。

## 验证

- 第一轮定向测试：`pytest tests/test_fetch_resolution.py tests/test_fetch.py tests/test_fetch_args.py tests/test_api_server.py`，81 passed。
- 第二轮定向测试：`pytest tests/test_fetch.py tests/test_fetch_resolution.py tests/test_fetch_args.py`，45 passed。
- 标准验证：`python scripts/verify.py`，Python 248 passed / 6 skipped，ruff 通过，前端 61 passed / 3 skipped，build 通过，doctor 找到 `ffmpeg`、`ffprobe`、`yt-dlp`。

## 后续

旧失败任务留下的 `.vtt` 是上一次过宽匹配或探测失败降级 `all` 产生的下载残留，修复不会自动删除用户输出目录内容。再次下载前可手动清理该目录，避免新旧产物混在一起。运行中的 API 进程不会热更新 Python 代码，修复后需要重启后端/统一启动脚本。
