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

## 修复

- `src/mediatools/core/fetch_resolution.py`：`original` 展开出的语言标签改为锚定正则，例如 `^zh\-CN\-orig$,^zh\-CN$,^zh\-orig$,^zh$`。
- `src/mediatools/core/fetch.py`：失败摘要改为记录已解析后的命令，避免日志继续显示未解析的 `original`。
- `tests/test_fetch_resolution.py`：新增 `zh-CN` 回归测试，确保不会再保留裸 `zh-CN` 片段。

## 验证

- 定向测试：`pytest tests/test_fetch_resolution.py tests/test_fetch.py tests/test_fetch_args.py tests/test_api_server.py`，81 passed。
- 标准验证：`python scripts/verify.py`，Python 245 passed / 6 skipped，ruff 通过，前端 61 passed / 3 skipped，build 通过，doctor 找到 `ffmpeg`、`ffprobe`、`yt-dlp`。

## 后续

旧失败任务留下的 `.vtt` 是上一次过宽匹配产生的下载残留，修复不会自动删除用户输出目录内容。再次下载前可手动清理该目录，避免新旧产物混在一起。
