# AI 行为准则

## 1. 总则

- 遵循 `AGENTS.md` 工作流：思考 → 编码 → 红绿灯审查 → **AI 自动验证** → 更新文档 → 推进任务。
- 优先最小可行改动，不引入与任务无关的重构。
- 所有路径、编码、外部命令调用必须考虑 Windows / macOS / Linux 一致性。
- **客观验证由 AI 执行**，不要求用户重复跑命令；用户只关注功能好不好用、能不能用。

## 2. 目录结构

```
src/mediatools/
  __init__.py          # 包版本
  __main__.py          # python -m mediatools 入口
  cli.py               # argparse 命令注册与调度
  core/                # 与 I/O、CLI 无关的纯逻辑
    paths.py           # 跨平台路径工具
tests/                 # pytest 测试，镜像 core/ 模块命名
scripts/
  verify.py            # 标准客观验证入口（AI / CI / 人工共用）
```

约定：
- **CLI 层**（`cli.py`）只做参数解析、输出格式、调用 core。
- **Core 层**（`core/`）不直接 `print`，不启动子进程，便于单元测试。
- **命令实现**后续放 `commands/` 或按功能分子包，不在 `cli.py` 堆业务逻辑。

## 3. Python 编码风格

- 目标版本：Python 3.11+；使用 `from __future__ import annotations`。
- 格式化与静态检查：`ruff`（`E`、`F`、`I`、`UP`、`B` 规则集）。
- 类型注解：公共函数必须有参数与返回值注解；复杂结构用 `dict[str, object]` 等内置泛型。
- 命名：`snake_case` 函数/变量，`PascalCase` 类，`UPPER_SNAKE` 常量。
- 文件读写显式 `encoding="utf-8"`。
- 禁止：占位 `pass` 冒充实现、无 issue 关联的大段注释代码、硬编码 `\` 或 `/` 拼路径。

## 4. 路径处理

- **必须**使用 `pathlib.Path`，通过 `mediatools.core.paths` 提供的工具函数操作路径。
- **禁止**字符串拼接路径分隔符（`os.path.join` 仅在与第三方 API 对接且无法避免时使用）。
- 用户输入路径在进入文件操作前须 `normalize()`；写入操作前用 `is_safe_child()` 防止目录穿越。
- 工作区、输出目录、缓存目录的路径约定在 Phase 1 配置模块确定前，测试中使用 `tmp_path` fixture。

## 5. 子进程与外部工具

- 调用 `ffmpeg` 等外部工具前，用 `shutil.which()` 探测是否可用（参考 `doctor` 命令）。
- 使用 `subprocess.run` / `subprocess.Popen` 时：
  - 显式传入参数列表，**禁止** `shell=True`。
  - 捕获超时与返回码，错误信息对用户可读。
- 不把第三方可执行文件 vendor 进仓库；依赖用户本机或 PATH 中的系统工具。

## 6. 错误处理

- Core 层抛标准异常（`ValueError`、`FileNotFoundError` 等）或自定义轻量异常；CLI 层统一转换为用户可读消息。
- 不向用户暴露完整堆栈，除非 `--verbose` 类调试开关（后续引入）。
- 文件不存在、权限不足、外部命令缺失须有明确降级或报错路径，禁止静默失败。

## 7. 依赖引入

引入新的运行时依赖前，在 PR/变更说明中回答：

1. 标准库能否实现？
2. 是否跨平台维护良好？
3. 许可证是否兼容 MIT？
4. 是否可用系统工具替代？

当前策略：`dependencies = []`，仅 dev 依赖 `pytest` 和 `ruff`。

## 8. 测试与验证

### 客观验证（AI / CI 自动）

改码后 **AI 必须自行执行**：

```bash
python scripts/verify.py
```

`verify.py` 覆盖：可编辑安装、pytest、ruff、CLI 版本、doctor 环境报告（含 ffmpeg / console script PATH 信息）。

- 本地通过后，推送并以 **CI 绿灯** 作为跨平台验收依据。
- 全绿 → AI 可直接将 `04_Features.md` 标为 `[已完成]` 并更新 `03_Context.md`。
- **禁止**把上述命令转交给用户重复执行。

### 主观验收（用户）

仅以下情况需要用户介入：

- 功能体验：好不好用、输出是否符合预期
- 业务判断：MVP 范围、迁移优先级
- AI/CI 失败且 AI 无法自行修复时

### 测试约定

- 框架：`pytest`；测试文件命名 `test_<module>.py`。
- Core 逻辑须有单元测试；CLI 用 `capsys` 或子进程 smoke test。
- 路径相关测试使用 `tmp_path`，不依赖本机固定目录。
- CI 矩阵覆盖 ubuntu / windows / macos。

## 9. 文档同步

变更代码或阶段进度时，同步检查并更新：

| 变更类型 | 需更新的文档 |
| --- | --- |
| 阶段/任务进度 | `03_Context.md`、`01_Project_Plan.md` |
| 功能状态 | `04_Features.md` |
| 重构策略 | `REFACTOR.md` |
| 避坑经验 | `05_Lessons.md` |
| 用户可见命令 | `README.md` |

`03_Context.md` 是实时快照，但**不能**作为其他文档滞后的借口；`REFACTOR.md`、`04_Features.md` 须与之间状态一致。

---

## 10. 红绿灯审查系统 (Traffic Light Audit)

> **核心逻辑**：隐性深度思考，显性简洁输出

### 审查维度（思考层，不输出）

**支柱 I：真实性与上下文**
1. 幻觉检测：引用的 API/路径真实存在？
2. 历史一致性：是否违背架构原则？
3. 用户意图：是否理解真实需求？

**支柱 II：健壮性与工艺**
4. 反惰性：严禁占位实现、TODO 留空
5. 异常路径：文件不存在、网络失败、无权限时怎么办？
6. 跨平台兼容：Windows/macOS/Linux 都能跑？

**支柱 III：架构与未来**
7. 熵增控制：是否重复造轮子？
8. 解耦原则：模块职责是否清晰？
9. 可测试性：能否编写单元测试？

### 输出格式（严格执行）

```markdown
## 🚦 Audit Report

**总体评价：** [ 🔴 阻断 / 🟡 可通行 / 🟢 完美 ]

**1. 🔴 阻断项（必须修复）:**
* (若无则写：无)

**2. 🟡 优化项（建议暂时忽略）:**
* (若无则写：无)

**3. 👮 指挥官建议:**
* (基于当前阶段给出明确指令)
```

### 分级标准
- 🔴 **红灯**：破坏架构、跨平台问题、安全漏洞、硬编码路径
- 🟡 **黄灯**：性能隐患、测试覆盖不足、文档不同步
- 🟢 **绿灯**：满足需求，无明显风险
