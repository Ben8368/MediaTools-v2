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
- [ ] Phase 2 功能迁移与实现

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
```

`probe`、`encode`、`screenshot` 需要本机 PATH 中可找到 `ffmpeg`/`ffprobe`；
`fetch` 需要本机 PATH 中可找到 `yt-dlp`，并只接受 `http` / `https` URL。`--write-subs` 下载人工字幕，`--write-auto-subs` 下载自动字幕。

## 🚀 本地开发

一键客观验证（AI / CI / 本地共用）：

```powershell
python scripts/verify.py
```

`verify.py` 会依次执行：安装 dev 依赖 → pytest → ruff → CLI 版本 → doctor 环境报告（含外部工具与 PATH 信息）。

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

## 📝 License

MIT

---

**Legacy Version**: [MediaTools](https://github.com/Ben8368/MediaTools) （仅作参考）
