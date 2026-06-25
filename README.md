# MediaTools v2

跨平台媒体工具集 - 精简重构版

> **提示**：AI 工具开发者请先阅读 [`AGENTS.md`](AGENTS.md)

## 🎯 项目目标

- **小巧精悍**：核心功能，最小依赖
- **跨平台**：Windows / macOS / Linux 统一体验
- **易用性**：简单直观的 API 和 CLI

## 🚧 开发中

项目正在重构中，当前阶段：

- [x] 治理体系建立（01-05 文档 + AGENTS.md）
- [x] 技术栈决策：Python CLI 优先
- [x] 最小 CLI 脚手架验证
- [x] Phase 1 核心架构（路径、日志、错误处理、配置）
- [x] Phase 2 首批 MVP 功能迁移与真实样本验收
- [x] Phase 3 下载工作流增强与字幕生产样本打磨
- [ ] Legacy 风格轻前端准备

详见 [`REFACTOR.md`](REFACTOR.md)

## 🧰 技术栈

- Python 3.11+
- 标准库 `argparse` 作为 CLI 入口
- `pyproject.toml` 管理项目元数据、命令入口和开发依赖
- `pytest` 用于测试
- `ruff` 用于格式/静态检查
- 系统 `ffmpeg` / `ffprobe` / `yt-dlp` 作为媒体处理外部工具，不 vendor 第三方源码

## ✅ 首批 MVP CLI

当前已实现首批 CLI 能力：

```powershell
python -m mediatools probe input.mp4 --json
python -m mediatools subtitle convert input.vtt output.srt
python -m mediatools encode input.mp4 output.mp4 --video-codec libx265 --audio-codec aac
python -m mediatools encode input.mp4 audio.mp3 --extract-audio
python -m mediatools screenshot input.mp4 shot.png --time 00:00:05
python -m mediatools screenshot input.mp4 frames --interval 5
python -m mediatools fetch "https://example.com/video" downloads --write-subs
python -m mediatools fetch "https://example.com/video" downloads --write-auto-subs --sub-langs en
python -m mediatools fetch downloads --input-file urls.txt --subtitles-only --sub-langs original --convert-subs srt --summary-json downloads/summary.json
python -m mediatools fetch downloads --input-file urls.txt --dry-run
python -m mediatools fetch downloads --input-file urls.txt --write-info-json --download-archive downloads/archive.txt --summary-json downloads/summary.json
python -m mediatools fetch "https://example.com/playlist" downloads --cookies-from-browser safari --preset mp4
python -m mediatools fetch "https://example.com/video" downloads --preset mp4
python -m mediatools fetch "https://example.com/video" downloads --preset mp4 --name-template "{platform}-{title}-{author}-{lang}.{ext}" --name-language EN
```

`probe`、`encode`、`screenshot` 需要本机 PATH 中可找到 `ffmpeg`/`ffprobe`；
`fetch` 需要本机 PATH 中可找到 `yt-dlp`，并只接受 `http` / `https` URL。默认使用 `--preset mp4`，优先得到 H264+AAC+MP4；单条下载默认超时为 3600 秒，如需长任务不限时可传 `--timeout 0`；`--write-subs` 下载人工字幕，`--write-auto-subs` 下载自动字幕；`--subtitles-only` 只下载字幕、不下载视频，若未显式指定字幕类型，会默认同时尝试人工字幕和自动字幕；`--sub-langs original --convert-subs srt` 可下载原语言字幕并转为 SRT；`--input-file` 支持一行一个 URL 的批量任务；`--dry-run` 只预览计划；`--summary-json` 输出结构化结果，便于后续前端读取。若站点要求登录态或反机器人确认，可显式传 `--cookies-from-browser safari|chrome|firefox` 或 `--cookies path/to/cookies.txt`；二者互斥，且不会默认读取浏览器登录态。

下载默认使用友好命名模板 `{lang}-{author}-{title}-{platform}.{ext}`。真实下载前会根据链接自动探测语言并映射为短码，例如 `KR`、`EN`、`JP`、`SC`、`TC`、`AR`、`PT`；作者、标题、平台名由 yt-dlp 元数据自动填充。`--name-template` 可调整字段顺序，支持 `{lang}`、`{author}`、`{title}`、`{platform}`、`{id}`、`{ext}`；`--name-language` 可手动覆盖语言码。默认传递 `--windows-filenames` 给 yt-dlp，以处理作者名和标题中本地文件系统不可用的字符；如需关闭可用 `--no-windows-filenames`。高级用法仍可用原始 yt-dlp `--output-template`，它会覆盖友好模板；模板必须相对输出目录，不能使用绝对路径或 `..` 路径片段。

## 🚀 本地开发

一键客观验证（AI / CI / 本地共用）：

```powershell
python scripts/verify.py
```

`verify.py` 会依次执行：Python 文件 500 行硬限制检查 → 安装 dev 依赖 → pytest → ruff → CLI 版本 → doctor 环境报告（含外部工具与 PATH 信息）。

macOS 推荐先使用 Homebrew 或 pyenv 的 Python 3.11+ 创建虚拟环境，再运行验证；不要使用 Apple Command Line Tools 自带的 Python 3.9，也不要向 Homebrew 的全局 Python 环境直接安装包：

```bash
/opt/homebrew/bin/python3 -m venv .venv
source .venv/bin/activate
python scripts/verify.py
```

也可分步执行：

```powershell
python -m pip install -e ".[dev]"
python -m mediatools --version
python -m mediatools doctor
python -m pytest
python -m ruff check .
```

Linux / macOS 等价命令相同（将 `python` 换为本机 Python 3.11+ 解释器即可）。

安装后也可以使用 console script：

```powershell
mediatools --version
mediatools doctor --json
```

## 📚 文档导航

### 开发者文档
- [`AGENTS.md`](AGENTS.md) - AI 工具统一入口
- [`01_Project_Plan.md`](01_Project_Plan.md) - 项目蓝图
- [`02_AI_Rules.md`](02_AI_Rules.md) - AI 行为准则
- [`03_Context.md`](03_Context.md) - 实时状态快照
- [`04_Features.md`](04_Features.md) - 功能评估池
- [`05_Lessons.md`](05_Lessons.md) - 经验与避坑

### Git 工作流
- [`docs/AI_COAUTHOR_SETUP.md`](docs/AI_COAUTHOR_SETUP.md) - AI 工具 Co-Author 自动追踪
- [`docs/AI_COMMIT_GUIDE.md`](docs/AI_COMMIT_GUIDE.md) - Commit 规范说明

### 重构计划
- [`REFACTOR.md`](REFACTOR.md) - 重构策略与迁移计划
- [`docs/UI_COMPAT.md`](docs/UI_COMPAT.md) - Legacy UI 兼容基线

## 📝 License

MIT

---

**Legacy Version**: [MediaTools](https://github.com/Ben8368/MediaTools) （仅作参考）
