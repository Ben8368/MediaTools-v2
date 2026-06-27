# MediaTools v2 - 下载工作台使用指南

## 🚀 快速开始

### 1. 一键启动后端和前端

```bash
python scripts/start.py
```

默认会启动：

- API: `http://127.0.0.1:7860`
- 前端: `http://127.0.0.1:5173`

如需只启动后端：

```bash
python scripts/start.py --backend-only
```

如需指定端口，可通过启动脚本传递：

```bash
python scripts/start.py --api-port 8000 --frontend-port 5174
```

启动脚本会把 API 地址通过 `VITE_MEDIATOOLS_API_TARGET` 注入 Vite proxy，通常不需要手动改配置文件。

### 2. 手动启动后端 API 服务器

```bash
# 使用默认端口 7860
python -m mediatools serve

# 或指定其他端口
python -m mediatools serve --port 8000
```

服务器启动后会显示：
```
[api] MediaTools API server listening on http://127.0.0.1:7860
```

### 3. 手动启动前端开发服务器

打开新的终端窗口：

```bash
cd frontend
npm run dev
```

前端会在 `http://localhost:5173` 启动，默认代理到 `http://localhost:7860`。若手动后端端口不是 7860，可临时设置环境变量：

```bash
cd frontend
VITE_MEDIATOOLS_API_TARGET=http://localhost:8000 npm run dev
```

### 4. 访问下载工作台

浏览器打开 http://localhost:5173

点击左侧导航栏的"下载"图标即可进入下载工作台。

---

## 📦 功能特性

### 当前支持的功能

✅ **任务提交**
- 支持单个或多个 URL（每行一个）
- 自动检测视频平台
- 可选下载字幕（人工 + 自动字幕）
- 通过目录选择器自定义保存目录，可浏览本机目录并新建文件夹
- 可显式选择 Chrome / Safari / Firefox 登录态，用于 YouTube 登录或反机器人校验
- 支持格式预设、自定义文件命名、并发数

✅ **任务列表**
- 实时任务状态（每 2 秒自动刷新）
- 任务进度显示
- 按状态分类（全部/下载中/已完成/失败/已暂停或取消）
- 搜索功能
- 任务 JSON 持久化
- 任务层取消、删除单条记录、批量清空完成/失败/取消记录
- 基于原任务参数重新提交的重试操作

✅ **下载配置**
- 默认 H264+AAC+MP4 格式
- 自动下载原语言字幕并转换为 SRT
- 自动清理 YouTube rolling 重复字幕
- 友好文件命名（语言-作者-标题-平台.ext）

✅ **运行状态**
- 右侧状态面板显示 ffmpeg、ffprobe、yt-dlp 可用性
- 显示 CPU、内存、GPU（best-effort）、网络速率和后端累计运行时间
- 刷新页面后后端 uptime 不会归零

### 暂未实现的功能

⏳ **计划中**（v2 后续版本）
- 硬杀底层 `yt-dlp` 子进程（当前取消是任务层状态标记）
- WebSocket/SSE 实时推送
- 前端字幕-only 专用表单
- 视频切片、资产扫描 / 搜索 / 统计

❌ **暂不纳入当前 CLI MVP**
- AI 字幕分析
- Photoshop 自动化
- After Effects 集成
- 完整文件管理器

---

## 🎨 界面说明

### 左侧边栏
- **全部**：显示所有任务
- **下载中**：正在进行的任务
- **已完成**：成功完成的任务
- **失败**：出错的任务
- **已暂停/取消**：显示暂停或取消记录

### 中间主区域
- **添加任务**：点击 `+` 按钮打开表单
- **任务列表**：显示所有任务及状态
- **搜索栏**：按标题、URL 搜索任务
- **工具栏**：根据选择的任务显示停止、重试、删除记录等操作

### 右侧状态面板
- **运行指标**：CPU、内存、GPU、网络速率和后端累计运行时间
- **服务状态**：ffmpeg、ffprobe、yt-dlp 的 PATH 探测结果
- **活动任务**：显示正在排队或运行的下载任务，并可发起任务层取消

