### H-002：最小依赖可行性
- **假设：** 媒体工具可以只依赖系统 ffmpeg + 轻量图像库
- **验证方式：** 实现核心功能后评估依赖数量
- **状态：** 待验证

### H-003：CLI 优先架构足够
- **假设：** 不需要 Web UI，CLI + 脚本集成即可满足需求
- **验证方式：** 用户反馈；实际使用场景
- **状态：** 待验证

### L-001：忽略规则验证以 `git ls-files --others --exclude-standard` 为准
- **时间：** 2026-06-24 11:55:05 +08:00
- **背景：** 工作区存在 Legacy 残留、运行产物和构建缓存，普通 `git status` 输出可能受命令执行时机影响。
- **经验：** 修改 `.gitignore` 后，使用 `git status --short --branch` 查看预期修改文件，再用 `git ls-files --others --exclude-standard` 确认是否仍有未被忽略的未跟踪文件。
- **状态：** 已采纳

### L-002：支持 `python -m package` 需要 `__main__.py`
- **时间：** 2026-06-24 12:10:01 +08:00
- **背景：** 最小 CLI 初版只配置了 console script，导致 `python -m mediatools` 报 `No module named mediatools.__main__`。
- **经验：** README 中若提供 `python -m package` 命令，必须添加 `src/<package>/__main__.py` 并用测试覆盖模块执行入口。
- **状态：** 已采纳

### L-003：极小入口文件可用 per-file ignore 精准豁免 ruff I001
- **时间：** 2026-06-24 12:10:01 +08:00
- **背景：** `src/mediatools/__main__.py` 仅包含入口胶水导入，但 ruff 在本机环境持续报 `I001`。
- **经验：** 保留全局 import 排序规则，只对入口胶水文件使用 `[tool.ruff.lint.per-file-ignores]` 精准豁免，避免为低价值格式问题牺牲整体质量门。
- **状态：** 已采纳