---

## 📝 使用示例

### 示例 1：下载单个 YouTube 视频（带字幕）

1. 点击 `+` 添加任务
2. 输入 URL：
   ```
   https://www.youtube.com/watch?v=dQw4w9WgXcQ
   ```
3. 平台选择"自动检测"
4. 字幕选择"下载字幕"
5. 若 YouTube 要求登录或机器人验证，在"登录态"选择已登录的浏览器
6. 可点击"选择目录"指定保存路径；留空则使用默认 `downloads`
7. 点击"确认添加"

结果：
- 视频：`downloads/EN-RickAstley-NeverGonnaGiveYouUp-youtube.mp4`
- 字幕：`downloads/EN-RickAstley-NeverGonnaGiveYouUp-youtube.srt`

### 示例 2：批量下载多个视频

1. 点击 `+` 添加任务
2. 输入多个 URL（每行一个）：
   ```
   https://www.youtube.com/watch?v=dQw4w9WgXcQ
   https://www.youtube.com/watch?v=jNQXAC9IVRw
   https://www.youtube.com/watch?v=L_jWHffIx5E
   ```
3. 确认添加

会创建一个批量任务。默认串行下载；若需要并发，可在表单或 API 中设置 `max_concurrent`，实际并发不会超过配置文件中的 `max_concurrent_downloads` 上限。

### 示例 3：只下载字幕（不下载视频）

当前前端暂不支持，可通过 CLI 实现：

```bash
python -m mediatools fetch "https://www.youtube.com/watch?v=dQw4w9WgXcQ" \
  --output-dir downloads --subtitles-only --sub-langs original --convert-subs srt
```

---

## 🔧 配置

### 后端配置

配置文件位置：
- **Windows**: `%LOCALAPPDATA%\mediatools\config.json`
- **macOS**: `~/Library/Application Support/mediatools/config.json`
- **Linux**: `~/.config/mediatools/config.json`

示例配置：
```json
{
  "max_concurrent_downloads": 2
}
```

### 前端配置

前端使用 Vite proxy 自动转发 API 请求到 `localhost:7860`。推荐通过 `python scripts/start.py --api-port ... --frontend-port ...` 管理端口；启动脚本会自动传递 API 地址。

手动启动前端时也可以使用环境变量：

```bash
cd frontend
VITE_MEDIATOOLS_API_TARGET=http://localhost:8000 npm run dev
```

---

## 🐛 故障排除

### 问题 1：前端无法连接后端

**症状**：任务列表为空，提交任务失败

**原因**：后端 API 服务器未启动

**解决**：
```bash
python scripts/start.py
```

### 问题 2：端口被占用

**症状**：
```
Error: Port 7860 is already in use
```

**解决**：
```bash
python scripts/start.py --api-port 8000 --frontend-port 5174
```

### 问题 3：任务提交后看不到进度

**症状**：任务提交成功但列表中没有显示

**原因**：任务列表每 2 秒轮询一次，或后端写入任务记录时出现错误

**解决**：
1. 等待 2-3 秒（自动刷新间隔）
2. 检查后端日志是否有 `[api]` 或下载错误
3. 刷新浏览器页面

### 问题 4：下载失败

**症状**：任务状态显示 "failed"

**常见原因**：
- yt-dlp 未安装或不在 PATH
- 网络问题
- YouTube 要求登录或机器人验证（需要显式使用浏览器登录态）

**解决**：
```bash
# 检查 yt-dlp
python -m mediatools doctor

# 使用浏览器 cookies
python -m mediatools fetch "URL" --output-dir downloads --cookies-from-browser chrome
```

前端下载工作台中，可在添加任务表单的"登录态"下拉框选择 `Chrome`、`Safari` 或 `Firefox`。该选项不会默认读取浏览器登录态，只有显式选择后才会传给 `yt-dlp`。

---

##  API 端点

v2 当前实现的 API 端点：

### `GET /api/doctor`
返回工具状态（ffmpeg、ffprobe、yt-dlp）

### `GET /api/system/metrics`
返回 CPU、内存、GPU、网络速率和后端 uptime 的 best-effort 快照。

### `POST /api/fetch/plan`
验证下载参数（dry-run）

### `POST /api/fetch/tasks`
提交下载任务

**请求体示例**：
```json
{
  "urls": ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"],
  "output_dir": "downloads",
  "write_subs": true,
  "write_auto_subs": true,
  "sub_langs": "original",
  "convert_subs": "srt",
  "preset": "mp4",
  "max_concurrent": 1
}
```

**响应示例**：
```json
{
  "task_id": "fetch-1719302400-abc123",
  "status": "pending",
  "url_count": 1
}
```

### `GET /api/fetch/tasks`
获取任务列表

**响应示例**：
```json
[
  {
    "id": "fetch-1719302400-abc123",
    "title": "Never Gonna Give You Up",
    "source_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "status": "completed",
    "progress": 1.0,
    "stage": "completed",
    "output_files": [
      "downloads/EN-RickAstley-NeverGonnaGiveYouUp-youtube.mp4",
      "downloads/EN-RickAstley-NeverGonnaGiveYouUp-youtube.srt"
    ]
  }
]
```

### `POST /api/fetch/tasks/<task_id>/cancel`
请求取消任务。当前是任务层取消标记，已经进入外部 `yt-dlp` 调用的子进程不会被强制杀死。

### `DELETE /api/fetch/tasks/<task_id>`
删除单条任务记录。

### `DELETE /api/fetch/tasks`
清空已完成、失败、取消、暂停或部分完成的任务记录；可传 `task_ids` 限定要清理的记录。

---

## 🚧 已知限制

1. **取消不是硬杀子进程**：当前取消会标记任务并阻止后续状态更新；若要强杀正在运行的 `yt-dlp`，需要后续重构外部进程封装。
2. **实时进度仍是轮询**：当前前端轮询任务状态；WebSocket/SSE 推送需等任务进度模型进一步稳定。
3. **前端字幕-only 入口仍待完善**：CLI 已支持 `--subtitles-only`，前端可通过后续表单补齐更完整的字幕-only 工作流。
4. **Legacy 大文件仍处于隔离状态**：部分旧样式和组件文件已通过验证脚本显式隔离，后续需逐步拆分或移出主源码路径。

这些限制将在后续版本中改进。

---

## 📚 相关文档

- [项目 README](../README.md) - 完整项目介绍
- [CLI 使用文档](../README.md#首批-mvp-cli) - 命令行用法
- [API 契约](UI_API_CONTRACT.md) - 完整 API 规范
- [优化计划](../OPTIMIZATION_PLAN.md) - 后续开发路线图

---

## 💡 开发技巧

### 调试后端

启动服务器时会输出日志：
```bash
python -m mediatools serve
# 观察 [api] 前缀的日志输出
```

### 调试前端

浏览器开发者工具 → Network 标签 → 查看 API 请求

### 手动测试 API

```bash
# 测试 doctor 端点
curl http://localhost:7860/api/doctor

# 提交任务
curl -X POST http://localhost:7860/api/fetch/tasks \
  -H "Content-Type: application/json" \
  -d '{"urls":["https://www.youtube.com/watch?v=dQw4w9WgXcQ"],"output_dir":"downloads","preset":"mp4"}'

# 查询任务
curl http://localhost:7860/api/fetch/tasks

# 取消任务
curl -X POST http://localhost:7860/api/fetch/tasks/fetch-1719302400-abc123/cancel

# 删除单条记录
curl -X DELETE http://localhost:7860/api/fetch/tasks/fetch-1719302400-abc123

# 清空完成/失败/取消记录
curl -X DELETE http://localhost:7860/api/fetch/tasks
```

---

**版本**：v2 MVP  
**更新日期**：2026-06-27
